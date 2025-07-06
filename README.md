# Smart Cafe - Restoran Yönetim Sistemi

Modern restoran yönetimi için tasarlanmış kapsamlı bir web uygulaması. QR kod tabanlı sipariş sistemi, çoklu restoran yönetimi ve gerçek zamanlı sipariş takibi özelliklerine sahiptir.

## Özellikler

### 🎯 Ana Özellikler
- **Çoklu Restoran Yönetimi**: Sistem sahibi merkezi panelden birden fazla restoranı yönetir
- **QR Kod Menü**: Müşteriler QR kod tarayarak temassız sipariş verebilir
- **Gerçek Zamanlı Siparişler**: Siparişler anında restoran paneline iletilir
- **Rol Tabanlı Erişim**: Sistem sahibi ve restoran sahibi rolleri
- **Mobil Uyumlu**: Tüm cihazlarda sorunsuz çalışır

### 👥 Kullanıcı Rolleri
- **Sistem Sahibi**: Yeni restoranlar ve kullanıcılar oluşturur
- **Restoran Sahibi**: Menü ve siparişleri yönetir
- **Müşteri**: QR kod ile sipariş verir

## Kurulum

### Gereksinimler
- Python 3.8+
- pip (Python paket yöneticisi)

### Adımlar

1. **Projeyi klonlayın**
```bash
git clone <repo-url>
cd smart_cafe
```

2. **Sanal ortam oluşturun** (önerilir)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

3. **Gerekli paketleri yükleyin**
```bash
pip install -r requirements.txt
```

4. **Uygulamayı başlatın**
```bash
python app.py
```

5. **Tarayıcıda açın**
```
http://localhost:5000
```

## Kullanım

### İlk Giriş
- **Kullanıcı Adı**: admin
- **Şifre**: admin123

### Sistem Sahibi Paneli
1. Giriş yaptıktan sonra dashboard'a erişin
2. "Yeni Restoran" ile restoran ekleyin
3. "Yeni Kullanıcı" ile restoran sahipleri oluşturun

### Restoran Sahibi Paneli
1. Restoran sahibi hesabıyla giriş yapın
2. Menü ürünlerini ekleyin
3. QR kodları yazdırın ve masalara yerleştirin
4. Gelen siparişleri takip edin

### Müşteri Deneyimi
1. Masadaki QR kodu tarayın
2. Menüden ürünleri seçin
3. Sipariş verin
4. Sipariş durumunu takip edin

## Teknik Detaylar

### Teknoloji Stack
- **Backend**: Flask (Python)
- **Veritabanı**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **QR Kod**: Python qrcode kütüphanesi

### Veritabanı Yapısı
- `users`: Kullanıcı bilgileri ve roller
- `restaurants`: Restoran bilgileri
- `tables`: Masa bilgileri ve QR kodları
- `menu_categories`: Menü kategorileri
- `menu_items`: Menü ürünleri
- `orders`: Siparişler
- `order_items`: Sipariş detayları

### API Endpoints

#### Kimlik Doğrulama
- `POST /login`: Kullanıcı girişi
- `GET /logout`: Kullanıcı çıkışı

#### Admin Endpoints
- `GET /admin/dashboard`: Admin ana sayfa
- `POST /admin/restaurants/new`: Yeni restoran
- `POST /admin/users/new`: Yeni kullanıcı

#### Restoran Endpoints
- `GET /restaurant/dashboard`: Restoran ana sayfa
- `GET /restaurant/menu`: Menü yönetimi
- `POST /restaurant/menu/item/new`: Yeni menü ürünü
- `GET /restaurant/orders`: Sipariş listesi
- `GET /restaurant/qr-codes`: QR kodları

#### Müşteri Endpoints
- `GET /<slug>/masa-<num>`: Müşteri menü sayfası
- `POST /api/order`: Sipariş oluştur

#### API Endpoints
- `GET /api/orders/<restaurant_id>`: Restoran siparişleri
- `PUT /api/order/<order_id>/status`: Sipariş durumu güncelle

## Güvenlik

- **Şifre Şifreleme**: Werkzeug PBKDF2 ile güvenli şifre hash'leme
- **Session Yönetimi**: Flask session ile güvenli oturum yönetimi
- **SQL Injection Koruması**: Parametreli sorgular
- **XSS Koruması**: Template auto-escaping
- **Rol Bazlı Erişim**: Decorator tabanlı yetkilendirme

## Özelleştirme

### Tema Değişikliği
`static/css/style.css` dosyasındaki CSS değişkenlerini düzenleyin:

```css
:root {
    --primary: #0d6efd;
    --secondary: #6c757d;
    /* Diğer renkler... */
}
```

### Veritabanı Ayarları
`app.py` dosyasında veritabanı ayarlarını değiştirin:

```python
app.config['DATABASE'] = 'smart_cafe.db'
```

## Sorun Giderme

### Yaygın Hatalar

1. **Veritabanı hatası**
   - `smart_cafe.db` dosyasını silin ve uygulamayı yeniden başlatın

2. **Port hatası**
   - 5000 portu kullanımdaysa `app.py`'de port numarasını değiştirin

3. **QR kod görünmüyor**
   - Pillow kütüphanesinin düzgün kurulduğundan emin olun

## Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'inizi push edin (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun

## Lisans

Bu proje MIT lisansı altında dağıtılmaktadır. Detaylar için `LICENSE` dosyasına bakın.

## İletişim

Sorularınız için: [your-email@example.com]

## Ekran Görüntüleri

### Admin Dashboard
![Admin Dashboard](docs/images/admin-dashboard.png)

### Restoran Paneli
![Restoran Paneli](docs/images/restaurant-panel.png)

### Müşteri Menüsü
![Müşteri Menüsü](docs/images/customer-menu.png)

### QR Kod Yönetimi
![QR Kod Yönetimi](docs/images/qr-management.png)

---

**Smart Cafe** - Modern restoran yönetimi için akıllı çözüm 🍽️