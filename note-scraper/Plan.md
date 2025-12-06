# Note記事スクレイピング計画

## 目的
- note.com/jyukenn_ の2025年8月13日以降の記事をすべてスクレイピング
- テキストと画像を保存

## 対象ユーザー
- URL: https://note.com/jyukenn_
- 参考記事: https://note.com/jyukenn_/n/n4fc2f512aa51

## 手順
1. ユーザーの記事一覧ページを取得
2. 2025年8月13日以降の記事を特定
3. 各記事のテキストをスクレイピング
4. 各記事の画像をダウンロード
5. 記事ごとにフォルダを作成して保存

## ファイル構成
```
note-scraper/
├── Plan.md          # 計画書
├── Status.md        # 進捗状況
├── log.md           # 作業ログ
├── scraper.py       # スクレイピングスクリプト
└── articles/        # 保存された記事
    └── [記事タイトル]/
        ├── content.md   # 記事テキスト
        └── images/      # 画像ファイル
```

## 技術的アプローチ
- Python + requests + BeautifulSoup4
- note.com APIを活用（可能であれば）
- User-Agentを適切に設定

---

## ローカル実行方法

この環境ではnote.comへのアクセスがブロックされているため、ローカルPCで実行してください。

### 1. 依存関係のインストール
```bash
cd note-scraper
pip install -r requirements.txt
```

### 2. スクリプトの実行
```bash
python scraper.py
```

### 3. 結果の確認
`articles/`フォルダに記事が保存されます。
