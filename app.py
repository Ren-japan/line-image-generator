"""
LINE マーケ画像自動生成ツール
エントリーポイント: ナビゲーション + 共通ステート初期化 + サイドバー

PU（プッシュアップ）バナーと診断カルーセル（複数枚シリーズ）に特化。
SEO Image Generator (seo-image-generator) と同じ参照画像方式・3層プロンプト構造を流用。
"""

import os
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

# プロジェクトルートを基準にする
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

# ----- ページ設定（最初に呼ぶ必要あり）-----
st.set_page_config(
    page_title="LINE Image Generator",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----- マネージャーは lib/dependencies.py から取得 -----
from lib.dependencies import get_config_manager


# ----- セッションステート初期化 -----
def init_session_state():
    defaults = {
        "api_key": os.getenv("GEMINI_API_KEY", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        # 画像生成プロバイダ: "gemini" or "openai"
        "image_provider": "openai",  # LINE版は image2.0 デフォルト（バナー的デザインが得意）
        "current_site": None,
        "site_config": {},
        # PUモード用
        "pu_input_keyword": "",
        "pu_input_theme": "",
        "pu_proposals": [],
        "pu_selected_proposals": [],
        "pu_generated_images": [],
        "pu_generation_in_progress": False,
        # カルーセルモード用
        "carousel_theme": "",
        "carousel_questions": "",
        "carousel_count": 6,
        "carousel_proposals": [],
        "carousel_generated_images": [],
        "carousel_generation_in_progress": False,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


init_session_state()

# ----- ナビゲーション定義 -----
pages = st.navigation(
    {
        "メイン": [
            st.Page("pages/01_pu_generation.py", title="PU画像生成", icon="📣", default=True),
            st.Page("pages/02_carousel_generation.py", title="カルーセル生成", icon="🎠"),
            st.Page("pages/03_pr_generation.py", title="PR画像生成（URL→トンマナ）", icon="🎯"),
            st.Page("pages/06_result_carousel_generation.py", title="結果カルーセル生成", icon="🏆"),
            st.Page("pages/05_diagnosis_brief.py", title="設計書・依頼書生成", icon="📋"),
        ],
        "設定": [
            st.Page("pages/04_site_settings.py", title="ジャンル設定", icon="🏷️"),
        ],
    }
)

# ----- 共通サイドバー -----
with st.sidebar:
    st.markdown("### 💬 LINE Image Generator")
    st.caption("PUバナーと診断カルーセルを自動生成")

    from lib.dependencies import get_storage_backend_status
    st.caption(f"保存先: {get_storage_backend_status()}")

    st.divider()

    # ジャンル選択
    cm = get_config_manager()
    sites = cm.list_sites()

    if sites:
        site_options = ["-- ジャンルを選択 --"] + sites
        current_idx = 0
        if st.session_state.current_site in sites:
            current_idx = sites.index(st.session_state.current_site) + 1

        selected = st.selectbox(
            "対象ジャンル",
            site_options,
            index=current_idx,
            key="sidebar_site_select",
            help="ジャンル（案件）単位で参照画像とブランドカラーを登録し、テイストを揃えます",
        )

        if selected != "-- ジャンルを選択 --":
            if st.session_state.current_site != selected:
                st.session_state.current_site = selected
                st.session_state.site_config = cm.load(selected)
                st.rerun()
        else:
            st.session_state.current_site = None
            st.session_state.site_config = {}
    else:
        st.info("ジャンルが未登録です。\n「ジャンル設定」から登録してください。")

    # 現在のサイト情報表示
    if st.session_state.current_site:
        config = st.session_state.site_config
        st.divider()
        st.markdown(f"**{config.get('brand_name', st.session_state.current_site)}**")

        # カラーパレットのプレビュー
        colors = [
            config.get("primary_color", "#06C755"),  # LINE グリーン デフォルト
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

    # 画像生成プロバイダ選択
    st.divider()
    st.markdown("### 画像生成プロバイダ")

    provider_options = {
        "openai": "OpenAI (gpt-image-2) ⭐ 推奨",
        "gemini": "Gemini (gemini-3-pro-image-preview)",
    }
    current_provider = st.session_state.image_provider
    selected_provider = st.radio(
        "使用モデル",
        options=list(provider_options.keys()),
        format_func=lambda p: provider_options[p],
        index=list(provider_options.keys()).index(current_provider),
        key="sidebar_provider_select",
        help="バナー的デザインは OpenAI gpt-image-2 推奨。複数枚で構造を厳密に揃えたいときは Gemini。",
    )
    if selected_provider != current_provider:
        st.session_state.image_provider = selected_provider
        st.rerun()

    # APIキー状態
    st.divider()
    st.markdown("### API Keys")

    if st.session_state.api_key:
        st.success("Gemini Key: 設定済み", icon="✅")
    else:
        st.warning("Gemini Key: 未設定（テキスト分析に必須）", icon="⚠️")
        api_key_input = st.text_input("Gemini API Key", type="password", key="sidebar_api_key")
        if api_key_input:
            st.session_state.api_key = api_key_input
            st.rerun()

    if st.session_state.openai_api_key:
        st.success("OpenAI Key: 設定済み", icon="✅")
    else:
        if st.session_state.image_provider == "openai":
            st.error("OpenAI Key: 未設定", icon="❌")
        else:
            st.caption("OpenAI Key: 未設定（OpenAI使用時に必要）")
        openai_key_input = st.text_input("OpenAI API Key", type="password", key="sidebar_openai_api_key")
        if openai_key_input:
            st.session_state.openai_api_key = openai_key_input
            st.rerun()

# ----- ページ実行 -----
pages.run()
