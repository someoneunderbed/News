import os
import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request
import re

# Civic.am son haberler sayfasını indir
url = "https://civic.am/last-news"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
except Exception as e:
    print(f"Siteye erişilemedi: {e}")
    exit(1)

# Basit HTML ayıklama (Regex) - Haber linklerini ve başlıklarını toplar
# Not: Sitenin HTML yapısına göre tasarlanmıştır.
pattern = re.compile(r'<a[^>]+href="(/news/[^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
matches = pattern.findall(html)

# XML Yapısını Oluşturma
rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")

title_elem = ET.SubElement(channel, "title")
title_elem.text = "Civic.am Son Haberler"

link_elem = ET.SubElement(channel, "link")
link_elem.text = url

desc_elem = ET.SubElement(channel, "description")
desc_elem.text = "Civic.am sitesinden otomatik üretilen RSS beslemesi"

seen_links = set()
count = 0

for link, title in matches:
    clean_title = re.sub('<[^<]+?>', '', title).strip() # HTML etiketlerini temizle
    full_link = f"https://civic.am{link}"

    if full_link not in seen_links and clean_title and count < 20:
        seen_links.add(full_link)
        count += 1

        item = ET.SubElement(channel, "item")

        i_title = ET.SubElement(item, "title")
        i_title.text = clean_title

        i_link = ET.SubElement(item, "link")
        i_link.text = full_link

        i_guid = ET.SubElement(item, "guid", isPermaLink="true")
        i_guid.text = full_link

        i_pub = ET.SubElement(item, "pubDate")
        i_pub.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0400")

# Klasör kontrolü ve dosyaya yazma
os.makedirs("NewsFolder", exist_ok=True)
tree = ET.ElementTree(rss)
ET.indent(tree, space="  ", level=0)
tree.write("NewsFolder/civic.xml", encoding="utf-8", xml_declaration=True)

print("civic.xml başarıyla güncellendi!")