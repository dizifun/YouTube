import requests
import json
import gzip
from io import BytesIO

def get_canli_tv_m3u():
    """
    KabloWebTV API'sinden kanal listesini çeker ve M3U dosyası oluşturur.
    Token GitHub'daki text dosyasından dinamik olarak alınır.
    """
    
    # --- 1. ADIM: Token'ı GitHub'dan Çek ve Temizle ---
    try:
        # Cache (önbellek) sorununu önlemek için rastgele sayı eklenebilir ama şimdilik düz çekiyoruz
        token_url = "https://raw.githubusercontent.com/koprulu555/kbl-token-store/main/token.txt"
        
        print(f"🔑 Token adresten çekiliyor: {token_url}")
        token_response = requests.get(token_url, timeout=15)
        token_response.raise_for_status()
        
        # .strip() ÇOK ÖNEMLİ: Satır sonundaki görünmez \n karakterini siler.
        dynamic_token = token_response.text.strip()
        
        # Token kontrolü (Hata ayıklama için ilk 10 karakteri yazdırır)
        print(f"✅ Token alındı (İlk 10 hane): {dynamic_token[:10]}...")
        
    except Exception as e:
        print(f"❌ Token çekme hatası: {e}")
        return False

    # --- 2. ADIM: API İsteği ---
    url = "https://core-api.kablowebtv.com/api/channels"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Referer": "https://tvheryerde.com",
        "Origin": "https://tvheryerde.com",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {dynamic_token}"  # Temizlenmiş token buraya ekleniyor
    }

    params = {
        "checkip": "false"
    }

    try:
        print("📡 CanliTV API'ye bağlanılıyor...")

        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        # Eğer token hatalıysa burada 401 Unauthorized hatası verir
        if response.status_code == 401:
            print("❌ HATA: 401 Unauthorized - Token geçersiz veya süresi dolmuş!")
            print(f"Kullanılan Token: {dynamic_token}")
            return False
            
        response.raise_for_status()

        # Gzip sıkıştırmasını çöz
        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')

        data = json.loads(content)

        # Veri kontrolü
        if not data.get('IsSucceeded') or not data.get('Data', {}).get('AllChannels'):
            print("❌ API yanıt verdi ama kanal verisi bulunamadı!")
            return False

        channels = data['Data']['AllChannels']
        print(f"✅ Başarılı! {len(channels)} kanal bulundu.")

        # --- 3. ADIM: M3U Dosyasını Yaz ---
        with open("yeni.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n") # Standart başlık eklendi

            kanal_sayisi = 0
            kanal_index = 1  

            for channel in channels:
                name = channel.get('Name')
                stream_data = channel.get('StreamData', {})
                hls_url = stream_data.get('HlsStreamUrl') if stream_data else None
                logo = channel.get('PrimaryLogoImageUrl', '')
                categories = channel.get('Categories', [])

                if not name or not hls_url:
                    continue

                group = categories[0].get('Name', 'Genel') if categories else 'Genel'

                if group == "Bilgilendirme":
                    continue

                tvg_id = str(kanal_index)

                # M3U formatı
                f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(f'{hls_url}\n')

                kanal_sayisi += 1
                kanal_index += 1  

        print(f"📺 yeni.m3u dosyası başarıyla oluşturuldu! ({kanal_sayisi} kanal)")
        return True

    except Exception as e:
        print(f"❌ Beklenmeyen bir hata oluştu: {e}")
        return False

if __name__ == "__main__":
    get_canli_tv_m3u()
