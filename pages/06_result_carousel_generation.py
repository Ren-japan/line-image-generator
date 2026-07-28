"""
結果カルーセル生成ページ
診断確定後に表示する「タイプ発表→根拠→解決策→CTA」等のカード群を、
タイプ別・複数枚組でまとめて生成する。診断カルーセル（表紙+設問+結果1枚）とは
別の参照画像セット（category="result_carousel"）を使う。

「📋 設計書・依頼書生成」ページで入力したタイプ別カード文言があれば、
そのままこちらに読み込んで画像生成できる（データはst.session_state.diag_dataで共有）。
"""

import io
import re
import zipfile
import datetime
import streamlit as st

from lib.gemini_client import SUPPORTED_ASPECT_RATIOS
from lib.image_generator import get_image_client, provider_label
from lib.prompt_templates import render_result_card_prompt
from lib.image_postprocessor import trim_whitespace, image_to_bytes


def get_cm():
    from lib.dependencies import get_config_manager
    return get_config_manager()


def _save_to_storage(image, site_name: str, type_name: str, label: str):
    from lib.dependencies import get_output_storage
    storage = get_output_storage()
    safe_type = re.sub(r'[\\/:*?"<>|]', '_', type_name)[:30]
    safe_label = re.sub(r'[\\/:*?"<>|]', '_', label)[:30]
    date_str = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    key = f"generated/{site_name}/result_carousel/{date_str}_{safe_type}_{safe_label}.png"
    storage.save(key, image_to_bytes(image))
    return key


def generate_result_card(card, position, total, type_name, accent_color, config, site_name,
                         image_width, image_height, aspect_ratio, pattern=None):
    image_client = get_image_client(
        provider=st.session_state.image_provider,
        gemini_api_key=st.session_state.api_key,
        openai_api_key=st.session_state.openai_api_key,
    )
    cm = get_cm()
    ref_images = []
    if site_name:
        ref_images = cm.get_reference_pil_images(site_name, category="result_carousel", preset_id=pattern)
        if not ref_images:
            ref_images = cm.get_reference_pil_images(site_name)

    site_colors = {
        "primary_color": config.get("primary_color", "#06C755"),
        "secondary_color": config.get("secondary_color", "#10B981"),
        "accent_color": config.get("accent_color", "#F59E0B"),
        "background_color": config.get("background_color", "#FFFFFF"),
        "text_color": config.get("text_color", "#1F2937"),
        "danger_color": config.get("danger_color", "#E74A3B"),
    }

    gen_prompt = render_result_card_prompt(
        card_role=card.get("role", ""),
        card_text=card.get("text", ""),
        type_name=type_name,
        card_position=position,
        total_cards=total,
        site_colors=site_colors,
        language=config.get("language", "Japanese"),
        has_reference_images=bool(ref_images),
        image_width=image_width,
        image_height=image_height,
        accent_color=accent_color or None,
    )

    gen_image, gen_text = image_client.generate_image(
        prompt=gen_prompt,
        reference_images=ref_images if ref_images else None,
        aspect_ratio=aspect_ratio,
        image_size="2K",
    )
    return gen_image, gen_text, gen_prompt, len(ref_images) if ref_images else 0


# =============================================================
# ヘッダー
# =============================================================
st.title("🏆 結果カルーセル生成")
st.caption("診断結果（タイプ発表→根拠→解決策→CTA等）のカード群を、タイプ別・複数枚組でまとめて生成します。")

if not st.session_state.current_site:
    st.warning("サイドバーからジャンルを選択してください。")
    st.stop()

if not st.session_state.api_key:
    st.error("Gemini API Keyが設定されていません。サイドバーから入力してください。")
    st.stop()

if st.session_state.image_provider == "openai" and not st.session_state.openai_api_key:
    st.error("画像生成プロバイダが OpenAI ですが OPENAI_API_KEY が未設定です。")
    st.stop()

config = st.session_state.site_config
site_name = st.session_state.current_site
st.info(
    f"対象ジャンル: **{config.get('brand_name', site_name)}** ／ "
    f"画像生成: **{provider_label(st.session_state.image_provider)}**"
)

cm = get_cm()

# 結果カルーセルは同一ジャンル内でも商材・タイプ別に複数パターンを持てる
rc_patterns = cm.list_reference_patterns(site_name, "result_carousel")
selected_rc_pattern = None
if rc_patterns:
    selected_rc_pattern = st.selectbox(
        "使用する結果カルーセルパターン（商材・タイプごとに登録された参照デザイン）",
        rc_patterns,
        key="rc_pattern_select",
    )
    rc_ref_count = len(cm.list_reference_images(site_name, category="result_carousel", preset_id=selected_rc_pattern))
    st.success(f"「{selected_rc_pattern}」パターンの参照画像: {rc_ref_count}枚登録済み")
else:
    rc_ref_count = len(cm.list_reference_images(site_name, category="result_carousel"))
    default_ref_count = len(cm.list_reference_images(site_name))
    if rc_ref_count > 0:
        st.success(f"結果カルーセル参照画像: {rc_ref_count}枚登録済み")
    elif default_ref_count > 0:
        st.info(f"結果カルーセル専用参照画像なし → 通常参照画像 {default_ref_count}枚を流用します")
    else:
        st.warning("参照画像未登録。「🏷️ジャンル設定」→「🏆結果カルーセル」タブからパターンを登録推奨。")

# =============================================================
# Step 1: タイプ別カード文言の入力
# =============================================================
st.subheader("Step 1: タイプ別カード文言")

if "rc_result_types" not in st.session_state:
    st.session_state.rc_result_types = []

diag_data = st.session_state.get("diag_data")
if diag_data and diag_data.get("result_types"):
    if st.button("📋 「設計書・依頼書生成」ページのデータを読み込む", use_container_width=True):
        import copy
        st.session_state.rc_result_types = copy.deepcopy(diag_data["result_types"])
        st.rerun()

result_types = st.session_state.rc_result_types

for ti, t in enumerate(result_types):
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            t["name"] = st.text_input("タイプ名", value=t.get("name", ""), key=f"rc_{ti}_name")
        with c2:
            t["accent_color"] = st.color_picker(
                "アクセント色", value=t.get("accent_color") or "#3B82F6", key=f"rc_{ti}_color",
            )
        with c3:
            if st.button("🗑️ タイプ削除", key=f"rc_{ti}_del"):
                result_types.pop(ti)
                st.rerun()

        cards = t.setdefault("cards", [])
        for ci, card in enumerate(cards):
            card["role"] = st.text_input(
                f"Card{ci+1}の役割", value=card.get("role", ""), key=f"rc_{ti}_card_{ci}_role",
            )
            card["text"] = st.text_area(
                f"Card{ci+1}のテキスト", value=card.get("text", ""), height=80, key=f"rc_{ti}_card_{ci}_text",
            )
            if st.button(f"🗑️ Card{ci+1}削除", key=f"rc_{ti}_card_{ci}_del"):
                cards.pop(ci)
                st.rerun()
        if st.button("+ カードを追加", key=f"rc_{ti}_card_add"):
            cards.append({"role": "", "text": ""})
            st.rerun()

if st.button("+ タイプを追加"):
    result_types.append({"name": "", "accent_color": "#3B82F6", "cards": []})
    st.rerun()

if not result_types or not any(t.get("cards") for t in result_types):
    st.info("タイプとカードを最低1つずつ追加してください。")
    st.stop()

# =============================================================
# Step 2: 生成設定
# =============================================================
st.subheader("Step 2: 生成設定")

size_preset = st.radio(
    "サイズ（全カード共通）",
    options=["縦長 (682×1024)", "スクエア (1080×1080)", "横長 (1200×630)", "カスタム"],
    horizontal=True,
    index=0,
    key="rc_size_preset",
)
if size_preset.startswith("縦長"):
    rc_width, rc_height = 682, 1024
elif size_preset.startswith("スクエア"):
    rc_width, rc_height = 1080, 1080
elif size_preset.startswith("横長"):
    rc_width, rc_height = 1200, 630
else:
    cs1, cs2 = st.columns(2)
    with cs1:
        rc_width = st.number_input("幅(px)", min_value=256, max_value=4096, value=682, step=10, key="rc_width")
    with cs2:
        rc_height = st.number_input("高さ(px)", min_value=256, max_value=4096, value=1024, step=10, key="rc_height")

target_ratio = rc_width / rc_height
best_ar = "1:1"
min_diff = float("inf")
for ar in SUPPORTED_ASPECT_RATIOS:
    w, h = map(int, ar.split(":"))
    diff = abs(w / h - target_ratio)
    if diff < min_diff:
        min_diff = diff
        best_ar = ar
st.caption(f"出力サイズ: **{rc_width}×{rc_height}px** / アスペクト比(自動): **{best_ar}**")

total_cards_all = sum(len(t.get("cards", [])) for t in result_types)
st.divider()
st.caption(f"全{len(result_types)}タイプ・合計{total_cards_all}枚を生成します。")

# =============================================================
# Step 3: 一括生成
# =============================================================
if "rc_generated_images" not in st.session_state:
    st.session_state.rc_generated_images = []

if st.button(f"🚀 全{total_cards_all}枚を一括生成", type="primary", use_container_width=True,
             disabled=(total_cards_all == 0)):
    st.session_state.rc_generated_images = []
    progress_bar = st.progress(0, text="結果カルーセルを生成中...")
    done = 0
    for t in result_types:
        cards = t.get("cards", [])
        total = len(cards)
        for i, card in enumerate(cards):
            position = i + 1
            done += 1
            progress_bar.progress(done / total_cards_all, text=f"{t.get('name','')} {position}/{total} を生成中...")
            try:
                gen_image, gen_text, gen_prompt, ref_count = generate_result_card(
                    card, position, total, t.get("name", ""), t.get("accent_color", ""),
                    config, site_name, rc_width, rc_height, best_ar, pattern=selected_rc_pattern,
                )
                if gen_image:
                    label = f"{position:02d}_{card.get('role', '')}"
                    saved_key = _save_to_storage(gen_image, site_name, t.get("name", ""), label)
                    st.session_state.rc_generated_images.append({
                        "type_name": t.get("name", ""),
                        "position": position,
                        "total": total,
                        "role": card.get("role", ""),
                        "image": gen_image,
                        "processed_image": None,
                        "generation_prompt": gen_prompt,
                        "reference_image_count": ref_count,
                        "saved_key": saved_key,
                    })
                else:
                    st.warning(f"{t.get('name','')} {position}/{total} の生成失敗: {gen_text or ''}")
            except Exception as e:
                st.error(f"{t.get('name','')} {position}/{total} のエラー: {e}")
    progress_bar.progress(1.0, text="全カード生成完了!")
    st.rerun()

# =============================================================
# 生成結果
# =============================================================
if st.session_state.rc_generated_images:
    st.subheader("生成結果")
    images = st.session_state.rc_generated_images

    types_seen = []
    for entry in images:
        if entry["type_name"] not in types_seen:
            types_seen.append(entry["type_name"])

    for type_name in types_seen:
        st.markdown(f"### {type_name}")
        type_images = [e for e in images if e["type_name"] == type_name]
        for i, entry in enumerate(type_images):
            d_col, c_col = st.columns([2, 1])
            with d_col:
                display_img = entry.get("processed_image") or entry["image"]
                st.image(display_img, caption=f"{entry['position']}/{entry['total']} - {entry['role']}",
                          use_container_width=True)
                with st.expander("📝 このプロンプトを見る", expanded=False):
                    ref_count = entry.get("reference_image_count", 0)
                    if ref_count > 0:
                        st.caption(f"⚠️ 参照画像を{ref_count}枚併用")
                    st.code(entry.get("generation_prompt", ""), language="text")
            with c_col:
                key_base = f"rc_result_{type_name}_{i}"
                if st.button("余白トリミング", key=f"{key_base}_trim"):
                    entry["processed_image"] = trim_whitespace(entry["image"])
                    st.rerun()
                download_img = entry.get("processed_image") or entry["image"]
                st.download_button(
                    "PNGダウンロード",
                    data=image_to_bytes(download_img),
                    file_name=f"{type_name}_{entry['position']:02d}_{entry['role']}.png",
                    mime="image/png",
                    key=f"{key_base}_dl",
                    use_container_width=True,
                )
        st.divider()

    if st.button("📦 全タイプ・全カードをZIPでダウンロード", use_container_width=True, key="rc_dl_all"):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for entry in images:
                dl_img = entry.get("processed_image") or entry["image"]
                safe_type = re.sub(r'[\\/:*?"<>|]', '_', entry["type_name"])
                filename = f"{safe_type}/{entry['position']:02d}_{entry['role']}.png"
                zf.writestr(filename, image_to_bytes(dl_img))
        st.download_button(
            "ZIPをダウンロード",
            data=buf.getvalue(),
            file_name=f"result_carousel_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            key="rc_zip_file",
            use_container_width=True,
        )
