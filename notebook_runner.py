# Jembatan web <-> notebook: menjalankan sel Web_revisi.ipynb dan mengambil hasilnya
import base64
import io
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # gambar dibuat di memori, tanpa membuka jendela


class NotebookPipeline:
    # Nomor sel notebook yang dijalankan per tahap (mulai dari 0)
    # PENTING: kalau sel notebook ditambah/dihapus, nomor di sini harus disesuaikan
    CELLS_PERSIAPAN = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    CELLS_ARIMA = [11, 12, 13, 14, 15, 16, 17]
    CELLS_LGBM = [18, 19, 20, 21, 22, 23, 24]

    def __init__(self):
        folder = Path(__file__).resolve().parent
        self.path = folder / 'Web_revisi.ipynb'
        with self.path.open('r', encoding='utf-8') as f:
            self.notebook = json.load(f)
        self.namespace = {}
        self.gambar_per_cell = {}
        self._reset_namespace()

    # "Meja kerja" bersama: semua variabel hasil sel disimpan di sini
    def _reset_namespace(self):
        self.gambar_per_cell = {}
        self.namespace = {
            '__name__': '__cabaicast_notebook__',
            'display': lambda *args, **kwargs: None,  # display() Jupyter dimatikan
        }

    # Grafik -> PNG -> teks base64 (supaya bisa ditampilkan di web)
    @staticmethod
    def _gambar_ke_base64(fig):
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=125, bbox_inches='tight')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('ascii')

    # Simpan semua grafik yang dibuat sebuah sel, lalu tutup
    def _simpan_gambar_yang_terbuka(self, nomor_cell):
        plt = self.namespace.get('plt')
        if plt is None:
            return
        nomor_figure = list(plt.get_fignums())
        if not nomor_figure:
            return
        self.gambar_per_cell[nomor_cell] = [
            self._gambar_ke_base64(plt.figure(num)) for num in nomor_figure
        ]
        plt.close('all')

    # Jalankan sel-sel notebook berdasarkan nomornya
    def _jalankan_cell(self, daftar_nomor_cell):
        for nomor in daftar_nomor_cell:
            cell = self.notebook['cells'][nomor]
            if cell.get('cell_type') != 'code':
                continue
            kode = ''.join(cell.get('source', []))
            exec(compile(kode, f'{self.path.name}:cell_{nomor}', 'exec'), self.namespace, self.namespace)
            if nomor == 0:
                self.namespace['plt'].show = lambda *a, **k: None  # grafik jangan dibuang
            self._simpan_gambar_yang_terbuka(nomor)

    # Tahap 1: data upload -> persiapan (step 1-4 di web)
    def prepare(self, df_upload):
        self._reset_namespace()
        self.namespace['df'] = df_upload.copy()
        self._jalankan_cell(self.CELLS_PERSIAPAN)
        return self.snapshot_prepare()

    # Tahap 2: rentang orde dari web -> ARIMA (step 5-7)
    def run_arima(self, rentang_orde):
        rentang = {}
        for pasar, r in rentang_orde.items():
            rentang[pasar] = {
                'p': (int(r['p'][0]), int(r['p'][1])),
                'd': (int(r['d'][0]), int(r['d'][1])),
                'q': (int(r['q'][0]), int(r['q'][1])),
            }
        self.namespace['order_ranges_input'] = rentang
        self._jalankan_cell(self.CELLS_ARIMA)
        return self.snapshot_arima()

    # Tahap 3: kandidat lag dari web -> Optuna, LightGBM, hybrid, prediksi (step 8-10)
    def run_lgbm(self, kandidat_lag):
        self.namespace['lag_candidates_input'] = {
            pasar: [int(x) for x in nilai] for pasar, nilai in kandidat_lag.items()
        }
        self._jalankan_cell(self.CELLS_LGBM)
        return self.snapshot_lgbm()

    # Ambil hasil tahap persiapan untuk ditampilkan web
    def snapshot_prepare(self):
        ns = self.namespace
        df = ns['df']
        statistik = {}
        for pasar in ns['pasar_list']:
            data = df[pasar].dropna()
            statistik[pasar] = {
                'n': int(data.size),
                'mean': float(data.mean()),
                'std': float(data.std()),
                'min': float(data.min()),
                'max': float(data.max()),
            }
        return {
            'pasar_list': list(ns['pasar_list']),
            'df': df.copy(),
            'stats': statistik,
            'split_table': ns['split_table_df'].copy(),
            'boxcox_summary': ns['boxcox_summary_df'].copy(),
            'boxcox_lambdas': dict(ns['boxcox_lambdas']),
            'datasets': ns['datasets'],
            'datasets_raw': ns['datasets_raw'],
            'adf_before': ns['adf_before_df'].copy(),
            'adf_compare': ns['adf_compare_df'].copy(),
            'diff_log': ns['diff_log_df'].copy(),
            'baris_dipangkas': int(ns['baris_dipangkas']),
            'tanggal_awal': ns['df'].index.min(),
            'tanggal_akhir': ns['df'].index.max(),
            'd_terpilih': dict(ns['d_terpilih']),
            'diff_results': ns['diff_results'],
            # Gambar per nomor sel
            'fig_raw': self.gambar_per_cell.get(4, []),
            'fig_boxcox': self.gambar_per_cell.get(6, []),
            'fig_acf_train': self.gambar_per_cell.get(8, []),
            'fig_arima_id': self.gambar_per_cell.get(10, []),
        }

    # Ambil hasil tahap ARIMA
    def snapshot_arima(self):
        ns = self.namespace
        return {
            'best_orders': dict(ns['best_orders']),
            'final_orders': dict(ns['final_orders']),
            'maks_lag_pacf': int(ns['MAKS_LAG_PACF']),
            'aic_tables': {p: df.copy() for p, df in ns['aic_tables'].items()},
            'fitted_models': ns['fitted_models'],
            'actuals_dict': {p: v.copy() for p, v in ns['actuals_dict'].items()},
            'forecasts_dict': {p: v.copy() for p, v in ns['forecasts_dict'].items()},
            'arima_eval': ns['arima_eval_df'].copy(),
            'assumptions': ns['assumption_results_df'].copy(),
            'pacf_tables': {p: df.copy() for p, df in ns['pacf_lag_tables'].items()},
            'pacf_significant': ns['pacf_significant_df'].copy(),
            'fig_arima_pred': self.gambar_per_cell.get(13, []),
            'fig_pacf_residual': self.gambar_per_cell.get(16, []),
        }

    # Ambil hasil tahap LightGBM & hybrid
    def snapshot_lgbm(self):
        ns = self.namespace
        return {
            'best_lag': dict(ns['best_lag_optuna']),
            'best_params': {p: dict(v) for p, v in ns['best_params_all_optuna'].items()},
            'optuna_lag_results': ns['optuna_lag_results'],
            'hybrid_forecasts': {p: v.copy() for p, v in ns['hybrid_forecasts_dict'].items()},
            'hybrid_eval': ns['hybrid_eval_df'].copy(),
            'future_tables': {p: df.copy() for p, df in ns['future_prediction_tables'].items()},
            'fig_hybrid': self.gambar_per_cell.get(22, []),
            'fig_future_static': self.gambar_per_cell.get(24, []),
        }
