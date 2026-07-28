"""
ジャンル設定ページ
ジャンル（=案件）ごとに、ブランドカラーと参照画像（PU/PR/カルーセル用）を一元管理する。

SEO版のサイト設定（MV/記事内画像・イラストスタイル・画像サイズ等）からLINE版に整理:
LINE版のPU/PR/カルーセル生成が実際に使うのは「6色 + 各カテゴリの参照画像」だけ。
"""

import streamlit as st
from lib.color_extractor import extract_colors_from_url


def get_cm():
    from lib.dependencies import get_config_manager
    return get_config_manager()


# 参照画像のカテゴリ定義（LINE版）
REF_CATEGORIES = [
    {"key": "pu", "icon": "📣", "label": "PU用バナー", "help": "「問いかけ＋はい/いいえ」型のプッシュアップバナーの参照デザイン。1枚もの。"},
    {"key": "pr", "icon": "🎯", "label": "PR用カルーセル", "help": "6〜7枚で1ストーリーのPRカルーセルの参照デザイン。順番通りにアップロード。"},
    {"key": "carousel", "icon": "🎠", "label": "診断カルーセル", "help": "診断（表紙→設問→結果）カルーセルの参照デザイン。"},
    {"key": "result_carousel", "icon": "🏆", "label": "結果カルーセル", "help": "診断結果（タイプ発表→根拠→解決策→CTA等）カード群の参照デザイン。タイプ別に複数枚組で使う。"},
]


def render_ref_image_tab(cm, site_name, cat):
    """1カテゴリ分の参照画像 アップロード・一覧・削除UI"""
    key = cat["key"]
    label = f"{cat['icon']} {cat['label']}"

    existing_keys = cm.list_reference_images(site_name, category=key)
    st.caption(cat["help"])

    if existing_keys:
        st.success(f"{label}: {len(existing_keys)}枚 登録済み")
        imgs = cm.get_reference_pil_images(site_name, category=key)
        cols = st.columns(min(len(imgs), 6))
        for i, img in enumerate(imgs):
            with cols[i % 6]:
                st.image(img, caption=f"{i+1}", use_container_width=True)
    else:
        st.info(f"{label}: まだ未登録です")

    uploaded = st.file_uploader(
        f"{label} をアップロード（複数可・順番通り）",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=f"uploader_{site_name}_{key}",
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 保存（上書き）", disabled=not uploaded, key=f"save_{site_name}_{key}"):
            # 既存を全削除してから保存（順番をリセット）
            for k in cm.list_reference_images(site_name, category=key):
                cm.delete_reference_image(k)
            saved = 0
            for f in uploaded:
                try:
                    cm.add_reference_image(site_name, f.name, f.getvalue(), category=key)
                    saved += 1
                except Exception as e:
                    st.warning(f"{f.name} 保存失敗: {e}")
            st.success(f"{label} を {saved}枚 保存しました")
            st.rerun()
    with c2:
        if st.button("🗑️ 全削除", disabled=not existing_keys, key=f"clear_{site_name}_{key}"):
            for k in cm.list_reference_images(site_name, category=key):
                cm.delete_reference_image(k)
            st.success(f"{label} を全削除しました")
            st.rerun()


# =============================================
# ヘッダー
# =============================================
st.title("🏷️ ジャンル設定")
st.caption("ジャンル（案件）ごとに、ブランドカラーと参照画像（PU/PR/カルーセル用）を登録します。一度登録すれば各生成ページで選ぶだけ。")

cm = get_cm()
sites = cm.list_sites()

tab_new, tab_edit = st.tabs(["➕ 新規ジャンル登録", "✏️ 既存ジャンル編集"])

# =============================================
# 新規ジャンル登録
# =============================================
with tab_new:
    st.subheader("新しいジャンル/案件を登録")

    new_site_name = st.text_input(
        "ジャンル識別名（英数字・ハイフン推奨）",
        placeholder="例: medical-diet-koizumi, nursing-levael, aga-dmm",
        key="new_site_name",
        help="内部の識別子。ジャンル×案件で1つ作るのがおすすめ（例: 医療ダイエット×こいずみ）",
    )
    new_brand_name = st.text_input(
        "表示名",
        placeholder="例: 医療ダイエット（こいずみ）",
        key="new_brand_name",
    )

    if st.button("ジャンルを登録", type="primary", key="btn_create_site"):
        if not new_site_name:
            st.error("ジャンル識別名を入力してください。")
        elif new_site_name in sites:
            st.error(f"「{new_site_name}」は既に存在します。")
        else:
            config = cm.get_default()
            config["brand_name"] = new_brand_name or new_site_name
            # LINE版デフォルトカラー（LINEグリーン）
            config["primary_color"] = "#06C755"
            cm.save(new_site_name, config)
            st.success(f"ジャンル「{new_site_name}」を登録しました。「既存ジャンル編集」タブで色と参照画像を設定してください。")
            st.rerun()

# =============================================
# 既存ジャンル編集
# =============================================
with tab_edit:
    if not sites:
        st.info("まだジャンルが登録されていません。「新規ジャンル登録」タブから作成してください。")
    else:
        site_name = st.selectbox("編集するジャンル", sites, key="edit_site_select")
        config = cm.load(site_name)

        st.subheader(f"ジャンル: {config.get('brand_name', site_name)}")

        # ----- 基本情報 -----
        st.markdown("#### 基本情報")
        config["brand_name"] = st.text_input(
            "表示名", value=config.get("brand_name", ""), key=f"edit_brand_{site_name}"
        )
        config["site_url"] = st.text_input(
            "遷移先LP URL（任意・色の自動抽出に使えます）",
            value=config.get("site_url", ""),
            placeholder="https://...",
            key=f"edit_url_{site_name}",
        )

        # ----- ブランドカラー -----
        st.markdown("#### ブランドカラー")
        st.caption("PU/PR/カルーセルの配色のアンカーになります。LP URLがあれば自動抽出も可能。")

        if config.get("site_url"):
            if st.button("🎨 LP URLから色を自動抽出", key=f"extract_colors_{site_name}"):
                with st.spinner("LPから色を抽出中..."):
                    try:
                        result = extract_colors_from_url(config["site_url"])
                        sug = result.get("suggested", {})
                        if sug.get("primary"):
                            config["primary_color"] = sug["primary"]
                        if sug.get("secondary"):
                            config["secondary_color"] = sug["secondary"]
                        if sug.get("accent"):
                            config["accent_color"] = sug["accent"]
                        if sug.get("background"):
                            config["background_color"] = sug["background"]
                        if sug.get("text"):
                            config["text_color"] = sug["text"]
                        cm.save(site_name, config)
                        st.success("色を抽出しました。下で微調整できます。")
                        st.rerun()
                    except Exception as e:
                        st.warning(f"色抽出に失敗（手動設定してください）: {e}")

        col1, col2, col3 = st.columns(3)
        with col1:
            config["primary_color"] = st.color_picker(
                "メインカラー", value=config.get("primary_color", "#06C755"), key=f"c_primary_{site_name}"
            )
            config["text_color"] = st.color_picker(
                "テキスト色", value=config.get("text_color", "#1F2937"), key=f"c_text_{site_name}"
            )
        with col2:
            config["accent_color"] = st.color_picker(
                "アクセント色（CTA等）", value=config.get("accent_color", "#F59E0B"), key=f"c_accent_{site_name}"
            )
            config["danger_color"] = st.color_picker(
                "強調/警告色", value=config.get("danger_color", "#E74A3B"), key=f"c_danger_{site_name}"
            )
        with col3:
            config["background_color"] = st.color_picker(
                "背景色", value=config.get("background_color", "#FFFFFF"), key=f"c_bg_{site_name}"
            )
            config["secondary_color"] = st.color_picker(
                "サブカラー", value=config.get("secondary_color", "#10B981"), key=f"c_secondary_{site_name}"
            )

        if st.button("💾 基本情報・カラーを保存", type="primary", key=f"save_basic_{site_name}"):
            cm.save(site_name, config)
            if st.session_state.get("current_site") == site_name:
                st.session_state.site_config = config
            st.success("保存しました。")

        st.divider()

        # ----- 参照画像（カテゴリ別） -----
        st.markdown("#### 参照画像（PU / PR / カルーセル用）")
        st.caption("各生成ページはここで登録した参照画像を自動で使います。一度登録すれば再利用OK。")

        ref_tabs = st.tabs([f"{c['icon']} {c['label']}" for c in REF_CATEGORIES])
        for tab, cat in zip(ref_tabs, REF_CATEGORIES):
            with tab:
                render_ref_image_tab(cm, site_name, cat)

        st.divider()

        # ----- 削除 -----
        with st.expander("⚠️ このジャンルを削除"):
            st.caption("ジャンル設定と全参照画像が削除されます。元に戻せません。")
            if st.button(f"「{site_name}」を削除する", key=f"delete_site_{site_name}"):
                cm.delete(site_name)
                if st.session_state.get("current_site") == site_name:
                    st.session_state.current_site = None
                    st.session_state.site_config = {}
                st.success(f"ジャンル「{site_name}」を削除しました。")
                st.rerun()
