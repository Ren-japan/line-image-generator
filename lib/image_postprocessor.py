"""
画像後処理モジュール（Pillow）
生成画像の余白トリミングを行う。
"""

from __future__ import annotations

import io
from PIL import Image
import numpy as np


def trim_whitespace(image: Image.Image, threshold: int = 245, padding: int = 10) -> Image.Image:
    """
    画像周囲の白/ほぼ白の余白を自動トリミング。

    Args:
        image: 入力画像
        threshold: この値以上のRGB値を「白」と判定（0-255）
        padding: トリミング後に残すパディング（px）
    """
    img_array = np.array(image.convert("RGB"))
    mask = np.any(img_array < threshold, axis=2)

    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)

    if not rows.any() or not cols.any():
        return image

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    # パディング追加
    h, w = img_array.shape[:2]
    rmin = max(0, rmin - padding)
    rmax = min(h - 1, rmax + padding)
    cmin = max(0, cmin - padding)
    cmax = min(w - 1, cmax + padding)

    return image.crop((cmin, rmin, cmax + 1, rmax + 1))


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """PIL Image → bytes変換"""
    buf = io.BytesIO()
    image.save(buf, format=format)
    return buf.getvalue()


def bytes_to_image(data: bytes) -> Image.Image:
    """bytes → PIL Image変換"""
    return Image.open(io.BytesIO(data))
