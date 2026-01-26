import requests
import json
import gzip
from io import BytesIO

def get_canli_tv_m3u():
    """"""
    
    # Token'ı URL'den çekme işlemi
    try:
        token_url = "https://raw.githubusercontent.com/koprulu555/kbl-token-store/main/token.txt"
        token_response = requests.get(token_url, timeout=10)
        token_response.raise_for_status()
        dynamic_token = token_response.text.strip() # Boşlukları temizle
        print("✅ Token başarıyla güncellendi.")
    except Exception as e:
        print(f"❌ Token çekilemedi: {e}")
        dynamic_token = "" # Hata durumunda boş bırakır veya eski tokenı buraya yedek olarak koyabilirsin

    url = "https://core-api.kablowebtv.com/api/channels"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Referer": "https://tvheryerde.com",
        "Origin": "https://tvheryerde.com",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {dynamic_token}"  # Dinamik token buraya eklendi
    }

    params = {
        "checkip": "false"
    }

    try:
        print("📡 CanliTV API'den veri alınıyor...")

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        try:
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                content = gz.read().decode('utf-8')
        except:
            content = response.content.decode('utf-8')

        data = json.loads(content)

        if not data.get('IsSucceeded') or not data.get('Data', {}).get('AllChannels'):
            print("❌ CanliTV API'den geçerli veri alınamadı!")
            return False

        channels = data['Data']['AllChannels']
        print(f"✅ {len(channels)} kanal bulundu")

        with open("yeni.m3u", "w", encoding="utf-8") as f:
            f.write("\n")

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
        print(f"❌ Hata: {e}")
        print("🔄 Yedek kaynaktan m3u indiriliyor...")

        try:
            # İlk yedek kaynak
            response = requests.get("https://mth.tc/boncuktv", timeout=10)
            response.raise_for_status()

            # İlk satırı atla
            lines = response.text.split('\n')
            content = '\n'.join(lines[1:]) if lines else response.text

            with open("yeni.m3u", "w", encoding="utf-8") as f:
                f.write(content)
            print("✅ Yedek kaynaktan m3u başarıyla indirildi (boncuktv)")
            return True

        except Exception as e2:
            print(f"❌ İlk yedek kaynak (boncuk tv) hatası: {e2}")
            print("🔄 İkinci yedek kaynaktan m3u indiriliyor...")

            try:
                # İkinci yedek kaynak
                response = requests.get("https://goldvod.org/get.php?username=hpgdisco&password=123456&type=m3u_plus", timeout=10)
                response.raise_for_status()

                # İlk satırı atla
                lines = response.text.split('\n')
                content = '\n'.join(lines[1:]) if lines else response.text

                with open("yeni.m3u", "w", encoding="utf-8") as f:
                    f.write(content)
                print("✅ İkinci yedek kaynaktan m3u başarıyla indirildi (goldvod)")
                return True

            except Exception as e3:
                print(f"❌ İkinci yedek kaynak (goldvod) hatası: {e3}")
                print("❌ Tüm kaynaklar başarısız oldu")
                return False

if __name__ == "__main__":
    get_canli_tv_m3u()
