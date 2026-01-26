import requests
import json
import gzip
from io import BytesIO
import random

def get_current_token():
    """GitHub'dan güncel tokeni çeker."""
    token_url = "https://raw.githubusercontent.com/koprulu555/kbl-token-store/main/token.txt"
    try:
        print("🌍 GitHub üzerinden güncel token kontrol ediliyor...")
        response = requests.get(token_url, timeout=15)
        response.raise_for_status()
        token = response.text.strip()
        if not token: return None
        if not token.lower().startswith("bearer "): token = f"Bearer {token}"
        print("✅ Güncel token başarıyla alındı.")
        return token
    except Exception as e:
        print(f"❌ Token alınırken hata: {e}")
        return None

def get_canli_tv_m3u():
    token = get_current_token()
    if not token: return False

    url = "https://core-api.kablowebtv.com/api/channels"
    
    # Rastgele bir Türk Telekom IP bloğundan IP üretelim ki her seferinde aynı olmasın
    random_ip = f"176.88.{random.randint(10, 250)}.{random.randint(10, 250)}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://tvheryerde.com",
        "Origin": "https://tvheryerde.com",
        "X-Forwarded-For": random_ip,  # SAHTE IP (ÖNEMLİ)
        "Client-IP": random_ip,        # YEDEK SAHTE IP
        "Cache-Control": "max-age=0",
        "Authorization": token
    }

    params = {"checkip": "false"}

    try:
        print(f"📡 CanliTV API'den veri alınıyor... (IP: {random_ip})")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        # Hata varsa içeriğini görelim
        if response.status_code != 200:
            print(f"❌ Sunucu Hatası Kodu: {response.status_code}")
            print(f"📄 Hata Detayı: {response.text[:200]}") # İlk 200 karakteri yazdır
            return False

        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')

        data = json.loads(content)
        channels = data.get('Data', {}).get('AllChannels')

        if not channels:
            print("❌ Kanal listesi boş geldi!")
            return False

        print(f"✅ {len(channels)} kanal bulundu")

        with open("yeni.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            kanal_index = 1
            for channel in channels:
                name = channel.get('Name')
                stream_data = channel.get('StreamData', {})
                hls_url = stream_data.get('HlsStreamUrl')
                logo = channel.get('PrimaryLogoImageUrl', '')
                group = channel.get('Categories', [{}])[0].get('Name', 'Genel')

                if name and hls_url and group != "Bilgilendirme":
                    f.write(f'#EXTINF:-1 tvg-id="{kanal_index}" tvg-logo="{logo}" group-title="{group}",{name}\n')
                    f.write(f'{hls_url}\n')
                    kanal_index += 1

        print(f"📺 yeni.m3u başarıyla oluşturuldu!")
        return True

    except Exception as e:
        print(f"❌ Kritik Hata: {e}")
        return False

if __name__ == "__main__":
    get_canli_tv_m3u()
