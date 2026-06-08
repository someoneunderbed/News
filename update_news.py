import os
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request
import re

# Civic.am son haberler sayfası
url = "https://civic.am/last-news"

# Detaylı tarayıcı taklidi (Header)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'hy,am,tr,en;q=0.8'
}

req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
except Exception as e:
    print(f"Siteye erişilemedi: {e}")
    exit(1)

# HTML'den haber detaylarını (Link, Başlık ve Görsel) yakalayan gelişmiş Regex deseni
# Hem linki, hem görseli (img src), hem de başlığı tek seferde yakalar
pattern = re.compile(r'<a[^>]+href="(/news/[^"]+)"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*>.*?<div[^>]*>(.*?)</div>', re.DOTALL)
matches = pattern.findall(html)

# Eğer üstteki spesifik yapı değişirse diye alternatif yedek regex (Sadece link ve başlık için)
if not matches:
    pattern = re.compile(r'href="(/news/[^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
    backup_matches = pattern.findall(html)
    matches = [(m[0], "", m[1]) for m in backup_matches]

# XML / RSS Kök Yapısı
rss = ET.Element("rss", version="2.0")
# PolitePaul çıktısındaki gibi standart Atom kütüphanesini de ekleyelim
rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

channel = ET.SubElement(rss, "channel")

# Ana Başlık ayarları
title_elem = ET.SubElement(channel, "title")
title_elem.text = "Վերջին Լուրեր"  # Çıktınızdaki gibi Ermenice "Son Haberler" yaptık

link_elem = ET.SubElement(channel, "link")
link_elem.text = url

desc_elem = ET.SubElement(channel, "description")
desc_elem.text = "Civic.am sitesinden otomatik üretilen RSS beslemesi"

lang_elem = ET.SubElement(channel, "language")
lang_elem.text = "hy"  # Dil kodunu Ermenice (hy) olarak düzelttik

seen_links = set()
count = 0

for link, img_url, title in matches:
    # Başlığın içindeki tüm HTML etiketlerini ve sağındaki-solundaki devasa boşlukları temizle
    clean_title = re.sub('<[^<]+?>', '', title).strip()
    full_link = f"https://civic.am{link}"

    # Link mükerrer değilse ve başlık doluysa ekle
    if full_link not in seen_links and clean_title and count < 20:
        seen_links.add(full_link)
        count += 1

        item = ET.SubElement(channel, "item")

        # Temizlenmiş Haber Başlığı
        i_title = ET.SubElement(item, "title")
        i_title.text = clean_title

        # Haber Linki
        i_link = ET.SubElement(item, "link")
        i_link.text = full_link

        # Benzersiz ID (GUID)
        i_guid = ET.SubElement(item, "guid", isPermaLink="true")
        i_guid.text = full_link

        # Görsel Desteği (FocusReader ve diğer okuyucuların resmi çekebilmesi için en önemli kısım)
        if img_url:
            # Eğer gelen görsel adresi yarım ise başına site adresini ekle
            full_img_url = img_url if img_url.startswith("http") else f"https://civic.am{img_url}"

            # Resim formatını uzantısından tahmin et (webp, jpeg, png)
            img_type = "image/jpeg"
            if "webp" in full_img_url:
                img_type = "image/webp"
            elif "png" in full_img_url:
                img_type = "image/png"

            # Enclosure etiketini ekle
            ET.SubElement(item, "enclosure", url=full_img_url, length="1000000", type=img_type)

        # Yayınlanma Tarihi (Şu anki zaman)
        i_pub = ET.SubElement(item, "pubDate")
        i_pub.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0400")

# Klasörü doğrula ve dosyayı oluştur
os.makedirs("NewsFolder", exist_ok=True)
tree = ET.ElementTree(rss)
ET.indent(tree, space="  ", level=0)
tree.write("NewsFolder/civic.xml", encoding="utf-8", xml_declaration=True)

print(f"civic.xml başarıyla senkronize edildi! Toplam {count} görsel destekli haber eklendi.")