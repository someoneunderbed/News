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

# Sitelerin listesi
SITELER = []
SITELER.append({"name": "Civic.am", "url": "https://civic.am/last-news", "xml_filename": "civic.xml", "base_url": "https://civic.am", "logo_url": "https://civic.am/assets/img/logo.svg"})
SITELER.append({"name": "Oragir.news", "url": "https://oragir.news/hy/materials/all", "xml_filename": "oragirnews.xml", "base_url": "https://oragir.news", "logo_url": "https://st2.oragir.news/header-logo2.png"})
SITELER.append({"name": "Shamshyan.news", "url": "https://shamshyan.com/hy/articles/all", "xml_filename": "shamshyan.xml", "base_url": "https://shamshyan.com", "logo_url": "https://shamshyan.com/build/assets/logotype.351a3a34.png"})
SITELER.append({"name": "5tv.am", "url": "https://news.5tv.am/news-feed", "xml_filename": "5tv.xml", "base_url": "https://5tv.am", "logo_url": "https://news.5tv.am//storage/settings/main-logo.png"})
SITELER.append({"name": "armenpress.am", "url": "https://armenpress.am/hy/articles", "xml_filename": "armenpress.xml", "base_url": "https://armenpress.am", "logo_url": "https://armenpress.am/assets/companies/armenpress-indigo-hy.svg"})
SITELER.append({"name": "tert.am", "url": "https://tert.am/am/news", "xml_filename": "tert.xml", "base_url": "https://tert.am", "logo_url": "https://tert.am/resources/favicons/apple-icon-precomposed.png"})
SITELER.append({"name": "radar.am", "url": "https://radar.am/hy/feed/", "xml_filename": "radar.xml", "base_url": "https://radar.am", "logo_url": "https://radar.am/static/radar/images/logo-white.4c8b6b003ba3.svg"})
SITELER.append({"name": "politik.am", "url": "https://politik.am/am/newsfeed/1", "xml_filename": "politik.xml", "base_url": "https://politik.am", "logo_url": "https://politik.am/imgs/page/header-logo-am.png"})
SITELER.append({"name": "arka.am", "url": "https://arka.am/am/news/", "xml_filename": "arka.xml", "base_url": "https://arka.am", "logo_url": "https://arka.am/local/templates/arka_new/images/ARKA_LOGO.svg"})

def fetch_html(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Connection error ({url}): {e}")
        return None

base_time = datetime.now()
os.makedirs("NewsFolder", exist_ok=True)

for site in SITELER:
    print(f"\n>>> Processing {site['name']}...")
    html_content = fetch_html(site["url"])

    if not html_content:
        continue

    soup = BeautifulSoup(html_content, 'html.parser')

    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

    # Hatalı locals() kontrolü düzeltildi, doğrudan kanal oluşturuluyor
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = site['name']
    ET.SubElement(channel, "link").text = site["url"]
    ET.SubElement(channel, "description").text = f"Cleaned RSS feed updated from {site['name']}."
    ET.SubElement(channel, "language").text = "hy"
    ET.SubElement(channel, "lastBuildDate").text = base_time.strftime("%a, %d %b %Y %H:%M:%S -0000")

    if "logo_url" in site and site["logo_url"]:
        image_tag = ET.SubElement(channel, "image")
        ET.SubElement(image_tag, "url").text = site["logo_url"]
        ET.SubElement(image_tag, "title").text = site['name']
        image_link = site["url"].replace(".com", ".news") if site["name"] == "Shamshyan.news" else site["url"]
        ET.SubElement(image_tag, "link").text = image_link

    count = 0
    seen_links = set()

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href'].strip()

        if site["name"] == "Civic.am" and not ("/news/" in href):
            continue
        if site["name"] == "Oragir.news" and not ("/hy/material/" in href):
            continue
        if site["name"] == "5tv.am" and not ("/news-feed" in href):
            continue
        if site["name"] == "armenpress.am" and not ("/hy/articles" in href):
            continue
        if site["name"] == "tert.am" and not ("/am/news" in href):
            continue
        if site["name"] == "radar.am" and not ("/hy/feed/" in href):
            continue
        if site["name"] == "politik.am" and not ("/newsfeed" in href or "/news/" in href):
            continue
        if site["name"] == "arka.am" and not ("/am/news/" in href):
            continue
        if site["name"] == "Shamshyan.news" and not ("/hy/article/" in href or "/article/" in href):
            continue

        if href.startswith('/'):
            full_link = f"{site['base_url']}{href}"
        elif href.startswith('http'):
            full_link = href
        else:
            full_link = f"{site['base_url']}/{href}"

        if full_link in seen_links:
            continue

        # --- Gelişmiş ve Kesin Başlık Ayıklama Mantığı ---
        if site["name"] == "Civic.am":
            # Tarih ve kategori içerebilecek alt etiketleri (span, div, p vb.) bul ve temizle
            tags_to_clear = a_tag.find_all(['span', 'div', 'p', 'time'])
            for target in tags_to_clear:
                # Başlık karmaşasını önlemek için tarih/kategori elementlerini geçici olarak devredışı bırakıyoruz
                target.extract()

            # Alt etiketler temizlendikten sonra kalan saf metin doğrudan haber başlığıdır
            title_text = a_tag.get_text(strip=True)
            title_text = " ".join(title_text.split())

            # Eğer hâlâ temizlenmemiş kalıntı regex varsa son bir kontrolle uçuruyoruz
            title_text = re.sub(r'^\d{2}\.\d{2}\.\d{4},\s+\d{2}:\d{2}\s*', '', title_text)
        else:
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
                if not img_tag and parent.parent:
                    img_tag = parent.parent.find('img')

        if img_tag and img_tag.get('src'):
            img_src = img_tag['src'].strip()
            if "thumbs/" in img_src or "storage/" in img_src or "uploads/" in img_src or "preview/" in img_src or "upload/" in img_src:
                img_url = img_src.split()[0]
                if img_url.startswith('/'):
                    img_url = f"{site['base_url']}{img_url}"
                elif not img_url.startswith('http'):
                    img_url = f"{site['base_url']}/{img_url}"

        seen_links.add(full_link)

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title_text
        ET.SubElement(item, "link").text = full_link
        ET.SubElement(item, "description").text = f"{title_text} - Read on {site['name']}."
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
        tree.write(f"NewsFolder/{site['xml_filename']}", encoding="utf-8", xml_declaration=True)
        print(f"Success: NewsFolder/{site['xml_filename']} has been saved. ({count} articles)")
    else:
        print(f"Error: No matching elements found for {site['name']}.")

print("\nAll processes completed successfully!")