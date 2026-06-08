import os
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request
import re

# Civic.am son haberler sayfası
url = "https://civic.am/last-news"

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

# RSS Kök Yapısı ve Atom Özelliği
rss = ET.Element("rss", version="2.0")
rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

channel = ET.SubElement(rss, "channel")

# Ana kanal bilgileri (PolitePaul çıktısıyla birebir uyumlu)
title_elem = ET.SubElement(channel, "title")
title_elem.text = "Վերջին Լուրեր"

link_elem = ET.SubElement(channel, "link")
link_elem.text = url

desc_elem = ET.SubElement(channel, "description")
desc_elem.text = "Civic.am sitesinden otomatik üretilen RSS beslemesi"

lang_elem = ET.SubElement(channel, "language")
lang_elem.text = "hy"

last_build = ET.SubElement(channel, "lastBuildDate")
last_build.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S -0000")

# Geliştirilmiş esnek veri yakalama bloku
# Haber kutularını ve içindeki görsel + link + başlık üçlüsünü arar
items_pattern = re.compile(r'<a[^>]+href="(/news/\d+[^"]*)"[^>]*>.*?<img[^>]+src="([^"]+)"[^>]*>.*?<div[^>]*>(.*?)</div>', re.DOTALL)
matches = items_pattern.findall(html)

# Eğer spesifik div yapısı yakalanamadıysa geniş kapsamlı yedek desen
if not matches:
    # Sitedeki tüm /news/ linklerini ve ilişkili resimleri kaba kuvvete yakın tarar
    links_and_titles = re.findall(r'href="(/news/(\d+)[^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
    images = re.findall(r'<img[^>]+src="([^"]+)"', html)

    matches = []
    for i, (l_url, l_id, l_title) in enumerate(links_and_titles):
        if i < len(images):
            matches.append((l_url, images[i], l_title))
        else:
            matches.append((l_url, "", l_title))

seen_links = set()
count = 0

for link, img_url, title in matches:
    # İçerideki tüm HTML etiketlerini ayıkla ve başlığı temizle
    clean_title = re.sub(r'<[^>]+>', '', title).strip()
    # Satır başı ve sonu boşluklarını, sekme (tab) karakterlerini tamamen temizle
    clean_title = " ".join(clean_title.split())

    full_link = f"https://civic.am{link}"

    # Geçerli bir başlık varsa ve mükerrer değilse ekle
    if full_link not in seen_links and clean_title and len(clean_title) > 10 and count < 20:
        seen_links.add(full_link)
        count += 1

        item = ET.SubElement(channel, "item")

        # 1. BAŞLIK (Temizlenmiş)
        i_title = ET.SubElement(item, "title")
        i_title.text = clean_title

        # 2. LİNK
        i_link = ET.SubElement(item, "link")
        i_link.text = full_link

        # 3. AÇIKLAMA (Boş kalmasın diye başlığı veya sabit metni ekliyoruz)
        i_desc = ET.SubElement(item, "description")
        i_desc.text = "Civic.am üzerinden oku"

        # 4. GUID
        i_guid = ET.SubElement(item, "guid", isPermaLink="false")
        i_guid.text = full_link

        # 5. GÖRSEL (Enclosure) - FocusReader'ın resmi görebilmesi için
        if img_url:
            full_img_url = img_url if img_url.startswith("http") else f"https://civic.am{img_url}"
            img_type = "image/webp" if "webp" in full_img_url else "image/jpeg"
            ET.SubElement(item, "enclosure", url=full_img_url, length="1000000", type=img_type)

        # 6. TARİH
        i_pub = ET.SubElement(item, "pubDate")
        i_pub.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S -0000")

# Klasör kontrolü ve yazma işlemi
os.makedirs("NewsFolder", exist_ok=True)
tree = ET.ElementTree(rss)
ET.indent(tree, space="  ", level=0)
tree.write("NewsFolder/civic.xml", encoding="utf-8", xml_declaration=True)

print(f"Başarıyla tamamlandı. {count} adet temizlenmiş haber eklendi.")