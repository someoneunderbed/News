import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
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

# Sitedeki tüm haber linklerini tam olarak üstten aşağıya (en güncelden eskiye) sırayla buluyoruz
# Civic.am üzerindeki her haber linki mutlaka /news/ ile başlar
all_links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if href.startswith('/news/') and href not in seen_links:
        all_links.append(a)
        seen_links.add(href)

# Zaman sıralamasının FocusReader'da düzgün görünmesi için her habere geriye doğru dakika düşüyoruz
base_time = datetime.now()

for index, a_tag in enumerate(all_links):
    href = a_tag['href']
    full_link = f"https://civic.am{href}"

    # 1. BAŞLIK: Link etiketinin içindeki veya en yakınındaki metni temizle
    title_text = a_tag.get_text()

    # Eğer linkin içi boşsa, parent element üzerinden metni aramaya çalış
    if not title_text.strip() and a_tag.find_parent():
        title_text = a_tag.find_parent().get_text()

    clean_title = " ".join(title_text.split())

    # Çok kısa başlıkları (reklam, kategori adı vb.) ele
    if len(clean_title) < 15 or clean_title.isdigit():
        continue

    # 2. RESİM: Sitedeki tembel yükleme (lazy-load) yapısını çözüyoruz
    # Önce linkin içinde veya en yakın div'de bir img arıyoruz
    img_tag = a_tag.find('img')
    if not img_tag and a_tag.find_parent():
        img_tag = a_tag.find_parent().find('img')

    img_url = ""
    if img_tag:
        # Sitenin asıl resmi sakladığı modern etiketleri sırasıyla kontrol et
        img_url = img_tag.get('data-src') or img_tag.get('data-srcset') or img_tag.get('src') or ""

        # Eğer data-srcset kullanılmışsa birden fazla link gelebilir, ilkini ayır
        if img_url and " " in img_url:
            img_url = img_url.split()[0]

        # Resim adresini tam URL'e dönüştür
        if img_url and not img_url.startswith('http'):
            img_url = f"https://civic.am{img_url}"

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

    # Zaman Karışıklığını Çözen Kronolojik Saat Ayarı
    # Her bir alt sıradaki haber için zamanı 2 dakika geriye çekiyoruz, böylece FocusReader sıralamayı asla karıştırmaz
    pub_time = base_time - timedelta(minutes=(index * 2))
    i_pub = ET.SubElement(item, "pubDate")
    i_pub.text = pub_time.strftime