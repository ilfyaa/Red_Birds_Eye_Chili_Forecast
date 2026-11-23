# Halaman Analisis Harga (/analisis) - upload data, jalankan notebook per tahap
import asyncio
import io
import traceback
import pandas as pd
from nicegui import ui, run

from components.sidebar import build_sidebar
from notebook_runner import NotebookPipeline

# Batas jumlah kolom pasar di file upload
MAKS_PASAR = 6
PAGE_BG = '#eef3e7'
# Kunci & nama 10 step
STEP_META = [
    ('s1', 'Data Awal'),
    ('s2', 'Split Data'),
    ('s3', 'Uji Stasioner Varians'),
    ('s4', 'Uji Stasioner Mean'),
    ('s5', 'Pemodelan ARIMA'),
    ('s6', 'Uji Asumsi'),
    ('s7', 'Pemilihan Lag'),
    ('s8', 'Pemodelan LightGBM'),
    ('s9', 'ARIMA-LightGBM'),
    ('s10', 'Prediksi 14 Hari'),
]


# Judul kartu step
def _title(text):
    ui.label(text).classes('w-full text-center').style(
        'font-size:22px;font-weight:800;color:#204b2a;margin-bottom:16px;'
    )


# Subjudul
def _sub(text):
    ui.label(text).style('font-size:17px;font-weight:800;color:#365d3c;margin:22px 0 12px')


# Tampilkan gambar (base64) dari notebook
def _image_b64(b64, align='center'):
    if not b64:
        ui.label('Plot belum tersedia.').style('color:#9a3412;font-size:12px')
        return
    justify = 'flex-start' if align == 'left' else 'center'
    with ui.row().style(f'width:100%;justify-content:{justify};gap:0;margin:8px 0 22px'):
        ui.image(f'data:image/png;base64,{b64}').style(
            'width:66%;max-width:780px;min-width:520px;height:auto;border-radius:12px;'
            'border:1px solid #dfe8dc;background:white'
        )


# Tabel serbaguna (DataFrame / list dict)
def _table(data, cols=None, formats=None):
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        df = pd.DataFrame(data)
    if df.empty:
        ui.label('Tidak ada data untuk ditampilkan.').style('font-size:12px;color:#6b7280')
        return
    if cols is not None:
        df = df[[c for c in cols if c in df.columns]]
    formats = formats or {}
    for col, fn in formats.items():
        if col in df.columns:
            df[col] = df[col].map(lambda x: fn(x) if pd.notna(x) else '')
    df = df.fillna('').astype(object)
    rows = []
    for rec in df.to_dict('records'):
        rows.append({k: (v.item() if hasattr(v, 'item') else v) for k, v in rec.items()})
    columns = [
        {'name': c, 'label': c, 'field': c, 'align': 'center', 'sortable': False}
        for c in df.columns
    ]
    min_width = min(1180, max(420, 150 * len(columns)))
    with ui.row().style('width:100%;justify-content:center;gap:0;overflow-x:auto;margin:8px 0 22px'):
        ui.table(columns=columns, rows=rows, row_key=df.columns[0]).props(
            'flat bordered dense separator=cell hide-pagination rows-per-page-options="[0]"'
        ).classes('analysis-table').style(
            f'width:auto;min-width:{min_width}px;max-width:100%;font-size:12px'
        )


# Kotak interpretasi
def _note(text, color='#2d6538', title='Interpretasi'):
    ui.html(
        f'<div style="margin-top:18px;background:#f4faf2;border-left:5px solid {color};'
        f'padding:11px 14px;border-radius:9px;font-size:12px;line-height:1.65;color:#26352b">'
        f'<b style="color:{color}">{title}:</b> {text}</div>'
    )


# Pita status berwarna
def _status(text, kind='info'):
    bg, fg = {
        'info': ('#eaf3ea', '#24572f'),
        'success': ('#e9f7ec', '#18783a'),
        'warn': ('#fff4dc', '#9b6500'),
    }[kind]
    ui.label(text).classes('w-full').style(
        f'background:{bg};color:{fg};padding:10px 12px;border-radius:10px;'
        'font-size:12px;font-weight:700;margin:8px 0'
    )


# ['A','B','C'] -> 'A, B, dan C'
def _gabung_nama(nama_list):
    nama_list = list(nama_list)
    if len(nama_list) <= 1:
        return ''.join(nama_list)
    if len(nama_list) == 2:
        return f'{nama_list[0]} dan {nama_list[1]}'
    return ', '.join(nama_list[:-1]) + f', dan {nama_list[-1]}'


# Kategori MAPE
def _kategori_mape(mape):
    if mape < 10:
        return 'sangat baik'
    if mape < 20:
        return 'baik'
    if mape < 50:
        return 'cukup'
    return 'kurang baik'


# Interpretasi otomatis step 1
def teks_data_awal(prep):
    df = prep['df']
    pasar_list = prep['pasar_list']
    stats = prep['stats']
    kalimat = []

    means = {p: stats[p]['mean'] for p in pasar_list}
    if len(pasar_list) >= 2:
        urut = sorted(means.items(), key=lambda kv: kv[1])
        p_rendah, v_rendah = urut[0]
        p_tinggi, v_tinggi = urut[-1]
        selisih_persen = abs(v_tinggi - v_rendah) / ((v_tinggi + v_rendah) / 2) * 100
        ket_jarak = 'relatif berdekatan' if selisih_persen < 10 else 'cukup berbeda'
        rata_str = ', '.join(f'{p} sekitar Rp{v:,.0f}' for p, v in means.items())
        kalimat.append(f'Rata-rata harga {rata_str}, sehingga tingkat harga antar pasar {ket_jarak}.')
    else:
        p = pasar_list[0]
        kalimat.append(f'Rata-rata harga {p} sekitar Rp{means[p]:,.0f}.')

    med_desc = []
    for p in pasar_list:
        median = float(df[p].median())
        mean = stats[p]['mean']
        if median < mean * 0.97:
            med_desc.append(f'{p} (median Rp{median:,.0f}, lebih rendah daripada rata-rata, menandakan ada lonjakan harga tinggi yang menarik rata-rata naik)')
        elif median > mean * 1.03:
            med_desc.append(f'{p} (median Rp{median:,.0f}, lebih tinggi daripada rata-rata)')
        else:
            med_desc.append(f'{p} (median Rp{median:,.0f}, mendekati rata-rata)')
    kalimat.append('Median: ' + '; '.join(med_desc) + '.')

    stds = {p: stats[p]['std'] for p in pasar_list}
    if len(pasar_list) >= 2:
        p_std_besar = max(stds, key=stds.get)
        p_std_kecil = min(stds, key=stds.get)
        if p_std_besar != p_std_kecil:
            kalimat.append(
                f'Standar deviasi {p_std_besar} (sekitar Rp{stds[p_std_besar]:,.0f}) lebih besar '
                f'daripada {p_std_kecil} (sekitar Rp{stds[p_std_kecil]:,.0f}), sehingga pergerakan '
                f'harga {p_std_besar} cenderung lebih lebar.'
            )

    lonjakan_str = ', '.join(f'sekitar Rp{stats[p]["max"]:,.0f} di {p}' for p in pasar_list)
    kalimat.append(
        f'Dari grafik historis, harga terlihat fluktuatif dari waktu ke waktu, dengan lonjakan '
        f'tertinggi mencapai {lonjakan_str}.'
    )
    return ' '.join(kalimat)


# Interpretasi otomatis step 4 (ADF & differencing)
def teks_adf(prep):
    tabel = prep['adf_compare']
    log = prep['diff_log']
    kolom_setelah = [c for c in tabel.columns if c.startswith('P-value Setelah')][0]
    kata_angka = {1: 'satu', 2: 'dua'}

    info = {}
    for _, baris in tabel.iterrows():
        pasar = baris['Pasar']
        log_pasar = log[log['Pasar'] == pasar]
        info[pasar] = {
            'p_awal': float(baris['P-value Sebelum Diff']),
            'p_diff': baris[kolom_setelah],
            'd': int(log_pasar.iloc[-1]['Differencing (d)']),
            'acf_lambat': 'ACF meluruh lambat' in log_pasar.iloc[0]['Keterangan'],
            'belum_stasioner': log_pasar.iloc[-1]['Keputusan'] == 'Tidak stasioner',
        }
    semua = list(info.keys())

    def _ringkas(pasar_stasioner, kelompok):
        label = 'seluruh pasar' if len(kelompok) == len(semua) else _gabung_nama(kelompok)
        if len(pasar_stasioner) == len(kelompok):
            return f'p-value di bawah 0,05 pada {label} sehingga secara statistik data sudah stasioner'
        if not pasar_stasioner:
            return f'p-value di atas 0,05 pada {label} sehingga data belum stasioner'
        return (f'p-value di bawah 0,05 pada {_gabung_nama(pasar_stasioner)}, sedangkan pasar lainnya belum '
                'menunjukkan kestasioneran')

    lambat = [p for p in semua if info[p]['acf_lambat']]
    cepat = [p for p in semua if not info[p]['acf_lambat']]
    if len(lambat) == len(semua):
        kal_acf = 'Secara visual, plot ACF meluruh cukup lambat sehingga data tampak belum stabil dalam mean.'
    elif not lambat:
        kal_acf = 'Secara visual, plot ACF meluruh cepat sehingga data tampak sudah stabil dalam mean.'
    else:
        kal_acf = (f'Secara visual, plot ACF meluruh cukup lambat pada {_gabung_nama(lambat)} sehingga data tampak '
                   f'belum stabil dalam mean, sedangkan pada {_gabung_nama(cepat)} ACF meluruh cepat.')

    adf_awal = [p for p in semua if info[p]['p_awal'] < 0.05]
    sejalan = all((info[p]['p_awal'] < 0.05) == (not info[p]['acf_lambat']) for p in semua)
    pembuka = 'Hasil ini sejalan dengan uji ADF sebelum differencing yang menghasilkan' if sejalan \
        else 'Namun, uji ADF sebelum differencing menghasilkan'
    kal_adf = f'{pembuka} {_ringkas(adf_awal, semua)}.'

    didiff = [p for p in semua if info[p]['d'] > 0]
    d_unik = sorted(set(info[p]['d'] for p in semua))
    if not didiff:
        kal_diff = 'Karena data sudah memenuhi kriteria stasioner dalam mean, differencing tidak diperlukan (d = 0).'
    elif len(d_unik) == 1:
        if all(info[p]['p_awal'] < 0.05 for p in didiff):
            alasan = ('tetap diterapkan karena pola ACF menunjukkan data belum stabil dalam mean, untuk menjaga '
                      'kestasioneran data dan konsistensi proses identifikasi ARIMA')
        elif all(info[p]['p_awal'] >= 0.05 for p in didiff):
            alasan = 'diterapkan karena data belum stasioner dalam mean'
        else:
            alasan = 'diterapkan karena data belum memenuhi kriteria stasioner dalam mean (uji ADF dan pola ACF)'
        kal_diff = f'Differencing orde {kata_angka[d_unik[0]]} {alasan}.'
    else:
        bagian = []
        for p in semua:
            if info[p]['d'] == 0:
                bagian.append(f'{p} tanpa differencing (d = 0)')
            else:
                bagian.append(f'{p} sebanyak {info[p]["d"]} kali (d = {info[p]["d"]})')
        kal_diff = 'Jumlah differencing disesuaikan dengan kebutuhan tiap pasar: ' + '; '.join(bagian) + '.'

    kalimat = [kal_acf, kal_adf, kal_diff]

    if didiff:
        stasioner_diff = [p for p in didiff if float(info[p]['p_diff']) < 0.05]
        kalimat.append(f'Setelah differencing, uji ADF menghasilkan {_ringkas(stasioner_diff, didiff)}.')

    belum = [p for p in semua if info[p]['belum_stasioner']]
    if belum:
        kalimat.append(
            f'Namun, pada {_gabung_nama(belum)} kriteria stasioner (ADF dan ACF) belum sepenuhnya terpenuhi '
            'meskipun differencing sudah mencapai batas maksimum, sehingga hasil pemodelan pada pasar tersebut '
            'perlu dicermati.'
        )
    return ' '.join(kalimat)


# Pisahkan pasar yang perlu / tidak perlu Box-Cox
def _status_boxcox(boxcox_summary):
    perlu_transform, sudah_stabil = [], []
    for _, baris in boxcox_summary.iterrows():
        pasar = baris['Pasar']
        keputusan = str(baris['Keputusan']).lower()
        if 'tidak perlu' in keputusan:
            sudah_stabil.append(pasar)
        else:
            perlu_transform.append(pasar)
    return perlu_transform, sudah_stabil


# Judul plot step 3
def judul_boxcox(boxcox_summary):
    perlu_transform, _ = _status_boxcox(boxcox_summary)
    if not perlu_transform:
        return 'Data Train Setelah Uji Stasioner Varians (Tanpa Transformasi)'
    return 'Hasil Transformasi Box-Cox'


# Interpretasi otomatis step 3
def teks_boxcox(boxcox_summary):
    perlu_transform, sudah_stabil = _status_boxcox(boxcox_summary)
    semua_pasar = list(boxcox_summary['Pasar'])

    if len(perlu_transform) == len(semua_pasar):
        return (
            'Nilai lambda awal seluruh pasar tidak sama dengan 1, sehingga seluruh data ditransformasi '
            'dengan Box-Cox untuk menstabilkan besar fluktuasi sebelum pemodelan ARIMA.'
        )
    if not perlu_transform:
        return (
            'Nilai lambda awal seluruh pasar sudah mendekati 1, sehingga variansnya dianggap sudah '
            'stasioner. Karena itu transformasi Box-Cox tidak diterapkan dan data train tetap memakai '
            'skala harga aslinya (Rupiah) sebelum masuk ke pemodelan ARIMA.'
        )
    return (
        f'Nilai lambda awal {_gabung_nama(perlu_transform)} tidak sama dengan 1 sehingga tetap ditransformasi '
        f'dengan Box-Cox untuk menstabilkan fluktuasinya, sedangkan {_gabung_nama(sudah_stabil)} sudah '
        'mendekati 1 sehingga variansnya dianggap stasioner dan tidak ditransformasi.'
    )


# Interpretasi otomatis evaluasi ARIMA
def teks_evaluasi_arima(ar_eval):
    kalimat = []
    for _, baris in ar_eval.iterrows():
        pasar = baris['Pasar']
        rmse = float(baris['RMSE (Rp)'])
        mae = float(baris['MAE (Rp)'])
        mape = float(baris['MAPE (%)'])
        if rmse < 1:
            kalimat.append(
                f'{pasar} menghasilkan error 0 (RMSE Rp0, MAE Rp0, MAPE 0.00%). Ini terjadi karena harga pada data '
                'test tidak berubah sama sekali sehingga mudah ditebak, jadi angka ini tidak menggambarkan '
                'kemampuan model yang sebenarnya'
            )
            continue
        kalimat.append(
            f'{pasar} menghasilkan RMSE sekitar Rp{rmse:,.0f}, MAE Rp{mae:,.0f}, dan MAPE {mape:.2f}% '
            f'(tingkat {_kategori_mape(mape)})'
        )
    return (
        f'Pada data test, {"; ".join(kalimat)}. Hasil ini menunjukkan ARIMA sudah menangkap sebagian pola '
        'harga, tetapi masih terdapat ruang perbaikan pada kesalahan prediksinya sebelum dikoreksi oleh LightGBM.'
    )


# Interpretasi otomatis step 6
def teks_uji_asumsi(assumptions):
    ks_gagal, lb_lulus, lb_gagal, arch_hetero, arch_homo = [], [], [], [], []
    for _, baris in assumptions.iterrows():
        pasar = baris['Pasar']
        if float(baris['KS p-value']) < 0.05:
            ks_gagal.append(pasar)
        if float(baris['Ljung-Box p-value']) >= 0.05:
            lb_lulus.append(pasar)
        else:
            lb_gagal.append(pasar)
        if float(baris['ARCH-LM p-value']) < 0.05:
            arch_hetero.append(pasar)
        else:
            arch_homo.append(pasar)

    semua_pasar = list(assumptions['Pasar'])
    kalimat = []

    if len(ks_gagal) == len(semua_pasar):
        kalimat.append('Uji Kolmogorov-Smirnov menghasilkan p-value di bawah 0,05 pada seluruh pasar, sehingga residual tidak berdistribusi normal.')
    elif not ks_gagal:
        kalimat.append('Uji Kolmogorov-Smirnov menghasilkan p-value di atas 0,05 pada seluruh pasar, sehingga residual berdistribusi normal.')
    else:
        kalimat.append(f'Uji Kolmogorov-Smirnov menunjukkan residual {_gabung_nama(ks_gagal)} tidak berdistribusi normal, sedangkan pasar lainnya berdistribusi normal.')
    kalimat.append('Kondisi ini tidak menghalangi penggunaan model untuk menghasilkan prediksi; normalitas terutama berkaitan dengan inferensi dan penyusunan interval prediksi berbasis asumsi distribusi error.')

    if len(lb_lulus) == len(semua_pasar):
        kalimat.append('Uji Ljung-Box menghasilkan p-value di atas 0,05 pada seluruh pasar, sehingga residual sudah bersifat white noise dan tidak menunjukkan autokorelasi yang signifikan.')
    elif not lb_lulus:
        kalimat.append('Uji Ljung-Box menghasilkan p-value di bawah 0,05 pada seluruh pasar, sehingga residual masih menunjukkan autokorelasi.')
    else:
        kalimat.append(f'Uji Ljung-Box menunjukkan residual {_gabung_nama(lb_lulus)} sudah white noise, sedangkan pasar lainnya masih menunjukkan autokorelasi.')

    if len(arch_hetero) == len(semua_pasar):
        kalimat.append('Sementara itu, ARCH-LM menunjukkan residual seluruh pasar bersifat heteroskedastis, artinya varians residual berubah-ubah dari waktu ke waktu.')
    elif not arch_hetero:
        kalimat.append('Sementara itu, ARCH-LM menunjukkan residual seluruh pasar bersifat homoskedastis, artinya varians residual relatif stabil.')
    else:
        kalimat.append(
            f'Sementara itu, ARCH-LM menunjukkan residual {_gabung_nama(arch_hetero)} bersifat heteroskedastis, '
            f'sedangkan {_gabung_nama(arch_homo)} bersifat homoskedastis, sehingga varians residualnya lebih stabil.'
        )
    kalimat.append('Residual tetap digunakan pada tahap berikutnya untuk dipelajari oleh LightGBM dan membentuk model hybrid ARIMA-LightGBM.')
    return ' '.join(kalimat)


# CSS kotak upload & tabel
CSS_HALAMAN = '''
<style>
  body{background:#eef3e7!important}
  .nicegui-content{padding:0!important;gap:0!important}
  .q-page{padding:0!important}
  .q-gutter-md{gap:0!important}
  .q-uploader__list{display:none!important}
  .q-uploader{border:1px dashed #799b70;border-radius:12px;background:#f8fbf6;width:100%}
  .q-uploader__header{background:transparent!important;color:#244d2d!important;padding:12px 14px!important;min-height:auto!important}
  .q-uploader__subtitle{display:none!important}
  .q-uploader__title{font-weight:800!important;font-size:13px!important}
  .analysis-table .q-table thead tr th{background:#e8f1e6;color:#24482d;font-weight:800;text-align:center;border-color:#cfdcca!important}
  .analysis-table .q-table tbody td{text-align:center;border-color:#dfe8dc!important;padding:8px 10px}
  .analysis-table .q-table__middle{border-radius:10px;overflow:auto}
  .analysis-table .q-table__bottom{display:none!important}
</style>
'''


# Gaya tampilan
GAYA_HEADER = (
    'background:linear-gradient(135deg,#1b5e20 0%,#2e7d32 68%,#c5a02c 100%);'
    'padding:18px 30px;color:white;width:100%'
)
GAYA_KOTAK_UPLOAD = (
    'background:#fff;border:1px solid #dce6da;border-radius:18px;padding:18px 20px;'
    'margin-bottom:16px;box-shadow:0 8px 24px rgba(26,71,42,.06);width:100%'
)
GAYA_KOTAK_NAVIGASI = (
    'background:#fff;border:1px solid #dce6da;border-radius:18px;padding:14px 16px;'
    'margin-bottom:18px;width:100%;box-shadow:0 8px 24px rgba(26,71,42,.04)'
)
GAYA_KOTAK_STEP = (
    'background:#fff;border:1px solid #dce6da;border-radius:18px;padding:22px 24px;'
    'margin-bottom:18px;box-shadow:0 8px 24px rgba(26,71,42,.05);width:100%'
)
GAYA_TOMBOL_MULAI = (
    'background:#2e7d32;color:white;border-radius:11px;min-width:210px;height:52px;'
    'padding:0 24px;font-size:13px;font-weight:800'
)
GAYA_TOMBOL_NAVIGASI = (
    'width:100%;background:#edf5eb;color:#204b2a;border:1px solid #d6e3d3;'
    'border-radius:11px;font-weight:800;font-size:11px;min-height:44px;padding:8px 10px'
)
GAYA_TOMBOL_LANJUT = (
    'background:#c77b12;color:white;border-radius:10px;font-weight:800;'
    'min-width:250px;height:46px;padding:0 22px;margin-top:10px'
)
GAYA_PETUNJUK = 'font-size:12px;color:#647268;line-height:1.7;margin:-4px 0 14px'
GAYA_LABEL_INPUT = 'font-size:11px;font-weight:700;color:#55615a;margin-left:2px'
GAYA_KOTAK_INPUT = 'border:1px solid #d8e5d5;border-radius:12px;padding:22px 24px;width:100%'
GAYA_STATUS_BELUM = 'font-size:12px;color:#6b7280'
GAYA_STATUS_BERHASIL = 'font-size:12px;color:#15803d;font-weight:800'
GAYA_STATUS_GAGAL = 'font-size:12px;color:#b42318;font-weight:700'


# Teks petunjuk & kesimpulan tetap
PETUNJUK_ACF_PACF = (
    'Perhatikan spike atau batang yang masih melewati batas signifikansi. Pada ACF, lag terakhir sebelum spike mulai '
    'melemah atau cut off menjadi kandidat q (MA). Pada PACF, pola yang sama menjadi kandidat p (AR). '
    'Nilai d mengikuti jumlah differencing pada uji stasioner mean.'
)
PETUNJUK_INPUT_ORDE = (
    'Ketik nilai p, d, dan q untuk tiap pasar. Isi satu angka kalau ingin mengunci satu nilai, misalnya 0. '
    'Kalau ingin menguji rentang, tulis dengan tanda strip, misalnya 0-1 atau 0-2. Program mencoba semua kombinasi '
    'p, d, dan q di dalam rentang, lalu memilih model dengan AIC terkecil.'
)
PETUNJUK_PACF_RESIDUAL = (
    'Plot PACF residual digunakan untuk mencari residual masa lalu yang masih memiliki hubungan langsung dengan '
    'residual saat ini. Spike yang melewati batas signifikansi menjadi kandidat lag fitur untuk LightGBM.'
)
KESIMPULAN_HYBRID_MEMBAIK = (
    'Model hybrid ARIMA-LightGBM menghasilkan nilai error yang lebih rendah daripada ARIMA pada seluruh metrik di '
    'seluruh pasar. Hal ini menunjukkan bahwa LightGBM mampu mempelajari sebagian pola residual yang belum '
    'tertangkap oleh ARIMA dan memperbaiki hasil prediksi pada data test.'
)
KESIMPULAN_HYBRID_CAMPUR = (
    'Pemodelan selesai. Hybrid tidak memperbaiki seluruh metrik secara seragam; kesimpulan mengikuti hasil '
    'evaluasi per pasar dan per metrik.'
)


# Baca & cek file upload (Tanggal + 1-6 pasar, min 60 baris, harga > 0)
def baca_file_upload(nama_file, isi_file):
    buf = io.BytesIO(isi_file)
    df = pd.read_excel(buf) if nama_file.lower().endswith('.xlsx') else pd.read_csv(buf)
    df.columns = [str(c).strip() for c in df.columns]
    if 'Tanggal' not in df.columns:
        raise ValueError('Kolom Tanggal tidak ditemukan.')
    kolom_pasar = [c for c in df.columns if c != 'Tanggal']
    if not kolom_pasar:
        raise ValueError('Tidak ada kolom harga pasar.')
    if len(kolom_pasar) > MAKS_PASAR:
        raise ValueError(f'Maksimal {MAKS_PASAR} pasar.')
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')
    df = df[['Tanggal'] + kolom_pasar].dropna(subset=['Tanggal']).sort_values('Tanggal')
    for p in kolom_pasar:
        df[p] = pd.to_numeric(df[p], errors='coerce')
    df = df.dropna(subset=kolom_pasar, how='all')
    if len(df) < 60:
        raise ValueError('Data terlalu sedikit (minimal 60 baris).')
    if (df[kolom_pasar] <= 0).any().any():
        raise ValueError('Harga harus bernilai positif (lebih dari 0).')
    return df, kolom_pasar


# Kotak upload + tombol MULAI ANALISIS
def buat_kotak_upload(state):
    with ui.element('div').style(GAYA_KOTAK_UPLOAD):
        _title('Input File')
        with ui.row().style('width:100%;gap:16px;align-items:flex-end;flex-wrap:wrap'):
            with ui.column().style('flex:1;min-width:360px;gap:5px'):
                status = ui.label('Belum ada file').style(GAYA_STATUS_BELUM)

                # Jalan otomatis setelah file dipilih
                async def upload(e):
                    try:
                        nama = e.file.name
                        isi = await e.file.read()
                        df, kolom_pasar = baca_file_upload(nama, isi)
                        state['df_raw'] = df
                        state['pasar_list'] = kolom_pasar
                        status.set_text(f'✓ {nama}')
                        status.style(GAYA_STATUS_BERHASIL)
                    except Exception as ex:
                        status.set_text(f'⚠ {ex}')
                        status.style(GAYA_STATUS_GAGAL)

                ui.upload(on_upload=upload, max_files=1, auto_upload=True).props(
                    'accept=".csv,.xlsx" label="Input File"'
                ).style('width:100%')

            tombol_mulai = ui.button('MULAI ANALISIS').style(GAYA_TOMBOL_MULAI)
    return tombol_mulai


# 10 tombol navigasi (scroll ke step)
def buat_navigasi():
    nav = {}
    with ui.element('div').style(GAYA_KOTAK_NAVIGASI):
        _title('Navigasi Step')
        with ui.element('div').style(
            'display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;width:100%'
        ):
            for kunci, nama in STEP_META:
                tombol = ui.button(nama).style(GAYA_TOMBOL_NAVIGASI)
                tombol.props('disable no-caps')
                tombol.on('click', lambda _, k=kunci: ui.run_javascript(
                    f"document.getElementById('step-{k}')?.scrollIntoView({{behavior:'smooth',block:'start'}})"
                ))
                nav[kunci] = tombol
    return nav


# 10 kartu step kosong (tersembunyi)
def buat_kartu_step():
    kartu, isi = {}, {}
    for kunci, nama in STEP_META:
        kartu[kunci] = ui.element('div').props(f'id=step-{kunci}').style('display:none;width:100%')
        with kartu[kunci]:
            isi[kunci] = ui.element('div').style(GAYA_KOTAK_STEP)
            with isi[kunci]:
                _title(nama)
    return kartu, isi


# Step 1: Data Awal
def isi_step1(kotak, prep):
    with kotak:
        if prep['baris_dipangkas'] > 0:
            _status(
                f"{prep['baris_dipangkas']} baris di ujung data dibuang karena ada pasar yang belum "
                f"memiliki harga. Periode yang dipakai: {prep['tanggal_awal']:%d-%m-%Y} sampai {prep['tanggal_akhir']:%d-%m-%Y}.",
                'warn',
            )
        if prep['fig_raw']:
            _image_b64(prep['fig_raw'][0])
        _sub('Statistik Deskriptif')
        baris = [
            {
                'Pasar': p, 'N': f"{v['n']:,}",
                'Rata-rata': f"Rp {v['mean']:,.0f}", 'Std': f"Rp {v['std']:,.0f}",
                'Min': f"Rp {v['min']:,.0f}", 'Maks': f"Rp {v['max']:,.0f}",
            }
            for p, v in prep['stats'].items()
        ]
        _table(baris)
        _note(teks_data_awal(prep), title='Interpretasi Data Awal')


# Step 2: Split Data
def isi_step2(kotak, prep):
    with kotak:
        _table(prep['split_table'])


# Step 3: Uji Stasioner Varians
def isi_step3(kotak, prep):
    with kotak:
        tabel = prep['boxcox_summary'][['Pasar', 'Lambda Awal', 'Keputusan']].copy()
        _table(tabel, formats={'Lambda Awal': lambda v: f'{float(v):.4f}'})
        _sub(judul_boxcox(prep['boxcox_summary']))
        if prep['fig_boxcox']:
            _image_b64(prep['fig_boxcox'][0])
        _note(teks_boxcox(prep['boxcox_summary']))


# Step 4: Uji Stasioner Mean
def isi_step4(kotak, prep):
    with kotak:
        _sub('Plot ACF Data Train')
        if prep['fig_acf_train']:
            _image_b64(prep['fig_acf_train'][0])
        _sub('Hasil Uji Stasioner Mean (ADF)')
        tabel_adf = prep['adf_compare']
        kolom_p = [c for c in tabel_adf.columns if c.startswith('P-value')]
        _table(tabel_adf, formats={c: (lambda v: f'{float(v):.6f}') for c in kolom_p})
        _note(teks_adf(prep))


# Batas atas tiap orde
MAKS_P, MAKS_D, MAKS_Q = 5, 2, 5


# Kotak isian orde (ketik manual)
def buat_input_orde(judul):
    with ui.column().style('gap:6px'):
        ui.label(judul).style(GAYA_LABEL_INPUT)
        kotak = ui.input().props('outlined dense').style('width:140px')
    return kotak


# Baca isian orde: "1" -> (1, 1), "0-2" -> (0, 2). Kalau salah, balikin None
def baca_rentang_orde(teks, batas_atas):
    teks = (teks or '').replace('–', '-').replace('—', '-').replace(' ', '')
    bagian = teks.split('-')
    if len(bagian) == 1 and bagian[0].isdigit():
        awal = akhir = int(bagian[0])
    elif len(bagian) == 2 and bagian[0].isdigit() and bagian[1].isdigit():
        awal, akhir = int(bagian[0]), int(bagian[1])
    else:
        return None
    if awal > akhir or akhir > batas_atas:
        return None
    return awal, akhir


# Step 5 (input): plot ACF/PACF + isian orde p, d, q
def isi_step5_input(kotak, prep, pasar_list, state, event_selesai):
    input_orde = {}
    with kotak:
        _sub('Plot ACF & PACF')
        ui.label(PETUNJUK_ACF_PACF).style(GAYA_PETUNJUK)
        for i, p in enumerate(pasar_list):
            if i < len(prep['fig_arima_id']):
                _image_b64(prep['fig_arima_id'][i])
        _sub('Input Rentang Orde ARIMA')
        ui.label(PETUNJUK_INPUT_ORDE).style(GAYA_PETUNJUK)
        with ui.row().style('gap:24px;flex-wrap:wrap;width:100%;align-items:flex-start'):
            for p in pasar_list:
                with ui.column().style('gap:8px;flex:1;min-width:420px'):
                    ui.label(p).style('font-size:14px;font-weight:800;color:#2e7d32;margin-left:4px')
                    with ui.element('div').style(GAYA_KOTAK_INPUT):
                        with ui.row().style('gap:22px;justify-content:center;width:100%;align-items:flex-start;flex-wrap:wrap'):
                            kotak_p = buat_input_orde('p')
                            kotak_d = buat_input_orde('d')
                            kotak_q = buat_input_orde('q')
                    input_orde[p] = {'p': kotak_p, 'd': kotak_d, 'q': kotak_q}
        tombol = ui.button('SIMPAN RENTANG ORDE DAN LANJUT').style(GAYA_TOMBOL_LANJUT)

        # Simpan orde lalu beri sinyal lanjut
        def simpan_orde():
            rentang = {}
            for p in pasar_list:
                kotak = input_orde[p]
                p_rentang = baca_rentang_orde(kotak['p'].value, MAKS_P)
                d_rentang = baca_rentang_orde(kotak['d'].value, MAKS_D)
                q_rentang = baca_rentang_orde(kotak['q'].value, MAKS_Q)
                if p_rentang is None or d_rentang is None or q_rentang is None:
                    ui.notify(
                        f'{p}: isi p, d, dan q dengan satu angka (misal 0) atau rentang (misal 0-2). '
                        f'Batas maksimum p = {MAKS_P}, d = {MAKS_D}, q = {MAKS_Q}.',
                        type='warning',
                    )
                    return
                rentang[p] = {'p': p_rentang, 'd': d_rentang, 'q': q_rentang}
            state['orders'] = rentang
            tombol.props('disable')
            event_selesai.set()

        tombol.on('click', simpan_orde)


# Step 5 (hasil): tabel AIC, plot prediksi, evaluasi
def isi_step5_hasil(kotak, ar, pasar_list):
    with kotak:
        for p in pasar_list:
            _sub(f'Mencari Model Terbaik — {p}')
            _table(ar['aic_tables'][p], formats={'AIC': lambda v: f'{float(v):.2f}'})
            jumlah_kandidat = len(ar['aic_tables'][p])
            ui.label(f'Model terpilih adalah ARIMA{tuple(ar["final_orders"][p])} (AIC terkecil dari {jumlah_kandidat} kandidat)').style(
                'font-size:12px;font-weight:800;color:#16803a;margin:8px 0'
            )
        _status('Mulai pemodelan ARIMA...', 'info')
        for i, p in enumerate(pasar_list):
            _sub(f'Prediksi ARIMA — {p}')
            if i < len(ar['fig_arima_pred']):
                _image_b64(ar['fig_arima_pred'][i])
        _sub('Evaluasi ARIMA')
        _table(
            ar['arima_eval'],
            formats={
                'RMSE (Rp)': lambda v: f'{float(v):,.2f}',
                'MAE (Rp)': lambda v: f'{float(v):,.2f}',
                'MAPE (%)': lambda v: f'{float(v):.4f}',
            },
        )
        _note(teks_evaluasi_arima(ar['arima_eval']))
        _status('Pemodelan ARIMA selesai!', 'success')


# Step 6: Uji Asumsi
def isi_step6(kotak, ar, pasar_list):
    with kotak:
        hasil_uji = []
        for p in pasar_list:
            baris_p = ar['assumptions'].loc[ar['assumptions']['Pasar'] == p]
            if baris_p.empty:
                continue
            baris = baris_p.iloc[0]
            ks = float(baris['KS p-value'])
            lb = float(baris['Ljung-Box p-value'])
            arch = float(baris['ARCH-LM p-value'])
            hasil_uji.extend([
                {'Pasar': p, 'Uji': 'Kolmogorov-Smirnov', 'P-value': f'{ks:.4f}', 'Interpretasi': 'Tidak berdistribusi normal' if ks < 0.05 else 'Berdistribusi normal'},
                {'Pasar': p, 'Uji': 'Ljung-Box', 'P-value': f'{lb:.4f}', 'Interpretasi': 'White noise' if lb >= 0.05 else 'Masih terdapat autokorelasi'},
                {'Pasar': p, 'Uji': 'ARCH-LM', 'P-value': f'{arch:.4f}', 'Interpretasi': 'Homoskedastis' if arch >= 0.05 else 'Heteroskedastis'},
            ])
        _table(hasil_uji, cols=['Pasar', 'Uji', 'P-value', 'Interpretasi'])
        _note(teks_uji_asumsi(ar['assumptions']))


# Step 7: PACF residual + isian kandidat lag
def isi_step7_input(kotak, ar, pasar_list, state, event_selesai):
    input_lag = {}
    maks_lag = ar['maks_lag_pacf']
    with kotak:
        if ar['fig_pacf_residual']:
            _image_b64(ar['fig_pacf_residual'][0])
        ui.label(PETUNJUK_PACF_RESIDUAL).style(GAYA_PETUNJUK)
        _sub('Nilai PACF yang Signifikan')
        baris_signifikan = []
        for p in pasar_list:
            tabel_pacf = ar['pacf_tables'][p]
            signifikan = tabel_pacf.loc[tabel_pacf['Ket'] == 'Signifikan'].copy()
            if not signifikan.empty:
                signifikan.insert(0, 'Pasar', p)
                baris_signifikan.extend(signifikan.to_dict('records'))
        _table(baris_signifikan, formats={'PACF': lambda v: f'{float(v):.4f}'})
        _sub('Input Kandidat Lag')
        ui.label(
            f'Lag yang boleh diisi: 1 sampai {maks_lag}. Kalau kandidatnya lebih dari satu, program menguji tiap lag '
            'satu per satu dengan Optuna, lalu memilih lag yang menghasilkan model hybrid dengan MAPE paling kecil.'
        ).style(GAYA_PETUNJUK)
        with ui.row().style('gap:20px;flex-wrap:wrap;width:100%'):
            for p in pasar_list:
                tabel_pacf = ar['pacf_tables'][p]
                lag_signifikan = tabel_pacf.loc[tabel_pacf['Ket'] == 'Signifikan', 'Lag'].tolist()
                if lag_signifikan:
                    isi_awal = ','.join(str(int(x)) for x in lag_signifikan)
                else:
                    isi_awal = str(int(tabel_pacf.loc[tabel_pacf['PACF'].abs().idxmax(), 'Lag']))
                with ui.element('div').style('border:1px solid #d8e5d5;border-radius:12px;padding:18px 20px;flex:1;min-width:360px'):
                    ui.label(p).style('font-size:13px;font-weight:800;color:#2e7d32;margin-bottom:10px')
                    ui.label('Masukkan kandidat lag, pisahkan dengan koma').style('font-size:10px;color:#737f76;margin-bottom:8px')
                    input_lag[p] = ui.input(value=isi_awal).style('width:100%;min-height:48px')
        tombol = ui.button('SIMPAN LAG DAN LANJUT').style(GAYA_TOMBOL_LANJUT)
        keterangan = ui.label('').style('font-size:12px;color:#16803a;font-weight:800;margin-top:8px')

        # Simpan lag lalu beri sinyal lanjut
        def simpan_lag():
            lag_pilihan = {}
            for p in pasar_list:
                daftar_lag = []
                for teks in input_lag[p].value.split(','):
                    teks = teks.strip()
                    if teks.isdigit() and 1 <= int(teks) <= maks_lag and int(teks) not in daftar_lag:
                        daftar_lag.append(int(teks))
                daftar_lag.sort()
                if not daftar_lag:
                    ui.notify(f'{p}: isi minimal satu lag antara 1 dan {maks_lag}.', type='warning')
                    return
                lag_pilihan[p] = daftar_lag
            state['lags'] = lag_pilihan
            keterangan.set_text('Rekonstruksi selesai!')
            tombol.props('disable')
            event_selesai.set()

        tombol.on('click', simpan_lag)


# Step 8: status menunggu Optuna
def isi_step8_menunggu(kotak):
    with kotak:
        _status('Mulai pemodelan LightGBM — sedang mencari hyperparameter yang cocok dengan Optuna...', 'warn')


# Step 8 (hasil): tabel hyperparameter
def isi_step8_hasil(kotak, lgbm, pasar_list):
    with kotak:
        _status('Hyperparameter ditemukan!', 'success')
        tabel_param = []
        for p in pasar_list:
            params = lgbm['best_params'][p]
            tabel_param.append({
                'Pasar': p,
                'Lag': lgbm['best_lag'][p],
                'n_estimators': params.get('n_estimators'),
                'learning_rate': f"{float(params.get('learning_rate', 0)):.6f}",
                'num_leaves': params.get('num_leaves'),
                'max_depth': params.get('max_depth'),
                'min_child_samples': params.get('min_child_samples'),
            })
        _table(tabel_param)
        _status('Mulai pemodelan LightGBM...', 'info')
        _status('Pemodelan LightGBM selesai!', 'success')


# Step 9: ARIMA vs Hybrid
def isi_step9(kotak, lgbm, pasar_list):
    with kotak:
        _status('Mulai model ARIMA-LightGBM...', 'info')
        for i, p in enumerate(pasar_list):
            _sub(p)
            if i < len(lgbm['fig_hybrid']):
                _image_b64(lgbm['fig_hybrid'][i])
            evaluasi_p = lgbm['hybrid_eval'][lgbm['hybrid_eval']['Pasar'] == p]
            _table(
                evaluasi_p,
                cols=['Metrik', 'ARIMA', 'Hybrid', 'Selisih', 'Kesimpulan'],
                formats={
                    'ARIMA': lambda v: f'{float(v):,.4f}',
                    'Hybrid': lambda v: f'{float(v):,.4f}',
                },
            )
        semua_membaik = (lgbm['hybrid_eval']['Kesimpulan'] == 'Membaik').all()
        if semua_membaik:
            _note(KESIMPULAN_HYBRID_MEMBAIK)
        else:
            _note(KESIMPULAN_HYBRID_CAMPUR)
        _status('Pemodelan selesai!', 'success')


# Step 10: Prediksi 14 hari
def isi_step10(kotak, lgbm, pasar_list):
    with kotak:
        for i, p in enumerate(pasar_list):
            _sub(p)
            if i < len(lgbm['fig_future_static']):
                _image_b64(lgbm['fig_future_static'][i], align='center')
            tabel_prediksi = lgbm['future_tables'][p].copy()
            tabel_prediksi['Tanggal'] = pd.to_datetime(tabel_prediksi['Tanggal']).dt.strftime('%d-%m-%Y')
            with ui.column().style('width:fit-content;max-width:100%;align-items:flex-start;gap:8px;margin:4px auto 24px'):
                ui.label('Nilai Prediksi 14 Hari ke Depan').style(
                    'font-size:16px;font-weight:800;color:#365d3c;margin-left:0'
                )
                _table(
                    tabel_prediksi,
                    formats={'Prediksi Hybrid Optuna (Rp)': lambda v: f'Rp {float(v):,.0f}'},
                )
        kisaran = []
        for p in pasar_list:
            nilai = pd.to_numeric(lgbm['future_tables'][p]['Prediksi Hybrid Optuna (Rp)'])
            kisaran.append(f'{p} berada pada kisaran Rp{nilai.min():,.0f}–Rp{nilai.max():,.0f} dengan rata-rata sekitar Rp{nilai.mean():,.0f}')
        _note(
            'Selama 14 hari ke depan, model memperkirakan harga ' + '; '.join(kisaran) + '. '
            'Plot menunjukkan arah perubahan harga yang diperkirakan dari hari ke hari, sedangkan tabel memberikan '
            'nilai prediksi pada setiap tanggal. Hasil ini merupakan estimasi model berdasarkan pola historis dan '
            'bukan harga pasti yang akan terjadi.'
        )


# Susun halaman & jalankan analisis
def render():
    ui.add_head_html(CSS_HALAMAN)

    # Memori halaman (data & hasil tiap tahap)
    state = {
        'df_raw': None, 'runner': None, 'prep': None, 'arima': None, 'lgbm': None,
        'pasar_list': [],
        'orders': {},
        'lags': {},
    }

    with ui.row().style('display:flex;min-height:100vh;width:100%;gap:0!important'):
        build_sidebar('/analisis')
        with ui.column().style(f'flex:1;min-width:0;background:{PAGE_BG}'):
            with ui.element('div').style(GAYA_HEADER):
                ui.label('Analisis Harga Cabai Rawit Merah').classes('w-full text-center').style(
                    'font-size:26px;font-weight:800'
                )

            with ui.column().style('padding:18px 28px 28px;width:100%;gap:0'):
                tombol_mulai = buat_kotak_upload(state)
                nav = buat_navigasi()
                kartu, isi = buat_kartu_step()

                # Munculkan kartu step & aktifkan tombol navigasinya
                def tampilkan(kunci):
                    kartu[kunci].style('display:block;width:100%')
                    nav[kunci].props(remove='disable')

                # Alur utama saat MULAI ANALISIS diklik
                async def jalankan_analisis():
                    if state['df_raw'] is None:
                        ui.notify('Upload file terlebih dahulu.', type='warning')
                        return
                    tombol_mulai.props('disable')
                    pasar_list = state['pasar_list']
                    try:
                        runner = NotebookPipeline()
                        state['runner'] = runner
                        ui.notify('Mulai Analisis', type='info')

                        # Tahap persiapan (di belakang layar)
                        prep = await run.io_bound(runner.prepare, state['df_raw'])
                        state['prep'] = prep
                        isi_step1(isi['s1'], prep)
                        tampilkan('s1')
                        isi_step2(isi['s2'], prep)
                        tampilkan('s2')
                        isi_step3(isi['s3'], prep)
                        tampilkan('s3')
                        isi_step4(isi['s4'], prep)
                        tampilkan('s4')

                        orde_selesai = asyncio.Event()
                        isi_step5_input(isi['s5'], prep, pasar_list, state, orde_selesai)
                        tampilkan('s5')
                        # Tunggu user simpan orde
                        await orde_selesai.wait()

                        with isi['s5']:
                            _status('Mencari model terbaik berdasarkan nilai AIC...', 'info')
                        # Tahap ARIMA
                        ar = await run.io_bound(runner.run_arima, state['orders'])
                        state['arima'] = ar
                        isi_step5_hasil(isi['s5'], ar, pasar_list)

                        isi_step6(isi['s6'], ar, pasar_list)
                        tampilkan('s6')
                        lag_selesai = asyncio.Event()
                        isi_step7_input(isi['s7'], ar, pasar_list, state, lag_selesai)
                        tampilkan('s7')
                        # Tunggu user simpan lag
                        await lag_selesai.wait()

                        isi_step8_menunggu(isi['s8'])
                        tampilkan('s8')
                        # Tahap LightGBM & hybrid
                        lgbm = await run.io_bound(runner.run_lgbm, state['lags'])
                        state['lgbm'] = lgbm
                        isi_step8_hasil(isi['s8'], lgbm, pasar_list)
                        isi_step9(isi['s9'], lgbm, pasar_list)
                        tampilkan('s9')
                        isi_step10(isi['s10'], lgbm, pasar_list)
                        tampilkan('s10')

                        ui.notify('Pipeline notebook selesai.', type='positive')
                    except Exception as ex:
                        traceback.print_exc()
                        ui.notify(f'Pipeline gagal: {ex}', type='negative', timeout=10000)
                    # Tombol MULAI aktif lagi, berhasil atau gagal
                    finally:
                        tombol_mulai.props(remove='disable')

                tombol_mulai.on('click', jalankan_analisis)
