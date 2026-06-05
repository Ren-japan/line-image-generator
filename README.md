# 💬 LINE Image Generator

LINEマーケ用画像（PUバナー + 診断カルーセル）を自動生成するStreamlitアプリ。

姉妹アプリ: [seo-image-generator](https://github.com/Ren-japan/seo-image-generator)（SEO記事画像専用）

## できること

### 📣 PU画像生成
- 「問いかけ＋はい/いいえ」型のLINE誘導バナー
- 訴求テーマを入力 → AIが文言案を提案 → 参照画像のテイストで画像生成
- 1枚 1024×1024 〜 任意サイズ

### 🎠 診断カルーセル生成
- 表紙 + 設問N枚 + 結果 のシリーズ画像
- 3〜10枚で可変（初期6枚）
- 全枚同じ参照画像セットでトーン統一
- ナンバリング自動付与（1/6, 2/6, ...）

## 構成

```
入力: 訴求テーマ / 診断テーマ
   ↓
Layer 2: 文言案提案プロンプト (Gemini 2.5 Flash)
   → PU: 「問いかけ＋はい/いいえ」型のJSON配列
   → カルーセル: 「表紙 + 設問N + 結果」のJSON
   ↓
Layer 3: 画像生成プロンプト (OpenAI gpt-image-2 推奨 / Gemini も可)
   → 参照画像で完全スタイルトランスファー
   → カルーセルは全枚同じ参照画像で生成（トーン統一）
   ↓
出力: PNG画像 (個別DL / ZIP一括DL)
```

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
# .env に GEMINI_API_KEY と OPENAI_API_KEY を記入
streamlit run app.py
```

## 推奨ワークフロー

1. **サイト/案件を登録**（左サイドバー → サイト設定）
   - ジャンル × クライアント単位で1つ（例: `medical-diet-koizumi`）
   - ブランドカラーを設定
2. **参照画像をアップロード**（サイト設定 → 参照画像）
   - `category=pu` でPU用ロールモデル画像（過去のヒット作）3〜5枚
   - `category=carousel` でカルーセル用ロールモデル画像3〜5枚
3. **PU or カルーセル を生成**
   - サイドバーでサイト選択 → メインメニューでモード選択
   - 訴求テーマを入れて → AIに文言案生成させて → 一括画像生成
4. **微調整 → ダウンロード**

## デプロイ構成

- 本番URL: `https://line-image-generator.streamlit.app`
- 本番デプロイ元: `Ren-japan/line-image-generator`（独立リポ）
- 開発履歴: `Ren-japan/claude-projects` monorepo内の `line-image-generator/`
- **更新時は両方push必須**（独立リポ側がStreamlit Cloudのソース）

## APIキー

- `GEMINI_API_KEY`: テキスト分析（文言案提案）に必須
- `OPENAI_API_KEY`: 画像生成プロバイダがOpenAI時に必須（推奨）

両キーともseo-image-generatorと同じものを使い回し可能。
