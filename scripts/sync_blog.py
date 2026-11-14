import requests
import xml.etree.ElementTree as ET
import json
import os
import re
import html
from datetime import datetime

# Configuration
BLOG_ID = "joecool00"
RSS_URL = f"https://rss.blog.naver.com/{BLOG_ID}"
CATEGORY_FILTER = "AI Mind"
DATA_FILE = "data/posts.json"
HTML_FILE = "index.html"
SITE_URL = "https://seoulproxy.com/"
SITE_NAME = "소담의 AI Mind"
SITE_NAME_EN = "Sodam's AI Mind"
AUTHOR = "소담"
AUTHOR_EN = "Sodam"
EXCERPT_CHARS = 300  # 글마다 보여 줄 본문 앞부분 길이(네이버 RSS 의 description)


def fetch_rss():
    response = requests.get(RSS_URL)
    if response.status_code != 200:
        print(f"Failed to fetch RSS: {response.status_code}")
        return None
    return response.content


def clean_excerpt(raw):
    """RSS description(HTML 조각)을 글자만 남긴 앞부분으로 — AI 가 원문을 못 열어도 이 화면에서 읽을 수 있게."""
    if not raw:
        return ""
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > EXCERPT_CHARS:
        text = text[:EXCERPT_CHARS].rsplit(" ", 1)[0] + "…"
    return text


def parse_rss(xml_content):
    root = ET.fromstring(xml_content)
    items = []
    for item in root.findall(".//item"):
        title = item.find("title").text
        link = item.find("link").text
        category = item.find("category").text if item.find("category") is not None else ""
        pub_date = item.find("pubDate").text
        description = item.find("description").text if item.find("description") is not None else ""

        # Extract post ID from link and strip any query parameters
        # Naver link format: https://blog.naver.com/joecool00/224179736852?fromRss=true...
        post_id = link.split("/")[-1].split("?")[0]

        # Clean the link itself for consistency
        clean_link = f"https://m.blog.naver.com/{BLOG_ID}/{post_id}"

        try:
            date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            formatted_date = date_obj.strftime("%Y-%m-%d")
        except Exception:
            formatted_date = pub_date

        items.append({
            "id": post_id,
            "title": title,
            "link": clean_link,
            "category": category,
            "date": formatted_date,
            "excerpt": clean_excerpt(description),
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
        if item["category"] != CATEGORY_FILTER:
            continue
        if item["id"] not in posts:
            posts[item["id"]] = {
                "title": item["title"],
                "link": item["link"],
                "date": item["date"],
                "category": item["category"],
                "excerpt": item["excerpt"],
            }
            updated = True
            print(f"Added new post: {item['title']}")
        elif item["excerpt"] and not posts[item["id"]].get("excerpt"):
            # 예전에 받은 글도 RSS 에 아직 있으면 본문 앞부분을 채운다
            posts[item["id"]]["excerpt"] = item["excerpt"]
            updated = True

    if updated:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)

    return posts


def clean_title(title):
    # 앞머리 꼬리표만 뗀다 — 제목을 바꿔 쓰지 않는다(원문 제목 = 손님이 검색하는 말)
    prefixes = ["AI - ", "AI | ", "국내: ", "구글 - ", "⚡️ 퀵메모 - "]
    for p in prefixes:
        if title.startswith(p):
            return title[len(p):]
    return title


def post_date(data):
    date = data.get("date", "0000-00-00")
    return "2024-01-01" if date == "Legacy Post" else date


def generate_html(posts):
    sorted_posts = sorted(posts.items(), key=lambda item: (post_date(item[1]), item[0]), reverse=True)
    latest = post_date(sorted_posts[0][1]) if sorted_posts else ""

    post_list_html = ""
    json_ld_items = []

    for post_id, data in sorted_posts:
        original_title = data["title"]
        display_title = html.escape(clean_title(original_title))
        link = data["link"]
        date = post_date(data)
        excerpt = data.get("excerpt", "")
        summary_html = f'\n            <p class="post-summary">{html.escape(excerpt)}</p>' if excerpt else ""

        post_list_html += f"""
        <article class="post-card">
            <div class="post-date">{date}</div>
            <h2 class="post-title"><a href="{link}" target="_blank">{display_title}</a></h2>{summary_html}
            <a href="{link}" class="read-more" target="_blank">원문 읽기 &rarr;</a>
        </article>
        """

        posting = {
            "@type": "BlogPosting",
            "headline": original_title,
            "url": link,
            "datePublished": date,
            "author": {"@type": "Person", "name": AUTHOR, "alternateName": AUTHOR_EN},
        }
        if excerpt:
            posting["description"] = excerpt
        json_ld_items.append(posting)

    json_ld_html = json.dumps({
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": SITE_NAME,
        "alternateName": SITE_NAME_EN,
        "url": SITE_URL,
        "author": {"@type": "Person", "name": AUTHOR, "alternateName": AUTHOR_EN,
                   "jobTitle": "Tech-Legal Specialist · NY-Qualified Attorney"},
        "blogPost": json_ld_items,
    }, ensure_ascii=False, indent=2)

    intro = (f"{SITE_NAME}는 뉴욕주 변호사인 {AUTHOR}이 AI와 테크-리걸(법 · 규제 · 리걸테크)을 다룬 글을 모은 곳이에요. "
             f"글 {len(sorted_posts)}편 · 마지막 글 {latest}. 원문은 네이버 블로그에 있어요.")

    html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-WTHX05VQS2"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());

      gtag('config', 'G-WTHX05VQS2');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{SITE_NAME}</title>
    <meta name="description" content="{intro}">
    <link rel="canonical" href="{SITE_URL}">
    <link rel="stylesheet" href="assets/style.css">
    <script type="application/ld+json">
{json_ld_html}
    </script>
</head>
<body>
    <header>
        <div class="container">
            <h1>{SITE_NAME}</h1>
            <p class="intro">{intro}</p>
        </div>
    </header>
    <main class="container">
        <div class="post-grid">
            {post_list_html}
        </div>
    </main>
    <footer>
        <div class="container">
            <p class="author-bio">Tech-Legal Specialist | NY-Qualified Attorney | Seoul, Korea<br>인공지능과 비즈니스의 융합을 연구하며 전문적인 기술-법률적 통찰을 기록합니다.</p>
            <p>&copy; 2026 {AUTHOR}. All rights reserved. <a href="https://blog.naver.com/{BLOG_ID}">원본 블로그 바로가기</a></p>
        </div>
    </footer>
</body>
</html>
"""
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_template)


def generate_sitemap(posts):
    # lastmod 은 마지막 글 날짜 — 날마다 오늘 날짜로 바꾸면 글이 없는데도 매일 커밋이 생긴다
    latest = max((post_date(p) for p in posts.values()), default=datetime.now().strftime("%Y-%m-%d"))
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{SITE_URL}</loc>
        <lastmod>{latest}</lastmod>
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
