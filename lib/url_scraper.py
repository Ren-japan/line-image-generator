"""
URL（遷移先LP）から og:image・主要画像・メタ情報を取得し、参照画像セットとして使えるようにする。
LP のトンマナを参照画像方式で踏襲したPR画像を生成するための入力収集モジュール。
"""

from __future__ import annotations

import io
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from PIL import Image


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en;q=0.8",
}

_MIN_IMAGE_SIZE = 200  # この未満は ロゴ/アイコン とみなしてスキップ
_REQUEST_TIMEOUT = 15  # 秒


def fetch_lp_metadata(url: str) -> dict:
    """
    URLからLPメタ情報と画像URLリストを取得する。

    Returns:
        {
            "url": str,
            "page_title": str,
            "og_title": str,
            "og_description": str,
            "og_image_urls": list[str],   # og:image（1つ前提だが複数対応）
            "main_image_urls": list[str], # 本文中の主要 img タグ
            "twitter_image_urls": list[str],
        }
    """
    resp = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT, allow_redirects=True)
    resp.raise_for_status()
    # 正しい encoding を推定（meta charset がHTML内にある場合）
    if resp.encoding == "ISO-8859-1":
        resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")

    # og:* メタ情報を抽出
    og: dict[str, str] = {}
    for m in soup.find_all("meta"):
        prop = m.get("property") or m.get("name") or ""
        content = m.get("content") or ""
        if prop and content:
            og[prop] = content

    og_image_urls = []
    for k in ("og:image", "og:image:url", "og:image:secure_url"):
        v = og.get(k)
        if v:
            og_image_urls.append(_absolutize(v, url))

    twitter_image_urls = []
    for k in ("twitter:image", "twitter:image:src"):
        v = og.get(k)
        if v:
            twitter_image_urls.append(_absolutize(v, url))

    # 本文 img の収集（重複除去・上から順）
    main_image_urls: list[str] = []
    seen = set(og_image_urls + twitter_image_urls)
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not src:
            continue
        abs_src = _absolutize(src, url)
        if abs_src in seen:
            continue
        # データURIや明らかに小さいアイコンを軽くフィルタ
        if abs_src.startswith("data:"):
            continue
        seen.add(abs_src)
        main_image_urls.append(abs_src)

    return {
        "url": url,
        "page_title": (soup.title.string.strip() if soup.title and soup.title.string else ""),
        "og_title": og.get("og:title", "").strip(),
        "og_description": og.get("og:description", "").strip(),
        "og_image_urls": og_image_urls,
        "main_image_urls": main_image_urls,
        "twitter_image_urls": twitter_image_urls,
    }


def _absolutize(src: str, base_url: str) -> str:
    """src を絶対URLに変換"""
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("http://") or src.startswith("https://"):
        return src
    return urljoin(base_url, src)


def download_pil_images(urls: list[str], max_count: int = 5) -> list[Image.Image]:
    """
    画像URLリストをダウンロードしてPIL Imageリストに変換。
    取得失敗・小さすぎる画像はスキップ。最大 max_count 枚で打ち切り。
    """
    images: list[Image.Image] = []
    for u in urls:
        if len(images) >= max_count:
            break
        try:
            resp = requests.get(u, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content))
            # RGBA -> RGB（OpenAI入力はRGB前提）
            if img.mode != "RGB":
                img = img.convert("RGB")
            # 小さすぎる画像（ロゴ・favicon相当）はスキップ
            if min(img.size) < _MIN_IMAGE_SIZE:
                continue
            images.append(img)
        except Exception:
            # 単発失敗は無視して次に進む
            continue
    return images


def fetch_lp_reference_images(url: str, max_count: int = 5) -> tuple[list[Image.Image], dict]:
    """
    URLからLPを取得し、参照画像セット（PIL Image）と メタ情報 を返す。
    優先順位: og:image → twitter:image → 本文 img

    Returns:
        (images, metadata)
    """
    metadata = fetch_lp_metadata(url)
    # 優先順で結合
    all_urls = (
        metadata["og_image_urls"]
        + metadata["twitter_image_urls"]
        + metadata["main_image_urls"]
    )
    # 重複除去（順序保持）
    seen = set()
    deduped = []
    for u in all_urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    images = download_pil_images(deduped, max_count=max_count)
    return images, metadata
