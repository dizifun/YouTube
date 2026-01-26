import requests
import json
import gzip
from io import BytesIO
import random

def get_current_token():
    """GitHub'dan güncel tokeni çeker."""
    token_url = "https://raw.githubusercontent.com/koprulu555/kbl-token-store/main/token.txt"
    try:
        # Tokenı çekiyoruz
        response = requests.get(token_url, timeout=15)
        response.raise_for_status()
        
        token = response.text.strip()
        
        if not token:
            return None
            
        # Başında Bearer yoksa ekle
        if not token.lower().startswith("bearer "):
            token = f"Bearer {token}"
            
        return token
    except Exception as e:
        print(f"⚠️ Token alınırken hata oluştu: {e}")
        return None

def get_canli_tv_m3u():
    # Rastgele Türk IP'si üret (Sunucuyu kandırmak için)
    random_ip = f"176.88.{random.randint(10, 250)}.{random.randint(10, 250)}"
    
    # Güncel tokeni al
    token = get_current_token()
    
    # Eğer token alamazsak veya boşsa, direkt yedeklere geçmek için token'ı boş string yapabiliriz
    # ama Authorization header boş olunca hata verebilir, o yüzden try bloğu yönetecek.
    
    url = "https://core-api.kablowebtv.com/api/channels"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Referer": "https://tvheryerde.com",
        "Origin": "https://tvheryerde.com",
        "X-Forwarded-For": random_ip,  # GİZLİ SİLAH: Sahte IP
        "Client-IP": random_ip,
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip",
        "Authorization": token if token else "Bearer gecersiztoken" 
    }

    params = {
        "checkip": "false"
    }

    try:
        if not token:
            raise Exception("GitHub'dan token alınamadı, yedeklere geçiliyor.")

        print(f"📡 CanliTV API'den veri alınıyor... (IP: {random_ip})")

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')

        data = json.loads(content)

        # Veri kontrolü
        if not data.get('IsSucceeded') or not data.get('Data', {}).get('AllChannels'):
            raise Exception("API yanıtı başarısız veya kanal listesi boş.")

        channels = data['Data']['AllChannels']
        print(f"✅ {len(channels)} kanal bulundu (Ana Kaynak)")

        with open("yeni.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n") # Standart M3U başlığı

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

                f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(f'{hls_url}\n')

                kanal_sayisi += 1
                kanal_index += 1  

        print(f"📺 yeni.m3u dosyası oluşturuldu! ({kanal_sayisi} kanal)")
        return True

    except Exception as e:
        print(f"❌ Ana Kaynak Hatası: {e}")
        print("🔄 Yedek kaynaktan m3u indiriliyor...")

        # --- YEDEK 1: BONCUK TV ---
        try:
            print("⏳ BoncukTV deneniyor...")
            response = requests.get("https://mth.tc/boncuktv", timeout=15)
            response.raise_for_status()

            # İlk satır #EXTM3U ise ve biz temiz dosya istiyorsak direkt yazalım
            # Senin kodundaki mantığı koruyorum (ilk satırı atlama) ama dikkatli ol:
            lines = response.text.split('\n')
            
            # Eğer dosya #EXTM3U ile başlıyorsa onu koruyarak yazmak daha iyidir
            # Ama senin kodundaki gibi 1. satırı atlayıp yazıyorum:
            content = '\n'.join(lines[1:]) if lines else response.text

            with open("yeni.m3u", "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n") # Başlığı biz ekleyelim garanti olsun
                f.write(content)
            print("✅ Yedek kaynaktan m3u başarıyla indirildi (BoncukTV)")
            return True

        except Exception as e2:
            print(f"❌ İlk yedek kaynak hatası: {e2}")
            print("🔄 İkinci yedek kaynaktan m3u indiriliyor...")

            # --- YEDEK 2: GOLDVOD ---
            try:
                print("⏳ GoldVOD deneniyor...")
                response = requests.get("https://goldvod.org/get.php?username=hpgdisco&password=123456&type=m3u_plus", timeout=15)
                response.raise_for_status()

                lines = response.text.split('\n')
                content = '\n'.join(lines[1:]) if lines else response.text

                with open("yeni.m3u", "w", encoding="utf-8") as f:
                    f.write("#EXTM3U\n") # Başlığı garantiye al
                    f.write(content)
                print("✅ İkinci yedek kaynaktan m3u başarıyla indirildi (GoldVod)")
                return True

            except Exception as e3:
                print(f"❌ İkinci yedek kaynak hatası: {e3}")
                print("❌❌ TÜM KAYNAKLAR BAŞARISIZ OLDU.")
                return False

if __name__ == "__main__":
    get_canli_tv_m3u()
