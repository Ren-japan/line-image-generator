"""
PR画像カルーセル生成ページ（6-7枚セット）

knowledge/pr-design-patterns.md の暗黙知に基づく設計。
PR=複数枚で1ストーリーが前提（1枚生成じゃない）。

パイプライン:
1. URL → og:image取得（LP色味の参照）
2. デザイン参照画像セット → Gemini Visionで構造抽出（テキストは捨て、構造のみ）
3. 商材情報 + LP情報 → 全N枚の役割別文言を一括設計
4. 各枚を順次生成（共通骨格・CTA・色味で統一、各枚=役割別コンテンツ）
"""

from __future__ import annotations
import io
import json
import re
import zipfile
import datetime
import streamlit as st
from PIL import Image

from lib.gemini_client import GeminiClient, SUPPORTED_ASPECT_RATIOS
from lib.image_generator import get_image_client, provider_label
from lib.prompt_templates import (
    render_pr_carousel_structure_prompt,
    render_pr_carousel_content_proposal,
    render_pr_carousel_slide_generation,
    render_product_info_extraction_prompt,
    format_product_info_for_proposal,
    PR_DEFAULT_ROLE_SETS,
    PR_ROLE_DEFINITIONS,
)
from lib.image_postprocessor import trim_whitespace, image_to_bytes
from lib.url_scraper import fetch_lp_reference_images, fetch_lp_text_content


def get_cm():
    from lib.dependencies import get_config_manager
    return get_config_manager()


def _save_to_storage(image, site_name: str, label: str):
    from lib.dependencies import get_output_storage
    storage = get_output_storage()
    safe_label = re.sub(r'[\\/:*?"<>|]', '_', label)[:50]
    date_str = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    key = f"generated/{site_name}/pr_carousel/{date_str}_{safe_label}.png"
    storage.save(key, image_to_bytes(image))
    return key


def _extract_json_obj(response_text: str) -> dict | None:
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", response_text, re.DOTALL)
    text = m.group(1).strip() if m else response_text.strip()
    s, e = text.find("{"), text.rfind("}")
    if s == -1 or e == -1:
        return None
    try:
        return json.loads(text[s:e+1])
    except json.JSONDecodeError:
        return None


# ----- セッションステート初期化 -----
for key, default in {
    "prc_target_url": "",
    "prc_lp_metadata": {},
    "prc_lp_tone_images": [],
    "prc_lp_body_text": "",
    "prc_lp_product_info": None,  # 自動抽出された商材情報JSON
    "prc_design_ref_images": [],
    "prc_design_structure": None,
    "prc_product_info": "",
    "prc_page_count": 6,
    "prc_roles": list(PR_DEFAULT_ROLE_SETS[6]),
    "prc_content": None,
    "prc_generated_images": [],
    "prc_in_progress": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# =============================================================
# ヘッダー
# =============================================================
st.title("🎯 PR画像カルーセル生成")
st.caption("LPのトンマナ + 過去のヒットPRの構造 = 6-7枚で1ストーリーのPRカルーセルを生成")

if not st.session_state.api_key:
    st.error("Gemini API Keyが設定されていません。サイドバーから入力してください。")
    st.stop()
if st.session_state.image_provider == "openai" and not st.session_state.openai_api_key:
    st.error("画像生成プロバイダが OpenAI ですが OPENAI_API_KEY が未設定です。")
    st.stop()

config = st.session_state.site_config or {}
if st.session_state.current_site:
    st.info(
        f"対象サイト: **{config.get('brand_name', st.session_state.current_site)}** ／ "
        f"画像生成: **{provider_label(st.session_state.image_provider)}**"
    )
else:
    st.info(
        f"サイト未選択（PRカルーセルはサイト未登録でも生成可能）／ "
        f"画像生成: **{provider_label(st.session_state.image_provider)}**"
    )

# =============================================================
# Step 1: 遷移先LP URL
# =============================================================
st.subheader("Step 1: 遷移先LPのURL（色味・雰囲気の参照）")

target_url = st.text_input(
    "遷移先LPのURL",
    value=st.session_state.prc_target_url,
    placeholder="例: https://top.dhc.co.jp/shop/ad/bbcream/...",
    key="prc_input_url",
)
st.session_state.prc_target_url = target_url

if st.button("URLから情報取得（画像＋商材情報を自動抽出）", disabled=not target_url.strip(), use_container_width=False, key="prc_fetch_lp", type="primary"):
    with st.status("LPから情報取得中...", expanded=True) as status:
        try:
            st.write("Step 1/3: LP画像とog:*メタを取得...")
            images, metadata = fetch_lp_reference_images(target_url, max_count=5)
            st.session_state.prc_lp_tone_images = images
            st.session_state.prc_lp_metadata = metadata
            st.write(f"  画像 {len(images)} 枚 / og_title: {(metadata.get('og_title') or '')[:40]}...")

            st.write("Step 2/3: LP本文テキストを取得...")
            try:
                body_text = fetch_lp_text_content(target_url, max_chars=6000)
            except Exception:
                body_text = ""
            st.session_state.prc_lp_body_text = body_text
            st.write(f"  本文 {len(body_text)} 文字（JSレンダ系LPだと0でも続行）")

            st.write("Step 3/3: 商材情報をGeminiで構造化抽出...")
            try:
                gemini = GeminiClient(api_key=st.session_state.api_key)
                extract_prompt = render_product_info_extraction_prompt(
                    page_title=metadata.get("page_title", ""),
                    og_title=metadata.get("og_title", ""),
                    og_description=metadata.get("og_description", ""),
                    body_text=body_text,
                )
                resp = gemini.analyze_text(extract_prompt)
                product_info = _extract_json_obj(resp)
                if product_info:
                    st.session_state.prc_lp_product_info = product_info
                    # 商材情報フォームに自動入力（既存値があれば上書きしない、空のときだけ補完）
                    formatted = format_product_info_for_proposal(product_info)
                    if not st.session_state.prc_product_info.strip():
                        st.session_state.prc_product_info = formatted
                    st.write(f"  商材情報抽出OK: 商品名={product_info.get('product_name', '?')}")
                else:
                    st.warning("商材情報のJSON解析失敗。og情報のみで続行します。")
            except Exception as ex_inner:
                st.warning(f"商材情報抽出スキップ: {ex_inner}")

            status.update(label="LP情報・商材情報取得完了", state="complete")
        except Exception as e:
            status.update(label="エラー", state="error")
            st.error(f"エラー: {e}")

if st.session_state.prc_lp_metadata:
    md = st.session_state.prc_lp_metadata
    with st.expander("取得したLP情報", expanded=False):
        st.markdown(f"**ページタイトル:** {md.get('page_title', '')}")
        st.markdown(f"**OG Title:** {md.get('og_title', '')}")
        st.markdown(f"**OG Description:** {md.get('og_description', '')}")
        imgs = st.session_state.prc_lp_tone_images
        if imgs:
            st.markdown(f"**LP参照画像 ({len(imgs)}枚)**")
            cols = st.columns(min(len(imgs), 5))
            for i, img in enumerate(imgs):
                with cols[i % 5]:
                    st.image(img, use_container_width=True)

# =============================================================
# Step 2: デザイン参照画像セット（ジャンル単位で管理）
# =============================================================
st.subheader("Step 2: デザイン参照画像セット（ジャンル別に保存・再利用）")

if not st.session_state.current_site:
    st.warning(
        "⚠️ サイドバーで **ジャンル/案件を選択** してください。\n"
        "選択中のジャンルに参照画像を保存します（次回以降は選ぶだけで再利用可能）。\n"
        "未登録なら「サイト設定」ページで新規作成してください。"
    )
else:
    site_name = st.session_state.current_site
    cm_pr = get_cm()

    # 既存のPR用参照画像を読み込み
    pr_ref_keys = cm_pr.list_reference_images(site_name, category="pr")
    if pr_ref_keys and not st.session_state.prc_design_ref_images:
        # session_stateにロード
        st.session_state.prc_design_ref_images = cm_pr.get_reference_pil_images(site_name, category="pr")

    pr_ref_images_now = st.session_state.prc_design_ref_images or []
    if pr_ref_images_now:
        st.success(f"「{site_name}」のPR参照画像: {len(pr_ref_images_now)} 枚登録済み")
        cols = st.columns(min(len(pr_ref_images_now), 6))
        for i, img in enumerate(pr_ref_images_now):
            with cols[i % 6]:
                st.image(img, caption=f"PR-{i+1}", use_container_width=True)
    else:
        st.info(f"「{site_name}」にPR用参照画像が未登録です。下からアップロードしてください。")

    with st.expander("📤 PR用参照画像をアップロード / 入れ替え", expanded=not pr_ref_images_now):
        st.caption("過去のヒットPRカルーセル6-7枚をまとめてアップロード（順番通りに）。このジャンルに永続保存され、次回以降は自動で読み込まれます。")
        uploaded_files = st.file_uploader(
            "PR参照画像（複数選択・順番通り）",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="prc_design_uploader",
        )
        c_up1, c_up2 = st.columns([1, 1])
        with c_up1:
            if st.button("💾 アップロードしたものを保存（上書き）", disabled=not uploaded_files, key="prc_save_uploads"):
                # 既存のPR参照画像を全削除してから新規保存
                for k in cm_pr.list_reference_images(site_name, category="pr"):
                    cm_pr.delete_reference_image(k)
                # 新規保存
                new_imgs = []
                for f in uploaded_files:
                    try:
                        cm_pr.add_reference_image(site_name, f.name, f.getvalue(), category="pr")
                        new_imgs.append(Image.open(f).convert("RGB"))
                    except Exception as e:
                        st.warning(f"{f.name} の保存失敗: {e}")
                st.session_state.prc_design_ref_images = new_imgs
                st.success(f"PR参照画像 {len(new_imgs)} 枚を保存しました。")
                st.rerun()
        with c_up2:
            if st.button("🗑️ 全削除（このジャンルのPR参照画像）", disabled=not pr_ref_images_now, key="prc_clear_refs"):
                for k in cm_pr.list_reference_images(site_name, category="pr"):
                    cm_pr.delete_reference_image(k)
                st.session_state.prc_design_ref_images = []
                st.session_state.prc_design_structure = None
                st.success("全削除しました。")
                st.rerun()

    # 構造抽出
    if pr_ref_images_now:
        if st.button("🔍 デザイン構造をGemini Visionで抽出", key="prc_extract_structure"):
            with st.status("構造抽出中...", expanded=True) as status:
                try:
                    gemini = GeminiClient(api_key=st.session_state.api_key)
                    struct_prompt = render_pr_carousel_structure_prompt()
                    resp = gemini.analyze_with_images(struct_prompt, pr_ref_images_now)
                    structure = _extract_json_obj(resp)
                    if structure:
                        st.session_state.prc_design_structure = structure
                        status.update(label="構造抽出完了", state="complete")
                    else:
                        status.update(label="JSON解析失敗", state="error")
                        st.error("Geminiの応答からJSONを抽出できませんでした。")
                except Exception as e:
                    status.update(label="エラー", state="error")
                    st.error(f"エラー: {e}")

        if st.session_state.prc_design_structure:
            with st.expander("抽出されたデザイン構造", expanded=False):
                st.json(st.session_state.prc_design_structure)

# =============================================================
# Step 3: 商材情報（LP取得時に自動入力済み。確認・調整できる）
# =============================================================
st.subheader("Step 3: 商材情報")

# 自動抽出された生JSON があれば表示
if st.session_state.prc_lp_product_info:
    with st.expander("🤖 LPから自動抽出した商材情報（参考・生データ）", expanded=False):
        st.json(st.session_state.prc_lp_product_info)
    if st.button("📋 自動抽出結果でフォームを再生成（手動編集をリセット）", key="prc_resync_product"):
        st.session_state.prc_product_info = format_product_info_for_proposal(st.session_state.prc_lp_product_info)
        st.rerun()
else:
    st.caption("Step 1 で「URLから情報取得」すると、LP本文から商材情報が自動抽出されます。")

product_info = st.text_area(
    "商材情報（自動入力済み。必要に応じて編集）",
    value=st.session_state.prc_product_info,
    placeholder="""URL未入力の場合は手入力。例:
商品名: DHC BBクリーム
主要訴求軸:
  - 化粧下地・ファンデ・日焼け止め一体型
  - 秒速美肌 / シミ小ジワをカバー
価格: 通常 ¥2,200 / 初回特別 ¥1,100
キャンペーン: 期間限定50%OFF + 送料無料
""",
    height=240,
    key="prc_input_product",
)
st.session_state.prc_product_info = product_info

# =============================================================
# Step 4: 枚数 + 役割編集
# =============================================================
st.subheader("Step 4: 枚数 + 各枚の役割")

# 枚数選択
page_count = st.slider(
    "総枚数",
    min_value=4, max_value=7,
    value=st.session_state.prc_page_count,
    key="prc_page_count_slider",
)
if page_count != st.session_state.prc_page_count:
    st.session_state.prc_page_count = page_count
    # 役割もデフォルトに更新
    st.session_state.prc_roles = list(PR_DEFAULT_ROLE_SETS.get(page_count, PR_DEFAULT_ROLE_SETS[6]))

# 役割編集UI
st.markdown("**各枚の役割（変更可能）**")
roles = st.session_state.prc_roles[:page_count]
# 不足分はデフォルトで補完
while len(roles) < page_count:
    roles.append("mechanism")

role_options = list(PR_ROLE_DEFINITIONS.keys())
role_labels = {k: PR_ROLE_DEFINITIONS[k]["label"] for k in role_options}

for i in range(page_count):
    current = roles[i] if i < len(roles) else "mechanism"
    if current not in role_options:
        current = "mechanism"
    selected = st.selectbox(
        f"PR-{i+1}",
        options=role_options,
        format_func=lambda k: f"{k} - {PR_ROLE_DEFINITIONS[k]['description'][:40]}...",
        index=role_options.index(current),
        key=f"prc_role_{i}",
    )
    roles[i] = selected

st.session_state.prc_roles = roles

# =============================================================
# Step 5: AI文言設計
# =============================================================
st.subheader("Step 5: 全枚分の文言を一括設計")

design_ok = bool(product_info.strip())

if st.button("🧠 AIで全枚分の文言を設計", type="primary", disabled=not design_ok, use_container_width=True, key="prc_design_content"):
    with st.status("文言設計中...", expanded=True) as status:
        try:
            gemini = GeminiClient(api_key=st.session_state.api_key)
            md = st.session_state.prc_lp_metadata or {}
            content_prompt = render_pr_carousel_content_proposal(
                product_info=product_info,
                role_list_for_pages=roles[:page_count],
                total_pages=page_count,
                page_title=md.get("page_title", ""),
                og_title=md.get("og_title", ""),
                og_description=md.get("og_description", ""),
            )
            resp = gemini.analyze_text(content_prompt)
            content = _extract_json_obj(resp)
            if content and "slides" in content:
                st.session_state.prc_content = content
                status.update(label="設計完了", state="complete")
            else:
                status.update(label="解析失敗", state="error")
                st.error("Geminiの応答からスライドJSONを抽出できませんでした。")
        except Exception as e:
            status.update(label="エラー", state="error")
            st.error(f"エラー: {e}")

# =============================================================
# Step 6: 文言の確認・編集
# =============================================================
if st.session_state.prc_content:
    content = st.session_state.prc_content
    st.subheader("Step 6: 文言確認・編集")

    # 全体コンセプト + 共通CTA
    with st.expander("カルーセル全体のコンセプト + 共通CTA", expanded=True):
        content["set_concept"] = st.text_area(
            "全体コンセプト",
            value=content.get("set_concept", ""),
            height=60,
            key="prc_set_concept",
        )
        cta = content.get("common_cta", {})
        c1, c2 = st.columns(2)
        with c1:
            cta["main_text"] = st.text_input(
                "CTAボタン文言（全枚共通）",
                value=cta.get("main_text", ""),
                key="prc_cta_main",
            )
        with c2:
            cta["sub_copy"] = st.text_input(
                "CTA上の補助コピー",
                value=cta.get("sub_copy", ""),
                key="prc_cta_sub",
            )
        content["common_cta"] = cta

    # 各スライド編集
    slides = content.get("slides", [])
    for i, slide in enumerate(slides):
        role = slide.get("role", "")
        role_label = PR_ROLE_DEFINITIONS.get(role, {}).get("label", role)
        with st.expander(f"【PR-{i+1}】 {role_label}", expanded=False):
            slide["headline"] = st.text_input(
                "ヘッドライン",
                value=slide.get("headline", ""),
                key=f"prc_slide_headline_{i}",
            )
            slide["sub_headline"] = st.text_input(
                "サブ見出し（任意）",
                value=slide.get("sub_headline", ""),
                key=f"prc_slide_sub_{i}",
            )
            elements_text = "\n".join(slide.get("key_elements", []))
            edited_elements = st.text_area(
                "主要要素（1行1項目）",
                value=elements_text,
                height=80,
                key=f"prc_slide_elements_{i}",
            )
            slide["key_elements"] = [l.strip() for l in edited_elements.split("\n") if l.strip()]
            slide["visual_description"] = st.text_area(
                "中央のメインビジュアル",
                value=slide.get("visual_description", ""),
                height=60,
                key=f"prc_slide_visual_{i}",
            )

    content["slides"] = slides
    st.session_state.prc_content = content

    # =============================================================
    # Step 7: 生成設定
    # =============================================================
    st.subheader("Step 7: 生成設定")

    size_preset = st.radio(
        "サイズ（全枚共通）",
        options=["縦長 (682×1024)", "スクエア (1080×1080)", "横長 (1200×630)", "カスタム"],
        horizontal=True,
        index=0,
        key="prc_size_preset",
    )
    if size_preset.startswith("縦長"):
        pr_w, pr_h = 682, 1024
    elif size_preset.startswith("スクエア"):
        pr_w, pr_h = 1080, 1080
    elif size_preset.startswith("横長"):
        pr_w, pr_h = 1200, 630
    else:
        cs1, cs2 = st.columns(2)
        with cs1:
            pr_w = st.number_input("幅(px)", min_value=256, max_value=4096, value=682, step=10, key="prc_w")
        with cs2:
            pr_h = st.number_input("高さ(px)", min_value=256, max_value=4096, value=1024, step=10, key="prc_h")

    target_ratio = pr_w / pr_h
    best_ar = "1:1"
    min_diff = float("inf")
    for ar in SUPPORTED_ASPECT_RATIOS:
        w, h = map(int, ar.split(":"))
        diff = abs(w / h - target_ratio)
        if diff < min_diff:
            min_diff = diff
            best_ar = ar
    st.caption(f"出力サイズ: **{pr_w}×{pr_h}px** / アスペクト比(自動): **{best_ar}**")

    st.divider()

    # =============================================================
    # Step 8: 一括生成
    # =============================================================
    st.subheader(f"Step 8: 全{len(slides)}枚を一括生成")

    structure = st.session_state.prc_design_structure or {}
    tone_imgs = st.session_state.prc_lp_tone_images or []

    info_lines = []
    info_lines.append(f"- 文言設計: 全{len(slides)}枚分準備済み")
    info_lines.append(f"- LP参照画像（色味）: {len(tone_imgs)}枚")
    info_lines.append(f"- デザイン構造: {'抽出済み' if structure else '未抽出（参照画像のスタイルだけ使用）'}")
    st.info("\n".join(info_lines))

    if st.session_state.prc_in_progress:
        st.session_state.prc_in_progress = False

    can_generate = bool(tone_imgs) and bool(slides) and bool(content.get("common_cta", {}).get("main_text"))
    if not can_generate:
        st.warning("URLからのLP参照画像取得と、文言設計を完了させてください。")

    if st.button(f"🚀 全{len(slides)}枚を一括生成", type="primary", disabled=not can_generate, use_container_width=True, key="prc_batch_generate"):
        st.session_state.prc_in_progress = True
        st.session_state.prc_generated_images = []

        # 共通骨格記述（構造から抽出）
        common_skeleton_text = ""
        if structure and "common_skeleton" in structure:
            cs = structure["common_skeleton"]
            common_skeleton_text = (
                f"- 左上: {cs.get('top_left_position', '')}\n"
                f"- 右上: {cs.get('top_right_position', '')}\n"
                f"- 最下部CTA: {cs.get('bottom_cta', '')}\n"
                f"- 配色運用: {cs.get('color_palette_role', '')}"
            )

        # 各スライドのレイアウト指示（構造から取得 or デフォルト）
        structure_pages = structure.get("pages", []) if structure else []

        site_colors = None
        if config:
            site_colors = {
                "primary_color": config.get("primary_color", "#06C755"),
                "accent_color": config.get("accent_color", "#F59E0B"),
                "background_color": config.get("background_color", "#FFFFFF"),
                "text_color": config.get("text_color", "#1F2937"),
            }

        image_client = get_image_client(
            provider=st.session_state.image_provider,
            gemini_api_key=st.session_state.api_key,
            openai_api_key=st.session_state.openai_api_key,
        )

        progress_bar = st.progress(0, text="PRカルーセルを生成中...")
        common_cta = content.get("common_cta", {})

        design_ref_images = st.session_state.prc_design_ref_images or []

        for i, slide in enumerate(slides):
            page_no = i + 1
            progress = page_no / len(slides)
            progress_bar.progress(progress, text=f"PR-{page_no}/{len(slides)} を生成中...")

            # この枚に対応するデザイン参照画像（あれば該当枚、なければ最初の1枚）
            design_ref_for_slide = None
            if design_ref_images:
                if i < len(design_ref_images):
                    design_ref_for_slide = design_ref_images[i]
                else:
                    design_ref_for_slide = design_ref_images[0]

            # 参照画像セット = デザイン参照1枚（先頭）+ LP参照群
            ref_images_for_gpt = []
            if design_ref_for_slide is not None:
                ref_images_for_gpt.append(design_ref_for_slide)
            ref_images_for_gpt.extend(tone_imgs)

            gen_prompt = render_pr_carousel_slide_generation(
                page_no=page_no,
                total_pages=len(slides),
                slide_role=slide.get("role", "introduction"),
                slide_data=slide,
                common_skeleton_desc=common_skeleton_text,
                layout_structure_desc="",  # 旧パラメータ（未使用）
                common_cta=common_cta,
                site_colors=site_colors,
                language=config.get("language", "Japanese") if config else "Japanese",
                image_width=pr_w,
                image_height=pr_h,
                tone_count=len(tone_imgs),
            )

            try:
                gen_image, gen_text = image_client.generate_image(
                    prompt=gen_prompt,
                    reference_images=ref_images_for_gpt,  # デザイン参照1枚 + LP参照群
                    aspect_ratio=best_ar,
                    image_size="2K",
                )
                if gen_image:
                    site_for_storage = st.session_state.current_site or "no-site"
                    label = f"{page_no:02d}_{slide.get('role', '')}"
                    saved_key = _save_to_storage(gen_image, site_for_storage, label)
                    st.session_state.prc_generated_images.append({
                        "page_no": page_no,
                        "role": slide.get("role", ""),
                        "slide_data": slide,
                        "image": gen_image,
                        "processed_image": None,
                        "response_text": gen_text,
                        "generation_prompt": gen_prompt,
                        "reference_image_count": len(tone_imgs),
                        "saved_key": saved_key,
                        "timestamp": datetime.datetime.now().isoformat(),
                    })
                else:
                    st.warning(f"PR-{page_no} の生成失敗: {gen_text or ''}")
            except Exception as e:
                st.error(f"PR-{page_no} のエラー: {e}")

        progress_bar.progress(1.0, text="全枚生成完了!")
        st.session_state.prc_in_progress = False
        st.rerun()

# =============================================================
# 生成結果
# =============================================================
if st.session_state.prc_generated_images:
    st.subheader("カルーセル生成結果")
    images = st.session_state.prc_generated_images

    for i, entry in enumerate(images):
        role = entry["role"]
        role_label = PR_ROLE_DEFINITIONS.get(role, {}).get("label", role)
        st.markdown(f"### PR-{entry['page_no']}/{len(images)} - {role_label}")

        d_col, c_col = st.columns([2, 1])
        with d_col:
            display_img = entry.get("processed_image") or entry["image"]
            st.image(display_img, use_container_width=True)
            with st.expander("📝 このプロンプトを見る", expanded=False):
                prompt_used = entry.get("generation_prompt", "")
                ref_count = entry.get("reference_image_count", 0)
                if prompt_used:
                    if ref_count > 0:
                        st.caption(f"⚠️ LP参照画像 {ref_count}枚併用")
                    st.code(prompt_used, language="text")
        with c_col:
            if st.button("余白トリミング", key=f"prc_trim_{i}"):
                entry["processed_image"] = trim_whitespace(entry["image"])
                st.rerun()
            download_img = entry.get("processed_image") or entry["image"]
            img_bytes = image_to_bytes(download_img)
            st.download_button(
                "このPNG DL",
                data=img_bytes,
                file_name=f"pr_{entry['page_no']:02d}_{entry['role']}.png",
                mime="image/png",
                key=f"prc_dl_{i}",
                use_container_width=True,
            )
        st.divider()

    # 一括ZIPダウンロード
    if st.button(f"📦 全{len(images)}枚をZIPでダウンロード", use_container_width=True, key="prc_dl_zip"):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for entry in images:
                dl_img = entry.get("processed_image") or entry["image"]
                img_bytes = image_to_bytes(dl_img)
                filename = f"{entry['page_no']:02d}_{entry['role']}.png"
                zf.writestr(filename, img_bytes)
        st.download_button(
            "ZIPをダウンロード",
            data=buf.getvalue(),
            file_name=f"pr_carousel_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            key="prc_zip_file",
            use_container_width=True,
        )
