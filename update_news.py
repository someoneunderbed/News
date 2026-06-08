import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
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

# Sitedeki tüm haber linklerini ve iç metinlerini bul
news_links = re.findall(r'href="(/news/\d+[^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)

# Sitedeki tüm gerçek haber görsellerini sırasıyla topla (SVG'leri ve logoları hariç tut)
all_images = []
img_matches = re.findall(r'<img[^>]+src="([^"]+)"', html)
for img in img_matches:
    if "thumbs/" in img:  # Sadece thumbs klasöründeki gerçek haber resimlerini al
        all_images.append(img)

seen_links = set()
count = 0
base_time = datetime.now()

# Eşleşen resim indeksini takip etmek için bir sayaç
img_index = 0

for index, (href, inner_html) in enumerate(news_links):
    if href in seen_links:
        continue

    full_link = f"https://civic.am{href}"

    # Başlık temizliği
    clean_title = re.sub(r'<[^>]+>', '', inner_html).strip()
    clean_title = " ".join(clean_title.split())

    # Başlığın önündeki tarih ve kategorileri temizle
    clean_title = re.sub(r'^\d{2}\.\d{2}\.\d{4},\s+\d{2}:\d{2}\s+[^\s]+\s+', '', clean_title)

    if len(clean_title) < 10 or clean_title.isdigit():
        continue

    # RESMİ SIRAYLA EŞLEŞTİRME
    # Eğer bu haber bloğunun kendi içinde resim yoksa, sayfadan topladığımız sıradaki resmi veriyoruz
    img_url = ""
    inner_img = re.search(r'src="([^"]+)"', inner_html)

    if inner_img and "thumbs/" in inner_img.group(1):
        img_url = inner_img.group(1)
    elif img_index < len(all_images):
        img_url = all_images[img_index]
        img_index += 1  # Sıradaki resme geç

    if img_url:
        if " " in img_url:
            img_url = img_url.split()[0]
        # Link birleştirme hatasını ve çift slash durumunu çözen garanti temizlik
        img_url = img_url.lstrip('/')
        img_url = f"https://civic.am/{img_url}"

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

    # Kusursuzlaştırılmış Görsel Linki
    if img_url:
        img_type = "image/webp" if "webp" in img_url else "image/jpeg"
        ET.SubElement(item, "enclosure", url=img_url, length="1000000", type=img_type)

    # Sıralı Zaman Damgası
    pub_time = base_time - timedelta(minutes=(index * 2))
    i_pub = ET.SubElement(item, "pubDate")
    i_pub.text = pub_time.strftime("%a, %d %b %Y %H:%M:%S -0000")

    if count >= 20:
        break

# Klasör kontrolü ve dosyaya yazma
os.makedirs("NewsFolder", exist_ok=True)
tree = ET.ElementTree(rss)
ET.indent(tree, space="  ", level=0)
tree.write("NewsFolder/civic.xml", encoding="utf-8", xml_declaration=True)

print(f"Güncelleme bitti. {count} adet kusursuz resimli haber eklendi.")