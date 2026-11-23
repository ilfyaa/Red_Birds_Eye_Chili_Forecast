# Halaman Prediksi (/prediksi) - panduan alur model, teks statis
from nicegui import ui
from components.sidebar import build_sidebar
from components.gaya import BARIS_UTAMA, KOLOM_ISI

# Isi penjelasan 10 step (ubah teks di sini)
STEPS = [
    {
        'name': 'Data Awal',
        'what': 'Tahap awal untuk melihat kondisi data harga sebelum dilakukan pemodelan.',
        'do': 'Sistem membaca data harga Pasar Genteng dan Pasar Keputran, menampilkan grafik historis, lalu merangkum jumlah data, rata-rata, standar deviasi, nilai minimum, dan maksimum.',
        'read': 'Perhatikan arah pergerakan pada grafik dan besarnya penyebaran pada tabel. Rata-rata menunjukkan tingkat harga secara umum, sedangkan standar deviasi dan rentang minimum–maksimum membantu melihat seberapa besar harga berfluktuasi.',
    },
    {
        'name': 'Split Data',
        'what': 'Pembagian data menjadi data train dan data test.',
        'do': 'Data train digunakan untuk membangun model. Sebanyak 14 observasi terakhir dipisahkan sebagai data test agar kemampuan model dapat diuji pada periode yang tidak digunakan saat pelatihan.',
        'read': 'Tabel menunjukkan periode serta jumlah data train dan test. Karena data berbentuk deret waktu, pembagian dilakukan berdasarkan urutan tanggal tanpa mengacak observasi.',
    },
    {
        'name': 'Uji Stasioner Varians',
        'what': 'Pemeriksaan kestabilan varians, yaitu apakah besar-kecilnya fluktuasi data relatif stabil sepanjang waktu.',
        'do': 'Sistem menghitung nilai lambda Box-Cox pada data train. Jika nilai lambda yang dibulatkan tidak sama dengan 1, data ditransformasi menggunakan Box-Cox agar skala fluktuasinya lebih stabil.',
        'read': 'Jika rounded lambda = 1, varians dianggap stasioner. Jika tidak sama dengan 1, transformasi diperlukan. Plot hasil transformasi menunjukkan data yang sudah disesuaikan sebelum masuk ke tahap berikutnya.',
    },
    {
        'name': 'Uji Stasioner Mean',
        'what': 'Pemeriksaan kestabilan rata-rata deret waktu menggunakan uji Augmented Dickey-Fuller (ADF).',
        'do': 'Sistem melakukan uji ADF pada data train dan kembali mengeceknya setelah differencing orde satu. Differencing mengubah data menjadi selisih antarperiode agar pola rata-rata lebih stabil.',
        'read': 'Jika p-value < 0,05, data dinyatakan stasioner dalam mean. Plot ACF juga membantu membaca kondisi secara visual: pola yang meluruh sangat lambat biasanya mengindikasikan data belum stabil. Jika hasil visual dan ADF berbeda, keputusan statistik tetap dilihat dari ADF, sedangkan differencing tetap dapat digunakan sesuai rancangan pemodelan untuk menjaga kestasioneran.',
    },
    {
        'name': 'Pemodelan ARIMA',
        'what': 'ARIMA (AutoRegressive Integrated Moving Average) adalah model deret waktu yang menggabungkan komponen AR, differencing, dan MA untuk menangkap pola linier data.',
        'do': 'Pertama, plot ACF dan PACF digunakan untuk menentukan kandidat orde. PACF membantu membaca kandidat p (AR), ACF membantu membaca kandidat q (MA), sedangkan d berasal dari jumlah differencing. Setelah orde dimasukkan, kandidat model diestimasi dengan Maximum Likelihood Estimation (MLE) dan dibandingkan menggunakan Akaike Information Criterion (AIC). Model terpilih kemudian dipakai untuk memprediksi data test.',
        'read': 'Pada plot ACF dan PACF, perhatikan spike yang melewati batas signifikansi dan titik ketika spike mulai melemah atau cut off. ACF digunakan sebagai petunjuk kandidat orde q, sedangkan PACF sebagai petunjuk kandidat orde p. Setelah kandidat orde diuji, lihat tabel AIC dan pilih nilai AIC paling kecil sebagai model terbaik. Setelah model ARIMA terbentuk, baca hasil evaluasi pada RMSE, MAE, dan MAPE: semakin kecil nilai error, semakin baik kemampuan prediksinya.',
    },
    {
        'name': 'Uji Asumsi Residual',
        'what': 'Tahap diagnosis untuk memeriksa karakter residual, yaitu selisih antara nilai aktual dan hasil yang diperkirakan ARIMA.',
        'do': 'Residual diperiksa dengan Kolmogorov-Smirnov untuk normalitas, Ljung-Box untuk autokorelasi/white noise, dan ARCH-LM untuk kestabilan varians residual.',
        'read': 'p-value dibandingkan dengan 0,05. Normalitas residual terutama berkaitan dengan inferensi dan interval prediksi, sedangkan Ljung-Box penting untuk memastikan tidak ada autokorelasi yang tersisa. ARCH-LM menunjukkan apakah varians residual stabil atau berubah dari waktu ke waktu. Residual selanjutnya digunakan pada LightGBM untuk menangkap pola yang masih tersisa.',
    },
    {
        'name': 'Pemilihan Lag Residual',
        'what': 'Tahap memilih residual masa lalu yang akan dijadikan fitur untuk LightGBM.',
        'do': 'Sistem menampilkan plot PACF residual ARIMA. Lag yang signifikan menjadi kandidat karena menunjukkan residual masa lalu masih memiliki hubungan langsung dengan residual saat ini.',
        'read': 'Perhatikan spike PACF yang melewati batas signifikansi. Nomor lag pada spike tersebut dapat dipilih sebagai kandidat fitur. Semakin relevan lag yang dipilih, semakin baik LightGBM memiliki informasi untuk mempelajari pola residual.',
    },
    {
        'name': 'Pemodelan LightGBM',
        'what': 'LightGBM (Light Gradient Boosting Machine) adalah algoritma machine learning berbasis gradient boosting decision tree. Pada model hybrid ini, LightGBM tidak memprediksi harga secara langsung, tetapi mempelajari pola residual ARIMA agar kesalahan yang masih tersisa dapat dikoreksi.',
        'do': 'Residual ARIMA direkonstruksi menjadi fitur berdasarkan lag residual yang dipilih dari PACF. Selanjutnya Optuna mencari kombinasi hyperparameter LightGBM yang memberikan error validasi paling kecil. Hyperparameter yang dioptimasi meliputi n_estimators sebagai jumlah pohon, learning_rate sebagai besar langkah pembelajaran, num_leaves sebagai jumlah daun maksimum, max_depth sebagai kedalaman maksimum pohon, dan min_child_samples sebagai jumlah minimum data pada sebuah daun. Jika ada lebih dari satu kandidat lag, setiap lag dioptimasi terlebih dahulu, lalu lag yang dipakai adalah lag yang menghasilkan model hybrid dengan MAPE paling kecil.',
        'read': 'Tabel hyperparameter menunjukkan kombinasi parameter terbaik yang ditemukan Optuna. Nilai tersebut kemudian digunakan untuk membangun LightGBM. Pada tahap ini, keluaran LightGBM berupa prediksi residual sebagai koreksi terhadap hasil ARIMA; prediksi harga akhir baru diperoleh setelah hasil ARIMA dan koreksi LightGBM digabungkan.',
    },
    {
        'name': 'ARIMA-LightGBM',
        'what': 'Tahap menggabungkan prediksi linier ARIMA dengan koreksi residual dari LightGBM menjadi model hybrid.',
        'do': 'Prediksi ARIMA ditambahkan dengan prediksi residual LightGBM. Hasil hybrid kemudian dibandingkan dengan ARIMA menggunakan RMSE, MAE, dan MAPE pada data test.',
        'read': 'Fokuskan pembacaan pada nilai Hybrid, lalu bandingkan dengan nilai ARIMA pada pasar dan metrik yang sama. Jika RMSE, MAE, atau MAPE Hybrid lebih kecil daripada ARIMA, berarti penambahan LightGBM berhasil menurunkan error pada metrik tersebut. Jika seluruh atau sebagian besar nilai evaluasi Hybrid lebih kecil, model hybrid memberikan perbaikan dibandingkan ARIMA.',
    },
    {
        'name': 'Prediksi 14 Hari',
        'what': 'Tahap akhir untuk menghasilkan perkiraan harga selama 14 hari setelah tanggal terakhir pada data.',
        'do': 'ARIMA dan LightGBM dibangun kembali menggunakan seluruh data yang tersedia, kemudian model hybrid menghasilkan prediksi harian untuk Pasar Genteng dan Pasar Keputran.',
        'read': 'Plot digunakan untuk melihat arah pergerakan harga yang diperkirakan, sedangkan tabel memberikan nilai prediksi pada setiap tanggal. Nilai tersebut merupakan estimasi model, sehingga digunakan sebagai gambaran kecenderungan harga dan bukan harga pasti yang akan terjadi.',
    },
]


# Tabel penjelasan metrik (muncul di step 5 & 9)
KETERANGAN_METRIK = [
    {'Metrik': 'RMSE', 'Fungsi': 'Mengukur besar error prediksi dan memberi penalti lebih besar pada error yang jauh. Semakin kecil semakin baik.'},
    {'Metrik': 'MAE', 'Fungsi': 'Mengukur rata-rata selisih absolut antara nilai aktual dan prediksi dalam Rupiah. Semakin kecil semakin baik.'},
    {'Metrik': 'MAPE', 'Fungsi': 'Mengukur rata-rata error dalam persen. <10% sangat baik; 10–20% baik; 20–50% cukup; >50% kurang baik.'},
]

# Gaya tampilan
GAYA_HEADER = (
    'background:#1f5f27;padding:17px 32px;color:white;width:100%;'
    'border-bottom:1px solid rgba(255,255,255,.12)'
)
GAYA_BANNER = (
    'background:linear-gradient(125deg,#174f24 0%,#2e7d32 62%,#c9a52f 100%);'
    'padding:24px 28px;color:white;width:100%;border-radius:15px;'
    'box-shadow:0 8px 22px rgba(31,74,42,.08);margin-bottom:28px'
)
GAYA_DAFTAR_STEP = (
    'display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;'
    'width:100%;margin-bottom:26px'
)
GAYA_TOMBOL_STEP = (
    'width:100%;min-height:52px;background:white;color:#294f31;'
    'border:1px solid #d5e1d2;border-radius:11px;font-size:11px;font-weight:800;'
    'padding:8px 10px;white-space:normal'
)
GAYA_KARTU = (
    'background:white;border:1px solid #d9e4d7;border-radius:14px;padding:17px 18px;'
    'box-shadow:0 5px 14px rgba(31,74,42,.04)'
)
GAYA_JUDUL_KARTU = 'font-size:15px;font-weight:800;color:#315c39;margin-bottom:8px'
GAYA_ISI_KARTU = 'font-size:12px;color:#55625a;line-height:1.85'

# Tampil / sembunyi (display flex / none)
DETAIL_TAMPIL = 'width:100%;gap:0;display:flex;margin-top:2px'
DETAIL_SEMBUNYI = 'width:100%;gap:0;display:none;margin-top:2px'
METRIK_TAMPIL = 'width:100%;display:flex;margin-top:16px;gap:10px'
METRIK_SEMBUNYI = 'width:100%;display:none;margin-top:16px;gap:10px'

TOMBOL_AKTIF = 'background:#2e7d32;color:white'
TOMBOL_BIASA = 'background:white;color:#294f31'


# Banner penjelasan model
def buat_banner():
    with ui.element('div').style(GAYA_BANNER):
        ui.label('Prediksi Model Hybrid ARIMA-LightGBM').style('font-size:23px;font-weight:800;margin-bottom:7px')
        ui.label(
            'ARIMA–LightGBM merupakan model prediksi deret waktu yang menggabungkan pendekatan statistik dengan machine learning. '
            'ARIMA digunakan untuk menangkap pola linier deret waktu, sedangkan LightGBM mempelajari pola pada residual. '
            'Sistem ini juga memanfaatkan Optimasi Optuna untuk membantu memilih hyperparameter yang sesuai pada LightGBM sebelum kedua komponen digabungkan.'
        ).style('font-size:13px;line-height:1.85;max-width:980px;opacity:.94')


# 10 tombol step
def buat_tombol_step():
    tombol = []
    with ui.element('div').style(GAYA_DAFTAR_STEP):
        for i, step in enumerate(STEPS):
            tombol.append(ui.button(f'{i+1}. {step["name"]}').style(GAYA_TOMBOL_STEP))
    return tombol


# Kartu berjudul; isi teks diisi saat step diklik
def buat_kartu(judul):
    with ui.element('div').style(GAYA_KARTU):
        ui.label(judul).style(GAYA_JUDUL_KARTU)
        return ui.label('').style(GAYA_ISI_KARTU)


# Kotak detail (awalnya tersembunyi)
def buat_kotak_detail():
    d = {}
    d['kotak'] = ui.column().style(DETAIL_SEMBUNYI)
    with d['kotak']:
        d['judul'] = ui.label('').style('font-size:22px;font-weight:800;color:#244b2e;margin-bottom:16px')

        with ui.grid(columns=3).style('gap:14px;width:100%;align-items:stretch'):
            d['apa'] = buat_kartu('Apa itu?')
            d['lakukan'] = buat_kartu('Apa yang dilakukan?')
            d['baca'] = buat_kartu('Bagaimana membaca hasilnya?')

        d['kotak_metrik'] = ui.column().style(METRIK_SEMBUNYI)
        with d['kotak_metrik']:
            d['judul_metrik'] = ui.label('Keterangan Metrik Evaluasi').style(
                'font-size:16px;font-weight:800;color:#315c39'
            )
            d['tabel_metrik'] = ui.table(
                columns=[
                    {'name': 'Metrik', 'label': 'Metrik', 'field': 'Metrik', 'align': 'left'},
                    {'name': 'Fungsi', 'label': 'Cara Membaca', 'field': 'Fungsi', 'align': 'left'},
                ],
                rows=[],
                row_key='Metrik',
            ).props('flat bordered dense separator=cell hide-bottom').style('width:min(900px,100%)')

        ui.separator().style('margin:22px 0 2px;background:#d9e3d6')
    return d


# Susun halaman & atur aksi klik
def render():
    # Step yang sedang terbuka
    aktif = {'nomor': None}

    with ui.row().style(BARIS_UTAMA):
        build_sidebar('/prediksi')
        with ui.column().style(KOLOM_ISI):
            with ui.element('div').style(GAYA_HEADER):
                ui.label('Prediksi — Panduan Alur Model').style('font-size:20px;font-weight:800')

            with ui.column().style('padding:24px 34px 46px;gap:0;width:100%'):
                buat_banner()

                ui.label('Alur Pipeline').style('font-size:21px;font-weight:800;color:#244b2e;margin-bottom:4px')
                ui.label('Klik salah satu step untuk melihat penjelasan lengkap.').style('font-size:12px;color:#6f7b72;margin-bottom:16px')

                tombol = buat_tombol_step()
                detail = buat_kotak_detail()

                # Buat fungsi klik khusus tiap tombol
                def buat_aksi_klik(nomor):
                    def klik():
                        step = STEPS[nomor]

                        # Klik tombol yang sama -> tutup detail
                        if aktif['nomor'] == nomor:
                            aktif['nomor'] = None
                            detail['kotak'].style(DETAIL_SEMBUNYI)
                            for b in tombol:
                                b.style(TOMBOL_BIASA)
                            return

                        aktif['nomor'] = nomor
                        detail['judul'].set_text(f'Step {nomor+1} — {step["name"]}')
                        detail['apa'].set_text(step['what'])
                        detail['lakukan'].set_text(step['do'])
                        detail['baca'].set_text(step['read'])

                        # Step 5 & 9 menampilkan tabel metrik
                        if nomor in (4, 8):
                            detail['tabel_metrik'].rows = KETERANGAN_METRIK
                            detail['tabel_metrik'].update()
                            if nomor == 4:
                                detail['judul_metrik'].set_text('Keterangan Metrik Evaluasi')
                            else:
                                detail['judul_metrik'].set_text('Keterangan Metrik untuk Membandingkan ARIMA dan Hybrid')
                            detail['kotak_metrik'].style(METRIK_TAMPIL)
                        else:
                            detail['kotak_metrik'].style(METRIK_SEMBUNYI)

                        detail['kotak'].style(DETAIL_TAMPIL)
                        for j, b in enumerate(tombol):
                            b.style(TOMBOL_AKTIF if j == nomor else TOMBOL_BIASA)
                    return klik

                for i, b in enumerate(tombol):
                    b.on('click', buat_aksi_klik(i))
