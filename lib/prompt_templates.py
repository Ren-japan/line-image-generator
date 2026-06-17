"""
3層プロンプトテンプレート
Layer1: デザインシステム（サイト固有のスタイル定義）
Layer2: 画像案提案（記事分析→3-5案のJSON出力）
Layer3: 画像生成（Layer1 + 構成説明を結合）
"""

from __future__ import annotations

# =============================================================
# Layer 1: デザインシステムプロンプト
# サイト設定のパラメータで動的に生成される
# =============================================================
DESIGN_SYSTEM_TEMPLATE = """あなたはプロのUIデザイナーです。
以下のデザインシステムを厳密に適用して画像を生成してください。

== ブランド ==
言語: {language}
※サイト名・ブランド名（{brand_name}）を画像内に表示してはならない。画像内テキストは読者にとって有益な情報のみにすること。

== 配色パレット ==
- 背景色: {background_color}
- メイン色: {primary_color}
- サブ色: {secondary_color}
- アクセント色（強調）: {accent_color}
- テキスト色: {text_color}
- 警告・重要色: {danger_color}
※上記以外の色の使用は禁止

== イラストレーション・タッチ ==
- スタイル: {illustration_style}
- 線の太さ・質感: {line_weight}
- 人物造形: {character_style}
- 塗り: {fill_style}
- 背景描写: 人物の背景（部屋、家具、床の線）は一切描かない

== UI・レイアウト構造 ==
- カード: {card_style}
- フォント: {font_family}相当の、癖のないモダンゴシック体。細字・丸文字は禁止
- 余白: {spacing}
- ブロック構造: 「小見出し帯 → イラスト → 説明文」の縦積みを基本とする

== 禁止事項 ==
{prohibited_elements}

== 追加スタイルノート ==
{additional_notes}

== 参照画像から抽出したデザイン特徴（最重要・厳守） ==
{ref_image_analysis}
"""

# =============================================================
# Layer 2: 画像案提案プロンプト
# 記事本文を分析して3-5個の画像案をJSON形式で提案する
# =============================================================
IMAGE_PROPOSAL_TEMPLATE = """あなたはSEO記事の画像設計ディレクターです。
あなたの仕事は「記事の構造整理」ではなく「読者の体験設計」です。

各H2セクションに来た読者が「今、何を不安に思っているか」「何がわかれば安心するか」を考え、
その読者の気持ちに寄り添う画像案を3〜5個設計してください。

== 記事本文 ==
{article_text}

== 最重要原則：読者ファーストの画像設計 ==
画像を設計する際、必ず以下の順序で考えること：

1. **読者の気持ちを想像する**: このH2に来た読者は今何を知りたい？何が不安？
2. **何を見せたら解決するか考える**: 比較表？具体的なモノの画像？ステップ？数字？
3. **記事の主題を視覚的に表現する**: 記事がリカバリーウェアの話ならリカバリーウェアを着た人を描く。料理の話なら料理を描く。読者が「この記事は自分に関係ある」と一瞬で感じるビジュアルにする
4. **最後に構図を決める**: 内容が決まってから、それを最も伝えやすい構図を選ぶ

== 画像案数の決定ルール ==
- 入口H2（導入・全体像）：必ず1つ。読者が「この記事は自分向けだ」と感じる画像
- 実務ブロックH2（具体手順・比較・選び方）：必ず1つ。読者の判断を助ける画像
- ケース系H2（例外・応用・パターン）：必要なら1つ
- 合計3〜5案（5案を超えない）

== 構図の選び方（内容に合わせて選ぶ） ==
使用可能な構図: {layout_types}

- 分類型（横3 or 横4 or 2×2）: 「3つのメリット」「4つのポイント」など項目を並列で見せたい時
- 比較型（横並び2〜3列）: 製品比較、A vs B、ビフォーアフター
- フロー型（横ステップ）: 手順・流れ・プロセスを見せる時のみ
- ピラミッド型: 重要度の階層がある時のみ

※構図は内容から自然に決まる。先に構図を決めてから内容を当てはめるのは禁止

== 各ブロックのイラスト指示ルール ==
- 記事の主題に関連する具体的なモノ・人・場面を描くこと
- 抽象的なアイコン（丸に￥マーク等）より、具体的なイラスト（実際のウェアを着た人等）を優先
- 読者が「あ、これのことか」と直感でわかるビジュアルにする

== 1画像あたりの情報量（厳守：文字化け防止のため文字数を抑える） ==
画像内テキストは最小限にすること。AI画像生成は文字が多いと描画が崩れる。
- 見出し: 最大8文字以内
- 説明文: 最大20文字×2行まで（それ以上は削る）
- 横3: 各カード見出し+説明1〜2行
- 横4: 各カード見出し+説明1行のみ
- 2×2: 各カード見出し+説明1〜2行
- 比較型: 左右で同じ情報量。各項目は見出し+1行
- フロー型: 各ステップ見出し+説明1行のみ（文字が多いと崩れるため最も注意）
- 画像全体で合計100文字以内を目安とする

== アスペクト比の推奨 ==
情報量が多い場合は縦長アスペクト比を推奨する。JSONに "recommended_aspect_ratio" で指定すること。
- ブロック2〜3個で情報少なめ → "16:9"（横長）
- ブロック3〜4個で標準量 → "4:3"（やや横長）
- ブロック4個以上 or 比較型で項目多め → "3:4"（やや縦長）
- 比較型で左右に3項目以上ずつ → "9:16"（縦長）

== トンマナ ==
- ブランドトーン: {brand_tone}
- 画像サイズ: {image_width}×{image_height}px の画角で潰れない情報量を維持

== 出力形式（JSON配列で必ず出力） ==
```json
[
  {{
    "placement": "H2: [見出しテキスト]",
    "reader_mindset": "このH2に来た読者が今思っていること・知りたいこと",
    "purpose": "この画像で読者の何を解決するか",
    "conclusion": "画像を見た読者が得る結論（1文）",
    "layout_type": "分類型|比較型|フロー型|ピラミッド型",
    "layout_reason": "読者にとってこの構図がベストな理由",
    "blocks": [
      {{"heading": "見出し", "description": "説明文", "illustration": "描くべき具体的なイラスト内容（記事の主題に関連するモノ・人・場面）"}}
    ],
    "recommended_aspect_ratio": "16:9|4:3|3:4|9:16（情報量に応じて選択）",
    "composition_description": "空間配置の説明のみ（下記ルール厳守）"
  }}
]
```

== composition_description の記述ルール（厳守） ==
書くこと：
- 要素の空間配置（「上部にタイトル帯、下部に横3カードを等間隔で配置」等）
- グリッド構造（「2×2グリッド」「横並び3列」等）
- 各ブロック内に描くイラストの配置（「カード上部にイラスト、下部にテキスト」等）

**絶対に書かない**こと：
- サイト名・ブランド名 → 画像内に入れない
- 色の指示 → デザインシステムが管理
- イラストのスタイル/タッチ → 参照画像が管理
- 雰囲気/印象の形容 → ブランドトーンが管理

== 禁止事項 ==
- サイト名・ブランド名を画像タイトルに入れること（読者にとって無意味）
- 表の丸写し、本文の長文転載
- 抽象的なアイコンだけで記事主題のビジュアルがない画像
- 構図を先に決めてから内容を当てはめること
- composition_descriptionにスタイル/色/雰囲気を記述すること
"""

# =============================================================
# Layer 3: 画像生成プロンプト
# デザインシステム + 構成説明を結合して最終プロンプトを組み立てる
# =============================================================
IMAGE_GENERATION_TEMPLATE = """{design_system_prompt}

== 画像生成リクエスト ==
以下の内容で{layout_type}のインフォグラフィック画像を作成してください。

【読者の状況】{reader_mindset}
【この画像の役割】{purpose}
【読者が得る結論】{conclusion}

== コンテンツブロック ==
{blocks_text}

== 構成イメージ ==
{composition_description}

== イラスト指示 ==
- 各ブロックには記事の主題に関連する具体的なイラストを必ず描くこと
- 抽象的なアイコン（丸に記号）ではなく、読者が「あ、これのことか」と直感でわかる具体的なモノ・人・場面を描く
- 人物イラストを描く場合は、参照画像と同じタッチ・頭身・表情で描くこと

== テキスト描画ルール（厳守：文字化け防止） ==
- 画像内テキストは最小限にすること。文字数が多いと描画が崩れる
- 各見出しは8文字以内、説明文は20文字×2行以内
- 画像全体で合計100文字以内
- 文字サイズは十分に大きく、判読可能なサイズで配置
- 文字が重なったり、はみ出したりしないよう余白を十分に確保
- 長い文は短く言い換えてでも文字数を削ること

== 技術要件 ==
- アスペクト比: {aspect_ratio}
- デザインシステムの配色を厳守
- 視覚的階層: タイトル > メインコンテンツ > 補足情報
- 画像内のテキストはすべて{language}で記述
- サイト名・ブランド名は画像内に表示しない
"""

# =============================================================
# 参照画像あり時の短縮プロンプト
# スタイルは全て参照画像に任せ、テキストでは「何を描くか」だけ伝える
# =============================================================
IMAGE_GENERATION_WITH_REF_TEMPLATE = """添付の参照画像と同じビジュアルスタイルで、{layout_type}のインフォグラフィック画像を作成してください。
スタイル（色・線・塗り・人物タッチ・カード形状・余白）はすべて参照画像を模倣すること。

【この画像の目的】{purpose}
【読者が得る結論】{conclusion}

{blocks_text}

【構成】{composition_description}

- 各ブロックのイラストは大きく、具体的に描く（アイコンではなく人物・モノの場面描写）
- テキストは{language}で記述。画像内テキストは合計100文字以内
- サイト名・ブランド名は画像内に入れない
"""

# =============================================================
# MV（メインビジュアル/アイキャッチ）用テンプレート
# テンプレート型: 構造・配置・装飾を完全固定、中身だけ変わる
# =============================================================

# デフォルトMVデザイン仕様書（色を柔軟にし、構造・比率・装飾のみ精密に記述）
# 参照画像5枚の共通パターンを抽出: 色はバラバラだが構造は統一
MV_DESIGN_SPEC_DEFAULT = """== 背景 ==
- 上部約65%: テーマカラーのグラデーション（左上から右下へ、濃→やや薄）
- 下部約35%: 白（またはごく薄いグレー）
- 境界: なめらかなグラデーション遷移（ハードな直線分割は避ける）

== 煽りテキスト（hook_text） ==
- 位置: 左上、画像上端から約8%の位置
- フォントサイズ: 画像高さの約4%
- スタイル: テーマカラー系の角丸ピル（pill型背景）に白文字
- ピルの角丸: 完全な丸み（radius 50%）
- ピルの内側余白: 上下2%, 左右4%程度

== メインタイトル（main_title） ==
- 位置: 左寄せ、画像左端から8%、上端から約25%
- フォントサイズ: 画像高さの約11%（最も大きい、超太字）
- 装飾:
  - 文字色: 白
  - 縁取り: テーマカラーの二重アウトライン（内側2px + 外側4px程度）
  - ドロップシャドウ: 右下方向に軽いシャドウ（opacity 30%程度）
- 占有幅: 画像幅の55〜60%（右側の人物と重ならない）

== サブタイトル（subtitle） ==
- 位置: メインタイトル直下、同じ左マージン
- フォントサイズ: 画像高さの約5%（太字）
- 装飾:
  - 文字色: アクセントカラー（暖色系推奨: 赤・オレンジ等）
  - 縁取り: 白の細い縁取り（1〜2px）
  - ドロップシャドウ: メインタイトルと同様

== 帯テキスト（band_text） ==
- 位置: サブタイトルの下、上端から約60%
- 帯の幅: 画像幅の55〜60%、高さ: 画像高さの約7%
- 帯の色: 白（または非常に薄い色）
- テキスト色: ダークグレー〜黒（コントラスト確保）
- フォントサイズ: 画像高さの約3.5%
- 角丸: 4px程度

== 補足テキスト（supplement_text） ==
- 位置: 帯の下、左寄せ
- フォントサイズ: 画像高さの約3%
- 文字色: ダークグレー（#2C2C2C程度）
- 装飾: なし（シンプル）

== メイン人物 ==
- 位置: 画像右側、右端から5%内側
- サイズ: 高さは画像高さの約75%、幅は画像幅の約35%
- 配置: 下揃え（足が画像下端に接する or わずかに切れる）
- スタイル: フォトリアリスティック（写真風・実写風）
- 背景: なし（人物のみ切り抜き風に配置、透過的に背景に溶け込む）

== 全体のレイアウトバランス ==
- 左側テキスト領域: 画像幅の約65%
- 右側人物領域: 画像幅の約35%
- テキストと人物は重ならない
- 上下左右マージン: 画像サイズの約8%
- テキストの縦方向の並び: 煽り → メインタイトル → サブタイトル → 帯 → 補足（上から順に等間隔ではなく、メインタイトル周辺に余白を多めにとる）

== テキストサイズ階層（厳守） ==
メインタイトル(11%) >> サブタイトル(5%) > 煽り(4%) ≈ 帯(3.5%) > 補足(3%)
※ メインタイトルとそれ以外のサイズ差を明確にすること（2倍以上の差）

== フォント ==
- すべて太めのゴシック体（Noto Sans JP Bold相当）
- メインタイトルは Extra Bold / Black ウェイト
"""

# MV用 Layer2: テンプレートの各スロットに入れる「中身」を提案
MV_PROPOSAL_TEMPLATE = """あなたはSEO記事のMV（メインビジュアル/アイキャッチ画像）のコピーライターです。

記事のタイトルと本文から、MV画像に入れるテキスト・ビジュアル要素の案を1〜3パターン考えてください。

== 記事タイトル ==
{article_title}

== 記事本文（概要把握用） ==
{article_text}

== MV画像のレイアウト構造（固定。変更不可） ==
以下の構造は固定です。あなたが考えるのは各スロットに入る「中身」だけです。

┌─────────────────────────────────────┐
│ [煽りテキスト]（左上・小さめ）        │
│                                     │
│ [メインタイトル]（左寄せ・超大きい）   │
│                                     │
│ [サブタイトル]（左寄せ・大きい・赤）   │
│                                     │
│ ┌帯─────────────────┐              │
│ │[帯テキスト1]        │ [メイン人物] │
│ └────────────────────┘（右側・大きい）│
│ [補足テキスト]（左下）                │
└─────────────────────────────────────┘
背景: 上部カラーグラデーション → 下部ホワイト

== 各スロットの役割 ==
- 煽りテキスト: 好奇心を刺激する短いフレーズ（5〜10文字。例: "今話題の", "〇〇で人気"）
- メインタイトル: 商品名やキーワード（2〜8文字。例: "リライブシャツ", "BAKUNE"）
- サブタイトル: 読者の疑問や関心事（8〜15文字。例: "本当に効果はある？", "口コミ・評判を調査！"）
- 帯テキスト1: 記事のベネフィットを一文で（10〜20文字。例: "リアルな口コミを調査！"）
- 補足テキスト: 記事でわかることの補足（15〜25文字。例: "期待できる効果や安く買う方法まで紹介"）
- メイン人物: MVに描く人物の説明（例: "スマホで口コミを見ている若い女性", "パジャマを着てリラックスしている人"）

== 出力形式（JSON配列で必ず出力） ==
```json
[
  {{
    "hook_text": "煽りテキスト",
    "main_title": "メインタイトル",
    "subtitle": "サブタイトル",
    "band_text": "帯テキスト1",
    "supplement_text": "補足テキスト",
    "person_description": "メイン人物の具体的な描写"
  }}
]
```

== ルール ==
- 各テキストは指定文字数の範囲内に収めること
- メインタイトルは記事の主題となる商品名・キーワードにする
- サブタイトルは読者の疑問形にすると効果的
- 帯テキスト1はベネフィットを端的に伝える
- メイン人物は記事のターゲット読者を想起させる人物にする
- テキストの内容は記事の本文に基づくこと（創作しない）
"""

# MV用 Layer3（参照画像あり・デザイン仕様書あり）: 参照画像 + 仕様書の二重指示
# 仕様書 = 手動記述 or Gemini自動分析結果。色はサイトカラーパレットで上書き。
MV_GENERATION_WITH_SPEC_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
この画像は{image_width}×{image_height}pxで使用される。すべてのテキスト・人物・装飾をこのキャンバスサイズに最適化して配置すること。

添付の参照画像と同じレイアウト構造・テキスト装飾・配置バランスで、テキスト内容と人物だけを差し替えたMV画像を作成してください。

== 重要: 配色の優先順位 ==
以下の配色ルールは、デザイン仕様書内の色指定（HEXコード）より**優先**する。
仕様書内の具体的な色コード（#36B0B0等）はあくまで参考値とし、実際の配色は以下に従うこと。

{color_instruction}

== デザイン仕様書（レイアウト・装飾・比率） ==
※ 以下の仕様書のうち、色以外の情報（位置%、サイズ%、装飾スタイル、配置ルール）は厳守すること。
{design_spec}

== 差し替えるテキスト内容 ==
- 左上の小さいテキスト: 「{hook_text}」
- メインタイトル（最も大きい文字）: 「{main_title}」
- サブタイトル（メインタイトルの下）: 「{subtitle}」
- 帯の上のテキスト: 「{band_text}」
- 下部の補足テキスト: 「{supplement_text}」
- 右側の人物: {person_description}

テキストはすべて{language}で記述。指定文字列のみ描画し、余計な文字を追加しない。
"""

# MV用 Layer3（参照画像あり・デザイン仕様書なし）: 参照画像 + サイト別補強ヒント
# Trial 16: 3層アーキテクチャ（参照画像主役 + 構造変数 + 条件付きoverrides）
#
# 設計思想:
#   Layer A: 参照画像がスタイルの主役（フォント・色・装飾は参照画像に委ねる）
#   Layer B: 構造系変数（person_crop等）でGeminiが苦手な空間配置のみ補強
#   Layer C: style_overrides（オプション）で参照画像だけでは伝わらない例外ルールのみ上書き
#
# JMROのように参照画像5枚+構造変数のみで80点超が出るケースでは
# overridesは空になり、「完全コピー」のみで矛盾ゼロのプロンプトになる。
#
# configの mv_style_hints に以下のキー:
#   [構造系 - 常に使用]
#   person_position    — 人物の配置位置（右側/左側）
#   person_size        — 人物の大きさ（高さ何%）
#   person_crop        — 人物のはみ出し方（右端で切れてよい等）
#   person_bottom      — 人物の足元処理（下端に接する等）
#   text_person_layer  — テキストと人物の前後関係（前面/背面）
#   background_style   — 背景のスタイル（白ベース+装飾 等）
#   supplement_style   — 補足テキストの表示スタイル
#   [装飾系 - オプション。overridesとして条件付き注入]
#   style_overrides    — 参照画像コピーへの上書きルール（文字列。なければ注入しない）
MV_GENERATION_WITH_REF_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
この画像は{image_width}×{image_height}pxで使用される。すべてのテキスト・人物・装飾をこのキャンバスサイズに最適化して配置すること。

添付の参照画像のデザインを完全にコピーして、テキスト内容と人物だけを差し替えた画像を生成してください。

【最重要原則】
参照画像のレイアウト構造・テキスト配置順序・フォント・色・装飾・背景・カード形状を完全にコピーすること。
参照画像に存在する要素だけを描画し、存在しない要素は絶対に追加しないこと。

{color_instruction}

== 人物 ==
- {person_crop}
- 配置: {person_position}
- 大きさ: {person_size}
- 足元: {person_bottom}
- {text_person_layer}
- 人物: {person_description}

== 背景 ==
{background_style}

== テキスト要素（文字列だけ差し替え。位置・順序・装飾は参照画像と完全に同じに） ==
{text_slots}
{style_overrides}
【テキストルール】
- 上記「」内の文字列を一字一句そのまま描画する。文言を変えたり省略したり追加しない
- テキストの配置順序は参照画像と同じにする（参照画像で上にあるものは上に、下にあるものは下に）
- 参照画像に存在しないテキスト要素は描画しない
- テキストは{language}のみ
"""

# MV用 Layer3（参照画像あり・スロット構造検出済み）: 超シンプル版
# mv_slot_structure がある場合のみ使用。参照画像に全て委ね、テキスト内容だけ差し替える。
MV_GENERATION_WITH_SLOT_STRUCTURE_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
この画像は{image_width}×{image_height}pxで使用される。すべてのテキスト・人物・装飾をこのキャンバスサイズに最適化して配置すること。

添付の参照画像のデザインを完全にコピーして、テキスト内容と人物だけを差し替えた画像を生成してください。

参照画像のレイアウト・色・フォント・装飾・背景・カード形状を全てコピーする。
参照画像に存在する要素だけを描画する。存在しない要素は追加しない。

{color_instruction}

== 差し替えるテキスト ==
{text_slots}

== 差し替える人物 ==
{person_description}

上記「」内の文字列を一字一句正確に描画する。それ以外のテキストは追加しない。テキストは{language}のみ。
{style_overrides}"""

# MV用 Layer3（参照画像なし）: テンプレート型フルプロンプト
# 色はサイトカラーパレット or AI自動判断。構造・比率・装飾のみ固定。
MV_GENERATION_TEMPLATE = """【出力画像サイズ: {image_width}×{image_height}px】
この画像は{image_width}×{image_height}pxで使用される。すべてのテキスト・人物・装飾をこのキャンバスサイズに最適化して配置すること。

SEO記事のMV（メインビジュアル/アイキャッチ）画像を作成してください。

== 配色ルール ==
{color_instruction}

== レイアウト（厳守） ==
画像サイズ: {image_width}×{image_height}px（{aspect_ratio}）
- 左側65%: テキスト要素すべて（上から煽り→タイトル→サブタイトル→帯→補足）
- 右側35%: メイン人物
- 上下左右マージン: 画像サイズの8%
- 背景: 上部65%はテーマカラー系のグラデーション → 下部35%は白（またはごく薄い色）

┌─────────────────────────────────────┐
│ [煽りテキスト] (ピル型の小さいラベル) │
│                                     │
│ [メインタイトル]（超大きい太字）      │
│     → 画像高さの11%相当フォント      │
│     → 白抜き+テーマカラーの二重縁取り │
│                                     │
│ [サブタイトル]（大きめ太字）          │
│     → 画像高さの5%相当フォント        │  [メイン人物]
│     → アクセントカラー or 白          │  → 右側配置
│                                     │  → 高さ75%
│ ┌帯─────────────────┐              │  → 幅35%
│ │[帯テキスト]         │              │  → フォトリアル
│ └────────────────────┘              │
│ [補足テキスト]（小さめ・控えめ）      │
│     → 画像高さの3%相当フォント        │
└─────────────────────────────────────┘

== メイン人物 ==
{person_description}
- フォトリアリスティックな人物として描く（イラストではなく写真風）
- 右側に配置、画像高さの約75%のサイズ
- 背景はなし（人物のみ切り抜き風に配置）

== テキスト装飾ルール（色名は配色ルールに従う） ==
- メインタイトル: 最も目立つ。白い文字+テーマカラーの太い縁取り（二重）+ドロップシャドウ
- サブタイトル: アクセントカラーの太字+白の縁取り+ドロップシャドウ
- 帯テキスト: 白帯（または淡色帯）+濃色テキスト、帯幅は画像幅の55〜60%
- 煽りテキスト: テーマカラーの角丸ピル背景+白文字、画像高さの4%相当フォント
- 補足テキスト: ダークグレー系、装飾なし
- すべて{language}の太めのゴシック体で描画

== テキスト階層（サイズ比 厳守） ==
メインタイトル(11%) > サブタイトル(5%) > 煽り/帯(4%) > 補足(3%)
※ パーセンテージは画像高さに対するフォントサイズ比

== 技術要件 ==
- アスペクト比: {aspect_ratio}
- 全テキストは{language}で記述
- 文字が崩れないよう、各テキストは短く保つ
- 視認性最優先：テキストが背景に埋もれないこと
"""


# 参照画像なし時に使う従来のスタイルトランスファー指示（フォールバック）
STYLE_TRANSFER_PREFIX = """【最重要指示】
この指示に添付されている参照画像は、出力すべきデザインスタイルの見本です。
以下の全要素において、参照画像のビジュアルスタイルを厳密に模倣してください：

- 背景の色味・質感を参照画像と同一にする
- カード/ボックスの角丸・枠線・影の有無を参照画像と完全一致させる
- 見出し帯の色・形状・テキスト色を参照画像に合わせる
- イラストの線の太さ・均一さ・ベクター感を参照画像と同一にする
- 人物の頭身・顔の描き方（目・口の表現）を参照画像に揃える
- 塗りスタイル（フラット/グラデーション/影の有無）を参照画像に完全一致させる
- 色使いを参照画像の配色パレットに限定する（参照画像にない色は使わない）
- 余白の取り方・要素間の間隔を参照画像に揃える

参照画像のスタイルと、下記のデザインシステム指示が矛盾する場合は、参照画像のビジュアルを優先してください。

---
"""


def render_design_system(config: dict) -> str:
    """サイト設定からデザインシステムプロンプトを生成"""
    return DESIGN_SYSTEM_TEMPLATE.format(
        brand_name=config.get("brand_name", ""),
        language=config.get("language", "Japanese"),
        background_color=config.get("background_color", "#FFFFFF"),
        primary_color=config.get("primary_color", "#3B82F6"),
        secondary_color=config.get("secondary_color", "#10B981"),
        accent_color=config.get("accent_color", "#F59E0B"),
        text_color=config.get("text_color", "#1F2937"),
        danger_color=config.get("danger_color", "#E74A3B"),
        illustration_style=config.get("illustration_style", "flat minimal"),
        line_weight=config.get("line_weight", "2.8〜3.2px統一"),
        character_style=config.get("character_style", "4頭身前後、記号的表現"),
        fill_style=config.get("fill_style", "フラット塗り"),
        card_style=config.get("card_style", "白背景 + 角丸28px"),
        font_family=config.get("font_family", "Noto Sans JP Medium"),
        spacing=config.get("spacing", "広めに均等"),
        prohibited_elements=config.get("prohibited_elements", ""),
        additional_notes=config.get("additional_notes", ""),
        ref_image_analysis=config.get("ref_image_analysis", "（参照画像なし）"),
    )


def render_proposal_prompt(article_text: str, config: dict) -> str:
    """記事本文とサイト設定から画像案提案プロンプトを生成"""
    image_size = config.get("image_sizes", {}).get("article", {})
    return IMAGE_PROPOSAL_TEMPLATE.format(
        article_text=article_text,
        layout_types="、".join(config.get("layout_types", [
            "分類型", "比較型", "フロー型", "ピラミッド型", "アイコン軽量型"
        ])),
        brand_tone=config.get("brand_tone", "professional and approachable"),
        image_width=image_size.get("width", 886),
        image_height=image_size.get("height", 600),
    )


def _build_blocks_text(proposal: dict) -> str:
    """proposalのblocksをテキスト化する共通処理"""
    blocks = proposal.get("blocks", [])
    if blocks and isinstance(blocks[0], dict):
        lines = []
        for b in blocks:
            line = f"- 【{b.get('heading', '')}】{b.get('description', '')}"
            illust = b.get("illustration", "")
            if illust:
                line += f"　→ イラスト: {illust}"
            lines.append(line)
        return "\n".join(lines)
    return "\n".join(f"- {b}" for b in blocks)


def render_mv_proposal_prompt(
    article_title: str,
    article_text: str,
    mv_slot_structure: dict | None = None,
) -> str:
    """記事タイトルと本文からMV画像案提案プロンプトを生成。

    mv_slot_structure がある場合、検出されたスロットのみ生成させる。
    """
    if not mv_slot_structure or "slots" not in mv_slot_structure:
        # フォールバック: 従来の5スロット版
        return MV_PROPOSAL_TEMPLATE.format(
            article_title=article_title,
            article_text=article_text[:3000],
        )

    # スロット構造対応版: 検出されたスロットのみ生成させる
    slots = mv_slot_structure["slots"]
    absent = mv_slot_structure.get("absent_slots", [])

    # スロット説明を組み立て
    role_labels = {
        "hook": ("煽りテキスト", "好奇心を刺激する短いフレーズ（5〜10文字）"),
        "main_title": ("メインタイトル", "記事の主題となる商品名・キーワード（2〜15文字）"),
        "subtitle": ("サブタイトル", "読者の疑問や関心事（8〜15文字）"),
        "band_text": ("帯テキスト", "記事のベネフィットを一文で（10〜20文字）"),
        "supplement_text": ("補足テキスト", "記事でわかることの補足（15〜25文字）"),
    }

    slot_lines = []
    json_keys = []
    for s in slots:
        role = s["role"]
        label, guide = role_labels.get(role, (role, ""))
        slot_lines.append(f"- {label}（{role}）: {guide}")
        json_keys.append(f'    "{role}": "{label}"')

    slot_section = "\n".join(slot_lines)
    json_fields = ",\n".join(json_keys)

    absent_section = ""
    if absent:
        absent_labels = [role_labels.get(a, (a, ""))[0] for a in absent]
        absent_section = (
            "\n※ 以下のスロットはこのMVデザインに存在しない。生成してはならない:\n"
            + "\n".join(f"- {lbl}" for lbl in absent_labels)
        )

    prompt = f"""あなたはSEO記事のMV（メインビジュアル/アイキャッチ画像）のコピーライターです。

記事のタイトルと本文から、MV画像に入れるテキスト・ビジュアル要素の案を1〜3パターン考えてください。

== 記事タイトル ==
{article_title}

== 記事本文（概要把握用） ==
{article_text[:3000]}

== このMVに存在するテキストスロット ==
{slot_section}
{absent_section}

== 出力形式（JSON配列で必ず出力） ==
```json
[
  {{
{json_fields},
    "person_description": "メイン人物の具体的な描写"
  }}
]
```

== ルール ==
- 上記スロットに対応するテキストのみ生成する。存在しないスロットのキーは出力に含めない
- 各テキストは指定文字数の範囲内に収めること
- メインタイトルは記事の主題となる商品名・キーワードにする
- メイン人物は記事のターゲット読者を想起させる人物にする
- テキストの内容は記事の本文に基づくこと（創作しない）
"""
    return prompt


def _build_mv_color_instruction(site_colors: dict | None = None, minimal: bool = False) -> str:
    """サイトカラーパレットからMV用の配色指示テキストを動的生成する。

    サイトカラーを配色のベース（アンカー）として渡す。
    参照画像が複数ありトーンがバラバラな場合でも、サイトカラーで配色を安定させる。

    minimal=True の場合（参照画像あり時）:
        テーマカラーのみ送る。accent_color等は参照画像に委ねる。
        accent_colorを送ると参照画像のスタイルと矛盾してタイトル色が狂う原因になる。
    """
    if site_colors:
        primary = site_colors.get("primary_color", "")

        if minimal:
            # 参照画像が主役の場合: テーマカラーだけで配色をアンカー
            lines = [
                "== 配色の基準 ==",
                f"- このサイトのテーマカラー: {primary}" if primary else "",
                "- それ以外の色は参照画像に従うこと",
            ]
        else:
            accent = site_colors.get("accent_color", "")
            bg = site_colors.get("background_color", "")
            text_c = site_colors.get("text_color", "")
            danger = site_colors.get("danger_color", "")
            lines = [
                "== 配色パレット（このサイトのブランドカラー。配色の基準として使うこと） ==",
                f"- テーマカラー: {primary}" if primary else "",
                f"- アクセントカラー: {accent or danger}" if (accent or danger) else "",
                f"- 背景ベース色: {bg}" if bg else "",
                f"- テキスト基本色: {text_c}" if text_c else "",
                "- 上記カラーパレットのトーンに合った配色で画像全体を統一すること",
            ]
        return "\n".join(line for line in lines if line)
    else:
        return (
            "== 配色 ==\n"
            "固定色の指定なし。参照画像がある場合は参照画像の配色に従うこと。\n"
            "参照画像がない場合は記事のテーマ・雰囲気に合った配色をAIが自動判断すること。"
        )


def _get_default_style_hints() -> dict:
    """mv_style_hintsが未設定の場合のデフォルト値（汎用的な指示）。

    Trial 16: 3層アーキテクチャ版
    構造系7変数のみ。フォント・色・装飾は参照画像に完全に委ねる。
    style_overrides は空文字列がデフォルト（= 参照画像コピーのみ、上書きなし）。

    デフォルト値は「参照画像のレイアウトを忠実にコピーする」ための汎用ガイド。
    参照画像から人物配置・背景・テキスト関係を自動的に読み取らせる。
    サイト固有のmv_style_hintsが設定されていればそちらが優先される。
    """
    return {
        "person_position": "参照画像と同じ位置・向き・ポーズで配置する。参照画像で人物が右側なら右側、左側なら左側に配置",
        "person_size": "参照画像と同じ大きさ・比率にする。参照画像で人物が大きければ大きく、小さければ小さく",
        "person_crop": "参照画像で人物が画像端で切れている場合、同じように切れてよい。全身が収まっている場合は全身を描く",
        "person_bottom": "参照画像と同じ足元の処理にする。下端で切れていれば切れてよい",
        "text_person_layer": "参照画像と同じ前後関係にする。テキストが人物の上に重なっているなら重ねる。分離しているなら分離する",
        "background_style": "参照画像と同じ背景スタイルを忠実に再現する。色・グラデーション・装飾パターン・カード型背景の有無をすべて参照画像からコピー",
        "supplement_style": "参照画像の補足テキストと同じスタイル。補足テキストがなければ描画しない",
        "style_overrides": "",  # 空 = 上書きなし。参照画像を完全コピー。
    }


def render_mv_generation_prompt(
    design_system: str,
    mv_proposal: dict,
    aspect_ratio: str,
    language: str = "Japanese",
    has_reference_images: bool = False,
    mv_design_analysis: str = "",
    site_colors: dict | None = None,
    mv_design_spec: str = "",
    mv_style_hints: dict | None = None,
    mv_slot_structure: dict | None = None,
    image_width: int | None = None,
    image_height: int | None = None,
) -> str:
    """MV画像案（テンプレート型）からMV生成プロンプトを組み立てる"""

    # サイズのデフォルト値
    _w = image_width or 1200
    _h = image_height or 630

    # 参照画像がある場合
    if has_reference_images:
        hook_text = mv_proposal.get("hook_text", "").strip()
        main_title = mv_proposal.get("main_title", "").strip()
        subtitle = mv_proposal.get("subtitle", "").strip()
        band_text = mv_proposal.get("band_text", "").strip()
        supplement_text = mv_proposal.get("supplement_text", "").strip()
        person_description = mv_proposal.get("person_description", "")
        text_params = dict(
            person_description=person_description,
            language=language,
            image_width=_w,
            image_height=_h,
        )

        # 手動デザイン仕様書がある場合 → 参照画像 + 仕様書 + 配色指示
        if mv_design_spec:
            color_instruction = _build_mv_color_instruction(site_colors)
            return MV_GENERATION_WITH_SPEC_TEMPLATE.format(
                design_spec=mv_design_spec,
                color_instruction=color_instruction,
                hook_text=hook_text,
                main_title=main_title,
                subtitle=subtitle,
                band_text=band_text,
                supplement_text=supplement_text,
                **text_params,
            )

        # V2: スロット構造検出済み → 超シンプルテンプレート
        # 参照画像に全て委ね、テキスト内容と人物だけ差し替える
        if mv_slot_structure and "slots" in mv_slot_structure:
            color_instruction = _build_mv_color_instruction(site_colors, minimal=True)
            # スロット構造からテキストスロットを組み立て
            text_lines = []
            for slot in mv_slot_structure["slots"]:
                role = slot["role"]
                value = mv_proposal.get(role, "").strip()
                if value:
                    desc = slot.get("description", role)
                    text_lines.append(f"- 「{value}」→ {desc}")
            text_slots = "\n".join(text_lines)
            # style_overrides（オプション）
            hints = mv_style_hints if mv_style_hints else {}
            raw_overrides = hints.get("style_overrides", "")
            if raw_overrides:
                style_overrides = (
                    "\n== 参照画像の補正ルール ==\n"
                    f"{raw_overrides}\n"
                )
            else:
                style_overrides = ""
            return MV_GENERATION_WITH_SLOT_STRUCTURE_TEMPLATE.format(
                color_instruction=color_instruction,
                text_slots=text_slots,
                person_description=person_description,
                language=language,
                style_overrides=style_overrides,
                image_width=_w,
                image_height=_h,
            )

        # Trial 16: 3層アーキテクチャ（V1フォールバック）
        #   Layer A: 参照画像（主役）
        #   Layer B: 構造系変数（人物配置・背景パターン）
        #   Layer C: style_overrides（オプション。参照画像で伝わらない例外ルールのみ）
        defaults = _get_default_style_hints()
        hints = mv_style_hints if mv_style_hints else defaults
        # 参照画像が主役 → カラーパレットは最小限（テーマカラーのみ）
        # accent_color等を送ると参照画像と矛盾してタイトル色が狂う
        color_instruction = _build_mv_color_instruction(site_colors, minimal=True)

        # style_overrides: 空なら注入しない。値があれば「上書きルール」として追加
        raw_overrides = hints.get("style_overrides", defaults["style_overrides"])
        if raw_overrides:
            style_overrides = (
                "\n== 参照画像の補正ルール（以下は参照画像のコピーに上書きする例外ルール） ==\n"
                f"{raw_overrides}\n"
            )
        else:
            style_overrides = ""

        # テキストスロットを動的組み立て: 空のスロットはプロンプトに含めない
        # 装飾指示は全て「参照画像と同じ」に委ねる（サイト固有の装飾ワードを混在させない）
        supplement_style = hints.get("supplement_style", defaults["supplement_style"])
        text_lines = []
        if hook_text:
            text_lines.append(f"- 「{hook_text}」→ 参照画像の煽りテキストと同じ位置・サイズ・色・装飾で描画")
        if main_title:
            text_lines.append(f"- 「{main_title}」→ 参照画像のメインタイトルと同じ位置・サイズ・色・太さ・装飾で描画（最も大きい文字）")
        if subtitle:
            text_lines.append(f"- 「{subtitle}」→ 参照画像のサブタイトルと同じ位置・サイズ・色・装飾で描画")
        if band_text:
            text_lines.append(f"- 「{band_text}」→ 参照画像の帯テキストと同じスタイルの帯/ボックス内に描画（帯の色・角丸・影も同じに）")
        if supplement_text:
            text_lines.append(f"- 「{supplement_text}」→ {supplement_style}")
        text_slots = "\n".join(text_lines)

        return MV_GENERATION_WITH_REF_TEMPLATE.format(
            color_instruction=color_instruction,
            person_position=hints.get("person_position", defaults["person_position"]),
            person_size=hints.get("person_size", defaults["person_size"]),
            person_crop=hints.get("person_crop", defaults["person_crop"]),
            person_bottom=hints.get("person_bottom", defaults["person_bottom"]),
            text_person_layer=hints.get("text_person_layer", defaults["text_person_layer"]),
            background_style=hints.get("background_style", defaults["background_style"]),
            style_overrides=style_overrides,
            text_slots=text_slots,
            **text_params,
        )

    # 参照画像なし → フルプロンプト（配色はサイトカラー or AI自動判断）
    color_instruction = _build_mv_color_instruction(site_colors)
    return MV_GENERATION_TEMPLATE.format(
        hook_text=mv_proposal.get("hook_text", ""),
        main_title=mv_proposal.get("main_title", ""),
        subtitle=mv_proposal.get("subtitle", ""),
        band_text=mv_proposal.get("band_text", ""),
        supplement_text=mv_proposal.get("supplement_text", ""),
        person_description=mv_proposal.get("person_description", ""),
        aspect_ratio=aspect_ratio,
        language=language,
        color_instruction=color_instruction,
        image_width=_w,
        image_height=_h,
    )


def render_generation_prompt(
    design_system: str,
    proposal: dict,
    aspect_ratio: str,
    language: str = "Japanese",
    has_reference_images: bool = False,
) -> str:
    """デザインシステム + 画像案から最終生成プロンプトを組み立てる"""
    blocks_text = _build_blocks_text(proposal)

    # 参照画像がある場合 → 短縮プロンプト（スタイルは画像に任せる）
    if has_reference_images:
        return IMAGE_GENERATION_WITH_REF_TEMPLATE.format(
            layout_type=proposal.get("layout_type", ""),
            purpose=proposal.get("purpose", ""),
            conclusion=proposal.get("conclusion", ""),
            blocks_text=blocks_text,
            composition_description=proposal.get("composition_description", ""),
            language=language,
        )

    # 参照画像なし → 従来のフルプロンプト
    return IMAGE_GENERATION_TEMPLATE.format(
        design_system_prompt=design_system,
        layout_type=proposal.get("layout_type", ""),
        reader_mindset=proposal.get("reader_mindset", ""),
        purpose=proposal.get("purpose", ""),
        conclusion=proposal.get("conclusion", ""),
        blocks_text=blocks_text,
        composition_description=proposal.get("composition_description", ""),
        aspect_ratio=aspect_ratio,
        language=language,
    )


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
