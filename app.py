# Pintu masuk web: daftarkan halaman lalu jalankan server
import os
from nicegui import ui
from pages import beranda, cabai, prediksi, analisis

# Baca style.css dari folder yang sama dengan file ini
folder = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(folder, "style.css")) as f:
    css = f.read()


# Tempel CSS ke <head> halaman
def pasang_css():
    ui.add_head_html(f"<style>{css}</style>")


# Alamat URL -> fungsi pembuat halaman
@ui.page("/")
def halaman_beranda():
    pasang_css()
    beranda.render()


@ui.page("/cabai")
def halaman_cabai():
    pasang_css()
    cabai.render()


@ui.page("/prediksi")
def halaman_prediksi():
    pasang_css()
    prediksi.render()


@ui.page("/analisis")
def halaman_analisis():
    pasang_css()
    analisis.render()


# Jalankan server di http://localhost:8080
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="CabaiCast", port=8080, reload=False)
