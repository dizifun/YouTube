import asyncio
import json
import logging
from aiohttp import ClientSession
from bs4 import BeautifulSoup, SoupStrainer

# Loglama ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Linklerin ve isimlerin bulunduğu liste. Buraya istediğin kadar ok.ru linki ekleyebilirsin.
CHANNELS = [
    {"name": "FANATIK Özel - OK.RU Video 1", "url": "https://ok.ru/video/11141660674721"},
    # {"name": "Video 2", "url": "https://ok.ru/video/BAŞKA_LINK_BURAYA"}
]

async def extract_okru(url: str, session: ClientSession) -> str:
    """Ok.ru sayfasından asıl m3u8 linkini çeker."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    async with session.get(url, headers=headers) as response:
        text = await response.text()

    # Sadece div etiketlerini parse ederek hız kazandırıyoruz
    soup = BeautifulSoup(text, "lxml", parse_only=SoupStrainer("div"))
    div = soup.find("div", {"data-module": "OKVideo"})
    
    if not div:
        raise Exception("Video elementi bulunamadı (Video silinmiş veya gizli olabilir)")

    data_options = div.get("data-options")
    data = json.loads(data_options)
    metadata = json.loads(data["flashvars"]["metadata"])
    
    # En iyi kalite m3u8 linkini bul
    final_url = (
        metadata.get("hlsMasterPlaylistUrl") or 
        metadata.get("hlsManifestUrl") or 
        metadata.get("ondemandHls")
    )
    
    if not final_url:
        raise Exception("M3U8 linki metadata içinden çıkarılamadı")
        
    return final_url

async def main():
    m3u_content = "#EXTM3U\n"
    
    async with ClientSession() as session:
        for ch in CHANNELS:
            try:
                logging.info(f"Çekiliyor: {ch['name']} ({ch['url']})")
                stream_url = await extract_okru(ch["url"], session)
                
                # M3U formatına uygun şekilde ekle
                m3u_content += f"#EXTINF:-1,{ch['name']}\n{stream_url}\n"
                logging.info(f"Başarılı: {stream_url}")
                
            except Exception as e:
                logging.error(f"Hata oluştu ({ch['name']}): {e}")

    # Dosyayı kaydet
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    logging.info("playlist.m3u dosyası başarıyla oluşturuldu/güncellendi.")

if __name__ == "__main__":
    asyncio.run(main())
