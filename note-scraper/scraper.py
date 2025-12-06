#!/usr/bin/env python3
"""
note.com記事スクレイパー
対象: jyukenn_ の2025年8月13日以降の記事
"""

import requests
import os
import re
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 設定
USERNAME = "jyukenn_"
BASE_URL = "https://note.com"
API_URL = f"https://note.com/api/v2/creators/{USERNAME}/contents"
CUTOFF_DATE = datetime(2025, 8, 13)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "articles")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    'Referer': f'https://note.com/{USERNAME}',
}

def get_articles_list():
    """記事一覧を取得"""
    articles = []
    page = 1

    while True:
        print(f"ページ {page} を取得中...")
        params = {'kind': 'note', 'page': page}

        try:
            response = requests.get(API_URL, headers=HEADERS, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'data' not in data or 'contents' not in data['data']:
                print("データ構造が予想と異なります")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                break

            contents = data['data']['contents']
            if not contents:
                print("これ以上記事がありません")
                break

            for item in contents:
                try:
                    # 日付を解析
                    publish_date_str = item.get('publishAt') or item.get('createdAt')
                    if publish_date_str:
                        # ISO形式の日付を解析
                        publish_date = datetime.fromisoformat(publish_date_str.replace('Z', '+00:00'))
                        publish_date = publish_date.replace(tzinfo=None)  # timezone-naive に変換
                    else:
                        continue

                    article = {
                        'id': item.get('id'),
                        'title': item.get('name', 'Untitled'),
                        'url': f"https://note.com/{USERNAME}/n/{item.get('key')}",
                        'key': item.get('key'),
                        'publish_date': publish_date,
                        'publish_date_str': publish_date_str,
                    }
                    articles.append(article)
                    print(f"  - {article['title']} ({publish_date.strftime('%Y-%m-%d')})")

                except Exception as e:
                    print(f"  記事解析エラー: {e}")
                    continue

            # 最後の記事がCUTOFF_DATEより古ければ終了
            if contents and articles:
                last_date = articles[-1]['publish_date']
                if last_date < CUTOFF_DATE:
                    print(f"CUTOFF_DATE ({CUTOFF_DATE.strftime('%Y-%m-%d')}) より古い記事に到達")
                    break

            page += 1
            time.sleep(1)  # レート制限対策

        except requests.exceptions.RequestException as e:
            print(f"API取得エラー: {e}")
            break

    return articles

def filter_articles_by_date(articles):
    """2025年8月13日以降の記事のみフィルタ"""
    filtered = [a for a in articles if a['publish_date'] >= CUTOFF_DATE]
    print(f"\n2025/8/13以降の記事: {len(filtered)}件")
    return filtered

def sanitize_filename(name):
    """ファイル名として使えない文字を置換"""
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', name)
    sanitized = sanitized.strip()
    return sanitized[:100]  # 長すぎる場合は切り詰め

def download_image(url, save_path):
    """画像をダウンロード"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"    画像ダウンロードエラー: {url} - {e}")
        return False

def scrape_article(article):
    """個別記事をスクレイピング"""
    print(f"\n記事取得中: {article['title']}")

    # 記事詳細APIを試す
    article_api_url = f"https://note.com/api/v3/notes/{article['key']}"

    try:
        response = requests.get(article_api_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()

        note_data = data.get('data', {})

        # テキスト本文を取得
        body = note_data.get('body', '')

        # 記事保存ディレクトリ作成
        article_dir = os.path.join(OUTPUT_DIR, sanitize_filename(article['title']))
        images_dir = os.path.join(article_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)

        # HTMLからテキストと画像を抽出
        soup = BeautifulSoup(body, 'html.parser')

        # 画像URLを収集
        images = []
        for idx, img in enumerate(soup.find_all('img')):
            src = img.get('src') or img.get('data-src')
            if src:
                images.append(src)

        # 画像をダウンロード
        downloaded_images = []
        for idx, img_url in enumerate(images):
            # 拡張子を推測
            ext = '.jpg'
            if '.png' in img_url.lower():
                ext = '.png'
            elif '.gif' in img_url.lower():
                ext = '.gif'
            elif '.webp' in img_url.lower():
                ext = '.webp'

            img_filename = f"image_{idx+1:03d}{ext}"
            img_path = os.path.join(images_dir, img_filename)

            if download_image(img_url, img_path):
                downloaded_images.append(img_filename)
                print(f"    画像保存: {img_filename}")

        # アイキャッチ画像
        eyecatch = note_data.get('eyecatch')
        if eyecatch:
            eyecatch_path = os.path.join(images_dir, 'eyecatch.jpg')
            if download_image(eyecatch, eyecatch_path):
                downloaded_images.insert(0, 'eyecatch.jpg')
                print(f"    アイキャッチ保存")

        # テキストを整形
        text_content = soup.get_text(separator='\n\n')

        # Markdownファイルを作成
        md_content = f"""# {article['title']}

**投稿日**: {article['publish_date'].strftime('%Y-%m-%d')}
**URL**: {article['url']}

---

{text_content}

---

## 画像一覧
"""
        for img in downloaded_images:
            md_content += f"- ![{img}](images/{img})\n"

        # 保存
        content_path = os.path.join(article_dir, 'content.md')
        with open(content_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"  保存完了: {article_dir}")
        return True

    except Exception as e:
        print(f"  記事スクレイピングエラー: {e}")

        # フォールバック: HTMLページから直接取得
        try:
            print("  フォールバック: HTMLページから取得を試行...")
            response = requests.get(article['url'], headers=HEADERS, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 記事本文を探す
            article_body = soup.find('div', class_='note-common-styles__textnote-body') or \
                          soup.find('div', {'data-name': 'body'}) or \
                          soup.find('article')

            if article_body:
                article_dir = os.path.join(OUTPUT_DIR, sanitize_filename(article['title']))
                images_dir = os.path.join(article_dir, 'images')
                os.makedirs(images_dir, exist_ok=True)

                # 画像を収集・ダウンロード
                downloaded_images = []
                for idx, img in enumerate(article_body.find_all('img')):
                    src = img.get('src') or img.get('data-src')
                    if src and src.startswith('http'):
                        ext = '.jpg'
                        if '.png' in src.lower():
                            ext = '.png'
                        elif '.gif' in src.lower():
                            ext = '.gif'

                        img_filename = f"image_{idx+1:03d}{ext}"
                        img_path = os.path.join(images_dir, img_filename)

                        if download_image(src, img_path):
                            downloaded_images.append(img_filename)

                text_content = article_body.get_text(separator='\n\n')

                md_content = f"""# {article['title']}

**投稿日**: {article['publish_date'].strftime('%Y-%m-%d')}
**URL**: {article['url']}

---

{text_content}

---

## 画像一覧
"""
                for img in downloaded_images:
                    md_content += f"- ![{img}](images/{img})\n"

                content_path = os.path.join(article_dir, 'content.md')
                with open(content_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)

                print(f"  フォールバック保存完了: {article_dir}")
                return True
        except Exception as e2:
            print(f"  フォールバックも失敗: {e2}")

        return False

def main():
    print("=" * 60)
    print("note.com スクレイパー")
    print(f"対象ユーザー: {USERNAME}")
    print(f"対象期間: 2025/8/13以降")
    print("=" * 60)

    # 出力ディレクトリ作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 記事一覧を取得
    print("\n[1/3] 記事一覧を取得中...")
    all_articles = get_articles_list()
    print(f"取得した記事数: {len(all_articles)}")

    # 日付でフィルタ
    print("\n[2/3] 日付でフィルタリング...")
    target_articles = filter_articles_by_date(all_articles)

    if not target_articles:
        print("対象の記事が見つかりませんでした")
        return

    print("\n対象記事:")
    for a in target_articles:
        print(f"  - {a['title']} ({a['publish_date'].strftime('%Y-%m-%d')})")

    # 各記事をスクレイピング
    print("\n[3/3] 記事をスクレイピング中...")
    success_count = 0
    for idx, article in enumerate(target_articles, 1):
        print(f"\n--- {idx}/{len(target_articles)} ---")
        if scrape_article(article):
            success_count += 1
        time.sleep(2)  # レート制限対策

    print("\n" + "=" * 60)
    print(f"完了: {success_count}/{len(target_articles)} 記事を保存")
    print(f"保存先: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
