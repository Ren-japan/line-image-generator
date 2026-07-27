"""
診断設計書・デザイン依頼書 生成ページ
診断プロジェクトの構造化データ(JSON)を貼り付けると、house format通りの
「診断設計書」「デザイン依頼書」のmarkdownを自動生成する。

入力データはClaude Code(CMO/marketing-craftフロー)がlib/diagnosis_schema.pyの
構造に沿って組む想定。データ構造の詳細はlib/diagnosis_schema.pyのdocstring参照。
"""

import json
import datetime
import streamlit as st

from lib.diagnosis_schema import get_sample_data
from lib.diagnosis_templates import render_design_doc, render_design_brief


st.title("📋 診断設計書・デザイン依頼書 生成")
st.caption("診断プロジェクトの構造化データ(JSON)から、house format通りの設計書・依頼書を自動生成します。")

if "diag_json_text" not in st.session_state:
    st.session_state.diag_json_text = ""

# =============================================================
# Step 1: データ入力
# =============================================================
st.subheader("Step 1: 診断データ(JSON)を貼り付け")

c1, c2 = st.columns([3, 1])
with c2:
    if st.button("📄 サンプルを読み込む", use_container_width=True):
        st.session_state.diag_json_text = json.dumps(get_sample_data(), ensure_ascii=False, indent=2)
        st.rerun()
    uploaded = st.file_uploader("または.jsonをアップロード", type=["json"], key="diag_json_upload")
    if uploaded is not None:
        st.session_state.diag_json_text = uploaded.getvalue().decode("utf-8")

with c1:
    with st.expander("データ構造の説明を見る（lib/diagnosis_schema.py）", expanded=False):
        from lib import diagnosis_schema
        st.code(diagnosis_schema.__doc__, language="text")

json_text = st.text_area(
    "診断データ(JSON)",
    value=st.session_state.diag_json_text,
    height=300,
    key="diag_json_input",
    placeholder="ここにJSONを貼り付け（構造はlib/diagnosis_schema.pyのdocstring参照。「サンプルを読み込む」で例を確認できます）",
)
st.session_state.diag_json_text = json_text

# =============================================================
# Step 2: パース・生成
# =============================================================
data = None
if json_text.strip():
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        st.error(f"JSONの解析に失敗しました: {e}")

if not data:
    st.info("診断データを入力すると、設計書・デザイン依頼書のプレビューがここに表示されます。")
    st.stop()

st.subheader("Step 2: 生成結果")

try:
    design_doc_md = render_design_doc(data)
    design_brief_md = render_design_brief(data)
except Exception as e:
    st.error(f"生成中にエラーが発生しました（データ構造を確認してください）: {e}")
    st.stop()

title = data.get("meta", {}).get("title", "診断")
date_str = datetime.datetime.now().strftime("%Y%m%d")

tab_doc, tab_brief = st.tabs(["📖 診断設計書", "🎨 デザイン依頼書"])

with tab_doc:
    st.download_button(
        "設計書(.md)をダウンロード",
        data=design_doc_md,
        file_name=f"診断-{title}.md",
        mime="text/markdown",
        key="dl_design_doc",
        use_container_width=True,
    )
    with st.expander("プレビュー(レンダリング表示)", expanded=True):
        st.markdown(design_doc_md)
    with st.expander("Markdownソース", expanded=False):
        st.code(design_doc_md, language="markdown")

with tab_brief:
    st.download_button(
        "デザイン依頼書(.md)をダウンロード",
        data=design_brief_md,
        file_name=f"デザイン依頼書-{title}.md",
        mime="text/markdown",
        key="dl_design_brief",
        use_container_width=True,
    )
    with st.expander("プレビュー(レンダリング表示)", expanded=True):
        st.markdown(design_brief_md)
    with st.expander("Markdownソース", expanded=False):
        st.code(design_brief_md, language="markdown")
