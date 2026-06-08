import os
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request
from bs4 import BeautifulSoup

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

# HTML'i profesyonelce ayrıştır
soup = BeautifulSoup(html, 'html.parser')

# RSS Kök Yapısı
rss = ET.Element("rss", version="2.0")
rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

channel = ET.SubElement(rss, "channel")

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

seen_links = set()
count = 0

# Sitedeki tüm link etiketlerini (a href) tara
for a_tag in soup.find_all('a', href=True):
    href = a_tag['href']

    # Sadece gerçek haber linklerini filtrele (Örn: /news/117236 gibi)
    if href.startswith('/news/') and href not in seen_links:
        full_link = f"https://civic.am{href}"

        # Linkin içindeki metni (başlığı) al ve temizle
        title_text = a_tag.get_text()
        clean_title = " ".join(title_text.split())

        # Linkin içinde bir görsel (img) var mı kontrol et
        img_tag = a_tag.find('img')
        img_url = ""
        if img_tag and img_tag.get('src'):
            img_url = img_tag['src']
            if not img_url.startswith('http'):
                img_url = f"https://civic.am{img_url}"

        # Eğer başlık çok kısaysa veya boşsa, bu bir menü veya tasarım elemanıdır, atla
        if len(clean_title) < 15:
            continue

        seen_links.add(href)
        count += 1

        item = ET.SubElement(channel, "item")

        # Doğru Konum 1: BAŞLIK
        i_title = ET.SubElement(item, "title")
        i_title.text = clean_title

        # Doğru Konum 2: LİNK
        i_link = ET.SubElement(item, "link")
        i_link.text = full_link

        # Doğru Konum 3: AÇIKLAMA
        i_desc = ET.SubElement(item, "description")
        i_desc.text = f"{clean_title} - Civic.am üzerinden oku."

        # Doğru Konum 4: GUID
        i_guid = ET.SubElement(item, "guid", isPermaLink="false")
        i_guid.text = full_link

        # Doğru Konum 5: GÖRSEL (Enclosure)
        if img_url:
            img_type = "image/webp" if "webp" in img_url else "image/jpeg"
            ET.SubElement(item, "enclosure", url=img_url, length="1000000", type=img_type)

        # Doğru Konum 6: TARİH
        i_pub = ET.SubElement(item, "pubDate")
        i_pub.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S -0000")

        if count >= 20:  # En güncel 20 haberi al
            break

# Kayıt İşlemi
os.makedirs("NewsFolder", exist_ok=True)
tree = ET.ElementTree(rss)
ET.indent(tree, space="  ", level=0)
tree.write("NewsFolder/civic.xml", encoding="utf-8", xml_declaration=True)

print(f"Başarıyla senkronize edildi. {count} adet tam verili haber eklendi.")