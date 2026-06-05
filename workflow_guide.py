"""
ワークフロー解説アプリ（独立版）
MV画像生成の裏で何が動いているかを可視化する。
デザイナーとの協業時の共有資料として使う。

起動: streamlit run workflow_guide.py
※ 本体アプリ（app.py）とは独立して動作する
"""

from __future__ import annotations

import os
import json
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

# ページ設定
st.set_page_config(
    page_title="MV生成 ワークフロー解説",
    page_icon="📋",
    layout="wide",
)

from lib.dependencies import get_config_manager
from lib.prompt_templates import (
    MV_PROPOSAL_TEMPLATE,
    MV_GENERATION_WITH_SLOT_STRUCTURE_TEMPLATE,
    MV_GENERATION_WITH_REF_TEMPLATE,
    MV_GENERATION_TEMPLATE,
    render_mv_proposal_prompt,
)

# =============================================
# サイドバー: サイト選択
# =============================================
cm = get_config_manager()
sites = cm.list_sites()

with st.sidebar:
    st.markdown("### ワークフロー解説")
    st.caption("サイトを選択すると、そのサイトの設定に基づいた具体的なプロンプトを確認できます")
    st.divider()

    if sites:
        site_options = ["-- サイトを選択 --"] + sites
        current_idx = 0
        if st.session_state.get("current_site") in sites:
            current_idx = sites.index(st.session_state["current_site"]) + 1

        selected = st.selectbox("対象サイト", site_options, index=current_idx)

        if selected != "-- サイトを選択 --":
            st.session_state["current_site"] = selected
            st.session_state["site_config"] = cm.load(selected)
        else:
            st.session_state["current_site"] = None
            st.session_state["site_config"] = {}
    else:
        st.info("サイトが未登録です。\n本体アプリのサイト設定から登録してください。")

    # カラーパレットプレビュー
    if st.session_state.get("current_site"):
        config = st.session_state["site_config"]
        st.divider()
        st.markdown(f"**{config.get('brand_name', st.session_state['current_site'])}**")
        colors = [
            config.get("primary_color", "#3B82F6"),
            config.get("secondary_color", "#10B981"),
            config.get("accent_color", "#F59E0B"),
            config.get("background_color", "#FFFFFF"),
            config.get("text_color", "#1F2937"),
        ]
        color_html = " ".join(
            f'<span style="display:inline-block;width:24px;height:24px;'
            f'background:{c};border:1px solid #ddd;border-radius:4px;"></span>'
            for c in colors
        )
        st.markdown(color_html, unsafe_allow_html=True)

# 設定取得
config = st.session_state.get("site_config", {})
site_name = st.session_state.get("current_site", "")

# =============================================
# メインコンテンツ
# =============================================
st.title("MV画像生成 ワークフロー解説")
st.caption("各ステップで何が起きているか、実際のプロンプトとともに確認できます")

if not site_name:
    st.info("👈 サイドバーからサイトを選択すると、そのサイトの設定に基づいた具体例が表示されます。")

# =============================================
# セクション1: 全体フロー
# =============================================
st.header("1. MV生成の全体フロー")

st.markdown("""
```
参照画像5枚 ──┐
              ├→ [Step1] スロット構造検出
              │    参照画像のテキスト枠を自動判定
記事テキスト ──┤
              ├→ [Step2] テキスト案生成
              │    各スロットに入れるコピーをAIが提案
              │
              ├→ [Step3] 画像生成
              │    参照画像のデザインをコピー、テキスト・人物だけ差替え
              │
              └→ [Step4] 後処理
                   トリミング・リサイズ
```
""")

st.info(
    "**核心**: 参照画像5枚をAIに見せて「これと同じデザインで中身だけ変えて」と指示する仕組み。\n\n"
    "参照画像の品質 = 出力品質。テキスト指示（プロンプト）の影響は2割程度。"
)

# =============================================
# セクション2: 各ステップの詳細
# =============================================
st.header("2. 各ステップの詳細")

# ----- Step1: スロット構造検出 -----
with st.expander("Step1: スロット構造検出", expanded=False):
    st.markdown("""
**何をしてるか:**
参照画像5枚をGemini Flash（テキスト分析AI）に送って、
「この画像にはどんなテキスト枠（スロット）があるか？」を自動判定する。

**5つのスロットタイプ:**
| スロット | 役割 | 例 |
|---------|------|-----|
| `hook` | 煽りテキスト | "今話題の", "〇〇で人気" |
| `main_title` | メインタイトル | "看護師ボーナス", "BAKUNE" |
| `subtitle` | サブタイトル | "本当に効果はある？" |
| `band_text` | 帯テキスト | "リアルな口コミを調査！" |
| `supplement_text` | 補足テキスト | "期待できる効果や安く買う方法まで紹介" |

**ルール:** 5枚全てに共通するスロットだけを採用。1枚だけにある要素は無視。
""")

    st.markdown("**AIに送っているプロンプト:**")
    slot_detection_prompt = """以下のMV（メインビジュアル/アイキャッチ）参照画像を分析し、テキストスロットの構造をJSON形式で抽出してください。

== 分析ルール ==
1. 画像内に存在するテキスト要素を上から順に全て列挙する
2. 各テキスト要素の役割を以下の5種類のいずれかに分類する:
   - hook: 煽りテキスト
   - main_title: メインタイトル（最も大きいテキスト）
   - subtitle: サブタイトル（メインタイトルの補足的なテキスト）
   - band_text: 帯テキスト（色付きの帯やボックス内のテキスト）
   - supplement_text: 補足テキスト（下部の小さいテキスト）
3. 各要素のスタイルを簡潔に記述する
4. 5枚全てに共通する要素だけを抽出する
5. 存在しないスロットは absent_slots に列挙する

== 出力形式（JSON） ==
{
  "slots": [
    {"role": "hook", "description": "スタイルの短い説明"},
    {"role": "main_title", "description": "..."}
  ],
  "absent_slots": ["subtitle", "supplement_text"],
  "person_style": "背景込み実写 / 切り抜き写真 / イラスト等",
  "background_summary": "背景の構造を短く説明"
}"""
    st.code(slot_detection_prompt, language="text")

    # 現在のサイトのスロット構造を表示
    mv_slot = config.get("mv_slot_structure")
    if mv_slot:
        st.markdown("**現在のサイトの検出結果:**")
        st.json(mv_slot)
    elif site_name:
        st.caption("このサイトではスロット構造が未検出です。")

# ----- Step2: テキスト案生成 -----
with st.expander("Step2: テキスト案生成（Layer2）", expanded=False):
    st.markdown("""
**何をしてるか:**
記事タイトル+本文をGemini Flashに送って、MVの各スロットに入れるテキスト案を1〜3パターン提案させる。

**スロット構造の有無で挙動が変わる:**
- **スロット構造あり（V2）**: 検出されたスロットのみ生成させる（例: hook + band_text + main_titleの3つだけ）
- **スロット構造なし（V1）**: 固定の5スロット全てを生成させる
""")

    mv_slot_structure = config.get("mv_slot_structure")

    sample_title = "【例】看護師ボーナスの相場と平均額"
    sample_text = "（記事本文がここに入ります）"

    tab_current, tab_v1, tab_v2 = st.tabs(["現在のサイト", "V1（5スロット固定）", "V2（検出スロットのみ）"])

    with tab_current:
        if site_name:
            current_prompt = render_mv_proposal_prompt(
                sample_title, sample_text,
                mv_slot_structure=mv_slot_structure,
            )
            path_label = "V2（スロット構造検出済み）" if mv_slot_structure else "V1（5スロット固定）"
            st.markdown(f"**使用パス:** {path_label}")
            st.code(current_prompt, language="text")
        else:
            st.caption("サイトを選択してください")

    with tab_v1:
        v1_prompt = render_mv_proposal_prompt(sample_title, sample_text, mv_slot_structure=None)
        st.code(v1_prompt, language="text")

    with tab_v2:
        sample_slot = {
            "slots": [
                {"role": "hook", "description": "上部の煽りテキスト"},
                {"role": "band_text", "description": "テーマカラーの帯内テキスト"},
                {"role": "main_title", "description": "最大サイズの黒太字タイトル"},
            ],
            "absent_slots": ["subtitle", "supplement_text"],
        }
        v2_prompt = render_mv_proposal_prompt(sample_title, sample_text, mv_slot_structure=sample_slot)
        st.code(v2_prompt, language="text")

# ----- Step3: 画像生成 -----
with st.expander("Step3: 画像生成（Layer3）", expanded=False):
    st.markdown("""
**何をしてるか:**
参照画像 + テキスト内容 + カラーパレットをGemini（画像生成AI）に渡して最終画像を生成する。

**3つのパス（状況に応じて自動選択）:**
""")

    has_refs = bool(cm.list_reference_images(site_name, category="mv")) if site_name else False
    has_slot = bool(config.get("mv_slot_structure"))
    has_spec = bool(config.get("mv_design_spec", "").strip())

    if site_name:
        if has_refs and has_slot:
            st.success("このサイトは **V2パス（スロット構造検出済み）** を使用 → 最もシンプルで安定")
        elif has_refs and has_spec:
            st.info("このサイトは **仕様書パス** を使用 → 参照画像 + 手動デザイン仕様書")
        elif has_refs:
            st.info("このサイトは **V1パス（参照画像コピー）** を使用")
        else:
            st.warning("このサイトは **テンプレートパス** を使用 → 参照画像なし、フルプロンプト")

    tab_v2_gen, tab_v1_gen, tab_noref_gen = st.tabs([
        "V2: スロット構造あり（推奨）",
        "V1: 参照画像コピー",
        "参照画像なし",
    ])

    with tab_v2_gen:
        st.markdown("""
**最もシンプルなプロンプト。** 参照画像にデザインの全てを委ね、テキストと人物だけ差し替える。

スロット構造で「この画像にはhook, band_text, main_titleの3つしかない」と分かっているので、
余計なスロット（subtitle等）を生成しない → ブレが減る。
""")
        st.code(MV_GENERATION_WITH_SLOT_STRUCTURE_TEMPLATE, language="text")

    with tab_v1_gen:
        st.markdown("""
**参照画像をコピーしつつ、構造ヒント（人物配置・背景等）で補強するパス。**

スロット構造が未検出の場合に使用。mv_style_hints で人物の位置やサイズを指定する。
""")
        st.code(MV_GENERATION_WITH_REF_TEMPLATE, language="text")

    with tab_noref_gen:
        st.markdown("""
**参照画像なしの場合のフォールバック。** プロンプトのみで全てのデザインを指示する。

テキストだけでデザインを指示するため精度が低い。参照画像の登録を推奨。
""")
        st.code(MV_GENERATION_TEMPLATE, language="text")

# ----- Step4: 後処理 -----
with st.expander("Step4: 後処理", expanded=False):
    st.markdown("""
AI生成後の画像に対する後処理:

1. **余白トリミング**: 画像端の不要な白余白を自動検出・削除
2. **リサイズ**: 指定サイズ（デフォルト1200×630px）に拡縮
3. **ロゴ追加**（設定時）: サイトロゴを指定位置に合成
""")

# =============================================
# セクション3: 現在のサイト設定
# =============================================
st.header("3. 現在のサイト設定")

if not site_name:
    st.info("サイドバーからサイトを選択してください。")
else:
    st.subheader(f"サイト: {config.get('brand_name', site_name)}")

    # カラーパレット
    with st.expander("カラーパレット", expanded=True):
        color_keys = [
            ("primary_color", "テーマカラー"),
            ("secondary_color", "サブカラー"),
            ("accent_color", "アクセント"),
            ("background_color", "背景"),
            ("text_color", "テキスト"),
            ("danger_color", "警告"),
        ]
        cols = st.columns(len(color_keys))
        for col, (key, label) in zip(cols, color_keys):
            color = config.get(key, "#000000")
            col.markdown(
                f'<div style="background:{color};width:40px;height:40px;border-radius:4px;'
                f'border:1px solid #ccc;margin:0 auto"></div>'
                f'<p style="text-align:center;font-size:12px;margin:4px 0">{label}<br>{color}</p>',
                unsafe_allow_html=True,
            )

    # 参照画像
    with st.expander("MV参照画像", expanded=True):
        mv_refs = cm.get_reference_pil_images(site_name, category="mv") if site_name else []
        if mv_refs:
            ref_cols = st.columns(min(len(mv_refs), 5))
            for col, img in zip(ref_cols, mv_refs):
                col.image(img, use_container_width=True)
            st.caption(f"{len(mv_refs)}枚の参照画像。これらの共通パターンをAIが学習して再現します。")
        else:
            st.caption("MV参照画像が未登録です。")

    # スロット構造
    with st.expander("MVスロット構造", expanded=False):
        mv_slot = config.get("mv_slot_structure")
        if mv_slot:
            for s in mv_slot.get("slots", []):
                st.markdown(f"- **{s['role']}**: {s.get('description', '')}")
            absent = mv_slot.get("absent_slots", [])
            if absent:
                st.caption(f"存在しないスロット: {', '.join(absent)}")
            if mv_slot.get("person_style"):
                st.caption(f"人物スタイル: {mv_slot['person_style']}")
            if mv_slot.get("background_summary"):
                st.caption(f"背景: {mv_slot['background_summary']}")
        else:
            st.caption("スロット構造が未検出です。")

    # mv_style_hints
    hints = config.get("mv_style_hints")
    if hints:
        with st.expander("MVスタイルヒント", expanded=False):
            for k, v in hints.items():
                if v:
                    st.markdown(f"- **{k}**: {v}")

# =============================================
# セクション4: デザイナーが調整できるポイント
# =============================================
st.header("4. デザイナーが調整できるポイント")

st.markdown("""
| 調整ポイント | 影響度 | やり方 |
|-------------|--------|--------|
| **参照画像の差し替え** | ★★★ 最大 | サイト設定 → 参照画像タブ |
| **カラーパレット** | ★★ 大 | サイト設定 → カラー欄 |
| **禁止事項の追加** | ★ 中 | サイト設定 → 禁止事項欄 |
| **ブランドトーン** | ★ 小 | サイト設定 → ブランドトーン欄 |
""")

st.subheader("参照画像の選び方（重要）")
st.markdown("""
- **5枚とも同じレイアウト構造にする** — 1枚でもレイアウトが違うと出力がブレる
- **「理想」を選ぶ** — AIはお手本に寄せようとするので、平均ではなく理想の品質を
- **色味はバラバラでもOK** — カラーパレット設定で上書きされる
- **テキスト配置の順序を統一** — 上から煽り → タイトル → サブタイ → 帯
""")

st.subheader("フィードバックの出し方")
st.markdown("""
**具体的に指摘する:**
- NG例: 「なんか違う」「イメージと違う」
- OK例: 「タイトルの縁取りが太すぎる」「人物が小さい」「背景のグラデーションが急すぎる」

**まず参照画像を疑う:**
1. 参照画像を変えて再生成してみる
2. それでもダメならプロンプト修正（エンジニアに相談）
""")
