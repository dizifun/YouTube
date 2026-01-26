import requests
import json
import gzip
from io import BytesIO
import time

def get_token_and_clean():
    """GitHub'dan tokeni çeker ve sunucunun istediği formata getirir."""
    url = "https://raw.githubusercontent.com/koprulu555/kbl-token-store/main/token.txt"
    
    try:
        print("🌍 Token GitHub'dan çekiliyor...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # 1. Adım: Token'ı metin olarak al ve sağındaki/solundaki boşlukları/satırları sil
        raw_token = response.text.strip()
        
        # 2. Adım: Token boş mu kontrol et
        if not raw_token:
            print("❌ Token dosyası boş!")
            return None
            
        # 3. Adım: 'Bearer ' kontrolü
        # Sunucu kesinlikle "Bearer <kod>" formatı ister.
        if raw_token.lower().startswith("bearer"):
            # Zaten başında Bearer yazıyorsa olduğu gibi kullan
            final_token = raw_token
        else:
            # Yazmıyorsa biz ekleyelim
            final_token = f"Bearer {raw_token}"
            
        return final_token

    except Exception as e:
        print(f"❌ Token alma hatası: {e}")
        return None

def fetch_channels():
    # Tokeni al
    token = get_token_and_clean()
    
    if not token:
        print("⛔ Token olmadığı için işlem iptal.")
        return False

    # API Ayarları
    url = "https://core-api.kablowebtv.com/api/channels"
    
    # Senin orijinal kodundaki headerlar (En sağlıklısı budur)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Referer": "https://tvheryerde.com",
        "Origin": "https://tvheryerde.com",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip",
        "Authorization": token  # Temizlenmiş token buraya
    }

    params = {
        "checkip": "false" # Bu parametre IP kontrolünü kapatmak için kritik
    }

    try:
        print("📡 KabloWebTV API'ye bağlanılıyor...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        # Eğer 500 hatası alırsak detayını yazdıralım
        if response.status_code != 200:
            print(f"⚠️ API Hatası: {response.status_code}")
            # Yine de devam etmeyip exception fırlatalım ki yedeğe geçsin
            response.raise_for_status()

        # Gzip Çözme İşlemi (Senin kodundan)
        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')

        data = json.loads(content)
        
        # Veri Kontrolü
        channels = data.get('Data', {}).get('AllChannels')
        if not channels:
            print("❌ Kanal listesi boş geldi.")
            raise Exception("Boş liste")

        print(f"✅ {len(channels)} kanal bulundu.")

        # Dosyayı Yazma
        with open("yeni.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n") # Başlık
            
            kanal_index = 1
            for channel in channels:
                name = channel.get('Name')
                stream_data = channel.get('StreamData', {})
                hls_url = stream_data.get('HlsStreamUrl')
                logo = channel.get('PrimaryLogoImageUrl', '')
                categories = channel.get('Categories', [])
                
                if not name or not hls_url:
                    continue
                    
                group = categories[0].get('Name', 'Genel') if categories else 'Genel'
                if group == "Bilgilendirme": continue

                f.write(f'#EXTINF:-1 tvg-id="{kanal_index}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(f'{hls_url}\n')
                kanal_index += 1
                
        print("📺 yeni.m3u başarıyla oluşturuldu (Ana Kaynak).")
        return True

    except Exception as e:
        print(f"❌ Ana Kaynak Başarısız: {e}")
        return run_backups()

def run_backups():
    print("🔄 Yedek kaynaklar deneniyor...")
    
    # Yedek 1: BoncukTV
    try:
        r = requests.get("https://mth.tc/boncuktv", timeout=15)
        if r.status_code == 200:
            with open("yeni.m3u", "w", encoding="utf-8") as f:
                # Eğer gelen veri #EXTM3U ile başlamıyorsa ekle
                if not r.text.startswith("#EXTM3U"):
                    f.write("#EXTM3U\n")
                f.write(r.text)
            print("✅ Yedek kaynak (BoncukTV) kaydedildi.")
            return True
    except:
        pass

    # Yedek 2: GoldVod
    try:
        r = requests.get("https://goldvod.org/get.php?username=hpgdisco&password=123456&type=m3u_plus", timeout=15)
        if r.status_code == 200:
            with open("yeni.m3u", "w", encoding="utf-8") as f:
                f.write(r.text)
            print("✅ Yedek kaynak (GoldVod) kaydedildi.")
            return True
    except:
        pass
    
    print("⛔ Tüm kaynaklar başarısız.")
    return False

if __name__ == "__main__":
    fetch_channels()
