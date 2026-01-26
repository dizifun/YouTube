import requests
import json
import gzip
from io import BytesIO
import random
import time

class TokenManager:
    """Token işlemlerini yöneten sınıf"""
    
    @staticmethod
    def get_token_from_github():
        url = "https://raw.githubusercontent.com/koprulu555/kbl-token-store/main/token.txt"
        print("🔑 Token GitHub deposundan çekiliyor...")
        
        try:
            headers = {'Cache-Control': 'no-cache'} # Önbelleği önle
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            raw_token = response.text.strip()
            
            # Token geçerlilik kontrolü (Basitçe dolu mu diye bakar)
            if len(raw_token) < 10:
                print("⚠️ GitHub'daki token geçersiz veya boş!")
                return None
                
            # Bearer eklemesi
            if not raw_token.lower().startswith("bearer "):
                return f"Bearer {raw_token}"
            return raw_token
            
        except Exception as e:
            print(f"❌ Token çekme hatası: {e}")
            return None

def get_real_browser_headers(token, random_ip):
    """Gerçek bir Chrome tarayıcısı gibi görünmek için detaylı headerlar"""
    return {
        "Host": "core-api.kablowebtv.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7", # Türkçe dil isteği
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://tvheryerde.com/",
        "Origin": "https://tvheryerde.com",
        "X-Forwarded-For": random_ip,  # Sahte Türkiye IP'si
        "Client-IP": random_ip,
        "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "Connection": "keep-alive",
        "Authorization": token
    }

def save_m3u(content, filename="yeni.m3u", add_header=True):
    with open(filename, "w", encoding="utf-8") as f:
        if add_header and not content.startswith("#EXTM3U"):
            f.write("#EXTM3U\n")
        f.write(content)

def main_process():
    # 1. Adım: Token al
    token = TokenManager.get_token_from_github()
    
    # Eğer token alamazsak bile yedeklere gitmek için süreci devam ettiriyoruz
    # ama ana kaynak için token şart.
    
    success = False
    
    # --- ANA KAYNAK DENEMESİ ---
    if token:
        try:
            # Rastgele Türk Telekom IP bloğu
            random_ip = f"176.88.{random.randint(10, 200)}.{random.randint(10, 200)}"
            
            print(f"📡 Ana kaynak (KabloWeb) deneniyor... (IP: {random_ip})")
            
            url = "https://core-api.kablowebtv.com/api/channels?checkip=false"
            headers = get_real_browser_headers(token, random_ip)
            
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                # Gzip çözme
                try:
                    with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                        content_str = gz.read().decode('utf-8')
                except:
                    content_str = response.content.decode('utf-8')

                data = json.loads(content_str)
                channels = data.get('Data', {}).get('AllChannels')

                if channels:
                    print(f"✅ Ana kaynaktan {len(channels)} kanal çekildi!")
                    
                    # M3U Oluşturma
                    m3u_content = "#EXTM3U\n"
                    kanal_index = 1
                    for ch in channels:
                        name = ch.get('Name')
                        stream = ch.get('StreamData', {}).get('HlsStreamUrl')
                        logo = ch.get('PrimaryLogoImageUrl', '')
                        group = ch.get('Categories', [{}])[0].get('Name', 'Genel')
                        
                        if name and stream and group != "Bilgilendirme":
                            m3u_content += f'#EXTINF:-1 tvg-id="{kanal_index}" tvg-logo="{logo}" group-title="{group}",{name}\n{stream}\n'
                            kanal_index += 1
                    
                    save_m3u(m3u_content, add_header=False)
                    success = True
                else:
                    print("❌ Veri geldi ama kanal listesi boş.")
            else:
                print(f"❌ Sunucu Hatası: {response.status_code} (Muhtemelen IP engeli)")
                
        except Exception as e:
            print(f"❌ Ana kaynak hatası: {e}")
    else:
        print("⚠️ Token olmadığı için ana kaynak atlandı.")

    # --- YEDEKLER (Eğer ana kaynak başarısızsa) ---
    if not success:
        print("\n🔄 Yedek kaynaklar devreye giriyor...")
        
        # Yedek 1
        try:
            print("⏳ BoncukTV deneniyor...")
            r = requests.get("https://mth.tc/boncuktv", timeout=15)
            if r.status_code == 200:
                # Gelen veriyi temizle (ilk satır boşluk vs varsa)
                lines = r.text.strip().split('\n')
                # Eğer ilk satır #EXTM3U değilse biz ekleriz, save_m3u fonksiyonu hallediyor
                content = '\n'.join(lines[1:]) if lines[0].startswith("#EXTM3U") else r.text
                
                save_m3u(r.text) # Direkt gelen veriyi yazalım, en garantisi
                print("✅ Başarılı: BoncukTV listesi kaydedildi.")
                success = True
        except Exception as e:
            print(f"❌ BoncukTV hatası: {e}")

    # Yedek 2 (Eğer hala başarı yoksa)
    if not success:
        try:
            print("⏳ GoldVOD deneniyor...")
            r = requests.get("https://goldvod.org/get.php?username=hpgdisco&password=123456&type=m3u_plus", timeout=15)
            if r.status_code == 200:
                save_m3u(r.text)
                print("✅ Başarılı: GoldVOD listesi kaydedildi.")
                success = True
        except Exception as e:
            print(f"❌ GoldVOD hatası: {e}")

    if not success:
        print("⛔ HİÇBİR KAYNAKTAN VERİ ALINAMADI.")
        exit(1) # GitHub Actions'a hata bildir

if __name__ == "__main__":
    main_process()
