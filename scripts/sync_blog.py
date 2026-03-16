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

def generate_summary(title):
    # 소문자로 변환하여 영어 키워드 검색 효율을 높임
    t = title.lower()
    
    if "데이터" in t or "전력" in t or "인프라" in t:
        return "폭발적으로 성장하는 AI 산업 이면의 인프라 구축과 전력 공급 이슈를 짚어봅니다."
    elif "법" in t or "규제" in t or "pipa" in t or "권리장전" in t or "컴플라이언스" in t:
        return "급변하는 기술 환경 속에서 반드시 알아야 할 법적 규제와 리스크 대응 방안을 살펴봅니다."
    elif "투자" in t or "주식" in t or "시장" in t:
        return "글로벌 AI 시장의 자본 흐름과 비즈니스 기회, 투자 관점의 핵심 포인트를 분석합니다."
    elif "코딩" in t or "lovable" in t or "개발" in t or "에이전트" in t:
        return "AI 코딩 에이전트와 노코드 툴을 활용한 새로운 개발 트렌드와 생생한 실전 팁을 공유합니다."
    elif "자격증" in t or "교육" in t or "essential" in t or "training" in t:
        return "AI 역량을 증명하고 실력을 한 단계 높일 수 있는 유용한 글로벌 교육 과정과 자격증 정보를 소개합니다."
    elif "rag" in t or "llm" in t or "프롬프트" in t:
        return "생성형 AI의 성능을 극대화하는 핵심 기술의 개념과 실무 적용 노하우를 다룹니다."
    elif "퍼플렉시티" in t or "제미나이" in t or "chatgpt" in t or "툴" in t or "옵시디언" in t or "안티그래비티" in t:
        return "생산성을 획기적으로 높여주는 최신 AI 서비스들의 특징과 실제 업무 활용기를 전해드립니다."
    elif "일자리" in t or "대체" in t or "시대" in t or "트렌드" in t:
        return "인공지능이 가져올 직업 환경의 변화와 우리가 준비해야 할 미래 생존 전략을 고민해 봅니다."
    else:
        # 키워드에 안 걸리는 일반적인 글일 경우
        return "테크-리걸 전문가의 시선으로 바라본 인공지능과 비즈니스 융합에 대한 깊이 있는 생각을 나눕니다."

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
        summary = generate_summary(original_title)
        
        post_list_html += f"""
        <article class="post-card">
            <div class="post-date">{date}</div>
            <h2 class="post-title"><a href="{link}" target="_blank">{display_title}</a></h2>
            <p class="post-summary">{summary}</p>
            <a href="{link}" class="read-more" target="_blank">원문 읽기 &rarr;</a>
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
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-WTHX05VQS2"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());

      gtag('config', 'G-WTHX05VQS2');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>소담의 AI Mind</title>
    <meta name="description" content="인공지능과 비즈니스의 융합을 연구하며 전문적인 기술-법률적 통찰을 기록합니다.">
    <link rel="stylesheet" href="assets/style.css">
    <script type="application/ld+json">
{json_ld_html}
    </script>
</head>
<body>
    <header>
        <div class="container">
            <h1>소담의 AI Mind</h1>
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
