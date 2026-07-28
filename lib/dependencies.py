"""
共有依存関係（マネージャーインスタンス）
app.pyの再実行を避けるため、ページからはこのモジュール経由でマネージャーにアクセスする。

設定・参照画像用ストレージ（get_config_storage）の切り替え優先順位:
  1. GITHUB_TOKEN が設定されていれば、このリポジトリへgit自動push（Streamlit Cloud
     再デプロイでも消えない。Google Cloud設定不要）
  2. GOOGLE_DRIVE_FOLDER_ID が設定されていれば Google Drive を使用
  3. どちらも未設定ならローカルファイルシステム（再デプロイで消える）

生成画像用ストレージ（get_output_storage）は常にローカル（一時的。数が多く
リポジトリ肥大化を避けるため、生成画像はgit同期の対象外）。
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from lib.storage import LocalStorage, StorageBackend
from lib.config_manager import ConfigManager

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _get_secret(key: str) -> str | None:
    """環境変数 or st.secrets から値を取得（Cloud/ローカル両対応）。
    st.secretsへのアクセス自体が失敗する場合（Secrets全体のTOML構文エラー等）は
    ログに出す。ここを握りつぶすと「設定したはずのSecretsが静かに無視される」
    事故に気づけなくなる（2026-07-28 実際に発生・原因特定に苦労した教訓）。"""
    val = os.getenv(key)
    if val:
        return val
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception as e:
        import sys
        print(f"[dependencies] st.secrets へのアクセスに失敗しました（key={key}）: {e}", file=sys.stderr)
    return None


def _use_git_sync() -> bool:
    """gitへの自動push方式を使うかどうか"""
    return bool(_get_secret("GITHUB_TOKEN"))


def _use_google_drive() -> bool:
    """Google Drive ストレージを使うかどうか"""
    return bool(_get_secret("GOOGLE_DRIVE_FOLDER_ID"))


def get_storage_backend_status() -> str:
    """現在有効な設定・参照画像ストレージの種類（サイドバー等での常時表示用）。
    「設定したつもりが実は効いてない」を見えなくしない目的（2026-07-28追加）。"""
    if _use_git_sync():
        return "🐙 GitHub自動保存 — コード更新後も残ります"
    if _use_google_drive():
        return "☁️ Google Drive保存 — コード更新後も残ります"
    return "⚠️ ローカル一時保存 — コード更新のたびに消えます"


@st.cache_resource
def _get_git_sync_storage(token: str) -> StorageBackend:
    """git自動push方式ストレージのシングルトン"""
    from lib.storage import GitSyncStorage
    return GitSyncStorage(PROJECT_ROOT, github_token=token)


@st.cache_resource
def _get_drive_storage(folder_id: str) -> StorageBackend:
    """Google Drive ストレージのシングルトン"""
    from lib.storage import GoogleDriveStorage
    return GoogleDriveStorage(
        folder_id=folder_id,
        credentials_json=_get_secret("GOOGLE_SERVICE_ACCOUNT_JSON"),
        credentials_file=_get_secret("GOOGLE_SERVICE_ACCOUNT_FILE"),
    )


@st.cache_resource
def get_config_storage():
    """設定・参照画像用: git自動push > Google Drive > ローカル の優先順位"""
    if _use_git_sync():
        return _get_git_sync_storage(_get_secret("GITHUB_TOKEN"))
    if _use_google_drive():
        return _get_drive_storage(_get_secret("GOOGLE_DRIVE_FOLDER_ID"))
    return LocalStorage(PROJECT_ROOT)


@st.cache_resource
def get_output_storage():
    """生成画像用: 常にローカル（一時的。git同期の対象外）"""
    return LocalStorage(PROJECT_ROOT)


@st.cache_resource
def get_config_manager():
    return ConfigManager(get_config_storage())
