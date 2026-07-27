"""
診断設計書・デザイン依頼書 生成ページ
診断プロジェクトのデータ(設問・タイプ別カード文言・PU文言・商材マッピング・トンマナ)を
画面上のフォームで編集し、house format通りの「診断設計書」「デザイン依頼書」markdownを生成する。

JSON貼り付け/サンプル読み込みは「初期データの流し込み」用（Claude Codeが下書きを渡す時等）。
読み込み後は全項目をこの画面上で直接編集できる。
"""

import json
import copy
import datetime
import streamlit as st

from lib.diagnosis_schema import get_sample_data
from lib.diagnosis_templates import render_design_doc, render_design_brief


def get_cm():
    from lib.dependencies import get_config_manager
    return get_config_manager()


EMPTY_DATA = {
    "meta": {"title": "", "created_date": datetime.date.today().isoformat(), "genre": "", "status": ""},
    "overview": "",
    "flow": {"questions": []},
    "result_types": [],
    "pu_copy": {"title": "", "variants": []},
    "tone": {"primary_color": "", "target": ""},
    "image_counts": {"pu_banner": 0, "question_panels": 0, "result_carousel": 0, "total": 0},
    "remaining_tasks": [],
}


def _init_state():
    if "diag_data" not in st.session_state:
        st.session_state.diag_data = copy.deepcopy(EMPTY_DATA)


_init_state()

st.title("📋 診断設計書・デザイン依頼書 生成")
st.caption("診断の設問・カード文言・PU文言・トンマナを画面上で編集し、house format通りの設計書・デザイン依頼書を生成します。")

# =============================================================
# ジャンル選択（サイドバー連動。色のデフォルト値に使う）
# =============================================================
cm = get_cm()
if not st.session_state.current_site:
    st.warning("サイドバーからジャンルを選択してください。")
    st.stop()

config = st.session_state.site_config
st.info(f"対象ジャンル: **{config.get('brand_name', st.session_state.current_site)}**")

# =============================================================
# Step 1: 初期データ読み込み（任意）
# =============================================================
with st.expander("Step 1: JSONから読み込む（Claude Codeが下書きを渡す時・任意）", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📄 サンプルを読み込む", use_container_width=True):
            st.session_state.diag_data = copy.deepcopy(get_sample_data())
            st.rerun()
    with c2:
        if st.button("🆕 空にする（新規作成）", use_container_width=True):
            st.session_state.diag_data = copy.deepcopy(EMPTY_DATA)
            st.rerun()

    uploaded = st.file_uploader("または.jsonをアップロード", type=["json"], key="diag_json_upload")
    json_paste = st.text_area("またはJSONを貼り付け", height=150, key="diag_json_paste")
    if st.button("この内容で読み込む", disabled=not (uploaded or json_paste.strip())):
        try:
            raw = uploaded.getvalue().decode("utf-8") if uploaded else json_paste
            st.session_state.diag_data = json.loads(raw)
            st.success("読み込みました。下のフォームで編集できます。")
            st.rerun()
        except json.JSONDecodeError as e:
            st.error(f"JSONの解析に失敗しました: {e}")

data = st.session_state.diag_data

# ジャンルの色をトンマナの初期値として反映（トンマナのメインカラーが未入力の時だけ補完）
data.setdefault("tone", {})
if not data["tone"].get("primary_color") and config.get("primary_color"):
    data["tone"]["primary_color"] = config.get("primary_color")
    data["tone"]["secondary_color"] = config.get("secondary_color", "")
    data["tone"]["background"] = config.get("background_color", "")

# =============================================================
# Step 2: フォーム編集
# =============================================================
st.subheader("Step 2: 内容を編集")

# ----- 基本情報 -----
with st.expander("📝 基本情報", expanded=True):
    meta = data.setdefault("meta", {})
    c1, c2 = st.columns(2)
    with c1:
        meta["title"] = st.text_input("診断タイトル", value=meta.get("title", ""), key="meta_title")
        meta["created_date"] = st.text_input("作成日", value=meta.get("created_date", ""), key="meta_date")
        meta["genre"] = st.text_input("ジャンル（任意）", value=meta.get("genre", ""), key="meta_genre")
    with c2:
        meta["status"] = st.text_input("ステータス（任意）", value=meta.get("status", ""), key="meta_status")
        meta["version_label"] = st.text_input("バージョン（任意）", value=meta.get("version_label", ""), key="meta_version")
        meta["type_label"] = st.text_input("タイプ（任意）", value=meta.get("type_label", ""), key="meta_type")
    data["overview"] = st.text_area("概要", value=data.get("overview", ""), height=100, key="overview_text")

# ----- 診断フロー（設問） -----
with st.expander("❓ 診断フロー（設問）", expanded=True):
    flow = data.setdefault("flow", {})
    flow["system_note"] = st.text_input(
        "システム制約メモ（任意。例: 診断結果は最終設問の回答のみで分岐する）",
        value=flow.get("system_note", ""), key="flow_system_note",
    )
    flow["welcome_card"] = st.text_area(
        "ウェルカムカード文言（任意）", value=flow.get("welcome_card", ""), height=80, key="flow_welcome",
    )

    questions = flow.setdefault("questions", [])
    for qi, q in enumerate(questions):
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 3, 3])
            with c1:
                q["id"] = st.text_input("ID", value=q.get("id", f"Q{qi+1}"), key=f"q_id_{qi}")
            with c2:
                q["text"] = st.text_input("設問本文", value=q.get("text", ""), key=f"q_text_{qi}")
            with c3:
                q["branch_label"] = st.text_input(
                    "分岐ラベル（例: 非分岐／最終設問・タイプ確定）",
                    value=q.get("branch_label", ""), key=f"q_branch_{qi}",
                )

            options = q.setdefault("options", [])
            st.caption("選択肢")
            for oi, opt in enumerate(options):
                oc1, oc2, oc3, oc4 = st.columns([1, 3, 3, 1])
                with oc1:
                    opt["label"] = st.text_input("記号", value=opt.get("label", ""), key=f"q_{qi}_opt_{oi}_label")
                with oc2:
                    opt["text"] = st.text_input("回答", value=opt.get("text", ""), key=f"q_{qi}_opt_{oi}_text")
                with oc3:
                    opt["result"] = st.text_input(
                        "確定タイプ（分岐する設問のみ）", value=opt.get("result", ""), key=f"q_{qi}_opt_{oi}_result",
                    )
                with oc4:
                    if st.button("🗑️", key=f"q_{qi}_opt_{oi}_del"):
                        options.pop(oi)
                        st.rerun()
            if st.button("+ 選択肢を追加", key=f"q_{qi}_opt_add"):
                options.append({"label": "", "text": ""})
                st.rerun()

            q["design_note"] = st.text_input(
                "設計意図（任意）", value=q.get("design_note", ""), key=f"q_{qi}_note",
            )
            if st.button("🗑️ この設問を削除", key=f"q_{qi}_del"):
                questions.pop(qi)
                st.rerun()

    if st.button("+ 設問を追加"):
        questions.append({"id": f"Q{len(questions)+1}", "text": "", "options": []})
        st.rerun()

# ----- 結果カード設計 -----
with st.expander("🃏 結果カード設計（タイプ別）", expanded=True):
    result_types = data.setdefault("result_types", [])
    for ti, t in enumerate(result_types):
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                t["name"] = st.text_input("タイプ名", value=t.get("name", ""), key=f"rt_{ti}_name")
            with c2:
                t["accent_color"] = st.color_picker(
                    "アクセント色", value=t.get("accent_color", "#3B82F6") or "#3B82F6", key=f"rt_{ti}_color",
                )

            cards = t.setdefault("cards", [])
            for ci, card in enumerate(cards):
                cc1, cc2 = st.columns([2, 1])
                with cc1:
                    card["role"] = st.text_input(
                        f"Card{ci+1}の役割", value=card.get("role", ""), key=f"rt_{ti}_card_{ci}_role",
                    )
                card["text"] = st.text_area(
                    f"Card{ci+1}のテキスト", value=card.get("text", ""), height=80, key=f"rt_{ti}_card_{ci}_text",
                )
                if st.button(f"🗑️ Card{ci+1}を削除", key=f"rt_{ti}_card_{ci}_del"):
                    cards.pop(ci)
                    st.rerun()
            if st.button("+ カードを追加", key=f"rt_{ti}_card_add"):
                cards.append({"role": "", "text": ""})
                st.rerun()
            if st.button("🗑️ このタイプを削除", key=f"rt_{ti}_del"):
                result_types.pop(ti)
                st.rerun()

    if st.button("+ タイプを追加"):
        result_types.append({"name": "", "accent_color": "#3B82F6", "cards": []})
        st.rerun()

# ----- PU文言 -----
with st.expander("📣 PU文言", expanded=True):
    pu_copy = data.setdefault("pu_copy", {})
    pu_copy["title"] = st.text_input("PU見出し（診断タイトル）", value=pu_copy.get("title", ""), key="pu_title")
    variants = pu_copy.setdefault("variants", [])
    for vi, v in enumerate(variants):
        with st.container(border=True):
            v["label"] = st.text_input("案ラベル", value=v.get("label", ""), key=f"pu_{vi}_label")
            v["headline"] = st.text_input("コピー", value=v.get("headline", ""), key=f"pu_{vi}_headline")
            v["sub"] = st.text_input("補足（例: カンタン5問診断）", value=v.get("sub", ""), key=f"pu_{vi}_sub")
            buttons_text = st.text_input(
                "ボタン（カンマ区切り。例: はい,いいえ）",
                value=",".join(v.get("buttons", [])), key=f"pu_{vi}_buttons",
            )
            v["buttons"] = [b.strip() for b in buttons_text.split(",") if b.strip()]
            if st.button("🗑️ この案を削除", key=f"pu_{vi}_del"):
                variants.pop(vi)
                st.rerun()
    if st.button("+ PU案を追加"):
        variants.append({"label": f"案{chr(65+len(variants))}", "headline": "", "buttons": ["はい", "いいえ"]})
        st.rerun()
    pu_copy["usage_note"] = st.text_area(
        "使い分けメモ（任意）", value=pu_copy.get("usage_note", ""), height=60, key="pu_usage_note",
    )

# ----- 商材マッピング（任意セクション） -----
with st.expander("🛒 商材マッピング（商材紹介がある診断のみ・任意）", expanded=False):
    has_pm = st.checkbox("このセクションを含める", value=bool(data.get("product_mapping")), key="has_product_mapping")
    if has_pm:
        pm = data.setdefault("product_mapping", {"axis_labels": [], "rows": []})
        axis_text = st.text_input(
            "列見出し（カンマ区切り。例: 肌タイプ,クレンジング推奨,化粧水推奨）",
            value=",".join(pm.get("axis_labels", [])), key="pm_axis",
        )
        pm["axis_labels"] = [a.strip() for a in axis_text.split(",") if a.strip()]
        rows = pm.setdefault("rows", [])
        for ri, row in enumerate(rows):
            row["axis"] = st.text_input(f"行{ri+1}: 軸（例: 乾燥肌）", value=row.get("axis", ""), key=f"pm_{ri}_axis")
            values_text = st.text_input(
                f"行{ri+1}: 各列の値（カンマ区切り）", value=",".join(row.get("values", [])), key=f"pm_{ri}_values",
            )
            row["values"] = [v.strip() for v in values_text.split(",")]
            if st.button(f"🗑️ 行{ri+1}を削除", key=f"pm_{ri}_del"):
                rows.pop(ri)
                st.rerun()
        if st.button("+ 行を追加", key="pm_row_add"):
            rows.append({"axis": "", "values": []})
            st.rerun()
        pm["notes"] = st.text_area("補足（任意）", value=pm.get("notes", ""), key="pm_notes")
    elif "product_mapping" in data:
        del data["product_mapping"]

# ----- ものさしづくり（任意セクション） -----
with st.expander("📏 ものさしづくり（任意）", expanded=False):
    has_mono = st.checkbox("このセクションを含める", value=bool(data.get("monosashi")), key="has_monosashi")
    if has_mono:
        mono = data.setdefault("monosashi", {})
        before_text = st.text_area(
            "今のものさし（1行1項目）", value="\n".join(mono.get("before", [])), height=80, key="mono_before",
        )
        mono["before"] = [l for l in before_text.split("\n") if l.strip()]
        voices_text = st.text_area(
            "リアルボイス（1行1項目・任意）", value="\n".join(mono.get("real_voices", [])), height=60, key="mono_voices",
        )
        mono["real_voices"] = [l for l in voices_text.split("\n") if l.strip()]
        after_text = st.text_area(
            "新しいものさし（1行1項目）", value="\n".join(mono.get("after", [])), height=80, key="mono_after",
        )
        mono["after"] = [l for l in after_text.split("\n") if l.strip()]
        mono["hammer"] = st.text_area("ハンマー（任意）", value=mono.get("hammer", ""), height=60, key="mono_hammer")
    elif "monosashi" in data:
        del data["monosashi"]

# ----- 推奨カルーセル（任意セクション） -----
with st.expander("🎁 おすすめ商品カルーセル（任意・商材紹介がある診断のみ）", expanded=False):
    has_rec = st.checkbox("このセクションを含める", value=bool(data.get("recommendation_carousel")), key="has_rec")
    if has_rec:
        rec = data.setdefault("recommendation_carousel", {"label": "おすすめ3点セットカル", "types": []})
        rec["label"] = st.text_input("カルーセル名", value=rec.get("label", ""), key="rec_label")
        rec_types = rec.setdefault("types", [])
        for ti, t in enumerate(rec_types):
            with st.container(border=True):
                t["name"] = st.text_input("タイプ名", value=t.get("name", ""), key=f"rec_{ti}_name")
                cards = t.setdefault("cards", [])
                for ci, card in enumerate(cards):
                    card["role"] = st.text_input(
                        f"Card{ci+1}の役割", value=card.get("role", ""), key=f"rec_{ti}_card_{ci}_role",
                    )
                    card["text"] = st.text_area(
                        f"Card{ci+1}のテキスト", value=card.get("text", ""), height=60, key=f"rec_{ti}_card_{ci}_text",
                    )
                    if st.button(f"🗑️ Card{ci+1}を削除", key=f"rec_{ti}_card_{ci}_del"):
                        cards.pop(ci)
                        st.rerun()
                if st.button("+ カードを追加", key=f"rec_{ti}_card_add"):
                    cards.append({"role": "", "text": ""})
                    st.rerun()
                if st.button("🗑️ このタイプを削除", key=f"rec_{ti}_del"):
                    rec_types.pop(ti)
                    st.rerun()
        if st.button("+ タイプを追加", key="rec_type_add"):
            rec_types.append({"name": "", "cards": []})
            st.rerun()
    elif "recommendation_carousel" in data:
        del data["recommendation_carousel"]

# ----- 残タスク -----
with st.expander("✅ 残タスク", expanded=False):
    tasks_text = st.text_area(
        "1行1項目（例: [x] 完了済みタスク / [ ] 未完了タスク）",
        value="\n".join(data.get("remaining_tasks", [])), height=100, key="tasks_text",
    )
    data["remaining_tasks"] = [l for l in tasks_text.split("\n") if l.strip()]

# ----- トンマナ -----
with st.expander("🎨 トンマナ", expanded=True):
    tone = data.setdefault("tone", {})
    c1, c2 = st.columns(2)
    with c1:
        tone["primary_color"] = st.text_input("メインカラー", value=tone.get("primary_color", ""), key="tone_primary")
        tone["secondary_color"] = st.text_input("サブカラー（任意）", value=tone.get("secondary_color", ""), key="tone_secondary")
    with c2:
        tone["background"] = st.text_input("背景（任意）", value=tone.get("background", ""), key="tone_bg")
        tone["illustration"] = st.text_input("イラストタッチ（任意）", value=tone.get("illustration", ""), key="tone_illust")
    tone["target"] = st.text_input("ターゲット", value=tone.get("target", ""), key="tone_target")

# ----- 画像枚数（依頼書用） -----
with st.expander("🖼️ 依頼書の画像枚数", expanded=True):
    ic = data.setdefault("image_counts", {})
    n_questions = len(flow.get("questions", []))
    n_types = len(result_types)
    card_count_per_type = len(result_types[0].get("cards", [])) if result_types else 0
    ic["pu_banner"] = len(pu_copy.get("variants", []))
    c1, c2, c3 = st.columns(3)
    with c1:
        ic["cover"] = st.number_input("診断表紙(枚)", min_value=0, value=int(ic.get("cover", 1)), key="ic_cover")
    with c2:
        ic["question_panels"] = st.number_input(
            "設問パネル(枚)", min_value=0, value=int(ic.get("question_panels", n_questions)), key="ic_qp",
        )
    with c3:
        default_result = ic.get("result_carousel", card_count_per_type * n_types)
        ic["result_carousel"] = st.number_input(
            "結果カルーセル(枚)", min_value=0, value=int(default_result), key="ic_result",
        )
    if data.get("recommendation_carousel"):
        rec_cards = data["recommendation_carousel"].get("types", [])
        default_rec = ic.get(
            "recommendation_carousel",
            (len(rec_cards[0].get("cards", [])) if rec_cards else 0) * len(rec_cards),
        )
        ic["recommendation_carousel"] = st.number_input(
            "おすすめカルーセル(枚)", min_value=0, value=int(default_rec), key="ic_rec",
        )
    ic["total"] = (
        ic.get("pu_banner", 0) + ic.get("cover", 0) + ic.get("question_panels", 0)
        + ic.get("result_carousel", 0) + ic.get("recommendation_carousel", 0)
    )
    st.caption(f"合計: {ic['total']}枚（自動計算）")

data["docs_url"] = st.text_input("設計書の公開URL（任意・依頼書からリンクする）", value=data.get("docs_url", ""), key="docs_url")

# =============================================================
# Step 3: 生成結果
# =============================================================
st.subheader("Step 3: 生成結果")

missing = []
if not data.get("meta", {}).get("title"):
    missing.append("診断タイトル")
if not flow.get("questions"):
    missing.append("設問（最低1問）")
if not result_types:
    missing.append("結果タイプ（最低1タイプ・カード最低1枚）")
elif not result_types[0].get("cards"):
    missing.append("結果タイプのカード（最低1枚）")
if not pu_copy.get("variants"):
    missing.append("PU文言案（最低1案）")

if missing:
    st.info("生成にはあと以下の入力が必要です: " + "、".join(missing))
    st.stop()

try:
    design_doc_md = render_design_doc(data)
    design_brief_md = render_design_brief(data)
except Exception as e:
    st.error(f"生成中にエラーが発生しました: {e}")
    st.stop()

title = data.get("meta", {}).get("title") or "診断"

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
