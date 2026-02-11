import requests
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime

# Configuration
BLOG_ID = "joecool00"
RSS_URL = f"https://rss.blog.naver.com/{BLOG_ID}"
CATEGORY_FILTER = "AI Mind"
DATA_FILE = "data/posts.json"
HTML_FILE = "index.html"

def fetch_rss():
    response = requests.get(RSS_URL)
    if response.status_code != 200:
        print(f"Failed to fetch RSS: {response.status_code}")
        return None
    return response.content

def parse_rss(xml_content):
    root = ET.fromstring(xml_content)
    items = []
    for item in root.findall(".//item"):
        title = item.find("title").text
        link = item.find("link").text
        category = item.find("category").text if item.find("category") is not None else ""
        pub_date = item.find("pubDate").text
        
        # Extract post ID from link and strip any query parameters
        # Naver link format: https://blog.naver.com/joecool00/224179736852?fromRss=true...
        post_id = link.split("/")[-1].split("?")[0]
        
        # Clean the link itself for consistency
        clean_link = f"https://m.blog.naver.com/{BLOG_ID}/{post_id}"
        
        try:
            date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            formatted_date = date_obj.strftime("%Y-%m-%d")
        except:
            formatted_date = pub_date

        items.append({
            "id": post_id,
            "title": title,
            "link": clean_link,
            "category": category,
            "date": formatted_date
        })
    return items

def update_data(new_items):
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            posts = json.load(f)
    else:
        posts = {}

    updated = False
    for item in new_items:
        if item["category"] == CATEGORY_FILTER:
            if item["id"] not in posts:
                posts[item["id"]] = {
                    "title": item["title"],
                    "link": item["link"],
                    "date": item["date"],
                    "category": item["category"]
                }
                updated = True
                print(f"Added new post: {item['title']}")
    
    if updated:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)
    
    return posts

def clean_title(title):
    # Remove common prefixes
    prefixes = ["AI - ", "AI | ", "국내: ", "구글 - ", "⚡️ 퀵메모 - "]
    cleaned = title
    for p in prefixes:
        if cleaned.startswith(p):
            cleaned = cleaned[len(p):]
            break
            
    # SEO/CTR Optimization
    if len(cleaned) < 15:
        cleaned = f"{cleaned} | AI 인사이트"
    
    transformations = {
        "수업 요약 노트": "핵심 요약 가이드",
        "사용기": "실제 활용 팁과 후기",
        "정리": "올인원 가이드",
        "트렌드": "최신 트렌드 분석"
    }
    
    for key, val in transformations.items():
        if key in cleaned:
            cleaned = cleaned.replace(key, val)
            
    return cleaned

def generate_html(posts):
    def sort_key(item):
        date = item[1].get("date", "0000-00-00")
        if date == "Legacy Post":
            date = "2024-01-01"
        return (date, item[0])

    sorted_posts = sorted(posts.items(), key=sort_key, reverse=True)

    post_list_html = ""
    json_ld_items = []

    for post_id, data in sorted_posts:
        original_title = data["title"]
        display_title = clean_title(original_title)
        link = data["link"]
        date = data["date"]
        
        post_list_html += f"""
        <article class="post-card">
            <div class="post-date">{date}</div>
            <h2 class="post-title"><a href="{link}" target="_blank">{display_title}</a></h2>
            <link rel="canonical" href="{link}">
        </article>
        """
        
        json_ld_items.append({
            "@type": "BlogPosting",
            "headline": original_title,
            "url": link,
            "datePublished": date if date != "Legacy Post" else "2024-01-01",
            "author": {
                "@type": "Person",
                "name": BLOG_ID
            }
        })

    json_ld_html = json.dumps({
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": "Sony's AI Mind Archive (Seoul Proxy)",
        "url": "https://seoulproxy.com/",
        "blogPost": json_ld_items
    }, ensure_ascii=False, indent=2)

    html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>소담의 AI Mind</title>
    <meta name="description" content="소담의 AI Mind: 네이버 블로그의 핵심 인공지능 인사이트를 보관합니다.">
    <link rel="stylesheet" href="assets/style.css">
    <script type="application/ld+json">
{json_ld_html}
    </script>
</head>
<body>
    <header>
        <div class="container">
            <h1>소담의 AI Mind</h1>
            <p class="subtitle">킹콩노트 - 네이버 블로그</p>
        </div>
    </header>
    <main class="container">
        <div class="post-grid">
            {post_list_html}
        </div>
    </main>
    <footer>
        <div class="container">
            <p class="author-bio">Tech-Legal Specialist | NY-Qualified Attorney | Seoul, Korea. 인공지능과 비즈니스의 융합을 연구하며 전문적인 기술-법률적 통찰을 기록합니다.</p>
            <p>&copy; 2026 {BLOG_ID}. All rights reserved. <a href="https://blog.naver.com/{BLOG_ID}">원본 블로그 바로가기</a></p>
        </div>
    </footer>
</body>
</html>
"""
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_template)

def generate_sitemap(posts):
    base_url = "https://seoulproxy.com/"
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <priority>1.0</priority>
    </url>
</urlset>"""
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_content)

if __name__ == "__main__":
    print("Starting sync...")
    xml_data = fetch_rss()
    if xml_data:
        items = parse_rss(xml_data)
        all_posts = update_data(items)
        generate_html(all_posts)
        generate_sitemap(all_posts)
        print("Sync completed successfully.")
