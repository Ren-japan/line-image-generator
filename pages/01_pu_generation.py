"""
PU（プッシュアップ）画像生成ページ
訴求テーマ → 文言案生成 → 画像生成（問いかけ＋はい/いいえ型バナー）
"""

import io
import json
import re
import datetime
import streamlit as st

from lib.gemini_client import GeminiClient, SUPPORTED_ASPECT_RATIOS, SUPPORTED_IMAGE_SIZES
from lib.image_generator import get_image_client, provider_label
from lib.prompt_templates import render_pu_proposal_prompt, render_pu_generation_prompt
from lib.image_postprocessor import (
    trim_whitespace,
    resize_to_target,
    image_to_bytes,
)


def get_cm():
    from lib.dependencies import get_config_manager
    return get_config_manager()


def _save_to_storage(image, site_name: str, label: str):
    """生成PU画像をストレージに自動保存"""
    from lib.dependencies import get_output_storage
    storage = get_output_storage()
    safe_label = re.sub(r'[\\/:*?"<>|]', '_', label)[:50]
    date_str = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    key = f"generated/{site_name}/pu/{date_str}_{safe_label}.png"
    img_bytes = image_to_bytes(image)
    storage.save(key, img_bytes)
    return key


def _parse_pu_proposals(response_text: str) -> list[dict]:
    """Geminiの応答から PU 案 JSON配列を抽出してパース"""
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


def generate_pu_image(pu_proposal: dict, idx: int, config: dict, site_name: str,
                      image_width: int, image_height: int, aspect_ratio: str):
    """1案分のPU画像を生成して session_state.pu_generated_images に追加"""
    image_client = get_image_client(
        provider=st.session_state.image_provider,
        gemini_api_key=st.session_state.api_key,
        openai_api_key=st.session_state.openai_api_key,
    )

    # サイト参照画像（PU用カテゴリ）を取得。なければ通常 reference_images を流用
    cm = get_cm()
    site_ref_images = []
    if site_name:
        # 「pu」カテゴリがあればそれ、なければデフォルトの reference_images
        site_ref_images = cm.get_reference_pil_images(site_name, category="pu")
        if not site_ref_images:
            site_ref_images = cm.get_reference_pil_images(site_name)

    # サイトカラー
    site_colors = {
        "primary_color": config.get("primary_color", "#06C755"),
        "secondary_color": config.get("secondary_color", "#10B981"),
        "accent_color": config.get("accent_color", "#F59E0B"),
        "background_color": config.get("background_color", "#FFFFFF"),
        "text_color": config.get("text_color", "#1F2937"),
        "danger_color": config.get("danger_color", "#E74A3B"),
    }

    gen_prompt = render_pu_generation_prompt(
        pu_proposal=pu_proposal,
        site_colors=site_colors,
        language=config.get("language", "Japanese"),
        has_reference_images=bool(site_ref_images),
        image_width=image_width,
        image_height=image_height,
    )

    gen_image, gen_text = image_client.generate_image(
        prompt=gen_prompt,
        reference_images=site_ref_images if site_ref_images else None,
        aspect_ratio=aspect_ratio,
        image_size="2K",
    )

    if gen_image:
        existing = [j for j, e in enumerate(st.session_state.pu_generated_images)
                    if e["proposal_idx"] == idx]
        label = pu_proposal.get("headline", f"pu_{idx}")
        saved_key = _save_to_storage(gen_image, site_name or "unknown", label)
        entry = {
            "proposal_idx": idx,
            "proposal": pu_proposal,
            "image": gen_image,
            "processed_image": None,
            "response_text": gen_text,
            "generation_prompt": gen_prompt,
            "reference_image_count": len(site_ref_images) if site_ref_images else 0,
            "saved_key": saved_key,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        if existing:
            st.session_state.pu_generated_images[existing[0]] = entry
        else:
            st.session_state.pu_generated_images.append(entry)
        return True, gen_text
    return False, gen_text


# =============================================================
# ヘッダー
# =============================================================
st.title("📣 PU画像生成")

if not st.session_state.current_site:
    st.warning("サイドバーからサイト/案件を選択してください。")
    st.stop()

if not st.session_state.api_key:
    st.error("Gemini API Keyが設定されていません。サイドバーから入力してください。")
    st.stop()

if st.session_state.image_provider == "openai" and not st.session_state.openai_api_key:
    st.error("画像生成プロバイダが OpenAI ですが OPENAI_API_KEY が未設定です。")
    st.stop()

config = st.session_state.site_config
st.info(
    f"対象サイト: **{config.get('brand_name', st.session_state.current_site)}** ／ "
    f"画像生成: **{provider_label(st.session_state.image_provider)}**"
)

# 参照画像状況
cm = get_cm()
pu_ref_count = len(cm.list_reference_images(st.session_state.current_site, category="pu"))
default_ref_count = len(cm.list_reference_images(st.session_state.current_site))
if pu_ref_count > 0:
    st.success(f"PU参照画像: {pu_ref_count}枚登録済み（PUカテゴリ）")
elif default_ref_count > 0:
    st.info(f"PU専用参照画像なし → 通常参照画像 {default_ref_count}枚を流用します（PU専用を「サイト設定」→ 参照画像 → category=pu で登録するとテイスト精度UP）")
else:
    st.warning("参照画像が未登録です。「サイト設定」から登録するとテイストが揃います（未登録でも生成可）。")

# =============================================================
# Step 1: 訴求テーマ入力
# =============================================================
st.subheader("Step 1: 訴求テーマ")

pu_theme = st.text_input(
    "訴求テーマ・記事KW",
    value=st.session_state.pu_input_theme,
    placeholder="例: 隠れ肥満度チェック、看護師の夜勤手当、包茎手術の必要度",
    key="input_pu_theme",
)
st.session_state.pu_input_theme = pu_theme

pu_target = st.text_area(
    "ターゲット読者の状況（任意）",
    placeholder="例: 30代女性、最近お腹周りが気になり始めた。BMIは正常範囲だが体型に不安。",
    height=80,
    key="input_pu_target",
)

# =============================================================
# Step 2: PU文言案を生成
# =============================================================
st.subheader("Step 2: PU文言案を生成")

btn_propose = st.button(
    "AIで文言案を生成",
    type="primary",
    disabled=not pu_theme.strip(),
    use_container_width=True,
)

if btn_propose and pu_theme.strip():
    with st.status("PU文言案を生成中...", expanded=True) as status:
        try:
            gemini = GeminiClient(api_key=st.session_state.api_key)
            prompt = render_pu_proposal_prompt(pu_theme, pu_target)
            response_text = gemini.analyze_text(prompt)
            proposals = _parse_pu_proposals(response_text)
            if proposals:
                st.session_state.pu_proposals = proposals
                st.session_state.pu_selected_proposals = [True] * len(proposals)
                status.update(label=f"{len(proposals)}案を生成", state="complete")
            else:
                status.update(label="案の生成に失敗", state="error")
                st.error("Geminiの応答を解析できませんでした。テーマを変えて再試行してください。")
        except Exception as e:
            status.update(label="エラー", state="error")
            st.error(f"エラー: {e}")

# =============================================================
# Step 3: 案の確認・編集
# =============================================================
if st.session_state.pu_proposals:
    pu_proposals = st.session_state.pu_proposals
    pu_selected = st.session_state.pu_selected_proposals

    st.subheader("Step 3: 文言案を確認・編集")

    for i, prop in enumerate(pu_proposals):
        pu_selected[i] = st.checkbox(
            f"PU案{i+1}: {prop.get('headline', '未設定')}",
            value=pu_selected[i],
            key=f"pu_sel_{i}",
        )
        with st.expander(f"PU案{i+1}を編集", expanded=(len(pu_proposals) == 1)):
            prop["headline"] = st.text_input(
                "ヘッドライン（疑問文・最大18文字）",
                value=prop.get("headline", ""),
                key=f"pu_headline_{i}",
            )
            prop["subcopy"] = st.text_input(
                "補助コピー（任意・最大15文字）",
                value=prop.get("subcopy", ""),
                key=f"pu_subcopy_{i}",
            )
            c1, c2 = st.columns(2)
            with c1:
                prop["yes_label"] = st.text_input(
                    "はいボタン", value=prop.get("yes_label", "はい"), key=f"pu_yes_{i}"
                )
            with c2:
                prop["no_label"] = st.text_input(
                    "いいえボタン", value=prop.get("no_label", "いいえ"), key=f"pu_no_{i}"
                )
            prop["person_or_visual"] = st.text_area(
                "主題ビジュアル説明",
                value=prop.get("person_or_visual", ""),
                height=80,
                key=f"pu_visual_{i}",
            )

    st.session_state.pu_selected_proposals = pu_selected

    # =============================================================
    # Step 4: 生成設定 + 生成ボタン
    # =============================================================
    st.subheader("Step 4: 生成設定")

    # サイズプリセット選択
    size_preset = st.radio(
        "サイズ",
        options=["縦長 (682×1024)", "スクエア (1080×1080)", "横長 (1200×630)", "カスタム"],
        horizontal=True,
        index=0,  # デフォルト: 縦長
        key="pu_size_preset",
    )
    if size_preset.startswith("縦長"):
        pu_width, pu_height = 682, 1024
    elif size_preset.startswith("スクエア"):
        pu_width, pu_height = 1080, 1080
    elif size_preset.startswith("横長"):
        pu_width, pu_height = 1200, 630
    else:  # カスタム
        c_size1, c_size2 = st.columns(2)
        with c_size1:
            pu_width = st.number_input("幅(px)", min_value=256, max_value=4096, value=682, step=10, key="pu_width")
        with c_size2:
            pu_height = st.number_input("高さ(px)", min_value=256, max_value=4096, value=1024, step=10, key="pu_height")

    # アスペクト比自動算出
    target_ratio = pu_width / pu_height
    best_ar = "1:1"
    min_diff = float("inf")
    for ar in SUPPORTED_ASPECT_RATIOS:
        w, h = map(int, ar.split(":"))
        diff = abs(w / h - target_ratio)
        if diff < min_diff:
            min_diff = diff
            best_ar = ar
    st.caption(f"出力サイズ: **{pu_width}×{pu_height}px** / アスペクト比(自動): **{best_ar}**")

    selected_count = sum(1 for s in pu_selected if s)
    st.divider()

    if st.session_state.pu_generation_in_progress:
        st.session_state.pu_generation_in_progress = False

    batch_btn = st.button(
        f"選択した{selected_count}案を一括生成",
        type="primary",
        disabled=(selected_count == 0),
        use_container_width=True,
    )

    if batch_btn:
        st.session_state.pu_generation_in_progress = True
        st.session_state.pu_generated_images = []
        selected_idx_list = [i for i, s in enumerate(pu_selected) if s]
        progress_bar = st.progress(0, text="PU画像を生成中...")
        for step, idx in enumerate(selected_idx_list):
            prop = pu_proposals[idx]
            progress = (step + 1) / len(selected_idx_list)
            progress_bar.progress(progress, text=f"案{idx+1}を生成中... ({step+1}/{len(selected_idx_list)})")
            try:
                ok, text = generate_pu_image(
                    prop, idx, config, st.session_state.current_site,
                    pu_width, pu_height, best_ar,
                )
                if not ok:
                    st.warning(f"案{idx+1}の生成失敗: {text or ''}")
            except Exception as e:
                st.error(f"案{idx+1}の生成エラー: {e}")
        progress_bar.progress(1.0, text="生成完了!")
        st.session_state.pu_generation_in_progress = False
        st.rerun()

# =============================================================
# 生成結果
# =============================================================
if st.session_state.pu_generated_images:
    st.subheader("生成結果")
    images = st.session_state.pu_generated_images
    for i, entry in enumerate(images):
        prop = entry["proposal"]
        img = entry["image"]
        processed = entry.get("processed_image")
        st.markdown(f"### PU案{entry['proposal_idx']+1}: {prop.get('headline', '')}")

        d_col, c_col = st.columns([2, 1])
        with d_col:
            display_img = processed if processed else img
            st.image(display_img, use_container_width=True)

            # プロンプト表示
            prompt_used = entry.get("generation_prompt", "")
            ref_count = entry.get("reference_image_count", 0)
            with st.expander("📝 このプロンプトを見る", expanded=False):
                if prompt_used:
                    if ref_count > 0:
                        st.caption(
                            f"⚠️ 参照画像を{ref_count}枚併用。テキストプロンプトだけでは100%再現できません。"
                        )
                    st.code(prompt_used, language="text")
                else:
                    st.caption("（プロンプト未記録）")

        with c_col:
            st.markdown("**後処理**")
            if st.button("余白トリミング", key=f"pu_trim_{i}"):
                entry["processed_image"] = trim_whitespace(img)
                st.rerun()

            download_img = processed if processed else img
            img_bytes = image_to_bytes(download_img)
            st.download_button(
                "PNGダウンロード",
                data=img_bytes,
                file_name=f"pu_{entry['proposal_idx']+1}_{i}.png",
                mime="image/png",
                key=f"pu_dl_{i}",
                use_container_width=True,
            )
        st.divider()
