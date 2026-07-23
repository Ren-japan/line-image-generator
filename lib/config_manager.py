"""
ジャンル（案件）設定の管理（JSON永続化）
ブランド名・カラーパレット・参照画像（PU/PR/カルーセル）を管理する。
"""

from __future__ import annotations

import json
from lib.storage import StorageBackend


DEFAULT_CONFIG = {
    "brand_name": "",
    "site_url": "",
    "language": "Japanese",
    # カラーパレット
    "primary_color": "#3B82F6",
    "secondary_color": "#10B981",
    "accent_color": "#F59E0B",
    "background_color": "#FFFFFF",
    "text_color": "#1F2937",
    "danger_color": "#E74A3B",
}


class ConfigManager:
    """サイト設定のCRUD管理"""

    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self._ensure_default()

    def _ensure_default(self):
        """デフォルト設定が存在しなければ作成"""
        if not self.storage.exists("configs/_default.json"):
            self.storage.save_text(
                "configs/_default.json",
                json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2),
            )

    def list_sites(self) -> list[str]:
        """登録済みサイト名一覧を返す"""
        keys = self.storage.list_keys(prefix="configs/", suffix=".json")
        return [
            k.replace("configs/", "").replace(".json", "")
            for k in keys
            if k != "configs/_default.json"
        ]

    def load(self, site_name: str) -> dict:
        """サイト設定を読み込む。存在しなければデフォルトを返す"""
        key = f"configs/{site_name}.json"
        if self.storage.exists(key):
            text = self.storage.load_text(key)
            return json.loads(text)
        default_text = self.storage.load_text("configs/_default.json")
        return json.loads(default_text)

    def save(self, site_name: str, config: dict) -> None:
        """サイト設定を保存"""
        key = f"configs/{site_name}.json"
        self.storage.save_text(
            key,
            json.dumps(config, ensure_ascii=False, indent=2),
        )

    def delete(self, site_name: str) -> None:
        """サイト設定を削除"""
        key = f"configs/{site_name}.json"
        if self.storage.exists(key):
            self.storage.delete(key)

    def get_default(self) -> dict:
        """デフォルト設定のコピーを返す"""
        return DEFAULT_CONFIG.copy()

    # =============================================
    # サイト参照画像の管理（カテゴリ別: article / mv）
    # =============================================

    def _ref_images_prefix(self, site_name: str, category: str = "article", preset_id: str | None = None) -> str:
        if category == "mv" and preset_id:
            return f"ref/{site_name}/mv/{preset_id}/"
        return f"ref/{site_name}/{category}/"

    def add_reference_image(self, site_name: str, filename: str, data: bytes, category: str = "article", preset_id: str | None = None) -> str:
        """参照画像を追加し、storage key を返す"""
        key = f"{self._ref_images_prefix(site_name, category, preset_id)}{filename}"
        self.storage.save(key, data)
        return key

    def list_reference_images(self, site_name: str, category: str = "article", preset_id: str | None = None) -> list[str]:
        """サイトの参照画像キー一覧を返す（カテゴリ指定、MV時はpreset_id指定可）"""
        prefix = self._ref_images_prefix(site_name, category, preset_id)
        return self.storage.list_keys(prefix=prefix)

    def load_reference_image(self, key: str) -> bytes:
        """参照画像のバイナリを読み込む"""
        return self.storage.load(key)

    def delete_reference_image(self, key: str) -> None:
        """参照画像を削除"""
        self.storage.delete(key)

    def get_reference_pil_images(self, site_name: str, category: str = "article", preset_id: str | None = None) -> list:
        """サイトの参照画像をPIL Imageのリストで返す（最大5枚）"""
        from PIL import Image
        import io
        keys = self.list_reference_images(site_name, category, preset_id)
        images = []
        for key in keys[:5]:  # 最大5枚制限
            try:
                data = self.storage.load(key)
                img = Image.open(io.BytesIO(data))
                images.append(img)
            except Exception:
                continue
        return images

