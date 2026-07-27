"""
診断プロジェクトの構造化データ(lib/diagnosis_schema.py参照)から
「診断設計書」「デザイン依頼書」のmarkdownを自動生成するテンプレート。

house format(過去の`data/output/briefs/`実例)に合わせて:
  設計書   = 概要 → (商材マッピング) → (ものさし) → 診断フロー → 結果カード設計
             → (推奨カルーセル) → PU文言 → (通しシミュレーション) → (期待効果)
             → 残タスク → トンマナ
  依頼書   = 必要な画像一覧 → 全体フロー → ★設計書リンク → 各制作物の詳細
             (PUバナー→診断表紙→設問パネル→結果カルーセル→推奨カルーセル) → トンマナ → 残タスク

節は()内が任意(dataに無ければ丸ごとスキップ)。設計書の番号は実際に出力される
節だけを数えて連番になる(spec-image-generatorのschema駆動と同じ思想で、
「型(house format)は固定、中身だけ差し替わる」を文書生成に適用したもの)。
"""

from __future__ import annotations

from jinja2 import Environment

_ENV = Environment(trim_blocks=True, lstrip_blocks=True)

_CIRCLED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]


def _circled(n: int) -> str:
    return _CIRCLED[n - 1] if 1 <= n <= len(_CIRCLED) else f"({n})"


def _to_slash(text: str) -> str:
    """カード本文の改行を依頼書の表セル用に " / " へつぶす(連続空行は1つの区切りにまとめる)"""
    lines = [line.strip() for line in (text or "").split("\n") if line.strip()]
    return " / ".join(lines)


_ENV.filters["to_slash"] = _to_slash


DESIGN_DOC_TEMPLATE = _ENV.from_string(
    """# 診断設計書：{{ meta.title }}

作成日: {{ meta.created_date }}
{% if meta.type_label %}タイプ: {{ meta.type_label }}
{% endif -%}
{% if meta.genre %}ジャンル: {{ meta.genre }}
{% endif -%}
{% if meta.status %}ステータス: {{ meta.status }}
{% endif -%}
{% if meta.related_note %}
{{ meta.related_note }}
{% endif %}
{% if revision_notes %}
{% for note in revision_notes %}
**{{ note }}**
{% endfor %}
{% endif %}
---

## 概要

{{ overview }}

---
{% set ns = namespace(n=0) %}
{% if product_mapping %}
{% set ns.n = ns.n + 1 %}
## {{ ns.n }}. 商材マッピング

| {{ product_mapping.axis_labels|join(' | ') }} |
|{% for _ in product_mapping.axis_labels %}---|{% endfor %}

{% for row in product_mapping.rows %}
| {{ row.axis }} | {{ row.values|join(' | ') }} |
{% endfor %}
{% if product_mapping.notes %}
{{ product_mapping.notes }}
{% endif %}

---
{% endif %}
{% if monosashi %}
{% set ns.n = ns.n + 1 %}
## {{ ns.n }}. ものさしづくり

### 今のものさし（診断前のユーザーの認識）

```
{{ monosashi.before|join('\\n  ↓\\n') }}
```
{% if monosashi.real_voices %}
リアルボイス:
{% for v in monosashi.real_voices %}
- {{ v }}
{% endfor %}
{% endif %}

### 新しいものさし

```
{{ monosashi.after|join('\\n  ↓\\n') }}
```
{% if monosashi.hammer %}

### ハンマー

{{ monosashi.hammer }}
{% endif %}

---
{% endif %}
{% set ns.n = ns.n + 1 %}
## {{ ns.n }}. 診断フロー

{% if flow.system_note %}
**システム制約への対応:** {{ flow.system_note }}

{% endif %}
{% if flow.welcome_card %}
### ウェルカム + 診断スタートカード

```
{{ flow.welcome_card }}
```

---

{% endif %}
{% for q in flow.questions %}
### {{ q.id }}｜{{ q.text }}{% if q.branch_label %}（{{ q.branch_label }}）{% endif %}

{% if q.options %}
| 選択肢 | 回答{% if q.options[0].result %} | 確定タイプ{% endif %} |
|---|---{% if q.options[0].result %}|---|{% else %}|{% endif %}

{% for opt in q.options %}
| {{ opt.label }} | {{ opt.text }}{% if opt.result %} | {{ opt.result }}{% endif %} |
{% endfor %}
{% endif %}
{% for variant in q.variants %}

**{{ q.id }}-{{ _circled(loop.index) }}（{{ variant.condition }}）**

「{{ variant.text }}」

| 選択肢 | 回答 | 確定タイプ |
|---|---|---|
{% for opt in variant.options %}
| {{ opt.label }} | {{ opt.text }} | {{ opt.result }} |
{% endfor %}
{% endfor %}
{% if q.design_note %}

**設計意図:** {{ q.design_note }}
{% endif %}

---

{% endfor %}
{% set ns.n = ns.n + 1 %}
## {{ ns.n }}. 結果カード設計（{{ result_types|length }}タイプ）

{% for t in result_types %}
### タイプ：{{ t.name }}

```
{% for card in t.cards %}
Card{{ loop.index }}｜{{ card.role }}
{{ card.text }}
{% if not loop.last %}

{% endif %}
{% endfor %}
```

{% endfor %}
---
{% if recommendation_carousel %}
{% set ns.n = ns.n + 1 %}
## {{ ns.n }}. {{ recommendation_carousel.label }}

{% for t in recommendation_carousel.types %}
### {{ t.name }}

```
{% for card in t.cards %}
Card{{ loop.index }}｜{{ card.role }}
{{ card.text }}
{% if not loop.last %}

{% endif %}
{% endfor %}
```

{% endfor %}
---
{% endif %}
{% set ns.n = ns.n + 1 %}
## {{ ns.n }}. PU文言

{% for v in pu_copy.variants %}
**{{ v.label }}**
```
見出し: {{ pu_copy.title }}

コピー: {{ v.headline }}
{% if v.sub %}
/{{ v.sub }}
{% endif %}

[{{ v.buttons|join('] / [') }}]
```

{% endfor %}
{% if pu_copy.usage_note %}
**使い分け:** {{ pu_copy.usage_note }}

{% endif %}
---
{% if simulations %}
{% set ns.n = ns.n + 1 %}
## {{ ns.n }}. 通しシミュレーション

{% for s in simulations %}
### シミュレーション{{ _circled(loop.index) }} — {{ s.persona }}

{{ s.walkthrough }}

**評価:** {{ s.evaluation }}

---

{% endfor %}
{% endif %}
{% if expected_impact %}
{% set ns.n = ns.n + 1 %}
## {{ ns.n }}. 期待効果

{% if expected_impact.assumptions %}
{{ expected_impact.assumptions }}

{% endif %}
{% if expected_impact.rows %}
| 指標 | 保守 | 標準 | 上振れ |
|---|---|---|---|
{% for r in expected_impact.rows %}
| {{ r.label }} | {{ r.conservative }} | {{ r.standard }} | {{ r.upside }} |
{% endfor %}

{% endif %}
{% if expected_impact.notes %}
{{ expected_impact.notes }}

{% endif %}
---
{% endif %}

## 残タスク

{% for task in remaining_tasks %}
- {{ task }}
{% endfor %}

---

## トンマナ

| 項目 | 内容 |
|---|---|
| メインカラー | {{ tone.primary_color }} |
{% if tone.secondary_color %}
| サブカラー | {{ tone.secondary_color }} |
{% endif %}
{% if tone.background %}
| 背景 | {{ tone.background }} |
{% endif %}
{% if tone.illustration %}
| イラスト | {{ tone.illustration }} |
{% endif %}
| ターゲット | {{ tone.target }} |
"""
)


DESIGN_BRIEF_TEMPLATE = _ENV.from_string(
    """# デザイン依頼書：{{ meta.title }}

{% if revision_notes %}
**{{ revision_notes[0] }}**

{% endif %}
## 必要な画像一覧

| カテゴリ | 枚数 | 備考 |
| --- | --- | --- |
| PUバナー | {{ image_counts.pu_banner }}枚 | コピー{{ image_counts.pu_banner }}種（ABテスト用） |
{% if image_counts.cover %}
| 診断表紙（タイトル画面） | {{ image_counts.cover }}枚 | 「{{ meta.title }}」 |
{% endif %}
| 設問パネル | {{ image_counts.question_panels }}枚 | {{ flow.questions[0].id }}〜{{ flow.questions[-1].id }} |
| 結果カルーセル | **{{ image_counts.result_carousel }}枚** | {{ result_types|length }}枚 × {{ result_types|length }}タイプ（{{ result_types|map(attribute='name')|join('・') }}） |
{% if recommendation_carousel %}
| {{ recommendation_carousel.label }} | **{{ image_counts.recommendation_carousel }}枚** | {{ recommendation_carousel.types|length }}タイプ分 |
{% endif %}

**合計: {{ image_counts.total }}枚**{% if image_counts.note %}（{{ image_counts.note }}）{% endif %}

---

## 全体フロー

```jsx
[PU] バナー（コピー{{ image_counts.pu_banner }}種ABテスト）
  ↓
[友だち追加]
  ↓
[ウェルカム ＋ 診断スタートカード]
  ↓
{% for q in flow.questions %}
[{{ q.id }}] {{ q.text }}{% if q.branch_label %}（{{ q.branch_label }}）{% endif %}

{% endfor %}
  ↓
{% for t in result_types %}
  ├─ {{ t.name }} 結果カル（{{ t.cards|length }}枚）
{% endfor %}
{% if recommendation_carousel %}
  ↓
[{{ recommendation_carousel.label }}]
{% endif %}
  ↓
[CV]
```

---
{% if docs_url %}
## ★設計書

設計・文言・トンマナすべてまとまっているので、こちらご確認いただけると幸いです🙇‍♀️

**設計書:** {{ docs_url }}

見辛いなどあればテキストベースで出すのでお申し付けください🙏

---
{% endif %}
## 各制作物の詳細
{% set ns = namespace(n=0) %}
{% set ns.n = ns.n + 1 %}

### {{ _circled(ns.n) }} PUバナー（{{ pu_copy.variants|length }}枚）

| ヘッドライン | {{ pu_copy.title }} |
| --- | --- |
{% for v in pu_copy.variants %}
| {{ v.label }} | {{ v.headline }} |
{% endfor %}
{% if pu_copy.variants[0].sub %}

/{{ pu_copy.variants[0].sub }}
{% endif %}

ボタン: {% for b in pu_copy.variants[0].buttons %}「{{ b }}」{% if not loop.last %} / {% endif %}{% endfor %}

{% if pu_copy.usage_note %}

**使い分けの目安:** {{ pu_copy.usage_note }}
{% endif %}

---
{% if flow.welcome_card %}
{% set ns.n = ns.n + 1 %}

### {{ _circled(ns.n) }} 診断表紙（1枚）

```
{{ flow.welcome_card }}
```

---
{% endif %}
{% set ns.n = ns.n + 1 %}

### {{ _circled(ns.n) }} 設問パネル（{{ flow.questions|length }}枚）

| # | 質問 | 選択肢 |
| --- | --- | --- |
{% for q in flow.questions %}
| {{ q.id }}{% if q.branch_label %}（{{ q.branch_label }}）{% endif %} | {{ q.text }} | {% if q.options %}{% for opt in q.options %}{{ opt.label }}: {{ opt.text }}{% if opt.result %} →{{ opt.result }}{% endif %}{% if not loop.last %} ／ {% endif %}{% endfor %}{% endif %}{% for variant in q.variants %}**{{ q.id }}-{{ _circled(loop.index) }}（{{ variant.condition }}）:** {{ variant.text }}{% if not loop.last %}<br>{% endif %}{% endfor %} |
{% endfor %}

---
{% set ns.n = ns.n + 1 %}

### {{ _circled(ns.n) }} 結果カルーセル（{{ image_counts.result_carousel }}枚）

{% for t in result_types %}
**{{ t.name }}（{{ t.cards|length }}枚）**

| Card | 役割 | テキスト |
| --- | --- | --- |
{% for card in t.cards %}
| {{ loop.index }} | {{ card.role }} | {{ card.text|to_slash }} |
{% endfor %}

{% endfor %}
---
{% if recommendation_carousel %}
{% set ns.n = ns.n + 1 %}

### {{ _circled(ns.n) }} {{ recommendation_carousel.label }}（{{ image_counts.recommendation_carousel }}枚）

{% for t in recommendation_carousel.types %}
**{{ t.name }}**

| Card | 内容 |
| --- | --- |
{% for card in t.cards %}
| {{ loop.index }}｜{{ card.role }} | {{ card.text|to_slash }} |
{% endfor %}

{% endfor %}
---
{% endif %}

## トンマナ

メインカラー: {{ tone.primary_color }}
{% if tone.secondary_color %}
サブカラー: {{ tone.secondary_color }}
{% endif %}
{% if tone.background %}
背景: {{ tone.background }}
{% endif %}
{% if tone.type_accent_colors %}

タイプ別アクセントカラー:
{% for name, color in tone.type_accent_colors.items() %}
{{ name }}: {{ color }}
{% endfor %}
{% endif %}

---

## 残タスク

{% for task in remaining_tasks %}
- {{ task }}
{% endfor %}
"""
)


def render_design_doc(data: dict) -> str:
    """診断設計書のmarkdownを生成"""
    return DESIGN_DOC_TEMPLATE.render(_circled=_circled, **data)


def render_design_brief(data: dict) -> str:
    """デザイン依頼書のmarkdownを生成"""
    return DESIGN_BRIEF_TEMPLATE.render(_circled=_circled, **data)
