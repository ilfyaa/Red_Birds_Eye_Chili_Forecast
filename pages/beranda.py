# Halaman Beranda (/)
from nicegui import ui
from components.sidebar import build_sidebar
from components.gaya import BARIS_UTAMA, KOLOM_ISI


# Gambar latar banner (titik-titik & lengkungan)
SVG_LATAR = '''
<svg style="position:absolute;inset:0;width:100%;height:100%;z-index:0;pointer-events:none"
     viewBox="0 0 1000 340" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice">
  <defs>
    <pattern id="hero-dots" x="0" y="0" width="30" height="30" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1.4" fill="rgba(255,255,255,.10)"/>
    </pattern>
    <linearGradient id="hero-glow" x1="0" x2="1">
      <stop offset="0" stop-color="rgba(255,255,255,.02)"/>
      <stop offset="1" stop-color="rgba(255,255,255,.09)"/>
    </linearGradient>
  </defs>
  <rect width="1000" height="340" fill="url(#hero-dots)"/>
  <path d="M650,-40 C790,40 920,20 1050,130 L1050,430 L730,430 C850,300 800,120 650,-40Z" fill="url(#hero-glow)"/>
  <circle cx="110" cy="320" r="125" fill="rgba(0,0,0,.05)"/>
</svg>
'''

# Ilustrasi cabai di kanan banner
SVG_CABAI = '''
<svg width="205" height="248" viewBox="0 0 250 300" xmlns="http://www.w3.org/2000/svg"
     style="display:block;width:205px;height:248px;filter:drop-shadow(0 18px 14px rgba(0,0,0,.16))">
  <ellipse cx="132" cy="270" rx="58" ry="13" fill="rgba(0,0,0,.16)"/>
  <path d="M120 54 C112 34 121 14 139 5" fill="none" stroke="#174b22" stroke-width="6" stroke-linecap="round"/>
  <path d="M120 45 C99 31 77 33 71 48 C87 55 106 53 120 45Z" fill="#2f7d32"/>
  <path d="M122 42 C139 27 164 28 170 43 C154 51 136 50 122 42Z" fill="#4d9544"/>
  <path d="M108 61 C96 79 91 107 96 135 C102 168 119 192 137 210 C151 225 157 244 151 261
           C174 246 190 218 193 187 C196 153 187 119 169 89 C155 66 125 48 108 61Z"
        fill="#d73732"/>
  <path d="M112 66 C102 85 100 111 106 136 C113 163 127 184 143 199 C127 177 120 154 118 128
           C116 101 121 78 132 59 C124 57 116 59 112 66Z" fill="rgba(255,255,255,.14)"/>
  <path d="M151 260 C151 270 147 279 141 287 C147 280 158 271 165 257Z" fill="#7e1718"/>
  <ellipse cx="132" cy="85" rx="6" ry="15" fill="rgba(255,255,255,.22)" transform="rotate(-18 132 85)"/>
</svg>
'''


# Gaya banner, teks, tombol, dan kartu menu
GAYA_BANNER = (
    'background:linear-gradient(125deg,#174f24 0%,#2e7d32 46%,#d0ad32 100%);'
    'padding:44px 68px;color:white;display:block;position:relative;overflow:hidden;'
    'width:100%;min-height:330px;max-height:350px'
)
GAYA_KOLOM_TEKS = (
    'gap:14px;position:absolute;left:68px;top:58px;z-index:2;width:650px;'
    'max-width:calc(100% - 420px);margin:0!important;padding:0!important;'
    'text-align:left!important;align-items:flex-start!important'
)
GAYA_JUDUL_PUTIH = (
    'font-size:32px!important;font-weight:900!important;line-height:1.05!important;'
    'color:white!important;margin:0!important;padding:0!important'
)
GAYA_JUDUL_KUNING = (
    'font-size:32px!important;font-weight:900!important;line-height:1.05!important;'
    'color:#fff3a7!important;margin:0!important;padding:0!important'
)
GAYA_TOMBOL = (
    'background:white;color:#1b5e20;border:none;border-radius:10px;'
    'padding:10px 20px;font-size:13px;font-weight:800;margin-top:10px'
)
GAYA_BOX_CABAI = (
    'position:absolute;right:68px;top:40px;width:205px;height:248px;'
    'z-index:3;display:block;pointer-events:none'
)
GAYA_BAGIAN_MENU = 'padding:42px 68px 56px;background:#eef3e7;width:100%'
GAYA_KARTU = (
    'background:white;border:1px solid #dbe5d8;border-radius:15px;padding:22px;'
    'display:flex;flex-direction:column;gap:12px;cursor:pointer;box-shadow:0 7px 18px rgba(31,74,42,.05)'
)

# Kartu menu: ikon, warna latar, warna ikon, judul, deskripsi, alamat
DAFTAR_MENU = [
    ('eco', '#fde8e8', '#c62828', 'Seputar Cabai Rawit Merah',
     'Informasi komoditas, ringkasan harga, tren singkat, dan data historis pasar.', '/cabai'),
    ('psychology', '#e8f5e9', '#2e7d32', 'Prediksi',
     'Pelajari setiap tahap pipeline ARIMA-LightGBM dan cara membaca hasilnya.', '/prediksi'),
    ('show_chart', '#fff8e1', '#f57f17', 'Analisis Harga',
     'Jalankan proses analisis dari notebook secara bertahap sampai prediksi 14 hari.', '/analisis'),
]


# Judul, deskripsi, tombol Mulai Analisis
def buat_teks_banner():
    with ui.column().style(GAYA_KOLOM_TEKS):
        with ui.column().style('gap:2px;align-items:flex-start;margin:0;padding:0'):
            ui.label('Prediksi Harga').style(GAYA_JUDUL_PUTIH)
            ui.label('Cabai Rawit Merah').style(GAYA_JUDUL_KUNING)
        ui.label(
            'Sistem Prediksi berbasis ARIMA-LightGBM untuk membantu membaca pola perubahan harga '
            'cabai rawit merah di pasar tradisional Kota Surabaya.'
        ).style('font-size:13px;opacity:.94;line-height:1.85;color:white;max-width:590px')
        ui.button('Mulai Analisis', icon='show_chart').style(GAYA_TOMBOL).on(
            'click', lambda: ui.navigate.to('/analisis')
        )


# Banner: latar + teks + gambar cabai
def buat_banner():
    with ui.element('div').style(GAYA_BANNER):
        ui.html(SVG_LATAR)
        buat_teks_banner()
        with ui.element('div').style(GAYA_BOX_CABAI):
            ui.html(SVG_CABAI)


# 3 kartu menu yang bisa diklik
def buat_kartu_menu():
    with ui.element('div').style(GAYA_BAGIAN_MENU):
        ui.html('<div style="font-size:21px;font-weight:900;color:#204b2a;margin-bottom:24px;text-align:left;line-height:1.2"><strong>Jelajahi Sistem</strong></div>')
        with ui.grid(columns=3).style('gap:18px'):
            for icon, bg, fg, judul, deskripsi, alamat in DAFTAR_MENU:
                with ui.element('div').style(GAYA_KARTU).on('click', lambda p=alamat: ui.navigate.to(p)):
                    with ui.element('div').style(f'width:46px;height:46px;border-radius:12px;background:{bg};display:flex;align-items:center;justify-content:center'):
                        ui.icon(icon).style(f'font-size:23px;color:{fg}')
                    ui.label(judul).style('font-size:15px;font-weight:800;color:#233c29')
                    ui.label(deskripsi).style('font-size:12px;color:#657169;line-height:1.75;flex:1')
                    ui.label('Selengkapnya →').style('font-size:11px;font-weight:700;color:#2e7d32')


# Susun halaman: sidebar + banner + kartu
def render():
    with ui.row().style(BARIS_UTAMA):
        build_sidebar('/')
        with ui.column().style(KOLOM_ISI):
            buat_banner()
            buat_kartu_menu()
