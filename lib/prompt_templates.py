"""
LINEマーケ画像生成 プロンプトテンプレート
PU（プッシュアップ）バナー・診断カルーセル・PRカルーセルの3種類の生成プロンプトを持つ。
参照画像へのスタイルトランスファー方式（Layer2: 文言案提案 → Layer3: 画像生成）を採用。
"""

from __future__ import annotations

# =============================================================
# LINE版: PU（プッシュアップ）画像 用テンプレート
# 「問いかけ＋はい/いいえ」型バナー。1枚生成。
# 参照画像のテイストにスタイルトランスファーする方式。
# =============================================================

PU_PROPOSAL_TEMPLATE = """あなたはLINEマーケのコピーライターです。
読者の不安・関心を1文の問いかけにし、「はい / いいえ」で答えたくなるPUバナー文言案を1〜3パターン考えてください。

== 訴求テーマ ==
{theme}

== ターゲット読者の状況 ==
{target_situation}

== 必須フォーマット（厳守） ==
- ヘッドライン = 必ず疑問文（「〜ですか？」「〜していませんか？」「〜ありますか？」）
- 補助コピー = ヘッドラインを補強する1行（任意・最大15文字）
- CTAは「はい / いいえ」または「YES / NO」の二択ボタンを前提とする
- ヘッドラインは最大18文字以内（崩れ防止）

== 出力形式（JSON配列で必ず出力） ==
```json
[
  {{
    "headline": "ヘッドライン疑問文（最大18文字）",
    "subcopy": "補助コピー（任意。最大15文字）",
    "yes_label": "はい",
    "no_label": "いいえ",
    "person_or_visual": "中央に描くべき主題ビジュアル（人物・モノ・場面）の説明"
  }}
]
```

== ルール ==
- ヘッドラインは「自分ごと化」する問いに。一般論NG
- 不安・後悔・コンプレックスに直接触れる
- 「読者が「はい」と答えそうな問い」を最低1案入れる
- 「読者が「いいえ」と答えそうな問い（=だからこの記事が必要）」も最低1案入れる
- person_or_visual は記事KW/訴求テーマに直結する具体的なモノ・場面・人物にする
- 文言はオフィシャル画像として成立するトーンにする。「みんな」「絶対」などカジュアルな主語・話し言葉の断定は、言いたいことを保ったまま公式らしい言い回しに翻訳する（例:「みんな○○します」→「○○が基本です」）
"""


PU_GENERATION_WITH_REF_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
この画像は{image_width}×{image_height}pxで使用される。すべてのテキスト・人物・装飾をこのキャンバスサイズに最適化して配置すること。

添付の参照画像のデザインを完全にコピーして、テキスト内容と主題ビジュアルだけ差し替えたPU（プッシュアップ）バナーを作成してください。

【最重要原則】
参照画像のレイアウト・色・フォント・装飾・背景・ボタン形状・余白を完全にコピーすること。
参照画像に存在する要素だけを描画し、存在しない要素は絶対に追加しないこと。

{color_instruction}

== 差し替えるテキスト内容 ==
- ヘッドライン（最も大きい疑問文）: 「{headline}」
- 補助コピー（ヘッドライン下の1行）: 「{subcopy}」
- 「はい」ボタン内のテキスト: 「{yes_label}」
- 「いいえ」ボタン内のテキスト: 「{no_label}」
- 主題ビジュアル（中央 or 背景）: {person_or_visual}

== 厳守ルール ==
- ヘッドラインは必ず疑問文として描画（「？」を必ず付ける）
- 「はい / いいえ」の二択ボタンを参照画像と同じ位置・形状で配置
- 上記文字列を一字一句そのまま描画。文言を変えない・省略しない・追加しない
- テキストは{language}のみ
- 参照画像にない要素（ロゴ・別ボタン・追加テキスト）は描画しない
"""


PU_GENERATION_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
LINEマーケ用のPU（プッシュアップ）バナー画像を作成してください。

== 配色 ==
{color_instruction}

== レイアウト（厳守） ==
画像サイズ: {image_width}×{image_height}px

┌─────────────────────────────────────┐
│                                     │
│     [ヘッドライン]（最も大きい疑問文）│
│         画像高さの12%相当フォント     │
│                                     │
│        [補助コピー]（任意）          │
│         画像高さの5%相当フォント      │
│                                     │
│        [主題ビジュアル]              │
│      （中央：人物 or モノ）           │
│                                     │
│   ┌─────┐         ┌─────┐         │
│   │はい │         │いいえ│          │
│   └─────┘         └─────┘         │
│                                     │
└─────────────────────────────────────┘

== テキスト内容 ==
- ヘッドライン: 「{headline}」（必ず疑問文。「？」を含める）
- 補助コピー: 「{subcopy}」
- はいボタン: 「{yes_label}」
- いいえボタン: 「{no_label}」
- 主題ビジュアル: {person_or_visual}

== ボタン装飾 ==
- 「はい」ボタン: テーマカラー塗り + 白文字、角丸ピル型
- 「いいえ」ボタン: 白塗り + テーマカラー枠線、角丸ピル型
- 両ボタン同じサイズで左右対称配置

== 全テキスト ==
{language}で記述。フォントは太めのゴシック体。
"""


# =============================================================
# LINE版: 診断カルーセル 用テンプレート
# 「表紙 → 設問N枚 → 結果」のシリーズ生成。全枚同じ参照画像でスタイル統一。
# =============================================================

CAROUSEL_PROPOSAL_TEMPLATE = """あなたはLINE診断カルーセルの設計者です。
診断テーマから「表紙1枚 + 設問{question_count}枚 + 結果1枚」の文言設計を出してください。

== 診断テーマ ==
{theme}

== ターゲット ==
{target}

== 出力形式（JSON必須） ==
```json
{{
  "cover": {{
    "title": "診断のタイトル（最大15文字）",
    "subtitle": "サブコピー（最大20文字）",
    "cta_text": "診断スタートを促す一言（最大10文字。例: タップでスタート）"
  }},
  "questions": [
    {{
      "question_no": 1,
      "question_text": "設問本文（疑問文、最大25文字）",
      "option_a": "選択肢A（最大10文字）",
      "option_b": "選択肢B（最大10文字）"
    }}
  ],
  "result": {{
    "title": "結果ページのタイトル（最大15文字。例: あなたは○○タイプ）",
    "body": "結果の説明文（最大40文字）",
    "cta_text": "次のアクションを促すCTA（最大15文字。例: 詳細はこちら）"
  }}
}}
```

== ルール ==
- 設問は{question_count}個ピッタリ生成
- 各設問は読者の自分ごと化を促す疑問形
- 選択肢A/Bは対立軸が明確（例: する/しない、ある/ない、はい/いいえ）
- 結果は「診断テーマに対する読者の現在地」が一文でわかる内容に
- 文言はオフィシャル画像として成立するトーンにする。「みんな」「絶対」などカジュアルな主語・話し言葉の断定は、言いたいことを保ったまま公式らしい言い回しに翻訳する（例:「みんな○○します」→「○○が基本です」）
"""


CAROUSEL_SLIDE_WITH_REF_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
添付の参照画像と同じデザインスタイル・レイアウト・配色・装飾で、診断カルーセルの{slide_type}スライドを作成してください。

【最重要原則】
参照画像のスタイル（背景・カード・色・フォント・装飾）を完全にコピーすること。
これは全{total_slides}枚のうちの{slide_position}枚目。**全{total_slides}枚で完全にトーンを統一すること。**

{color_instruction}

{nav_instruction}

== 差し替えるテキスト内容 ==
{slide_content}

== 厳守ルール ==
- 上記の「」内文字列を一字一句そのまま描画
- 参照画像にない要素は描画しない
- テキストは{language}のみ
- 参照画像と同じ位置にナンバリング（例「{slide_position}/{total_slides}」）を入れる
"""


CAROUSEL_SLIDE_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
LINE診断カルーセルの{slide_type}スライドを作成してください。
これは全{total_slides}枚のうちの{slide_position}枚目です。全枚で同じデザイントーンを保ってください。

{color_instruction}

== 画面構成（厳守） ==
- 上部右端 or 上部中央に小さく「{slide_position}/{total_slides}」のナンバリング
- 中央に主たるテキスト/ビジュアル
- 下部に CTA（任意）

== テキスト内容 ==
{slide_content}

== 全テキスト ==
{language}で記述。太めのゴシック体。視認性最優先。
"""


def _build_line_color_instruction(site_colors: dict | None = None, minimal: bool = False) -> str:
    """LINE 版の配色指示テキスト生成。MV版と同等のロジック。"""
    if site_colors:
        primary = site_colors.get("primary_color", "")
        if minimal:
            lines = [
                "== 配色の基準 ==",
                f"- このサイト/案件のテーマカラー: {primary}" if primary else "",
                "- それ以外の色は参照画像に従うこと",
            ]
        else:
            accent = site_colors.get("accent_color", "")
            bg = site_colors.get("background_color", "")
            text_c = site_colors.get("text_color", "")
            danger = site_colors.get("danger_color", "")
            lines = [
                "== 配色パレット ==",
                f"- テーマカラー: {primary}" if primary else "",
                f"- アクセントカラー: {accent or danger}" if (accent or danger) else "",
                f"- 背景ベース色: {bg}" if bg else "",
                f"- テキスト基本色: {text_c}" if text_c else "",
            ]
        return "\n".join(l for l in lines if l)
    return "== 配色 ==\n参照画像があればそれに従う。なければ案件のブランドカラーに合った配色をAIが自動判断。"


def render_pu_proposal_prompt(theme: str, target_situation: str = "") -> str:
    """PU文言案提案プロンプトを生成"""
    return PU_PROPOSAL_TEMPLATE.format(
        theme=theme,
        target_situation=target_situation or "（特定なし。一般的な読者を想定）",
    )


def render_pu_generation_prompt(
    pu_proposal: dict,
    site_colors: dict | None = None,
    language: str = "Japanese",
    has_reference_images: bool = False,
    image_width: int = 1080,
    image_height: int = 1080,
) -> str:
    """PU生成プロンプトを組み立てる"""
    if has_reference_images:
        color_instruction = _build_line_color_instruction(site_colors, minimal=True)
        return PU_GENERATION_WITH_REF_TEMPLATE.format(
            color_instruction=color_instruction,
            headline=pu_proposal.get("headline", "").strip(),
            subcopy=pu_proposal.get("subcopy", "").strip(),
            yes_label=pu_proposal.get("yes_label", "はい").strip(),
            no_label=pu_proposal.get("no_label", "いいえ").strip(),
            person_or_visual=pu_proposal.get("person_or_visual", "").strip(),
            language=language,
            image_width=image_width,
            image_height=image_height,
        )
    color_instruction = _build_line_color_instruction(site_colors)
    return PU_GENERATION_TEMPLATE.format(
        color_instruction=color_instruction,
        headline=pu_proposal.get("headline", "").strip(),
        subcopy=pu_proposal.get("subcopy", "").strip(),
        yes_label=pu_proposal.get("yes_label", "はい").strip(),
        no_label=pu_proposal.get("no_label", "いいえ").strip(),
        person_or_visual=pu_proposal.get("person_or_visual", "").strip(),
        language=language,
        image_width=image_width,
        image_height=image_height,
    )


def render_carousel_proposal_prompt(theme: str, target: str = "", question_count: int = 6) -> str:
    """カルーセル文言設計プロンプトを生成"""
    # cover + result で2枚使うので、設問数は全体枚数 - 2
    q_count = max(1, question_count - 2)
    return CAROUSEL_PROPOSAL_TEMPLATE.format(
        theme=theme,
        target=target or "（特定なし。一般的な読者を想定）",
        question_count=q_count,
    )


def render_carousel_slide_prompt(
    slide_type: str,
    slide_content: str,
    slide_position: int,
    total_slides: int,
    site_colors: dict | None = None,
    language: str = "Japanese",
    has_reference_images: bool = False,
    image_width: int = 1080,
    image_height: int = 1080,
    show_nav: bool = True,
) -> str:
    """カルーセルの1枚分の生成プロンプトを組み立てる

    Args:
        slide_type: "表紙" / "設問" / "結果"
        slide_content: そのスライドに入れるテキスト内容（HEREDOC形式の文字列）
        slide_position: 何枚目か（1-indexed）
        total_slides: 全部で何枚か
        show_nav: ナンバリングを表示するか
    """
    nav_instruction = ""
    if show_nav:
        nav_instruction = (
            f"== ナンバリング ==\n"
            f"上部に「{slide_position}/{total_slides}」のナンバリングを参照画像と同じ位置・スタイルで描画。"
        )

    if has_reference_images:
        color_instruction = _build_line_color_instruction(site_colors, minimal=True)
        return CAROUSEL_SLIDE_WITH_REF_TEMPLATE.format(
            color_instruction=color_instruction,
            nav_instruction=nav_instruction,
            slide_type=slide_type,
            slide_content=slide_content,
            slide_position=slide_position,
            total_slides=total_slides,
            language=language,
            image_width=image_width,
            image_height=image_height,
        )
    color_instruction = _build_line_color_instruction(site_colors)
    return CAROUSEL_SLIDE_TEMPLATE.format(
        color_instruction=color_instruction,
        slide_type=slide_type,
        slide_content=slide_content,
        slide_position=slide_position,
        total_slides=total_slides,
        language=language,
        image_width=image_width,
        image_height=image_height,
    )


# =============================================================
# LINE版: 結果カルーセル 用テンプレート
# 診断確定後に表示する「タイプ発表→根拠→解決策→CTA」等のカード群。
# タイプごとに複数枚組・複数タイプ分を生成する（診断カルーセルの表紙/設問とは別の参照画像セット）。
# =============================================================

RESULT_CARD_WITH_REF_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
添付の参照画像と同じデザインスタイル・レイアウト・配色・装飾で、診断結果カードを作成してください。

【最重要原則】
参照画像のスタイル（背景・カード・色・フォント・装飾）を完全にコピーすること。
これは「{type_name}」タイプの結果カルーセル、全{total_cards}枚のうちの{card_position}枚目（役割: {card_role}）。
同じタイプ内の{total_cards}枚で完全にトーンを統一すること。

{color_instruction}

== このカードの役割 ==
{card_role}

== 差し替えるテキスト内容 ==
{card_text}

== 厳守ルール ==
- 上記のテキストの構造（チェックリスト☑・矢印図式→・成分リスト✓等の記号）をそのまま維持して描画
- 参照画像にない要素は描画しない
- テキストは{language}のみ
"""


RESULT_CARD_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
LINE診断の結果カード（「{type_name}」タイプ）を作成してください。
これは全{total_cards}枚のうちの{card_position}枚目（役割: {card_role}）です。同じタイプ内で同じデザイントーンを保ってください。

{color_instruction}

== このカードの役割 ==
{card_role}

== テキスト内容 ==
{card_text}

== 画面構成 ==
- 上部または中央にこのカードの主題（タイプ名・見出し等）
- 本文はチェックリスト☑・矢印図式→・成分リスト✓等、テキスト内の記号構造に沿ったレイアウトで配置
- 下部にCTA（ボタン等）があればそれも描画

== 全テキスト ==
{language}で記述。太めのゴシック体。視認性最優先。
"""


def render_result_card_prompt(
    card_role: str,
    card_text: str,
    type_name: str,
    card_position: int,
    total_cards: int,
    site_colors: dict | None = None,
    language: str = "Japanese",
    has_reference_images: bool = False,
    image_width: int = 1080,
    image_height: int = 1080,
    accent_color: str | None = None,
) -> str:
    """結果カルーセルの1枚分（タイプ内の1カード）の生成プロンプトを組み立てる"""
    colors = dict(site_colors or {})
    if accent_color:
        colors["accent_color"] = accent_color

    if has_reference_images:
        color_instruction = _build_line_color_instruction(colors, minimal=True)
        return RESULT_CARD_WITH_REF_TEMPLATE.format(
            color_instruction=color_instruction,
            type_name=type_name,
            card_role=card_role,
            card_text=card_text,
            card_position=card_position,
            total_cards=total_cards,
            language=language,
            image_width=image_width,
            image_height=image_height,
        )
    color_instruction = _build_line_color_instruction(colors)
    return RESULT_CARD_TEMPLATE.format(
        color_instruction=color_instruction,
        type_name=type_name,
        card_role=card_role,
        card_text=card_text,
        card_position=card_position,
        total_cards=total_cards,
        language=language,
        image_width=image_width,
        image_height=image_height,
    )


# =============================================================
# LINE版: PR画像 用テンプレート
# 遷移先LPのトンマナにスタイル合わせ。参照画像はLPのog:image+主要img
# =============================================================

PR_PROPOSAL_TEMPLATE = """あなたはLINEマーケのコピーライターです。
遷移先LPの商品/サービスに合わせて、PRバナー文言案を1〜3パターン考えてください。

== 商品/サービス情報（任意入力）==
{product_info}

== LP情報（自動取得）==
- ページタイトル: {page_title}
- OG Title: {og_title}
- OG Description: {og_description}

== 出力形式（JSON配列で必ず出力） ==
```json
[
  {{
    "headline": "ヘッドライン（最大18文字。商品の核心メリットを1文で）",
    "subcopy": "サブコピー（最大20文字。ヘッドラインを補強）",
    "cta_text": "CTAボタン文言（最大10文字。例: 詳細を見る、無料で試す、公式サイトへ）",
    "visual_description": "主題ビジュアルの描写（商品やシーン）"
  }}
]
```

== ルール ==
- LPの遷移後にユーザーが「同じバナーだ」と認識できる連続性を意識
- ヘッドラインは商品の核心メリットをストレートに
- 抽象的な「最高」「最強」よりも具体的なベネフィットを優先
- CTAは行動を明確に促す動詞ベース
- 文言はオフィシャル画像として成立するトーンにする。「みんな」「絶対」などカジュアルな主語・話し言葉の断定は、言いたいことを保ったまま公式らしい言い回しに翻訳する（例:「みんな○○します」→「○○が基本です」）
"""


PR_GENERATION_WITH_REF_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
この画像は{image_width}×{image_height}pxで使用される。

添付の参照画像（遷移先LPの実画像）と同じビジュアルスタイル・配色・トンマナで、商品/サービスのPR用バナー画像を作成してください。

【最重要原則】
参照画像のテイスト（色・フォント・装飾・人物スタイル・カード形状・全体の雰囲気）を完全にコピーすること。
LP遷移後にユーザーが「このバナーで見たものだ」と認識できる視覚的連続性を保つこと。
参照画像に存在しないブランドロゴや別商品の写真を勝手に追加しないこと。

{color_instruction}

== 差し替えるテキスト内容 ==
- ヘッドライン（最も大きい）: 「{headline}」
- サブコピー: 「{subcopy}」
- CTAボタン: 「{cta_text}」
- 主題ビジュアル（中央 or 背景）: {visual_description}

== 厳守ルール ==
- 上記「」内の文字列を一字一句そのまま描画
- 参照画像のトンマナを最優先（テキストの装飾・配色も参照画像準拠）
- テキストは{language}のみ
- CTAボタンは必ず1つだけ描画（重複させない）
- 商品名やブランド名は「{headline}」「{visual_description}」に含まれる範囲のみ
"""


PR_GENERATION_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】

LINEマーケ用のPRバナー画像を作成してください。

== 配色 ==
{color_instruction}

== レイアウト（厳守） ==
画像サイズ: {image_width}×{image_height}px

上部:  [ヘッドライン]（最も大きい、画像高さの10%相当フォント）
中央上: [サブコピー]（画像高さの5%相当フォント）
中央:   [主題ビジュアル]（商品/シーン）
下部:   [CTAボタン]（テーマカラー塗り、白文字、角丸ピル型、1つだけ）

== テキスト内容 ==
- ヘッドライン: 「{headline}」
- サブコピー: 「{subcopy}」
- CTAボタン: 「{cta_text}」
- 主題ビジュアル: {visual_description}

== 厳守 ==
- 「はい/いいえ」型ではなく、行動を促す1つのボタンのみ
- テキストは{language}で記述、太めのゴシック体
"""


def render_pr_proposal_prompt(product_info: str, page_title: str = "",
                              og_title: str = "", og_description: str = "") -> str:
    """PR文言案提案プロンプトを生成"""
    return PR_PROPOSAL_TEMPLATE.format(
        product_info=product_info or "（特定なし。LP情報から推測）",
        page_title=page_title or "（取得失敗 or 未取得）",
        og_title=og_title or "（なし）",
        og_description=og_description or "（なし）",
    )


def render_pr_generation_prompt(
    pr_proposal: dict,
    site_colors: dict | None = None,
    language: str = "Japanese",
    has_reference_images: bool = False,
    image_width: int = 682,
    image_height: int = 1024,
) -> str:
    """PR生成プロンプトを組み立てる"""
    if has_reference_images:
        color_instruction = _build_line_color_instruction(site_colors, minimal=True)
        return PR_GENERATION_WITH_REF_TEMPLATE.format(
            color_instruction=color_instruction,
            headline=pr_proposal.get("headline", "").strip(),
            subcopy=pr_proposal.get("subcopy", "").strip(),
            cta_text=pr_proposal.get("cta_text", "").strip(),
            visual_description=pr_proposal.get("visual_description", "").strip(),
            language=language,
            image_width=image_width,
            image_height=image_height,
        )
    color_instruction = _build_line_color_instruction(site_colors)
    return PR_GENERATION_TEMPLATE.format(
        color_instruction=color_instruction,
        headline=pr_proposal.get("headline", "").strip(),
        subcopy=pr_proposal.get("subcopy", "").strip(),
        cta_text=pr_proposal.get("cta_text", "").strip(),
        visual_description=pr_proposal.get("visual_description", "").strip(),
        language=language,
        image_width=image_width,
        image_height=image_height,
    )


# =============================================================
# LINE版: PR画像 デュアル参照テンプレート
# デザイン参照画像（構造・レイアウト）+ LP参照画像（色・雰囲気）の役割分担
# =============================================================

PR_GENERATION_WITH_DUAL_REF_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】

添付の参照画像は **役割の違う2種類** が並んでいます。順番が重要：

【参照画像の役割分担（厳守）】
- 最初の {design_count} 枚 = **デザイン参照画像**（過去のヒットPR）
  → このバナーの構造・レイアウト・要素配置・テキストの並び・ボタンの形状・装飾パターンを完全にコピーする
  → 「どこに何があるか」「どんな構成か」は全部この画像群の通りに作る

- {tone_start} 枚目以降 = **LP雰囲気参照画像**（遷移先LPの実画像）
  → このバナーから **色味（配色パレット）・フォント感・写真トーン・全体の雰囲気** だけを抽出
  → デザイン参照の構造に、この色味・雰囲気を適用する
  → 商品ジャンルの世界観（化粧品・医療・etc）が伝わる質感を借りる

【最終結果のイメージ】
「過去のヒットPRと同じ構造（=ユーザーが反応するレイアウト）」を、
「遷移先LPと同じ色・雰囲気（=LP遷移後の視覚的連続性）」で塗り直したバナー。

【絶対やらないこと】
- デザイン参照画像の色をそのまま使う（色はLP参照優先）
- LP参照画像のレイアウト構造を真似る（構造はデザイン参照優先）
- デザイン参照やLP参照の元の文字・ロゴ・人物を勝手に残す（テキストは下記指定のみ）

{color_instruction}

== 差し替えるテキスト内容 ==
- ヘッドライン（最も大きい）: 「{headline}」
- サブコピー: 「{subcopy}」
- CTAボタン（必ず1つだけ）: 「{cta_text}」
- 主題ビジュアル（中央 or 背景）: {visual_description}

== 厳守ルール ==
- 上記「」内の文字列を一字一句そのまま描画
- 構造 = デザイン参照を完全コピー / 色味 = LP参照から借用
- テキストは{language}のみ
- CTAボタンは1つだけ。デザイン参照に複数あっても1つに統合
"""


def render_pr_generation_prompt_dual(
    pr_proposal: dict,
    design_count: int,
    tone_count: int,
    site_colors: dict | None = None,
    language: str = "Japanese",
    image_width: int = 682,
    image_height: int = 1024,
) -> str:
    """デザイン参照 + LP参照 のデュアル参照向け生成プロンプト"""
    color_instruction = _build_line_color_instruction(site_colors, minimal=True)
    return PR_GENERATION_WITH_DUAL_REF_TEMPLATE.format(
        color_instruction=color_instruction,
        headline=pr_proposal.get("headline", "").strip(),
        subcopy=pr_proposal.get("subcopy", "").strip(),
        cta_text=pr_proposal.get("cta_text", "").strip(),
        visual_description=pr_proposal.get("visual_description", "").strip(),
        language=language,
        image_width=image_width,
        image_height=image_height,
        design_count=design_count,
        tone_start=design_count + 1,
    )


# =============================================================
# LINE版 PRカルーセル（6-7枚セット）テンプレート群
# 1枚生成じゃなく「複数枚で1ストーリー」のPRカルーセル設計
# knowledge/pr-design-patterns.md の暗黙知を内蔵
# =============================================================

# PR-1〜N の役割定義（knowledge/pr-design-patterns.md ベース）
PR_ROLE_DEFINITIONS = {
    "introduction": {
        "label": "PR-1: 商材紹介（Attention）",
        "description": "商品/サービス名 + キャッチビジュアル + 権威性バッジ + おすすめポイント3項目",
        "content_keys": ["intro_header", "brand_name", "authority_badges", "key_points"],
    },
    "price": {
        "label": "価格訴求（Interest）",
        "description": "通常価格→値引き→特別価格、限定条件、送料・診察料の優位性",
        "content_keys": ["price_headline", "normal_price", "special_price", "discount_rate", "limited_terms"],
    },
    "mechanism": {
        "label": "効果メカニズム / 症状解説（Desire）",
        "description": "物販なら成分・実証データ。サービスなら症状分類+放置リスク+解決ベネフィット",
        "content_keys": ["mechanism_headline", "scientific_proof", "before_after", "benefit_chain"],
    },
    "social_proof": {
        "label": "社会的証明（Trust）",
        "description": "累計実績数 + 満足度% + 顧客口コミ2-3件（星5評価）",
        "content_keys": ["track_record", "satisfaction_rate", "testimonials"],
    },
    "comparison": {
        "label": "競合比較",
        "description": "他社との比較表で自社の優位性を直接示す",
        "content_keys": ["comparison_table", "self_advantages"],
    },
    "campaign": {
        "label": "キャンペーン詳細（Action）",
        "description": "期間限定 + 適用条件 + 緊急性煽り + 価格再掲",
        "content_keys": ["urgency", "conditions", "discount_recap"],
    },
    "risk_reversal": {
        "label": "懸念払拭（Risk Reversal）",
        "description": "金銭・痛み・羞恥心・効果への不安を1枚で解消（返金保証、分割払い、匿名配送、相談OK等）",
        "content_keys": ["concern", "solution", "guarantee"],
    },
}

# デフォルト枚数別の役割割当（6枚パターン）
PR_DEFAULT_ROLE_SETS = {
    6: ["introduction", "price", "mechanism", "social_proof", "campaign", "risk_reversal"],
    7: ["introduction", "price", "mechanism", "mechanism", "social_proof", "campaign", "risk_reversal"],
    5: ["introduction", "price", "mechanism", "social_proof", "campaign"],
    4: ["introduction", "price", "social_proof", "campaign"],
}


# ============================================
# Phase 1: デザイン参照画像セット → 構造抽出
# ============================================
PR_CAROUSEL_STRUCTURE_EXTRACTION_PROMPT = """添付の画像は、過去にコンバージョン率の高かったLINE誘導PRカルーセル（N枚で1セット）です。

これらの **デザイン構造・レイアウト・装飾パターン** を分析してください。

【重要前提】
- 添付画像はN枚で1ストーリーのカルーセル
- 各枚に役割がある（1枚目=商材紹介、2枚目=価格、3枚目=効果メカニズム/症状解説、4枚目=社会的証明、5枚目=キャンペーン詳細、6枚目=懸念払拭 などの順序が典型）
- 役割は順序入れ替わることもある（物販系とサービス系で違う）

【記述ルール】
- 元の文字内容（商品名・価格・コピー・社名）は一切含めない
- 構造（どこに何があるか）と装飾（リボン・カード・色感・形状）だけを抽出
- 全枚共通の「骨格」（左上ロゴ位置・右上[PR]ラベル・最下部CTAボタン形状）を抽出
- 各枚固有の構造（特徴リスト形・比較表形・口コミカード形・価格表形・症状分類形 等）も抽出

【出力形式（JSON必須）】
```json
{
  "set_summary": "カルーセル全体の構造サマリー（50〜120字）",
  "total_pages": N,
  "common_skeleton": {
    "top_left_position": "ブランドロゴの配置と装飾",
    "top_right_position": "【PR】ラベル等の配置",
    "bottom_cta": "CTAボタンの形状・色・装飾（角丸/矢印/補助コピー等）",
    "color_palette_role": "メインカラー/アクセントカラー/ベース色の使い分けパターン"
  },
  "pages": [
    {
      "page_no": 1,
      "estimated_role": "introduction / price / mechanism / social_proof / comparison / campaign / risk_reversal",
      "layout_type": "ヒーロー型 / ポイント列挙型 / 比較表型 / 口コミカード型 / 価格表型 / 症状分類型 / ベネフィット連鎖型 など",
      "key_visual": "中央に来るビジュアル要素（商品/人物/数字/比較表/イラスト 等）",
      "text_blocks": [
        {"position": "上部 / 中央 / 下部", "type": "見出し / 帯ナビ / 強調数字 / リスト項目 / 説明文", "size_relative": "大/中/小", "decoration": "装飾"}
      ],
      "decorative_elements": ["リボン", "星マーク", "チェックマーク", "吹き出し", "比較矢印", "etc"]
    }
  ]
}
```

文字内容は絶対に含めず、「構造」と「装飾パターン」のみを抽出してください。
"""


# ============================================
# Phase 2: 商材情報 → 全N枚分の役割別文言設計
# ============================================
PR_CAROUSEL_CONTENT_PROPOSAL_TEMPLATE = """あなたはLINEマーケのPRカルーセル設計者です。
商材情報と各枚の役割をもとに、{total_pages}枚分の文言設計を一括で提案してください。

== 商材情報 ==
{product_info}

== LP情報（自動取得） ==
- ページタイトル: {page_title}
- OG Title: {og_title}
- OG Description: {og_description}

== 各枚の役割（順序固定）==
{role_list}

== 出力形式（JSON必須）==
```json
{{
  "set_concept": "カルーセル全体のコンセプト（30〜80字）",
  "common_cta": {{
    "main_text": "全枚共通のCTAボタン文言（最大10文字。行動敷居を低く: 例「ご相談だけでもOK」「お得に試してみる」「無料で見てみる」）",
    "sub_copy": "ボタン上の補助コピー（最大20文字）"
  }},
  "slides": [
    {{
      "page_no": 1,
      "role": "introduction",
      "headline": "メイン見出し（最大25文字）",
      "sub_headline": "サブ見出し（任意・最大20文字）",
      "key_elements": [
        "要素1（例: 商品名・権威性・特徴）",
        "要素2",
        "要素3"
      ],
      "visual_description": "中央に描くビジュアル（商品/人物/数字/比較等を具体的に）"
    }}
  ]
}}
```

== 役割別のコンテンツ指針（厳守）==

- **introduction**: 「あなたにおすすめな〇〇は」型のヘッダ + ブランド名 + おすすめポイント3項目（チェックリスト形式）
- **price**: 通常価格→値引き→特別価格、送料・診察料の優位性、限定枠（「毎月N名様」「期間限定」）
- **mechanism**: 物販=成分名・由来・実証データ・ベネフィット連鎖 / サービス系=症状分類（〇〇型/△△型）+ 放置リスク + 解決ベネフィット
- **social_proof**: 累計利用者数（具体的数字）+ 満足度% + 顧客口コミ2-3件（星5評価、年齢・性別付き）
- **comparison**: 3社比較表（自社+他社2-3）or 「一般〇〇 vs 自社」の優位性比較
- **campaign**: 「今だけ」「期間限定」緊急性 + 適用条件3つ + 価格再掲（PR-2より具体的に）
- **risk_reversal**: 想定される不安（「まとまったお金がない」「効果なかったら」「他人に知られたくない」等）→ 解決策（分割払い・返金保証・匿名配送・相談OK等）

== 全体ルール ==
- 各枚で役割を重複させない（価格訴求とキャンペーン詳細は混同しない）
- 共通CTAは「行動敷居を低く」: "購入"・"決定" は禁止、"見てみる"・"相談する"・"試す" を使う
- 数字には必ず単位をつける（「100万件」「90%」「4,000回」）
- 強調すべき部分は「色変え想定」のキーワードとして key_elements に明記
"""


# ============================================
# Phase 3: 各枚の生成プロンプト（構造+LP色味+役割記述）
# ============================================
PR_CAROUSEL_SLIDE_GENERATION_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
全{total_pages}枚のPRカルーセルのうち {page_no} 枚目を作成します。

【添付の参照画像の役割（厳守。順番が極めて重要）】
- **最初の1枚 = デザイン参照画像**（過去のヒットPRカルーセルの{page_no}枚目）
  → このレイアウト・構造・装飾・要素配置・テキストブロックの位置を **完全コピー**
  → 「どこに、何が、どんなサイズ・装飾で配置されているか」は全てこの1枚目の通りに作る
  → ただし: **元の文字内容（商品名・コピー・社名・実績数字）は無視**
  → ただし: **元の人物・商品・ロゴは無視**（位置はそのまま使い、中身を下記指定に差し替える）

- **残りの {tone_count} 枚 = LP参照画像**（遷移先LPの実画像）
  → **色味（配色パレット）・フォント感・写真トーン・全体の雰囲気** のみ抽出
  → これらの画像のレイアウトには一切影響されない（レイアウトは1枚目を厳守）

【最終結果のイメージ】
「1枚目（デザイン参照）のレイアウトと装飾」に「LP参照の色味」を塗って、
テキスト内容と中央のビジュアルを下記指定に差し替えた1枚を作る。

【絶対やらないこと】
- 1枚目の元の文字をそのまま残す
- 1枚目の元の人物・商品・ロゴをそのまま残す
- 残り{tone_count}枚（LP参照）のレイアウトに引っ張られる
- 上記指定文字以外のテキストを描画する
- CTAボタンを複数描画する
- 関係ない人物・商品を追加する

== このセット全体の共通骨格（全{total_pages}枚で統一）==
{common_skeleton}

{color_instruction}

== このスライド（{page_no}/{total_pages}枚目）の役割 ==
**役割**: {slide_role_label}
**目的**: {slide_role_description}

== 描画するテキスト内容（厳守。これ以外の文字は一切描画しない）==
- ヘッドライン（最も大きい）: 「{headline}」
{sub_headline_line}
== 主要要素（このスライドで強調する内容）==
{key_elements_text}

== 中央のメインビジュアル（1枚目の人物・商品の位置に差し替えて配置）==
{visual_description}

== CTAボタン（1枚目のCTA位置に、形状もコピーして配置）==
- メインテキスト: 「{cta_main}」
- 補助コピー: 「{cta_sub}」

== 厳守ルール ==
- テキストは{language}のみ
- 「{page_no}/{total_pages}」のページナンバリングは描画しない
"""


def render_pr_carousel_structure_prompt() -> str:
    """デザイン参照画像群から構造抽出するプロンプト"""
    return PR_CAROUSEL_STRUCTURE_EXTRACTION_PROMPT


def render_pr_carousel_content_proposal(
    product_info: str,
    role_list_for_pages: list[str],
    total_pages: int,
    page_title: str = "",
    og_title: str = "",
    og_description: str = "",
) -> str:
    """商材情報 + 各枚の役割 → 全枚文言設計プロンプト"""
    role_lines = []
    for i, role_key in enumerate(role_list_for_pages, 1):
        role_def = PR_ROLE_DEFINITIONS.get(role_key, {"label": role_key, "description": ""})
        role_lines.append(f"  PR-{i}: {role_def['label']} - {role_def['description']}")
    role_list = "\n".join(role_lines)

    return PR_CAROUSEL_CONTENT_PROPOSAL_TEMPLATE.format(
        product_info=product_info or "（特定なし。LP情報から推測）",
        page_title=page_title or "（未取得）",
        og_title=og_title or "（なし）",
        og_description=og_description or "（なし）",
        total_pages=total_pages,
        role_list=role_list,
    )


def render_pr_carousel_slide_generation(
    page_no: int,
    total_pages: int,
    slide_role: str,
    slide_data: dict,
    common_skeleton_desc: str,
    layout_structure_desc: str,
    common_cta: dict,
    site_colors: dict | None = None,
    language: str = "Japanese",
    image_width: int = 682,
    image_height: int = 1024,
    tone_count: int = 0,
) -> str:
    """1枚分のスライド生成プロンプトを組み立てる

    Args:
        tone_count: LP参照画像の枚数（プロンプト内で「残り{tone_count}枚」と表記）
        - layout_structure_desc は使われなくなった（旧版互換のためパラメータは残置）
    """
    role_def = PR_ROLE_DEFINITIONS.get(slide_role, {})
    role_label = role_def.get("label", slide_role)
    role_desc = role_def.get("description", "")

    color_instruction = _build_line_color_instruction(site_colors, minimal=True)

    sub_headline = slide_data.get("sub_headline", "").strip()
    sub_headline_line = f"- サブ見出し: 「{sub_headline}」" if sub_headline else ""

    key_elements = slide_data.get("key_elements", [])
    if key_elements:
        key_elements_text = "\n".join(f"  - {e}" for e in key_elements)
    else:
        key_elements_text = "  （特になし。ヘッドラインのみ）"

    return PR_CAROUSEL_SLIDE_GENERATION_TEMPLATE.format(
        page_no=page_no,
        total_pages=total_pages,
        tone_count=tone_count,
        common_skeleton=common_skeleton_desc or "（参照画像のトンマナに従う）",
        color_instruction=color_instruction,
        slide_role_label=role_label,
        slide_role_description=role_desc,
        headline=slide_data.get("headline", "").strip(),
        sub_headline_line=sub_headline_line,
        key_elements_text=key_elements_text,
        visual_description=slide_data.get("visual_description", "").strip(),
        cta_main=common_cta.get("main_text", "").strip(),
        cta_sub=common_cta.get("sub_copy", "").strip(),
        language=language,
        image_width=image_width,
        image_height=image_height,
    )


# =============================================================
# 商材情報の構造化抽出（PRページStep3自動化用）
# LP本文 + og_* メタ情報 → 商品名/特徴/価格/キャンペーン/懸念 をJSON化
# =============================================================

PRODUCT_INFO_EXTRACTION_TEMPLATE = """以下はLINE誘導先のLP（ランディングページ）の情報です。
LPのテキスト情報 **と添付されたLP画像** の両方から商材情報を読み取り、PRバナー生成に使えるよう構造化してください。

【重要】価格・キャンペーン・実績数字・権威性バッジは、HTMLテキストに無くても
**添付画像（LPのファーストビュー等）に焼き込まれている**ことが多い。
画像内の文字（「初回○○円」「○%OFF」「累計○万個」「楽天1位」等）を必ず読み取ること。

== LP情報（テキスト）==
- ページタイトル: {page_title}
- OG Title: {og_title}
- OG Description: {og_description}

== LP本文（抜粋）==
{body_text}

== 出力形式（JSON必須）==
```json
{{
  "product_name": "商品名（最も推されている主商品）",
  "product_category": "商品カテゴリ（例: 化粧品、サプリ、医療サービス、転職サービス）",
  "key_features": [
    "特徴1（例: 化粧下地・ファンデ・日焼け止め一体型）",
    "特徴2",
    "特徴3"
  ],
  "price_normal": "通常価格（円表記。不明なら空文字）",
  "price_special": "特別価格・初回価格（円表記。不明なら空文字）",
  "discount_rate": "値引き率（例: 20%OFF、半額）",
  "campaign": "キャンペーン詳細（送料無料・期間限定・初回限定 等）",
  "social_proof": "実績数字（累計販売数・満足度・利用者数 等）",
  "authority_badges": [
    "権威性バッジ（楽天N冠、医師監修、機能性表示食品 等）"
  ],
  "guarantees": "返金保証・解約しやすさ・サポート体制等の安心要素",
  "likely_concerns": [
    "想定される顧客の懸念1（例: 厚塗り感が出ないか）",
    "懸念2（例: 自分の肌色に合うか）"
  ],
  "target_persona": "ターゲット層の推測（年代・性別・状況）"
}}
```

== 抽出ルール ==
- LP本文・OG情報から **明示的に書かれている情報** だけを抽出
- 不明な項目は空文字 "" にする（憶測で埋めない）
- 価格は税込/税抜の明記があればそのまま含める
- 数字は単位付きで（「100万件」「90%」「¥2,200」）
- 重要キーワードは元のLPの表現をそのまま使う（「秒速美肌」等のフックワードを保持）
"""


def render_product_info_extraction_prompt(
    page_title: str = "",
    og_title: str = "",
    og_description: str = "",
    body_text: str = "",
) -> str:
    """LP情報から商材情報を構造化抽出するプロンプト"""
    return PRODUCT_INFO_EXTRACTION_TEMPLATE.format(
        page_title=page_title or "（未取得）",
        og_title=og_title or "（なし）",
        og_description=og_description or "（なし）",
        body_text=body_text[:6000] if body_text else "（本文取得失敗。og情報だけで判断してください）",
    )


def format_product_info_for_proposal(product_info: dict) -> str:
    """抽出した商材情報を、文言設計プロンプト用のテキスト形式に整形する"""
    lines = []
    if product_info.get("product_name"):
        lines.append(f"商品名: {product_info['product_name']}")
    if product_info.get("product_category"):
        lines.append(f"カテゴリ: {product_info['product_category']}")
    features = product_info.get("key_features") or []
    if features:
        lines.append("主要訴求軸:")
        for f in features:
            lines.append(f"  - {f}")
    if product_info.get("price_normal") or product_info.get("price_special"):
        price_parts = []
        if product_info.get("price_normal"):
            price_parts.append(f"通常 {product_info['price_normal']}")
        if product_info.get("price_special"):
            price_parts.append(f"初回/特別 {product_info['price_special']}")
        if product_info.get("discount_rate"):
            price_parts.append(f"値引 {product_info['discount_rate']}")
        lines.append(f"価格: {' / '.join(price_parts)}")
    if product_info.get("campaign"):
        lines.append(f"キャンペーン: {product_info['campaign']}")
    if product_info.get("social_proof"):
        lines.append(f"実績/社会的証明: {product_info['social_proof']}")
    badges = product_info.get("authority_badges") or []
    if badges:
        lines.append(f"権威性バッジ: {', '.join(badges)}")
    if product_info.get("guarantees"):
        lines.append(f"安心要素: {product_info['guarantees']}")
    concerns = product_info.get("likely_concerns") or []
    if concerns:
        lines.append("想定される顧客の懸念:")
        for c in concerns:
            lines.append(f"  - {c}")
    if product_info.get("target_persona"):
        lines.append(f"ターゲット層: {product_info['target_persona']}")
    return "\n".join(lines) if lines else "（LP情報から商材情報を抽出できませんでした）"


# =============================================================
# 全画像生成に自動適用されるハードルール（2026-07-06 ren恒久指示）
# 経路: openai_image_client / gemini_client の generate_image() が
# 送信直前に必ず append する。テンプレ個別対応ではなく物理注入。
# 背景: マンジャロ値下げショット実戦(t143)での差し戻し3点＋
#       参照文言混入バグ(t137)の実戦対策4点を仕組み化したもの。
# =============================================================

LINE_IMAGE_HARD_RULES = """
【システム共通ルール（全画像生成に自動適用・違反禁止）】
1. 参照画像は配色・装飾・レイアウトの雰囲気（スタイル）だけを真似ること。参照画像内の文言・価格・キャンペーン内容を新しい画像に描かない
2. 画像に描く文字は、上の指示で明示されたテキストだけ。一字一句正確に。指示にない文字・帯・キャッチコピーを追加しない
3. 「今だけ」「期間限定」「在庫僅少」「残りわずか」など期間・在庫の限定を匂わせる表現は、指示に明記されていない限り文字でも装飾でも入れない
4. CTAボタン・行動喚起バッジは指示で明示された場合のみ描く。指示にないボタン風装飾を追加しない（カルーセルの中間カードには原則入れない）
5. イラストは参照画像のタッチに厳密に合わせ、シリーズ内で統一する。参照がない場合は「細い単色アウトライン＋フラットな少色ベタ塗り・点目の顔」のシンプル線画にする。水彩風・アニメ顔・リアル調・厚塗りなど"AI生成っぽい"タッチは禁止
"""


def append_hard_rules(prompt: str) -> str:
    """画像生成プロンプトの末尾にハードルールを注入する（重複注入は防止）"""
    if "【システム共通ルール" in prompt:
        return prompt
    return prompt.rstrip() + "\n" + LINE_IMAGE_HARD_RULES


# =============================================================
# JSON構造化プロンプト（2026-07-13 ren採用手法）
# 出典: X @gibkun1「JSON形式でプロンプトを出力してから画像生成すると
# クオリティが段違いに上がる」→ 薬MCVリテP4/P5で実証（注記5行の高密度
# レイアウトでも崩れゼロ・一発合格）。以後の画像生成はJSON形式を推奨。
# =============================================================

def render_json_image_prompt(spec: dict) -> str:
    """画像仕様dict（task/style/layout_zones/text_elements/prohibitions等）を
    JSON構造化プロンプトに変換する。text_elementsのtextは一字一句描画される前提で書くこと。"""
    import json as _json
    return (
        "以下のJSON仕様に厳密に従って画像を1枚生成してください。"
        "text_elementsの文字列は一字一句正確に描画し、それ以外の文字は描かない。"
        "prohibitionsは絶対遵守。\n\n"
        + _json.dumps(spec, ensure_ascii=False, indent=2)
    )


# =============================================================
# LINE配信カードの標準生成レシピ（2026-07-13 ren確定・固定）
# JSON構造化プロンプト＋design_details（装飾密度）＋人間実物参照の3点セット。
# 実績: 薬MCVリテ5枚が全て一発合格（高密度レイアウト崩れゼロ・「手抜き感」解消）。
# 使い方:
#   spec = build_line_card_spec(text_elements=[...], illustration_spec="...")
#   prompt = render_json_image_prompt(spec)
#   client.generate_image(prompt, reference_images=[人間実物のみ], aspect_ratio="2:3")
# =============================================================

LINE_CARD_SPEC_BASE = {
    "task": "LINE配信用リッチメッセージ画像（縦長・日本語・1枚単発）",
    "reference_usage": "参照画像は人間のデザイナー制作の実物。配色・タイポグラフィ・イラストタッチ・紙面の密度感を忠実に再現する。参照内の文言・価格は絶対に描かない",
    "style": {
        "palette": "コーラルピンク×クリーム系のやさしい暖色",
        "tone": "押さない・売り込まない。ただし紙面はプロのデザイナーが作り込んだ密度にする（余白だらけの簡素なスライドにしない）",
        "illustration": "繊細な線・丁寧な陰影の線画（参照の人物タッチに厳密に合わせる）。私服。点目の記号顔・水彩・アニメ顔・リアル調は禁止",
    },
    "design_details": [
        "ドン見出しのキーワードに蛍光マーカー風の下線 or 色付き帯（参照実物のタイポ装飾を踏襲）",
        "白カードは角丸＋ごく淡いソフトシャドウ＋左端に丸いアイコンバッジ（テーマに合う線画アイコン）",
        "セクションの区切りに点線 or 細い仕切り線",
        "背景の上下に淡い曲線・波形のあしらい（コーラル淡色。キラキラは禁止）",
        "キーワード・数字はコーラル太字で部分強調（1ゾーン1箇所まで）",
        "余白が大きく空くレイアウトは禁止。要素間の間隔を詰めて情報密度を出す",
    ],
    "layout_zones": {
        "top_25pct": "ドン見出し（結論1本・最大2行・最大級の文字サイズ）",
        "middle_55pct": "主役コンテンツ＋サブコピー",
        "bottom_20pct": "控えめなCTA帯（細い帯＋テキスト1行＋『＞』。緑の大ボタン・バッジは禁止）",
    },
    "prohibitions": [
        "text_elements以外の文字を描かない（単語の重複・勝手な帯・キャッチコピー追加禁止）",
        "キラキラ・十字の輝きを背景に散らさない",
        "警告色（赤・黄の強い面）を使わない",
        "ビフォーアフター的な体型描写・体重数値を描かない",
        "「今だけ」等の期間・在庫の限定表現を入れない",
        "手指は解剖学的に正しく（左右の手を間違えない・指5本）",
    ],
}


def build_line_card_spec(text_elements, illustration_spec="", extra_prohibitions=None, overrides=None):
    """標準レシピにカード固有の要素を合成してJSON仕様dictを返す。
    text_elements: [{"zone","role","text","style"}] のリスト（textは一字一句描画される）
    illustration_spec: このカードのイラスト指示（シリーズ内でシーンは1枚ごとに変えること）
    extra_prohibitions: 案件固有の禁止（例: クーポン券風デザイン禁止）
    overrides: layout_zones等を差し替えたい場合のdict（例: カルーセルCTAカードのフッター）"""
    import copy
    spec = copy.deepcopy(LINE_CARD_SPEC_BASE)
    spec["text_elements"] = text_elements
    if illustration_spec:
        spec["illustration_spec"] = illustration_spec
    if extra_prohibitions:
        spec["prohibitions"] = spec["prohibitions"] + list(extra_prohibitions)
    if overrides:
        spec.update(overrides)
    return spec
