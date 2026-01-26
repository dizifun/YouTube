import requests
import json
import os

def get_token():
    """GitHub'dan tokeni çeker."""
    try:
        url = "https://raw.githubusercontent.com/koprulu555/kbl-token-store/main/token.txt"
        response = requests.get(url, timeout=10)
        token = response.text.strip()
        if not token.lower().startswith("bearer"):
            token = f"Bearer {token}"
        print("✅ Token GitHub'dan alındı.")
        return token
    except:
        print("⚠️ Token alınamadı, boş devam ediliyor.")
        return ""

def save_file(content):
    """M3U dosyasını kaydeder."""
    with open("yeni.m3u", "w", encoding="utf-8") as f:
        f.write(content)
    print("💾 'yeni.m3u' dosyası başarıyla kaydedildi!")

def main():
    # 1. TOKEN AL
    token = get_token()

    # 2. ANA KAYNAĞI DENEMEK (KabloWeb)
    print("🌍 Ana kaynak deneniyor...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Authorization": token,
            "Referer": "https://tvheryerde.com",
            "Origin": "https://tvheryerde.com"
        }
        # Timeout'u kısa tuttum ki takılmasın
        resp = requests.get("https://core-api.kablowebtv.com/api/channels?checkip=false", headers=headers, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            channels = data.get('Data', {}).get('AllChannels', [])
            
            if channels:
                m3u_text = "#EXTM3U\n"
                for ch in channels:
                    name = ch.get('Name')
                    url = ch.get('StreamData', {}).get('HlsStreamUrl')
                    logo = ch.get('PrimaryLogoImageUrl', '')
                    group = ch.get('Categories', [{}])[0].get('Name', 'Genel')
                    if name and url:
                        m3u_text += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n{url}\n'
                
                save_file(m3u_text)
                return # Başarılı oldu, çık
            
    except Exception as e:
        print(f"❌ Ana kaynak hatası (IP Engeli olabilir): {e}")

    # 3. YEDEKLERİ DENEMEK (Ana kaynak olmazsa burası çalışır)
    print("🔄 Ana kaynak olmadı, yedeklere geçiliyor...")
    
    # Yedek 1: BoncukTV
    try:
        print("⏳ BoncukTV indiriliyor...")
        r = requests.get("https://mth.tc/boncuktv", timeout=15)
        if r.status_code == 200:
            content = r.text
            if not content.startswith("#EXTM3U"):
                content = "#EXTM3U\n" + content
            save_file(content)
            return
    except:
        pass

    # Yedek 2: GoldVod
    try:
        print("⏳ GoldVod indiriliyor...")
        r = requests.get("https://goldvod.org/get.php?username=hpgdisco&password=123456&type=m3u_plus", timeout=15)
        if r.status_code == 200:
            save_file(r.text)
            return
    except:
        pass

    # HİÇBİRİ OLMAZSA BOŞ DOSYA OLUŞTUR (Hata vermemesi için)
    print("⚠️ Hiçbir kaynak çalışmadı ama hata vermemek için boş dosya oluşturuluyor.")
    with open("yeni.m3u", "w") as f:
        f.write("#EXTM3U\n")

if __name__ == "__main__":
    main()
