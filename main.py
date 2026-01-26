import requests
import json
import gzip
from io import BytesIO
import random
import time

def get_token():
    """GitHub'dan güncel tokeni çeker ve temizler."""
    url = "https://raw.githubusercontent.com/koprulu555/kbl-token-store/main/token.txt"
    try:
        print("🔑 Token güncelleniyor...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        token = response.text.strip()
        # Bearer kontrolü
        if not token.lower().startswith("bearer"):
            token = f"Bearer {token}"
        return token
    except Exception as e:
        print(f"❌ Token hatası: {e}")
        return None

def fetch_kablo_tv():
    token = get_token()
    if not token:
        print("⛔ Token olmadığı için işlem durduruldu.")
        return False

    api_url = "https://core-api.kablowebtv.com/api/channels"
    
    # 3 Kez Deneme Hakkı (Retry Logic)
    for deneme in range(1, 4):
        # Her denemede farklı bir sahte IP üret
        fake_ip = f"176.88.{random.randint(10, 250)}.{random.randint(10, 250)}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://tvheryerde.com",
            "Origin": "https://tvheryerde.com",
            "X-Forwarded-For": fake_ip, # Engel aşmak için sahte IP
            "Client-IP": fake_ip,
            "Authorization": token
        }

        print(f"📡 KabloTV Bağlanıyor (Deneme {deneme}/3) - IP: {fake_ip}...")

        try:
            response = requests.get(api_url, headers=headers, params={"checkip": "false"}, timeout=15)
            
            if response.status_code == 200:
                # Gzip çözme
                try:
                    with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                        content = gz.read().decode('utf-8')
                except:
                    content = response.content.decode('utf-8')

                data = json.loads(content)
                channels = data.get('Data', {}).get('AllChannels')

                if channels:
                    print(f"✅ Başarılı! {len(channels)} kanal çekildi.")
                    
                    # Dosyayı yaz
                    with open("yeni.m3u", "w", encoding="utf-8") as f:
                        f.write("#EXTM3U\n")
                        kanal_no = 1
                        for ch in channels:
                            name = ch.get('Name')
                            url = ch.get('StreamData', {}).get('HlsStreamUrl')
                            logo = ch.get('PrimaryLogoImageUrl', '')
                            group = ch.get('Categories', [{}])[0].get('Name', 'Genel')
                            
                            if name and url and group != "Bilgilendirme":
                                f.write(f'#EXTINF:-1 tvg-id="{kanal_no}" tvg-logo="{logo}" group-title="{group}",{name}\n{url}\n')
                                kanal_no += 1
                    
                    print("💾 'yeni.m3u' dosyası oluşturuldu.")
                    return True # İşlem tamam, çık
                else:
                    print("⚠️ Veri geldi ama kanal listesi boş.")
            else:
                print(f"❌ Hata Kodu: {response.status_code} (Sunucu reddetti)")

        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
        
        # Başarısız olursa 2 saniye bekle tekrar dene
        time.sleep(2)

    # 3 deneme de başarısız olursa
    print("⛔ Tüm denemeler başarısız oldu. KabloTV çekilemedi.")
    
    # Git hatası vermemesi için boş dosya oluşturuyoruz (İsteğe bağlı)
    with open("yeni.m3u", "w") as f:
        f.write("#EXTM3U\n")
    return False

if __name__ == "__main__":
    fetch_kablo_tv()
