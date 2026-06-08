import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import urllib.request
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'hy,am,tr,en;q=0.9'
}

SITELER = [
    {
        "ad": "Civic.am",
        "url": "https://civic.am/last-news",
        "xml_adi": "civic.xml",
        "base_url": "https://civic.am"
    },
    {
        "ad": "Oragir.news",
        "url": "https://oragir.news/hy/materials/all",
        # ÇÖZÜM: İsmi senin depondaki gibi 'oragirnews.xml' yaptık!
        "xml_adi": "oragirnews.xml",
        "base_url": "https://oragir.news/hy/"
    }
]

def html_cek(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Bağlantı hatası ({url}): {e}")
        return None

base_time = datetime.now()
os.makedirs("NewsFolder", exist_ok=True)

for site in SITELER:
    print(f"\n>>> {site['ad']} işleniyor...")
    html_content = html_cek(site["url"])

    if not html_content:
        continue

    soup = BeautifulSoup(html_content, 'html.parser')

    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = f"Վերջին Լուրեր - {site['ad']}"
    ET.SubElement(channel, "link").text = site["url"]
    ET.SubElement(channel, "description").text = f"{site['ad']} sitesinden güncellenen temiz akış."
    ET.SubElement(channel, "language").text = "hy"
    ET.SubElement(channel, "lastBuildDate").text = base_time.strftime("%a, %d %b %Y %H:%M:%S -0000")

    count = 0
    seen_links = set()

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']

        if site["ad"] == "Civic.am" and not href.startswith("/news/"):
            continue
        if site["ad"] == "Oragir.news" and not href.startswith("/hy/material/"):
            continue

        full_link = f"{site['base_url']}{href}" if href.startswith('/') else href

        if full_link in seen_links:
            continue

        title_text = a_tag.get_text(strip=True)
        title_text = " ".join(title_text.split())
        title_text = re.sub(r'^\d{2}\.\d{2}\.\d{4},\s+\d{2}:\d{2}\s+[^\s]+\s+', '', title_text)

        if len(title_text) < 10 or title_text.isdigit():
            continue

        img_url = ""
        img_tag = a_tag.find('img')
        if not img_tag:
            parent = a_tag.parent
            if parent:
                img_tag = parent.find('img')

        if img_tag and img_tag.get('src'):
            img_src = img_tag['src'].strip()
            if "thumbs/" in img_src or "storage/" in img_src:
                img_url = img_src.split()[0]
                if img_url.startswith('/'):
                    img_url = f"{site['base_url']}{img_url}"

        seen_links.add(full_link)

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title_text
        ET.SubElement(item, "link").text = full_link
        ET.SubElement(item, "description").text = f"{title_text} - {site['ad']} üzerinden oku."
        ET.SubElement(item, "guid", isPermaLink="false").text = full_link

        if img_url:
            img_type = "image/webp" if "webp" in img_url else "image/jpeg"
            ET.SubElement(item, "enclosure", url=img_url, length="1000000", type=img_type)

        pub_time = base_time - timedelta(minutes=(count * 2))
        ET.SubElement(item, "pubDate").text = pub_time.strftime("%a, %d %b %Y %H:%M:%S -0000")

        count += 1
        if count >= 20:
            break

    if count > 0:
        tree = ET.ElementTree(rss)
        ET.indent(tree, space="  ", level=0)
        tree.write(f"NewsFolder/{site['xml_adi']}", encoding="utf-8", xml_declaration=True)
        print(f"Başarılı: NewsFolder/{site['xml_adi']} kaydedildi. ({count} haber)")
    else:
        print(f"Hata: {site['ad']} için hiçbir eşleşen eleman bulunamadı.")

print("\nTüm işlemler tamamlandı!")