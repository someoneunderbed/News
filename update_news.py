import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import urllib.request
import re

# ORTAK BAĞLANTI AYARLARI
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'hy,am,tr,en;q=0.8'
}

# SİTE AYARLARI VE AYIKLAMA KURALLARI
SITELER = [
    {
        "ad": "Civic.am",
        "url": "https://civic.am/last-news",
        "xml_adi": "civic.xml",
        "mod": "html_scrape"  # Ham HTML kazıma yöntemi
    },
    {
        "ad": "Oragir.news",
        "url": "https://oragir.news/hy/materials/all",
        "xml_adi": "oragir.xml",
        "mod": "rss_proxy"   # Doğrudan var olan bir RSS'i temizleme/yeniden dizme yöntemi
    }
]

def html_cek(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Bağlantı hatası ({url}): {e}")
        return None

# ANA ÇALIŞMA DÖNGÜSÜ
base_time = datetime.now()
os.makedirs("NewsFolder", exist_ok=True)

for site in SITELER:
    print(f"\n>>> {site['ad']} işleniyor...")
    kaynak_veri = html_cek(site["url"])

    if not kaynak_veri:
        continue

    # Yeni RSS Yapısı Kurulumu
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Վերջին Լուրեր - " + site["ad"]
    ET.SubElement(channel, "link").text = site["url"]
    ET.SubElement(channel, "description").text = f"{site['ad']} sitesinden güncellenen temiz akış."
    ET.SubElement(channel, "language").text = "hy"
    ET.SubElement(channel, "lastBuildDate").text = base_time.strftime("%a, %d %b %Y %H:%M:%S -0000")

    count = 0

    # METHOT 1: CIVIC.AM İÇİN HTML KAZIMA
    if site["mod"] == "html_scrape":
        news_links = re.findall(r'href="(/news/\d+[^"]*)"[^>]*>(.*?)</a>', kaynak_veri, re.DOTALL)
        all_images = [img for img in re.findall(r'<img[^>]+src="([^"]+)"', kaynak_veri) if "thumbs/" in img]

        seen_links = set()
        img_index = 0

        for index, (href, inner_html) in enumerate(news_links):
            if href in seen_links:
                continue

            full_link = f"https://civic.am{href}"
            clean_title = re.sub(r'<[^>]+>', '', inner_html).strip()
            clean_title = " ".join(clean_title.split())
            clean_title = re.sub(r'^\d{2}\.\d{2}\.\d{4},\s+\d{2}:\d{2}\s+[^\s]+\s+', '', clean_title)

            if len(clean_title) < 10 or clean_title.isdigit():
                continue

            img_url = ""
            inner_img = re.search(r'src="([^"]+)"', inner_html)
            if inner_img and "thumbs/" in inner_img.group(1):
                img_url = inner_img.group(1)
            elif img_index < len(all_images):
                img_url = all_images[img_index]
                img_index += 1

            if img_url:
                img_url = img_url.split()[0].lstrip('/')
                img_url = f"https://civic.am/{img_url}"

            seen_links.add(href)

            # XML Element Ekleme
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = clean_title
            ET.SubElement(item, "link").text = full_link
            ET.SubElement(item, "description").text = f"{clean_title} - {site['ad']} üzerinden oku."
            ET.SubElement(item, "guid", isPermaLink="false").text = full_link

            if img_url:
                img_type = "image/webp" if "webp" in img_url else "image/jpeg"
                ET.SubElement(item, "enclosure", url=img_url, length="1000000", type=img_type)

            pub_time = base_time - timedelta(minutes=(index * 2))
            ET.SubElement(item, "pubDate").text = pub_time.strftime("%a, %d %b %Y %H:%M:%S -0000")

            count += 1
            if count >= 20:
                break

    # METHOT 2: ORAGIR.NEWS İÇİN MEVCUT BESLEMEYİ TEMİZLEME
    elif site["mod"] == "rss_proxy":
        try:
            root = ET.fromstring(kaynak_veri)
            items = root.findall(".//item")

            for index, old_item in enumerate(items):
                title = old_item.find("title").text if old_item.find("title") is not None else ""
                link = old_item.find("link").text if old_item.find("link") is not None else ""
                desc = old_item.find("description").text if old_item.find("description") is not None else ""

                # PolitePaul yazısını ve boşlukları temizle
                if desc:
                    desc = desc.replace("Delivered by PolitePaul service", "").strip()
                    desc = " ".join(desc.split())

                enclosure = old_item.find("enclosure")
                img_url = enclosure.get("url") if enclosure is not None else ""

                item = ET.SubElement(channel, "item")
                ET.SubElement(item, "title").text = title
                ET.SubElement(item, "link").text = link
                ET.SubElement(item, "description").text = desc if desc else f"{title} - {site['ad']} üzerinden oku."
                ET.SubElement(item, "guid", isPermaLink="false").text = link

                if img_url:
                    ET.SubElement(item, "enclosure", url=img_url, length="1000000", type="image/jpeg")

                pub_time = base_time - timedelta(minutes=(index * 2))
                ET.SubElement(item, "pubDate").text = pub_time.strftime("%a, %d %b %Y %H:%M:%S -0000")

                count += 1
                if count >= 20:
                    break
        except Exception as e:
            print(f"Oragir RSS ayrıştırma hatası: {e}")
            continue

    # Dosyaya Yazma İşlemi
    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ", level=0)
    tree.write(f"NewsFolder/{site['xml_adi']}", encoding="utf-8", xml_declaration=True)
    print(f"Başarılı: NewsFolder/{site['xml_adi']} kaydedildi. ({count} haber)")

print("\nTüm sitelerin güncelleme işlemi başarıyla tamamlandı!")