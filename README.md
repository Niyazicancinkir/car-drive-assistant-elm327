🚗 Custom OBD2 Telemetri ve Agresif Sürüş Asistanı
Hazır satılan gecikmeli Bluetooth OBD uygulamalarına tahammül edemediğim için kendi yol bilgisayarımı kodladım. Bu proje, 16 yıllık bir Ford Fiesta Van'ın (2008) beynine (ECU) USB üzerinden bağlanarak 50ms gecikme ile canlı telemetri verisi çeker. Sadece veri okumakla kalmaz, 3000 deviri geçtiğinizde sizi sesli olarak azarlayan kaba bir asistana dönüşür.

🛠️ Proje Mimarisi ve Dosya Yapısı
Sistem, veriyi işleme, loglama ve kullanıcıya sunma (UI/Ses) olarak modüler şekilde ayrılmıştır:

app.py: Sistemin ana orkestratörü. Tüm servisleri (telemetri, UI, ses) burada ayağa kaldırıyoruz.

telemetry.py: İşin kirli kısmı. ECU'dan ham veriyi çekip, aracın vermediği anlık tüketim gibi metrikleri kendi algoritmalarımızla hesapladığımız modül.

ui.py: Verilerin 50ms gecikmeyle ekrana basıldığı arayüz.

audio.py & play_sound.vbs: Araba 3000 deviri geçtiğinde veya hatalı bir işlemde tetiklenen agresif asistanın ses kontrolcüsü.

cimenlere_girme.m4a: Asistanın sizi uyarırken kullandığı o meşhur ses dosyası.

logger.py: Saha testlerinde nerede çuvalladığımızı görmek için telemetri verilerini telemetry_log_*.csv formatında saniye saniye kaydeder.

⚙️ Kurulum ve Çalıştırma
Sistemin donanımla çarpıştığı bir laboratuvar projesi olduğunu unutmayın. Gerekli kütüphaneleri kurduktan sonra doğrudan ana betiği çalıştırın:

Gereksinimleri yükleyin: pip install -r requirements.txt

OBD2 USB kablonuzu bağlayın ve portu kontrol edin.

Sistemi başlatın: python app.py
