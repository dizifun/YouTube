import json
import yt_dlp
import os
import time
from datetime import datetime

# --- AYARLAR ---
GIRIS_DOSYASI = "idler.json"
CIKIS_DOSYASI = "playlist.m3u" # Direkt ana dizine kaydet
BEKLEME_SURESI = 1 # Sunucu hızlı olduğu için 1 sn yeter

def master_linki_bul(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    ayarlar = {
        'quiet': True, 'no_warnings': True, 'simulate': True, 
        'skip_download': True, 'ignoreerrors': True, 'format': 'best'
    }
    try:
        with yt_dlp.YoutubeDL(ayarlar) as ydl:
            bilgi = ydl.extract_info(url, download=False)
            if bilgi:
                # Master Link (Tüm kaliteler)
                if 'manifest_url' in bilgi: return bilgi['manifest_url']
                # Tek Kalite
                elif 'url' in bilgi: return bilgi['url']
    except: pass
    return None

def baslat():
    print("--- TARAMA BAŞLADI ---")
    
    if not os.path.exists(GIRIS_DOSYASI):
        print("JSON dosyası yok!")
        return

    with open(GIRIS_DOSYASI, "r") as f:
        veri = json.load(f)

    # Başlık
    m3u_icerik = '#EXTM3U x-tvg-url="http://epg.site/xml"\n'
    bulunan = 0
    
    for item in veri:
        if item.get("type") == "channel":
            isim = item.get("name", "Bilinmiyor")
            cid = item.get("original_id", item["id"])
            grup = item.get("subfolder", "GENEL").upper()
            slug = item.get("slug", "")
            
            print(f"Kontrol: {isim}...", end=" ")
            
            link = master_linki_bul(cid)
            
            if link:
                print("✅")
                bulunan += 1
                # Logo ayarı (Repo adını kendine göre düzenle)
                # Örn: https://raw.githubusercontent.com/KULLANICI/REPO/main/logos/
                logo = "" 
                m3u_icerik += f'#EXTINF:-1 group-title="{grup}" tvg-id="{slug}" tvg-logo="{logo}", {isim}\n{link}\n'
            else:
                print("❌")
            
            time.sleep(BEKLEME_SURESI)

    # Dosyayı Kaydet
    with open(CIKIS_DOSYASI, "w", encoding="utf-8") as f:
        f.write(m3u_icerik)
    
    print(f"\nToplam {bulunan} kanal güncellendi.")

if __name__ == "__main__":
    baslat()
