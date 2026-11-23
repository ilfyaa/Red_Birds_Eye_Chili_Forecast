# Sidebar menu kiri (dipakai semua halaman)
from nicegui import ui

# Daftar menu: tulisan, ikon, alamat tujuan
MENU_ITEMS = [
    {"label": "Beranda",             "icon": "home",       "path": "/"},
    {"label": "Seputar Cabai Rawit", "icon": "eco",        "path": "/cabai"},
    {"label": "Prediksi",            "icon": "psychology", "path": "/prediksi"},
    {"label": "Analisis Harga",      "icon": "show_chart", "path": "/analisis"},
]

# Gaya sidebar (sticky: tetap di tempat saat di-scroll)
GAYA_SIDEBAR = (
    "width:220px;flex-shrink:0;background:#1b5e20;display:flex;"
    "flex-direction:column;min-height:100vh;position:sticky;top:0;height:100vh;overflow-y:auto"
)
GAYA_BARIS_LOGO = "padding:18px 16px 14px;border-bottom:1px solid rgba(255,255,255,0.08);align-items:center;gap:10px"
GAYA_IKON_LOGO = (
    "font-size:24px;color:white;background:rgba(255,255,255,0.15);"
    "border-radius:8px;padding:6px"
)
GAYA_JUDUL_MENU = (
    "font-size:9px;color:rgba(255,255,255,0.35);letter-spacing:0.08em;"
    "text-transform:uppercase;padding:12px 14px 4px"
)


# Logo + nama aplikasi
def buat_logo():
    with ui.row().style(GAYA_BARIS_LOGO):
        ui.icon("local_fire_department").style(GAYA_IKON_LOGO)
        with ui.column().style("gap:0"):
            ui.label("CabaiCast").style("font-size:14px;font-weight:600;color:white")
            ui.label("Surabaya").style("font-size:10px;color:rgba(255,255,255,0.45)")


# Tombol menu; menu halaman aktif disorot
def buat_menu(halaman_aktif):
    for item in MENU_ITEMS:
        aktif = halaman_aktif == item["path"]
        warna_latar = "rgba(255,255,255,0.18)" if aktif else "transparent"
        # Klik -> pindah halaman (p dikunci per menu)
        with ui.row().style(
            f"padding:8px 12px;margin:2px 8px;border-radius:8px;background:{warna_latar};"
            "color:rgba(255,255,255,0.65);cursor:pointer;align-items:center;gap:10px;"
            "transition:background 0.15s"
        ).on("click", lambda p=item["path"]: ui.navigate.to(p)):
            ui.icon(item["icon"]).style("font-size:18px;color:inherit")
            ui.label(item["label"]).style("font-size:12px;color:inherit")


# Fungsi utama: susun logo, judul, menu
def build_sidebar(current_path="/"):
    with ui.column().style(GAYA_SIDEBAR):
        buat_logo()
        ui.separator().style("background:rgba(255,255,255,0.08);margin:0")
        ui.label("MENU UTAMA").style(GAYA_JUDUL_MENU)
        buat_menu(current_path)
        # Pengisi ruang kosong di bawah menu
        ui.element("div").style("flex:1")
