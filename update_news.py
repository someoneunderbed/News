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

# RSS Kök Yapısı ve Başlık Tanımlamaları
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

# Sitedeki tüm haber bloklarını (Link, Resim ve Başlık) ham HTML üzerinden yakalayan esnek Regex yapısı
# Görselleri ve başlıkları kaçırmamak için en geniş HTML alanlarını yakalar
news_blocks = re.findall(r'href="(/news/\d+[^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)

seen_links = set()
count = 0
base_time = datetime.now()

# HTML içindeki resim yollarını (data-src, src vb.) topluca listele
all_images = re.findall(r'<img[^>]+(?:data-src|src)="([^"]+)"', html)

for index, (href, inner_html) in enumerate(news_blocks):
    if href in seen_links:
        continue

    full_link = f"https://civic.am{href}"

    # 1. BAŞLIK TEMİZLİĞİ: HTML etiketlerini tamamen kaldır ve boşlukları temizle
    clean_title = re.sub(r'<[^>]+>', '', inner_html).strip()
    clean_title = " ".join(clean_title.split())

    # Başlık geçerli değilse veya çok kısaysa bir sonraki bloğa geç
    if len(clean_title) < 15 or clean_title.isdigit():
        continue

    # 2. RESMİ DOĞRU EŞLEŞTİRME: Bloğun kendi içindeki resmi ara, yoksa sıradaki resmi tahmin et
    img_match = re.search(r'(?:data-src|src)="([^"]+)"', inner_html)
    img_url = ""

    if img_match:
        img_url = img_match.group(1)
    elif index < len(all_images):
        img_url = all_images[index]

    if img_url and not img_url.startswith('http'):
        img_url = f"https://civic.am{img_url}"

    seen_links.add(href)
    count += 1

    item = ET.SubElement(channel, "item")

    # Başlık Ataması
    i_title = ET.SubElement(item, "title")
    i_title.text = clean_title

    # Link Ataması
    i_link = ET.SubElement(item, "link")
    i_link.text = full_link

    # Açıklama
    i_desc = ET.SubElement(item, "description")
    i_desc.text = f"{clean_title} - Civic.am üzerinden oku."

    # Benzersiz ID
    i_guid = ET.SubElement(item, "guid", isPermaLink="false")
    i_guid.text = full_link

    # Kesin Eşleşen Görsel (Enclosure)
    if img_url:
        img_type = "image/webp" if "webp" in img_url else "image/jpeg"
        ET.SubElement(item, "enclosure", url=img_url, length="1000000", type=img_type)

    # Kronolojik Sıralama Ayarı: Her haber için zamanı geriye çekerek FocusReader sırasını korur
    pub_time = base_time - timedelta(minutes=(index * 2))
    i_pub = ET.SubElement(item, "pubDate")
    i_pub.text = pub_time.strftime("%a, %d %b %Y %H:%M:%S -0000")

    if count >= 20:
        break

# Klasör kontrolü ve dosyaya yazdırma işlemi
os.makedirs("NewsFolder", exist_ok=True)
tree = ET.ElementTree(rss)
ET.indent(tree, space="  ", level=0)
tree.write("NewsFolder/civic.xml", encoding="utf-8", xml_declaration=True)

print(f"Başarıyla güncellendi. {count} adet güncel haber listelendi.")