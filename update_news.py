import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import urllib.request
from bs4 import BeautifulSoup
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'hy-AM,hy;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}

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
        with urllib.request.urlopen(req, timeout=25) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Connection error ({url}): {e}")
        return None

base_time = datetime.now()
os.makedirs("NewsFolder", exist_ok=True)

for site in SITELER:
    print(f"\n>>> Processing {site['name']}...")

    # --- TERT.AM: ENGELLENMEYEN GİZLİ RESMİ RSS SERVİSİ ---
    if site["name"] == "tert.am":
        rss_content = fetch_html("https://www.tert.am/am/news/rss")
        if rss_content:
            try:
                xml_path = f"NewsFolder/{site['xml_filename']}"
                if os.path.exists(xml_path): os.remove(xml_path)
                with open(xml_path, "wb") as f:
                    f.write(rss_content.encode('utf-8'))
                print(f"Success: {xml_path} saved via hidden official RSS service.")
                continue
            except Exception as e:
                print(f"Tert RSS backup error: {e}")

    # --- RADAR.AM: ENGELLENMEYEN RESMİ RSS BESLEMESİ ---
    if site["name"] == "radar.am":
        rss_content = fetch_html("https://radar.am/hy/feed/")
        if rss_content:
            try:
                xml_path = f"NewsFolder/{site['xml_filename']}"
                if os.path.exists(xml_path): os.remove(xml_path)
                with open(xml_path, "wb") as f:
                    f.write(rss_content.encode('utf-8'))
                print(f"Success: {xml_path} saved directly from official feed.")
                continue
            except Exception as e:
                print(f"Radar RSS error: {e}")

    # --- CIVIC.AM: ENGELLENMEYEN GİZLİ VERİ API'SI ---
    if site["name"] == "Civic.am":
        # Sitenin korumasız ham veri API'sinden güncel makaleleri çekiyoruz
        api_content = fetch_html("https://civic.am/api/posts?limit=20")
        if api_content:
            try:
                data = json.loads(api_content)
                # Eğer standart JSON listesiyse veya 'data' key'i altındaysa normalize et
                posts = data.get('data', data) if isinstance(data, dict) else data

                if isinstance(posts, list) and len(posts) > 0:
                    rss = ET.Element("rss", version="2.0")
                    channel = ET.SubElement(rss, "channel")
                    ET.SubElement(channel, "title").text = site['name']
                    ET.SubElement(channel, "link").text = site["url"]
                    ET.SubElement(channel, "description").text = f"Cleaned RSS feed from {site['name']} API."
                    ET.SubElement(channel, "language").text = "hy"
                    ET.SubElement(channel, "lastBuildDate").text = base_time.strftime("%a, %d %b %Y %H:%M:%S -0000")

                    if "logo_url" in site and site["logo_url"]:
                        image_tag = ET.SubElement(channel, "image")
                        ET.SubElement(image_tag, "url").text = site["logo_url"]
                        ET.SubElement(image_tag, "title").text = site['name']
                        ET.SubElement(image_tag, "link").text = site["url"]

                    for idx, post in enumerate(posts[:20]):
                        title_text = post.get('title', post.get('name', '')).strip()
                        slug = post.get('slug', str(post.get('id', '')))
                        full_link = f"https://civic.am/news/{slug}"

                        # API'den gelen verilerde yapışık tarih/kategori derdi olmaz, başlık tertemizdir
                        if len(title_text) < 10: continue

                        item = ET.SubElement(channel, "item")
                        ET.SubElement(item, "title").text = title_text
                        ET.SubElement(item, "link").text = full_link
                        ET.SubElement(item, "description").text = f"{title_text} - Read on {site['name']}."
                        ET.SubElement(item, "guid", isPermaLink="false").text = full_link

                        # Resim kontrolü
                        img_path = post.get('image', post.get('img', post.get('avatar', '')))
                        if img_path:
                            img_url = f"https://civic.am{img_path}" if img_path.startswith('/') else img_path
                            ET.SubElement(item, "enclosure", url=img_url, length="1000000", type="image/jpeg")

                        pub_time = base_time - timedelta(minutes=(idx * 2))
                        ET.SubElement(item, "pubDate").text = pub_time.strftime("%a, %d %b %Y %H:%M:%S -0000")

                    xml_path = f"NewsFolder/{site['xml_filename']}"
                    if os.path.exists(xml_path): os.remove(xml_path)
                    with open(xml_path, "wb") as f:
                        tree = ET.ElementTree(rss)
                        ET.indent(tree, space="  ", level=0)
                        tree.write(f, encoding="utf-8", xml_declaration=True)
                    print(f"Success: {xml_path} has been saved fresh via JSON API.")
                    continue
            except Exception as e:
                print(f"Civic API parsing failed: {e}, falling back to scraping.")

    # --- DIĞER STANDART SİTELER İÇİN NORMAL HTML KAZIMA AKIŞI ---
    html_content = fetch_html(site["url"])
    if not html_content:
        print(f"Skipping {site['name']} - empty content.")
        continue

    soup = BeautifulSoup(html_content, 'html.parser')

    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
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

    # Armenpress Özel Blok Yakalayıcı
    if site["name"] == "armenpress.am":
        items = soup.find_all(['div', 'article', 'a'], class_=re.compile(r'news|item|article', re.IGNORECASE))
        for item in items:
            a_tag = item if item.name == 'a' else item.find('a', href=True)
            if not a_tag or not a_tag.get('href'): continue
            href = a_tag['href'].strip()
            if not any(x in href for x in ["/article", "/hy/"]): continue

            full_link = f"{site['base_url']}{href}" if href.startswith('/') else href
            if full_link in seen_links: continue

            title_text = a_tag.get_text(strip=True)
            if not title_text and item.name != 'a': title_text = item.get_text(strip=True)

            title_text = " ".join(title_text.split())
            title_text = re.sub(r'^\d{2}\.\d{2}\.\d{4},\s+\d{2}:\d{2}\s*', '', title_text)
            if len(title_text) < 10: continue

            img_url = ""
            img_tag = item.find('img') if item.name != 'a' else a_tag.find('img')
            if img_tag and img_tag.get('src'):
                img_url = img_tag['src'].strip().split()[0]
                if img_url.startswith('/'): img_url = f"{site['base_url']}{img_url}"

            seen_links.add(full_link)
            rss_item = ET.SubElement(channel, "item")
            ET.SubElement(rss_item, "title").text = title_text
            ET.SubElement(rss_item, "link").text = full_link
            ET.SubElement(rss_item, "description").text = f"{title_text} - Read on {site['name']}."
            ET.SubElement(rss_item, "guid", isPermaLink="false").text = full_link
            if img_url: ET.SubElement(rss_item, "enclosure", url=img_url, length="1000000", type="image/jpeg")
            pub_time = base_time - timedelta(minutes=(count * 2))
            ET.SubElement(rss_item, "pubDate").text = pub_time.strftime("%a, %d %b %Y %H:%M:%S -0000")
            count += 1
            if count >= 20: break

        if count > 0:
            xml_path = f"NewsFolder/{site['xml_filename']}"
            if os.path.exists(xml_path): os.remove(xml_path)
            with open(xml_path, "wb") as f:
                tree = ET.ElementTree(rss)
                ET.indent(tree, space="  ", level=0)
                tree.write(f, encoding="utf-8", xml_declaration=True)
            continue

    # Diğer Standart Siteler İçin Tarama Döngüsü
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href'].strip()

        if site["name"] == "Oragir.news" and not ("/hy/material/" in href): continue
        if site["name"] == "5tv.am" and not any(x in href for x in ["/news/", "/v/"]): continue
        if site["name"] == "politik.am" and not any(x in href for x in ["/newsfeed", "/news/", "/am/"]): continue
        if site["name"] == "arka.am" and not any(x in href for x in ["/am/news/", "/news/"]): continue
        if site["name"] == "Shamshyan.news" and not any(x in href for x in ["/hy/article/", "/article/"]): continue

        full_link = f"{site['base_url']}{href}" if href.startswith('/') else (href if href.startswith('http') else f"{site['base_url']}/{href}")
        if full_link in seen_links: continue

        title_text = a_tag.get_text(strip=True)
        title_text = " ".join(title_text.split())
        title_text = re.sub(r'^\d{2}\.\d{2}\.\d{4},\s+\d{2}:\d{2}\s+[^\s]+\s+', '', title_text)
        title_text = re.sub(r'^\d{2}\.\d{2}\.\d{4},\s+\d{2}:\d{2}\s*', '', title_text).strip()

        if len(title_text) < 10 or title_text.isdigit(): continue

        img_url = ""
        img_tag = a_tag.find('img') or (a_tag.parent.find('img') if a_tag.parent else None)
        if img_tag and img_tag.get('src'):
            img_src = img_tag['src'].strip().split()[0]
            img_url = f"{site['base_url']}{img_src}" if img_src.startswith('/') else (img_src if img_src.startswith('http') else f"{site['base_url']}/{img_src}")

        seen_links.add(full_link)
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title_text
        ET.SubElement(item, "link").text = full_link
        ET.SubElement(item, "description").text = f"{title_text} - Read on {site['name']}."
        ET.SubElement(item, "guid", isPermaLink="false").text = full_link
        if img_url: ET.SubElement(item, "enclosure", url=img_url, length="1000000", type="image/jpeg")
        pub_time = base_time - timedelta(minutes=(count * 2))
        ET.SubElement(item, "pubDate").text = pub_time.strftime("%a, %d %b %Y %H:%M:%S -0000")

        count += 1
        if count >= 20: break

    if count > 0:
        xml_path = f"NewsFolder/{site['xml_filename']}"
        if os.path.exists(xml_path): os.remove(xml_path)
        with open(xml_path, "wb") as f:
            tree = ET.ElementTree(rss)
            ET.indent(tree, space="  ", level=0)
            tree.write(f, encoding="utf-8", xml_declaration=True)
        print(f"Success: {xml_path} has been saved fresh. ({count} articles)")

print("\nAll processes completed successfully!")