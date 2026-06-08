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

# Sitedeki tüm haber kartlarını taramak için en kararlı yöntem:
# Önce sitedeki tüm /news/ linklerini buluyoruz
for a_tag in soup.find_all('a', href=True):
    href = a_tag['href']

    if href.startswith('/news/') and href not in seen_links:
        full_link = f"https://civic.am{href}"

        # Başlığı bulmak için: a etiketinin içindeki metne bak,
        # yoksa en yakınındaki div veya başlık etiketlerini kontrol et
        title_text = a_tag.get_text()

        # Eğer a etiketinin içi boşsa (sadece resim barındırıyorsa) yanındaki metin alanını ara
        if not title_text.strip():
            parent = a_tag.find_parent()
            if parent:
                title_text = parent.get_text()

        clean_title = " ".join(title_text.split())

        # Başlık temizlendikten sonra çok kısaysa veya sadece sayı/tarihten ibaretse atla
        if len(clean_title) < 15 or clean_title.isdigit():
            continue

        # Görseli bulmak için: a etiketinin içindeki veya en yakınındaki img elementini ara
        img_tag = a_tag.find('img')
        if not img_tag and a_tag.find_parent():
            img_tag = a_tag.find_parent().find('img')

        img_url = ""
        if img_tag and img_tag.get('src'):
            img_url = img_tag['src']
            if not img_url.startswith('http'):
                img_url = f"https://civic.am{img_url}"

        seen_links.add(href)
        count += 1

        item = ET.SubElement(channel, "item")

        i_title = ET.SubElement(item, "title")
        i_title.text = clean_title

        i_link = ET.SubElement(item, "link")
        i_link.text = full_link

        i_desc = ET.SubElement(item, "description")
        i_desc.text = f"{clean_title} - Civic.am üzerinden oku."

        i_guid = ET.SubElement(item, "guid", isPermaLink="false")
        i_guid.text = full_link

        if img_url:
            img_type = "image/webp" if "webp" in img_url else "image/jpeg"
            ET.SubElement(item, "enclosure", url=img_url, length="1000000", type=img_type)

        i_pub = ET.SubElement(item, "pubDate")
        i_pub.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S -0000")

        if count >= 20:
            break

# Klasör doğrulama ve yazma
os.makedirs("NewsFolder", exist_ok=True)
tree = ET.ElementTree(rss)
ET.indent(tree, space="  ", level=0)
tree.write("NewsFolder/civic.xml", encoding="utf-8", xml_declaration=True)

print(f"Senkronizasyon bitti. {count} adet güncel haber eklendi.")