"""
診断プロジェクトの構造化データ定義。
CMO(marketing-craft)が設計した診断1件分（設問ツリー・タイプ別カード文言・
PU文言・商材マッピング・トンマナ）を1つのJSONにまとめ、
diagnosis_templates.pyのテンプレートで「設計書」「デザイン依頼書」を自動生成する。

想定データ構造（キーは全てトップレベル。無い項目はその節ごと省略される）:

{
  "meta": {
    "title": "総合肌タイプ診断（コスメ④横断診断）",   # 必須
    "created_date": "2026-07-17",                     # 必須
    "version_label": "v2",                            # 任意
    "type_label": "Type B（新規診断）",                 # 任意
    "genre": "コスメ（Carena / carenacosmetic.co.jp）", # 任意
    "status": "v2初稿 / Noaレビュー待ち",               # 任意
    "related_note": "関連: コスメ診断ロードマップ④..."   # 任意
  },
  "revision_notes": ["⚠️2026-07-21追記（...）: ..."],   # 任意。冒頭の警告ブロック群
  "overview": "①②③のいずれにも属さない記事に設置する横断診断。...",  # 必須(概要)

  "product_mapping": {                                # 任意（商材紹介がある診断のみ）
    "axis_labels": ["肌タイプ", "①クレンジング推奨", "②スキンケア推奨", "③化粧水推奨"],
    "rows": [{"axis": "乾燥肌", "values": ["...", "...", "..."]}],
    "notes": "..."                                     # 任意の補足プローズ
  },

  "monosashi": {                                       # 任意（ものさしセクション）
    "before": ["「評判がいいこの商品...", "..."],
    "real_voices": ["「レビューの星が高くても...」（出典）"],
    "after": ["「単品を良いものに変えるより...」", "..."],
    "hammer": "6問で肌タイプを診断し、3ステップ分のおすすめ商品を..."
  },

  "flow": {
    "system_note": "NG-2: 診断結果は最終設問の回答のみで分岐する。...",  # 任意
    "welcome_card": "あなたの肌タイプ診断\n\n...\n\n[スタートする →]",     # 任意
    "questions": [
      {
        "id": "Q1", "text": "年代を教えてください",
        "branch_label": "非分岐",                       # 任意（見出しに (非分岐) 等を付ける）
        "options": [{"label": "A", "text": "10〜20代"}, ...],
        "design_note": "競合リサーチ（AYAKA）で..."        # 任意
      },
      {
        "id": "Q6", "text": "グループ別設問",
        "branch_label": "第二分岐・最終設問＝ここで確定",
        "variants": [                                    # 分岐で表示が分かれる設問はvariantsを使う
          {"condition": "Q5でA/Dを選んだ人向け＝乾燥・敏感グループ",
           "text": "新しいコスメを使うと、赤みやかゆみが出やすいですか？",
           "options": [{"label": "A", "text": "はい、出やすい", "result": "敏感肌"},
                       {"label": "B", "text": "いいえ、特にない", "result": "乾燥肌"}]}
        ],
        "design_note": "..."
      }
    ]
  },

  "result_types": [
    {
      "name": "乾燥肌", "accent_color": "#f4a460",
      "cards": [
        {"role": "タイプ発表＋チェックリスト", "text": "あなたは「乾燥肌」\n\n☑ 洗顔後すぐ、肌がつっぱる\n..."},
        {"role": "根本示唆＋矢印図式", "text": "..."},
        {"role": "おすすめケア", "text": "..."},
        {"role": "未来＋メリット列挙＋CTA", "text": "..."}
      ]
    }
  ],

  "recommendation_carousel": {                          # 任意（3点セットカル等、商材紹介カルがある場合）
    "label": "おすすめ3点セットカル",
    "types": [
      {"name": "乾燥肌", "cards": [{"role": "クッションカード", "text": "..."}, ...]}
    ]
  },

  "pu_copy": {
    "title": "あなたの肌タイプ診断",
    "variants": [
      {"label": "案A（気づき型／主推薦）", "headline": "その化粧品、自分の肌タイプに合わせて選べてる？",
       "sub": "カンタン6問診断", "buttons": ["チェックする", "いいえ"]}
    ],
    "usage_note": "3案を全対象記事に均等にABテストで出す（記事タイプ別の決め打ち振り分けはしない）"
  },

  "simulations": [                                       # 任意
    {"persona": "BBクリーム比較記事から流入した30代女性（脂性肌想定）",
     "walkthrough": "PU（案B）→...", "evaluation": "◎ 問題なし。"}
  ],

  "expected_impact": {                                    # 任意（フェルミ推定）
    "assumptions": "対象記事の実URL一覧・実PVは未確定。...",
    "rows": [{"label": "月間クリック（逆算値）", "conservative": "3,967", "standard": "3,967", "upside": "3,967"}],
    "notes": "..."
  },

  "tone": {
    "primary_color": "ティールグリーン系", "secondary_color": "ピーチオレンジ系",
    "background": "白 ＋ ライトミント / ライトピーチ",
    "illustration": "シンプルな線画タッチ",
    "target": "20〜40代女性（ファンデ/オイル/成分に個別関心を持つ層）",
    "type_accent_colors": {"乾燥肌": "#f4a460"}            # 任意（依頼書のタイプ別アクセント色表示用）
  },

  "image_counts": {                                       # デザイン依頼書の「必要な画像一覧」表
    "pu_banner": 3, "cover": 1, "question_panels": 6,
    "result_carousel": 16, "recommendation_carousel": 16,
    "total": 42, "note": "Q6を2パターン別々の画像として作る場合は43枚"
  },

  "remaining_tasks": ["[x] マッピング表のアフィリリンク最終確認", "[ ] 対象記事の実URL一覧を確定させる"],

  "docs_url": "https://plussaitounoa-lgtm.github.io/noa-docs/xxx.html"   # 任意（依頼書からのリンク）
}
"""

from __future__ import annotations


def get_sample_data() -> dict:
    """テンプレート動作確認用の最小サンプル(化粧水診断ベースの簡略版)"""
    return {
        "meta": {
            "title": "サンプル診断",
            "created_date": "2026-07-27",
            "version_label": "v1",
            "genre": "コスメ（サンプル）",
            "status": "サンプル",
        },
        "overview": "これはテンプレート動作確認用のサンプルデータです。",
        "flow": {
            "questions": [
                {
                    "id": "Q1",
                    "text": "年代を教えてください",
                    "branch_label": "非分岐",
                    "options": [{"label": "A", "text": "20代"}, {"label": "B", "text": "30代"}],
                },
                {
                    "id": "Q2",
                    "text": "一番気になる悩みは？",
                    "branch_label": "最終設問・タイプ確定",
                    "options": [
                        {"label": "A", "text": "乾燥", "result": "タイプA"},
                        {"label": "B", "text": "皮脂", "result": "タイプB"},
                    ],
                },
            ]
        },
        "result_types": [
            {
                "name": "タイプA",
                "accent_color": "#3a94b8",
                "cards": [
                    {"role": "タイプ発表", "text": "あなたは「タイプA」\n\n☑ サンプル項目1"},
                    {"role": "未来＋CTA", "text": "サンプル本文\n\n[ボタン] 詳しく見る →"},
                ],
            }
        ],
        "pu_copy": {
            "title": "サンプル診断",
            "variants": [
                {"label": "案A", "headline": "サンプルヘッドライン？", "sub": "カンタン2問診断",
                 "buttons": ["はい", "いいえ"]}
            ],
        },
        "tone": {
            "primary_color": "ティールグリーン系",
            "background": "白",
            "target": "サンプルターゲット",
        },
        "image_counts": {"pu_banner": 1, "cover": 1, "question_panels": 2, "result_carousel": 2, "total": 6},
        "remaining_tasks": ["[ ] サンプルタスク"],
    }
