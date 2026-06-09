"""
PR画像生成ページ
遷移先LPのURL入力 → og:image+主要画像で参照画像セット → 商品情報入力 → 文言案 → PR画像生成

サイト/案件は任意。URLからLPのトンマナを取れるので、サイト未登録でも動く。
"""

import io
import json
import re
import datetime
import streamlit as st
from PIL import Image

from lib.gemini_client import GeminiClient, SUPPORTED_ASPECT_RATIOS
from lib.image_generator import get_image_client, provider_label
from lib.prompt_templates import render_pr_proposal_prompt, render_pr_generation_prompt
from lib.image_postprocessor import trim_whitespace, image_to_bytes
from lib.url_scraper import fetch_lp_reference_images


def get_cm():
    from lib.dependencies import get_config_manager
    return get_config_manager()


def _save_to_storage(image, site_name: str, label: str):
    """生成PR画像をストレージに自動保存"""
    from lib.dependencies import get_output_storage
    storage = get_output_storage()
    safe_label = re.sub(r'[\\/:*?"<>|]', '_', label)[:50]
    date_str = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    key = f"generated/{site_name}/pr/{date_str}_{safe_label}.png"
    img_bytes = image_to_bytes(image)
    storage.save(key, img_bytes)
    return key


def _parse_pr_proposals(response_text: str) -> list[dict]:
    """Geminiの応答からPR案JSON配列を抽出"""
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", response_text, re.DOTALL)
    text = m.group(1).strip() if m else response_text.strip()
    s = text.find("[")
    e = text.rfind("]")
    if s == -1 or e == -1:
        return []
    try:
        data = json.loads(text[s:e+1])
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


# ----- セッションステート初期化（PRページ専用追加） -----
for key, default in {
    "pr_target_url": "",
    "pr_lp_metadata": {},
    "pr_lp_reference_images": [],   # PIL Image のリスト
    "pr_product_info": "",
    "pr_proposals": [],
    "pr_selected_proposals": [],
    "pr_generated_images": [],
    "pr_generation_in_progress": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# =============================================================
# ヘッダー
# =============================================================
st.title("🎯 PR画像生成")
st.caption("遷移先LPのURLを入れると、そのLPのトンマナを学習してPRバナーを生成します")

if not st.session_state.api_key:
    st.error("Gemini API Keyが設定されていません。サイドバーから入力してください。")
    st.stop()

if st.session_state.image_provider == "openai" and not st.session_state.openai_api_key:
    st.error("画像生成プロバイダが OpenAI ですが OPENAI_API_KEY が未設定です。")
    st.stop()

config = st.session_state.site_config or {}

# サイト選択は任意
if st.session_state.current_site:
    st.info(
        f"対象サイト: **{config.get('brand_name', st.session_state.current_site)}** ／ "
        f"画像生成: **{provider_label(st.session_state.image_provider)}**"
    )
else:
    st.info(
        f"サイト未選択（PRはサイト未登録でもLPのURLから生成できます）／ "
        f"画像生成: **{provider_label(st.session_state.image_provider)}**"
    )

# =============================================================
# Step 1: 遷移先LP URL入力
# =============================================================
st.subheader("Step 1: 遷移先LPのURL")

target_url = st.text_input(
    "遷移先LPのURL",
    value=st.session_state.pr_target_url,
    placeholder="https://例: https://www.dhc.co.jp/goods/foundation",
    key="input_pr_url",
)
st.session_state.pr_target_url = target_url

fetch_col1, fetch_col2 = st.columns([1, 3])
with fetch_col1:
    btn_fetch = st.button(
        "URLから情報取得",
        type="primary",
        disabled=not target_url.strip(),
        use_container_width=True,
    )

if btn_fetch and target_url.strip():
    with st.status("LPから情報を取得中...", expanded=True) as status:
        try:
            st.write("HTMLとメタ情報を取得...")
            images, metadata = fetch_lp_reference_images(target_url, max_count=5)
            st.session_state.pr_lp_metadata = metadata
            st.session_state.pr_lp_reference_images = images
            st.write(f"画像 {len(images)} 枚取得（og:image優先）")
            status.update(label=f"取得完了: 画像{len(images)}枚 / タイトル取得OK", state="complete")
        except Exception as e:
            status.update(label="取得エラー", state="error")
            st.error(f"エラー: {e}")

# 取得済みLP情報の表示
if st.session_state.pr_lp_metadata:
    metadata = st.session_state.pr_lp_metadata
    with st.expander("取得したLP情報", expanded=True):
        st.markdown(f"**ページタイトル:** {metadata.get('page_title', '')}")
        if metadata.get('og_title'):
            st.markdown(f"**OG Title:** {metadata['og_title']}")
        if metadata.get('og_description'):
            st.markdown(f"**OG Description:** {metadata['og_description']}")
        # 取得画像のプレビュー
        images = st.session_state.pr_lp_reference_images
        if images:
            st.markdown(f"**取得した参照画像（{len(images)}枚）**")
            cols = st.columns(min(len(images), 5))
            for i, img in enumerate(images):
                with cols[i % 5]:
                    st.image(img, use_container_width=True)

# =============================================================
# Step 2: 商品/サービス情報（任意）
# =============================================================
st.subheader("Step 2: 商品/サービス情報")
st.caption("LP情報から自動推測されますが、強調したいキーワードや訴求軸があればここに")

product_info = st.text_area(
    "商品名・特徴・訴求軸（任意）",
    value=st.session_state.pr_product_info,
    placeholder="例: DHC ファンデーション、無添加、敏感肌向け、初回半額、リピート率90%以上",
    height=80,
    key="input_pr_product_info",
)
st.session_state.pr_product_info = product_info

# =============================================================
# Step 3: PR文言案を生成
# =============================================================
st.subheader("Step 3: PR文言案を生成")

btn_propose = st.button(
    "AIで文言案を生成",
    type="primary",
    disabled=not (product_info.strip() or st.session_state.pr_lp_metadata),
    use_container_width=True,
)

if btn_propose:
    with st.status("PR文言案を生成中...", expanded=True) as status:
        try:
            metadata = st.session_state.pr_lp_metadata or {}
            gemini = GeminiClient(api_key=st.session_state.api_key)
            prompt = render_pr_proposal_prompt(
                product_info=product_info,
                page_title=metadata.get("page_title", ""),
                og_title=metadata.get("og_title", ""),
                og_description=metadata.get("og_description", ""),
            )
            response_text = gemini.analyze_text(prompt)
            proposals = _parse_pr_proposals(response_text)
            if proposals:
                st.session_state.pr_proposals = proposals
                st.session_state.pr_selected_proposals = [True] * len(proposals)
                status.update(label=f"{len(proposals)}案を生成", state="complete")
            else:
                status.update(label="案の生成に失敗", state="error")
                st.error("Geminiの応答を解析できませんでした。商品情報を変えて再試行を。")
        except Exception as e:
            status.update(label="エラー", state="error")
            st.error(f"エラー: {e}")

# =============================================================
# Step 4: 案の確認・編集
# =============================================================
if st.session_state.pr_proposals:
    pr_proposals = st.session_state.pr_proposals
    pr_selected = st.session_state.pr_selected_proposals

    st.subheader("Step 4: 文言案を確認・編集")

    for i, prop in enumerate(pr_proposals):
        pr_selected[i] = st.checkbox(
            f"PR案{i+1}: {prop.get('headline', '未設定')}",
            value=pr_selected[i],
            key=f"pr_sel_{i}",
        )
        with st.expander(f"PR案{i+1}を編集", expanded=(len(pr_proposals) == 1)):
            prop["headline"] = st.text_input(
                "ヘッドライン（最大18文字）",
                value=prop.get("headline", ""),
                key=f"pr_headline_{i}",
            )
            prop["subcopy"] = st.text_input(
                "サブコピー（最大20文字）",
                value=prop.get("subcopy", ""),
                key=f"pr_subcopy_{i}",
            )
            prop["cta_text"] = st.text_input(
                "CTAボタン（最大10文字）",
                value=prop.get("cta_text", ""),
                key=f"pr_cta_{i}",
            )
            prop["visual_description"] = st.text_area(
                "主題ビジュアル説明",
                value=prop.get("visual_description", ""),
                height=80,
                key=f"pr_visual_{i}",
            )

    st.session_state.pr_selected_proposals = pr_selected

    # =============================================================
    # Step 5: 生成設定 + 生成ボタン
    # =============================================================
    st.subheader("Step 5: 生成設定")

    size_preset = st.radio(
        "サイズ",
        options=["縦長 (682×1024)", "スクエア (1080×1080)", "横長 (1200×630)", "カスタム"],
        horizontal=True,
        index=0,
        key="pr_size_preset",
    )
    if size_preset.startswith("縦長"):
        pr_width, pr_height = 682, 1024
    elif size_preset.startswith("スクエア"):
        pr_width, pr_height = 1080, 1080
    elif size_preset.startswith("横長"):
        pr_width, pr_height = 1200, 630
    else:
        cs1, cs2 = st.columns(2)
        with cs1:
            pr_width = st.number_input("幅(px)", min_value=256, max_value=4096, value=682, step=10, key="pr_width")
        with cs2:
            pr_height = st.number_input("高さ(px)", min_value=256, max_value=4096, value=1024, step=10, key="pr_height")

    target_ratio = pr_width / pr_height
    best_ar = "1:1"
    min_diff = float("inf")
    for ar in SUPPORTED_ASPECT_RATIOS:
        w, h = map(int, ar.split(":"))
        diff = abs(w / h - target_ratio)
        if diff < min_diff:
            min_diff = diff
            best_ar = ar
    st.caption(f"出力サイズ: **{pr_width}×{pr_height}px** / アスペクト比(自動): **{best_ar}**")

    selected_count = sum(1 for s in pr_selected if s)
    st.divider()

    if st.session_state.pr_generation_in_progress:
        st.session_state.pr_generation_in_progress = False

    batch_btn = st.button(
        f"選択した{selected_count}案を一括生成",
        type="primary",
        disabled=(selected_count == 0),
        use_container_width=True,
    )

    if batch_btn:
        st.session_state.pr_generation_in_progress = True
        st.session_state.pr_generated_images = []
        selected_idx_list = [i for i, s in enumerate(pr_selected) if s]
        progress_bar = st.progress(0, text="PR画像を生成中...")

        # 参照画像セット: LP取得画像 + サイト参照画像(あれば)を結合
        ref_images = list(st.session_state.pr_lp_reference_images or [])
        if st.session_state.current_site:
            cm = get_cm()
            # PR専用カテゴリがあれば追加
            site_pr = cm.get_reference_pil_images(st.session_state.current_site, category="pr")
            if site_pr:
                ref_images.extend(site_pr)

        # サイトカラー(設定があれば)
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

        for step, idx in enumerate(selected_idx_list):
            prop = pr_proposals[idx]
            progress = (step + 1) / len(selected_idx_list)
            progress_bar.progress(progress, text=f"案{idx+1}を生成中... ({step+1}/{len(selected_idx_list)})")
            try:
                gen_prompt = render_pr_generation_prompt(
                    pr_proposal=prop,
                    site_colors=site_colors,
                    language=config.get("language", "Japanese") if config else "Japanese",
                    has_reference_images=bool(ref_images),
                    image_width=pr_width,
                    image_height=pr_height,
                )
                gen_image, gen_text = image_client.generate_image(
                    prompt=gen_prompt,
                    reference_images=ref_images if ref_images else None,
                    aspect_ratio=best_ar,
                    image_size="2K",
                )
                if gen_image:
                    label = prop.get("headline", f"pr_{idx}")
                    site_for_storage = st.session_state.current_site or "no-site"
                    saved_key = _save_to_storage(gen_image, site_for_storage, label)
                    st.session_state.pr_generated_images.append({
                        "proposal_idx": idx,
                        "proposal": prop,
                        "image": gen_image,
                        "processed_image": None,
                        "response_text": gen_text,
                        "generation_prompt": gen_prompt,
                        "reference_image_count": len(ref_images) if ref_images else 0,
                        "saved_key": saved_key,
                        "timestamp": datetime.datetime.now().isoformat(),
                    })
                else:
                    st.warning(f"案{idx+1} の生成失敗: {gen_text or ''}")
            except Exception as e:
                st.error(f"案{idx+1} のエラー: {e}")

        progress_bar.progress(1.0, text="生成完了!")
        st.session_state.pr_generation_in_progress = False
        st.rerun()

# =============================================================
# 生成結果
# =============================================================
if st.session_state.pr_generated_images:
    st.subheader("生成結果")
    images = st.session_state.pr_generated_images
    for i, entry in enumerate(images):
        prop = entry["proposal"]
        img = entry["image"]
        processed = entry.get("processed_image")
        st.markdown(f"### PR案{entry['proposal_idx']+1}: {prop.get('headline', '')}")
        d_col, c_col = st.columns([2, 1])
        with d_col:
            display_img = processed if processed else img
            st.image(display_img, use_container_width=True)
            prompt_used = entry.get("generation_prompt", "")
            ref_count = entry.get("reference_image_count", 0)
            with st.expander("📝 このプロンプトを見る", expanded=False):
                if prompt_used:
                    if ref_count > 0:
                        st.caption(
                            f"⚠️ 参照画像を{ref_count}枚併用（LP取得画像含む）。"
                            "テキストプロンプトだけでは100%再現できません。"
                        )
                    st.code(prompt_used, language="text")
                else:
                    st.caption("（プロンプト未記録）")
        with c_col:
            if st.button("余白トリミング", key=f"pr_trim_{i}"):
                entry["processed_image"] = trim_whitespace(img)
                st.rerun()
            download_img = processed if processed else img
            img_bytes = image_to_bytes(download_img)
            st.download_button(
                "PNGダウンロード",
                data=img_bytes,
                file_name=f"pr_{entry['proposal_idx']+1}_{i}.png",
                mime="image/png",
                key=f"pr_dl_{i}",
                use_container_width=True,
            )
        st.divider()
