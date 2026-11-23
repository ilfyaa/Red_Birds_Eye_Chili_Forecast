# Halaman Seputar Cabai Rawit (/cabai) - membaca data/CRMPKG.xlsx
from pathlib import Path
import pandas as pd
from nicegui import ui
from components.sidebar import build_sidebar
from components.gaya import BARIS_UTAMA, KOLOM_ISI

# Nama kolom pasar (harus sama dengan judul kolom Excel)
PASAR_LIST = ['Pasar Genteng', 'Pasar Keputran']
DATA_PATH = Path(__file__).resolve().parents[1] / 'data' / 'CRMPKG.xlsx'
BARIS_PER_HALAMAN = 20

# Warna judul kolom tabel
CSS_TABEL = '''
<style>
  .cabai-table .q-table thead th{background:#e7f0e4;color:#264b2f;font-weight:800}
</style>
'''

# Gaya kotak & kartu
GAYA_KOTAK = 'background:white;border:1px solid #dce6da;border-radius:15px;padding:18px'
GAYA_JUDUL_KOTAK = 'font-size:16px;font-weight:800;color:#263e2c;margin-bottom:8px'
GAYA_KARTU_INFO = (
    'background:#f8fbf7;border:1px solid #dce6da;border-radius:13px;'
    'padding:17px 18px;min-height:190px'
)

# Isi 3 kartu informasi cabai
INFO_CABAI = [
    (
        'Apa itu?',
        'Cabai rawit merah atau <i>Capsicum frustescens L.</i> merupakan tanaman hortikultura dari famili <i>Solanaceae</i>. '
        'Buahnya umumnya berukuran sekitar 2–4 cm dan memiliki sekitar 20–40 biji per buah. '
        'Tingkat kepedasannya tinggi, sekitar 104.300–141.200 <i>Scoville Heat Unit</i> (SHU), terutama karena kandungan capsaicin.'
    ),
    (
        'Kandungan dan Budidaya',
        'Selain capsaicin, cabai rawit merah mengandung vitamin C, vitamin A, minyak atsiri, resin, dan flavonoid. '
        'Tanaman ini sesuai dibudidayakan di wilayah tropis dengan media tanam yang memiliki struktur serta unsur hara yang baik, '
        'dan memerlukan penyinaran matahari yang cukup untuk mendukung pertumbuhan.'
    ),
    (
        'Peran dan Pemanfaatan',
        'Cabai rawit merah banyak digunakan sebagai bumbu dan penyedap, serta penting bagi usaha kuliner dan industri pengolahan pangan. '
        'Komoditas ini juga memiliki nilai ekonomi tinggi dan dapat dimanfaatkan di bidang kesehatan. '
        'Pada sistem ini, data harga Pasar Genteng dan Pasar Keputran digunakan untuk membaca perubahan harga dan mendukung proses prediksi.'
    ),
]


# Baca & rapikan data Excel (tanggal terbaru di atas)
def muat_data():
    df = pd.read_excel(DATA_PATH)
    df.columns = [str(c).strip() for c in df.columns]
    df['Tanggal'] = pd.to_datetime(df['Tanggal'], errors='coerce')
    for p in PASAR_LIST:
        df[p] = pd.to_numeric(df[p], errors='coerce')
    df = df.dropna(subset=['Tanggal'] + PASAR_LIST)
    return df.sort_values('Tanggal', ascending=False, kind='stable').reset_index(drop=True)


# Tabel riwayat harga, 20 baris per halaman
def buat_tabel_historis(df):
    semua_baris = [
        {
            'Tanggal': tgl.strftime('%d-%m-%Y'),
            'Pasar Genteng (Rp)': f'{genteng:,.0f}',
            'Pasar Keputran (Rp)': f'{keputran:,.0f}',
        }
        for tgl, genteng, keputran in zip(df['Tanggal'], df['Pasar Genteng'], df['Pasar Keputran'])
    ]
    kolom = [
        {'name': nama, 'label': nama, 'field': nama, 'align': 'center'}
        for nama in ['Tanggal', 'Pasar Genteng (Rp)', 'Pasar Keputran (Rp)']
    ]
    # Nomor halaman tabel yang sedang tampil
    halaman = {'nomor': 0}
    jumlah_halaman = max(1, (len(semua_baris) + BARIS_PER_HALAMAN - 1) // BARIS_PER_HALAMAN)

    def baris_halaman_ini():
        awal = halaman['nomor'] * BARIS_PER_HALAMAN
        return semua_baris[awal:awal + BARIS_PER_HALAMAN]

    with ui.column().style('width:100%;align-items:center;gap:8px'):
        tabel = ui.table(
            columns=kolom,
            rows=baris_halaman_ini(),
            row_key='Tanggal',
        ).props('flat bordered dense separator=cell hide-bottom').classes('cabai-table').style('width:min(980px,100%);')

        with ui.row().style('width:min(980px,100%);justify-content:flex-end;align-items:center;gap:8px;padding:2px 4px'):
            label_halaman = ui.label(f'1–{min(BARIS_PER_HALAMAN, len(semua_baris))} dari {len(semua_baris):,}').style('font-size:11px;color:#68736b')
            tombol_mundur = ui.button(icon='chevron_left').props('flat round dense').style('color:#5d6a60')
            tombol_maju = ui.button(icon='chevron_right').props('flat round dense').style('color:#5d6a60')

            # Ganti isi tabel & atur tombol aktif/nonaktif
            def segarkan():
                awal = halaman['nomor'] * BARIS_PER_HALAMAN
                akhir = min(awal + BARIS_PER_HALAMAN, len(semua_baris))
                tabel.rows = baris_halaman_ini()
                tabel.update()
                label_halaman.set_text(f'{awal + 1}–{akhir} dari {len(semua_baris):,}')
                if halaman['nomor'] <= 0:
                    tombol_mundur.props('disable')
                else:
                    tombol_mundur.props(remove='disable')
                if halaman['nomor'] >= jumlah_halaman - 1:
                    tombol_maju.props('disable')
                else:
                    tombol_maju.props(remove='disable')

            def halaman_sebelumnya():
                if halaman['nomor'] > 0:
                    halaman['nomor'] -= 1
                    segarkan()

            def halaman_berikutnya():
                if halaman['nomor'] < jumlah_halaman - 1:
                    halaman['nomor'] += 1
                    segarkan()

            tombol_mundur.on('click', halaman_sebelumnya)
            tombol_maju.on('click', halaman_berikutnya)
            segarkan()


# Pita judul halaman
def buat_judul_halaman():
    with ui.element('div').style(
        'background:linear-gradient(125deg,#174f24 0%,#2e7d32 56%,#c5a02c 100%);'
        'padding:18px 30px;color:white;width:100%'
    ):
        ui.label('Seputar Cabai Rawit Merah').style('font-size:20px;font-weight:800')


# 3 kartu informasi
def buat_info_cabai():
    with ui.element('div').style(
        'background:white;border:1px solid #dce6da;border-radius:16px;padding:24px 26px;'
        'box-shadow:0 7px 18px rgba(31,74,42,.05);width:100%'
    ):
        ui.label('Mengenal Cabai Rawit Merah').style('font-size:20px;font-weight:800;color:#234b2d;margin-bottom:16px')
        with ui.grid(columns=3).style('gap:14px;width:100%'):
            for judul, isi in INFO_CABAI:
                with ui.element('div').style(GAYA_KARTU_INFO):
                    ui.label(judul).style('font-size:14px;font-weight:800;color:#2b5734;margin-bottom:9px')
                    ui.html(f'<div style="font-size:12px;color:#5b675f;line-height:1.85;text-align:left">{isi}</div>')


# 4 kotak ringkasan: rata-rata, tertinggi, terendah, selisih
def buat_harga_terkini(df):
    terbaru = df.iloc[0]
    rata_hari_ini = (terbaru['Pasar Genteng'] + terbaru['Pasar Keputran']) / 2

    daftar_tertinggi = []
    daftar_terendah = []
    for p in PASAR_LIST:
        baris_max = df[p].idxmax()
        baris_min = df[p].idxmin()
        daftar_tertinggi.append((float(df.loc[baris_max, p]), p, df.loc[baris_max, 'Tanggal']))
        daftar_terendah.append((float(df.loc[baris_min, p]), p, df.loc[baris_min, 'Tanggal']))
    nilai_tertinggi, pasar_tertinggi, tgl_tertinggi = max(daftar_tertinggi, key=lambda x: x[0])
    nilai_terendah, pasar_terendah, tgl_terendah = min(daftar_terendah, key=lambda x: x[0])

    selisih = abs(float(terbaru['Pasar Genteng']) - float(terbaru['Pasar Keputran']))
    pasar_lebih_mahal = 'Pasar Genteng' if terbaru['Pasar Genteng'] >= terbaru['Pasar Keputran'] else 'Pasar Keputran'

    ringkasan = [
        ('Rata-rata harga hari ini', f'Rp {rata_hari_ini:,.0f}', terbaru['Tanggal'].strftime('%d %B %Y')),
        ('Harga tertinggi', f'Rp {nilai_tertinggi:,.0f}', f'{pasar_tertinggi} · {tgl_tertinggi.strftime("%d %B %Y")}'),
        ('Harga terendah', f'Rp {nilai_terendah:,.0f}', f'{pasar_terendah} · {tgl_terendah.strftime("%d %B %Y")}'),
        ('Selisih harga hari ini', f'Rp {selisih:,.0f}', f'{pasar_lebih_mahal} lebih tinggi'),
    ]
    with ui.element('div').style('width:100%'):
        ui.label('Informasi Harga Terkini').style('font-size:17px;font-weight:800;color:#234b2d;margin-bottom:10px')
        with ui.grid(columns=4).style('gap:12px;width:100%'):
            for judul, nilai, keterangan in ringkasan:
                with ui.element('div').style('background:white;border:1px solid #dce6da;border-radius:13px;padding:14px 16px'):
                    ui.label(judul).style('font-size:10px;color:#748077')
                    ui.label(nilai).style('font-size:15px;font-weight:800;color:#263e2c;margin-top:4px')
                    ui.label(keterangan).style('font-size:10px;color:#6f7c72;margin-top:2px')


# Grafik interaktif 14 hari terakhir
def buat_grafik_tren(df):
    terakhir = df.head(14).sort_values('Tanggal').copy()
    tanggal = terakhir['Tanggal'].dt.strftime('%d %b').tolist()

    with ui.element('div').style(GAYA_KOTAK):
        ui.label('Tren Harga 14 Hari Terakhir').style(GAYA_JUDUL_KOTAK)
        ui.label('Arahkan kursor ke titik untuk melihat tanggal dan harga.').style('font-size:10px;color:#7b867e;margin-bottom:8px')
        ui.echart({
            'tooltip': {'trigger': 'axis', 'show': True, 'axisPointer': {'type': 'cross', 'snap': True}},
            'legend': {'data': ['Genteng', 'Keputran'], 'top': 0, 'left': 0},
            'grid': {'left': 65, 'right': 18, 'top': 42, 'bottom': 38},
            'xAxis': {'type': 'category', 'boundaryGap': False, 'data': tanggal, 'axisLabel': {'interval': 2}},
            'yAxis': {'type': 'value'},
            'series': [
                {'name': 'Genteng', 'type': 'line', 'smooth': True, 'data': terakhir['Pasar Genteng'].tolist(), 'symbol': 'circle', 'symbolSize': 7, 'lineStyle': {'width': 3}, 'areaStyle': {'opacity': 0.05}},
                {'name': 'Keputran', 'type': 'line', 'smooth': True, 'data': terakhir['Pasar Keputran'].tolist(), 'symbol': 'circle', 'symbolSize': 7, 'lineStyle': {'width': 3, 'type': 'dashed'}, 'areaStyle': {'opacity': 0.04}},
            ],
        }).style('width:100%;height:260px')


# Harga terbaru dibanding rata-rata historis tiap pasar
def buat_posisi_harga(df):
    terbaru = df.iloc[0]
    with ui.element('div').style(GAYA_KOTAK):
        ui.label('Posisi Harga Hari Ini').style('font-size:16px;font-weight:800;color:#263e2c;margin-bottom:14px')
        for p in PASAR_LIST:
            rata_historis = float(df[p].mean())
            persen = (float(terbaru[p]) - rata_historis) / rata_historis * 100 if rata_historis else 0
            arah = 'di atas' if persen >= 0 else 'di bawah'
            with ui.element('div').style('border-bottom:1px solid #edf1eb;padding:13px 2px'):
                with ui.row().style('align-items:flex-start;justify-content:space-between;width:100%;gap:14px'):
                    with ui.column().style('gap:3px'):
                        ui.label(p).style('font-size:13px;font-weight:800;color:#324a38')
                        ui.label(terbaru['Tanggal'].strftime('%d %B %Y')).style('font-size:10px;color:#7a857d')
                    with ui.column().style('gap:2px;align-items:flex-end'):
                        ui.label(f"Rp {terbaru[p]:,.0f} / kg").style('font-size:16px;font-weight:800;color:#2e7d32')
                        ui.label(f"{abs(persen):.1f}% {arah} rata-rata historis").style('font-size:10px;color:#708077')
        ui.label('Bagian ini menunjukkan posisi harga terbaru dibandingkan rata-rata historis masing-masing pasar, sehingga kondisi harga hari ini dapat dibaca dalam konteks data jangka panjang.').style('font-size:10px;color:#7a857d;line-height:1.6;margin-top:12px')


# Kotak pembungkus tabel riwayat
def buat_tabel_data(df):
    with ui.element('div').style(GAYA_KOTAK + ';width:100%'):
        ui.label('Historis Harga Cabai Rawit Merah').style(GAYA_JUDUL_KOTAK)
        buat_tabel_historis(df)


# Susun halaman
def render():
    df = muat_data()
    ui.add_head_html(CSS_TABEL)

    with ui.row().style(BARIS_UTAMA):
        build_sidebar('/cabai')
        with ui.column().style(KOLOM_ISI):
            buat_judul_halaman()
            with ui.column().style('padding:28px 34px 42px;gap:20px;width:100%'):
                buat_info_cabai()
                buat_harga_terkini(df)
                with ui.grid(columns=2).style('gap:16px;width:100%'):
                    buat_grafik_tren(df)
                    buat_posisi_harga(df)
                buat_tabel_data(df)
