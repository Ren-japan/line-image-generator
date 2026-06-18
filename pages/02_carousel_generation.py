"""
診断カルーセル生成ページ
診断テーマ → 文言設計（表紙+設問N+結果） → 全枚一括生成（同じ参照画像でトーン統一）
"""

import io
import json
import re
import zipfile
import datetime
import streamlit as st

from lib.gemini_client import GeminiClient, SUPPORTED_ASPECT_RATIOS
from lib.image_generator import get_image_client, provider_label
from lib.prompt_templates import render_carousel_proposal_prompt, render_carousel_slide_prompt
from lib.image_postprocessor import trim_whitespace, image_to_bytes


def get_cm():
    from lib.dependencies import get_config_manager
    return get_config_manager()


def _save_to_storage(image, site_name: str, label: str):
    """生成カルーセル画像をストレージに自動保存"""
    from lib.dependencies import get_output_storage
    storage = get_output_storage()
    safe_label = re.sub(r'[\\/:*?"<>|]', '_', label)[:50]
    date_str = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    key = f"generated/{site_name}/carousel/{date_str}_{safe_label}.png"
    img_bytes = image_to_bytes(image)
    storage.save(key, img_bytes)
    return key


def _parse_carousel_proposal(response_text: str) -> dict | None:
    """Geminiの応答から カルーセル設計 JSON を抽出してパース"""
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", response_text, re.DOTALL)
    text = m.group(1).strip() if m else response_text.strip()
    s = text.find("{")
    e = text.rfind("}")
    if s == -1 or e == -1:
        return None
    try:
        data = json.loads(text[s:e+1])
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _build_slide_content(slide_type: str, slide_data: dict, slide_position: int = 1, total: int = 1) -> str:
    """各スライドのテキスト内容HEREDOCを組み立てる"""
    if slide_type == "表紙":
        return (
            f'- メインタイトル（最も大きい）: 「{slide_data.get("title", "")}」\n'
            f'- サブコピー: 「{slide_data.get("subtitle", "")}」\n'
            f'- CTA（タップ促進）: 「{slide_data.get("cta_text", "")}」'
        )
    if slide_type == "設問":
        return (
            f'- 設問本文（最も大きい）: 「{slide_data.get("question_text", "")}」\n'
            f'- 選択肢A（左 or 上）: 「{slide_data.get("option_a", "")}」\n'
            f'- 選択肢B（右 or 下）: 「{slide_data.get("option_b", "")}」\n'
            f'- 上部ナンバリング: 「Q{slide_data.get("question_no", slide_position)}」'
        )
    if slide_type == "結果":
        return (
            f'- 結果タイトル（最も大きい）: 「{slide_data.get("title", "")}」\n'
            f'- 結果説明文: 「{slide_data.get("body", "")}」\n'
            f'- CTA: 「{slide_data.get("cta_text", "")}」'
        )
    return ""


def generate_carousel_slide(slide_type: str, slide_data: dict, slide_position: int,
                            total_slides: int, config: dict, site_name: str,
                            image_width: int, image_height: int, aspect_ratio: str):
    """1枚分のカルーセルスライドを生成"""
    image_client = get_image_client(
        provider=st.session_state.image_provider,
        gemini_api_key=st.session_state.api_key,
        openai_api_key=st.session_state.openai_api_key,
    )

    # カルーセル参照画像（全枚統一のため同じセットを毎回使う）
    cm = get_cm()
    ref_images = []
    if site_name:
        ref_images = cm.get_reference_pil_images(site_name, category="carousel")
        if not ref_images:
            # フォールバック: 通常 reference_images
            ref_images = cm.get_reference_pil_images(site_name)

    site_colors = {
        "primary_color": config.get("primary_color", "#06C755"),
        "secondary_color": config.get("secondary_color", "#10B981"),
        "accent_color": config.get("accent_color", "#F59E0B"),
        "background_color": config.get("background_color", "#FFFFFF"),
        "text_color": config.get("text_color", "#1F2937"),
        "danger_color": config.get("danger_color", "#E74A3B"),
    }

    slide_content = _build_slide_content(slide_type, slide_data, slide_position, total_slides)

    gen_prompt = render_carousel_slide_prompt(
        slide_type=slide_type,
        slide_content=slide_content,
        slide_position=slide_position,
        total_slides=total_slides,
        site_colors=site_colors,
        language=config.get("language", "Japanese"),
        has_reference_images=bool(ref_images),
        image_width=image_width,
        image_height=image_height,
        show_nav=True,
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
st.title("🎠 診断カルーセル生成")

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
st.info(
    f"対象ジャンル: **{config.get('brand_name', st.session_state.current_site)}** ／ "
    f"画像生成: **{provider_label(st.session_state.image_provider)}**"
)

# 参照画像状況
cm = get_cm()
carousel_ref_count = len(cm.list_reference_images(st.session_state.current_site, category="carousel"))
default_ref_count = len(cm.list_reference_images(st.session_state.current_site))
if carousel_ref_count > 0:
    st.success(f"カルーセル参照画像: {carousel_ref_count}枚登録済み（全スライドで使い回しトーン統一）")
elif default_ref_count > 0:
    st.info(f"カルーセル専用参照画像なし → 通常参照画像 {default_ref_count}枚を流用します")
else:
    st.warning("参照画像未登録。複数枚のトーン統一には参照画像必須レベル。「🏷️ ジャンル設定」→「🎠 診断カルーセル」タブ から登録推奨。")

# =============================================================
# Step 1: 診断テーマ入力
# =============================================================
st.subheader("Step 1: 診断テーマ")

theme = st.text_input(
    "診断テーマ",
    value=st.session_state.carousel_theme,
    placeholder="例: 隠れ肥満度チェック、包茎治療必要度チェック、AGA進行度診断",
    key="input_carousel_theme",
)
st.session_state.carousel_theme = theme

target_input = st.text_area(
    "ターゲット読者（任意）",
    placeholder="例: 30代女性、BMI正常範囲だがお腹周りに不安、運動習慣なし",
    height=60,
    key="input_carousel_target",
)

slide_count = st.slider(
    "総スライド枚数（表紙1 + 設問N + 結果1）",
    min_value=3, max_value=10,
    value=st.session_state.carousel_count,
    key="input_carousel_count",
    help="3枚: 表紙+設問1+結果 / 10枚: 表紙+設問8+結果",
)
st.session_state.carousel_count = slide_count
question_count = slide_count - 2
st.caption(f"内訳: 表紙1枚 + 設問{question_count}枚 + 結果1枚")

# =============================================================
# Step 2: AI設計
# =============================================================
st.subheader("Step 2: カルーセル文言を設計")

btn_design = st.button(
    "AIで文言を設計",
    type="primary",
    disabled=not theme.strip(),
    use_container_width=True,
)

if btn_design and theme.strip():
    with st.status("カルーセル文言を設計中...", expanded=True) as status:
        try:
            gemini = GeminiClient(api_key=st.session_state.api_key)
            prompt = render_carousel_proposal_prompt(theme, target_input, slide_count)
            response_text = gemini.analyze_text(prompt)
            design = _parse_carousel_proposal(response_text)
            if design and "cover" in design and "questions" in design and "result" in design:
                st.session_state.carousel_proposals = [design]
                status.update(label="設計完了", state="complete")
            else:
                status.update(label="設計の解析に失敗", state="error")
                st.error("Geminiの応答が想定の JSON 構造になっていません。テーマを変えて再試行を。")
        except Exception as e:
            status.update(label="エラー", state="error")
            st.error(f"エラー: {e}")

# =============================================================
# Step 3: 文言の確認・編集
# =============================================================
if st.session_state.carousel_proposals:
    design = st.session_state.carousel_proposals[0]

    st.subheader("Step 3: 文言を確認・編集")

    # 表紙
    with st.expander("【1】表紙", expanded=True):
        design["cover"]["title"] = st.text_input(
            "タイトル（最大15文字）", value=design["cover"].get("title", ""), key="cover_title"
        )
        design["cover"]["subtitle"] = st.text_input(
            "サブコピー（最大20文字）", value=design["cover"].get("subtitle", ""), key="cover_subtitle"
        )
        design["cover"]["cta_text"] = st.text_input(
            "CTA（最大10文字）", value=design["cover"].get("cta_text", ""), key="cover_cta"
        )

    # 設問
    questions = design.get("questions", [])
    for qi, q in enumerate(questions):
        with st.expander(f"【{qi+2}】設問{qi+1} (Q{q.get('question_no', qi+1)})", expanded=False):
            q["question_text"] = st.text_input(
                "設問本文（最大25文字）", value=q.get("question_text", ""), key=f"q_text_{qi}"
            )
            c1, c2 = st.columns(2)
            with c1:
                q["option_a"] = st.text_input("選択肢A", value=q.get("option_a", ""), key=f"q_a_{qi}")
            with c2:
                q["option_b"] = st.text_input("選択肢B", value=q.get("option_b", ""), key=f"q_b_{qi}")

    # 結果
    with st.expander(f"【{len(questions)+2}】結果", expanded=True):
        design["result"]["title"] = st.text_input(
            "結果タイトル（最大15文字）", value=design["result"].get("title", ""), key="result_title"
        )
        design["result"]["body"] = st.text_area(
            "結果説明文（最大40文字）", value=design["result"].get("body", ""), height=60, key="result_body"
        )
        design["result"]["cta_text"] = st.text_input(
            "CTA（最大15文字）", value=design["result"].get("cta_text", ""), key="result_cta"
        )

    # =============================================================
    # Step 4: 生成設定 + 一括生成
    # =============================================================
    st.subheader("Step 4: 生成設定")

    size_preset = st.radio(
        "サイズ（全スライド共通）",
        options=["縦長 (682×1024)", "スクエア (1080×1080)", "横長 (1200×630)", "カスタム"],
        horizontal=True,
        index=0,
        key="c_size_preset",
    )
    if size_preset.startswith("縦長"):
        c_width, c_height = 682, 1024
    elif size_preset.startswith("スクエア"):
        c_width, c_height = 1080, 1080
    elif size_preset.startswith("横長"):
        c_width, c_height = 1200, 630
    else:
        cs1, cs2 = st.columns(2)
        with cs1:
            c_width = st.number_input("幅(px)", min_value=256, max_value=4096, value=682, step=10, key="c_width")
        with cs2:
            c_height = st.number_input("高さ(px)", min_value=256, max_value=4096, value=1024, step=10, key="c_height")

    target_ratio = c_width / c_height
    best_ar = "1:1"
    min_diff = float("inf")
    for ar in SUPPORTED_ASPECT_RATIOS:
        w, h = map(int, ar.split(":"))
        diff = abs(w / h - target_ratio)
        if diff < min_diff:
            min_diff = diff
            best_ar = ar
    st.caption(f"出力サイズ: **{c_width}×{c_height}px** / アスペクト比(自動): **{best_ar}**")

    total_slides = 2 + len(questions)
    st.divider()
    st.caption(f"全{total_slides}枚のスライドを生成します。同じ参照画像セットでトーンを統一します。")

    if st.session_state.carousel_generation_in_progress:
        st.session_state.carousel_generation_in_progress = False

    batch_btn = st.button(
        f"全{total_slides}枚を一括生成",
        type="primary",
        use_container_width=True,
    )

    if batch_btn:
        st.session_state.carousel_generation_in_progress = True
        st.session_state.carousel_generated_images = []
        slides_def = [("表紙", design["cover"])] + \
                     [("設問", q) for q in questions] + \
                     [("結果", design["result"])]
        progress_bar = st.progress(0, text="カルーセルを生成中...")
        for step, (slide_type, slide_data) in enumerate(slides_def):
            position = step + 1
            progress = position / total_slides
            progress_bar.progress(progress, text=f"{position}/{total_slides} {slide_type}を生成中...")
            try:
                gen_image, gen_text, gen_prompt, ref_count = generate_carousel_slide(
                    slide_type, slide_data, position, total_slides,
                    config, st.session_state.current_site,
                    c_width, c_height, best_ar,
                )
                if gen_image:
                    label = f"{position:02d}_{slide_type}"
                    saved_key = _save_to_storage(gen_image, st.session_state.current_site or "unknown", label)
                    st.session_state.carousel_generated_images.append({
                        "slide_position": position,
                        "slide_type": slide_type,
                        "slide_data": slide_data,
                        "image": gen_image,
                        "processed_image": None,
                        "response_text": gen_text,
                        "generation_prompt": gen_prompt,
                        "reference_image_count": ref_count,
                        "saved_key": saved_key,
                        "timestamp": datetime.datetime.now().isoformat(),
                    })
                else:
                    st.warning(f"{position}/{total_slides} {slide_type} の生成失敗: {gen_text or ''}")
            except Exception as e:
                st.error(f"{position}/{total_slides} {slide_type} のエラー: {e}")
        progress_bar.progress(1.0, text="全スライド生成完了!")
        st.session_state.carousel_generation_in_progress = False
        st.rerun()

# =============================================================
# 生成結果
# =============================================================
if st.session_state.carousel_generated_images:
    st.subheader("カルーセル生成結果")
    images = st.session_state.carousel_generated_images

    # 全画像表示（順番通り）
    for i, entry in enumerate(images):
        img = entry["image"]
        processed = entry.get("processed_image")
        st.markdown(f"### {entry['slide_position']}/{len(images)} - {entry['slide_type']}")
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
                            f"⚠️ 参照画像を{ref_count}枚併用。テキストプロンプトだけでは100%再現できません。"
                        )
                    st.code(prompt_used, language="text")
                else:
                    st.caption("（プロンプト未記録）")
        with c_col:
            if st.button("余白トリミング", key=f"car_trim_{i}"):
                entry["processed_image"] = trim_whitespace(img)
                st.rerun()
            download_img = processed if processed else img
            img_bytes = image_to_bytes(download_img)
            st.download_button(
                "このスライドDL",
                data=img_bytes,
                file_name=f"carousel_{entry['slide_position']:02d}_{entry['slide_type']}.png",
                mime="image/png",
                key=f"car_dl_{i}",
                use_container_width=True,
            )
        st.divider()

    # 一括ZIPダウンロード
    st.subheader("全スライドをZIPでダウンロード")
    if st.button("📦 全スライドをZIPでダウンロード", use_container_width=True, key="car_dl_all"):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for entry in images:
                dl_img = entry.get("processed_image") or entry["image"]
                img_bytes = image_to_bytes(dl_img)
                filename = f"{entry['slide_position']:02d}_{entry['slide_type']}.png"
                zf.writestr(filename, img_bytes)
        st.download_button(
            "ZIPをダウンロード",
            data=buf.getvalue(),
            file_name=f"carousel_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            key="car_zip_file",
            use_container_width=True,
        )
