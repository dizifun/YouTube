import json
import yt_dlp
import os
import time
from datetime import datetime

# --- AYARLAR ---
GIRIS_DOSYASI = "idler.json"
CIKIS_DOSYASI = "Youtube.m3u"
BEKLEME_SURESI = 2

def master_linki_bul(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    
    # --- YOUTUBE ENGELİNİ AŞMA AYARLARI ---
    ayarlar = {
        'quiet': True, 
        'no_warnings': True, 
        'simulate': True, 
        'skip_download': True, 
        'ignoreerrors': True, 
        'format': 'best',
        # 1. SSL hatalarını görmezden gel
        'nocheckcertificate': True,
        # 2. Kendini Android Telefon gibi tanıt (Bu çok önemli!)
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
        # 3. Gerçek bir tarayıcı User-Agent'ı kullan
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        with yt_dlp.YoutubeDL(ayarlar) as ydl:
            # Bilgi çekmeyi dene
            bilgi = ydl.extract_info(url, download=False)
            
            if bilgi:
                # Canlı yayın gerçekten var mı kontrol et
                if bilgi.get('is_live') is True or bilgi.get('was_live') is True:
                    if 'manifest_url' in bilgi: return bilgi['manifest_url']
                    elif 'url' in bilgi: return bilgi['url']
    except Exception as e:
        # Hata olursa loglara yaz (GitHub Actions kısmında görmek için)
        print(f"HATA ({channel_id}): {e}")
        pass
    
    return None

def baslat():
    print("--- GÜÇLENDİRİLMİŞ TARAMA BAŞLADI ---")
    
    if not os.path.exists(GIRIS_DOSYASI):
        print("idler.json bulunamadı!")
        return

    with open(GIRIS_DOSYASI, "r") as f:
        veri = json.load(f)

    m3u_icerik = '#EXTM3U x-tvg-url="http://epg.site/xml"\n'
    bulunan = 0
    toplam = 0
    
    for item in veri:
        if item.get("type") == "channel":
            toplam += 1
            isim = item.get("name", "Bilinmiyor")
            cid = item.get("original_id", item["id"])
            grup = item.get("subfolder", "GENEL").upper()
            slug = item.get("slug", "")
            
            print(f"[{toplam}] Kontrol: {isim}...", end=" ")
            
            link = master_linki_bul(cid)
            
            if link:
                print("✅ BULUNDU")
                bulunan += 1
                # GitHub'daki logo klasör yolunu buraya yazabilirsin
                logo = "" 
                m3u_icerik += f'#EXTINF:-1 group-title="{grup}" tvg-id="{slug}" tvg-logo="{logo}", {isim}\n{link}\n'
            else:
                print("❌ BULUNAMADI")
            
            time.sleep(BEKLEME_SURESI)

    # Dosyayı Kaydet
    with open(CIKIS_DOSYASI, "w", encoding="utf-8") as f:
        f.write(m3u_icerik)
    
    print(f"\nSONUÇ: {bulunan} kanal bulundu, {toplam} kanal tarandı.")

if __name__ == "__main__":
    baslat()
