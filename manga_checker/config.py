"""アフィリエイトID・楽天APIキーなど、環境変数 / 設定ファイルから読む。"""

from __future__ import annotations

import json
import os
from pathlib import Path

_CACHE: dict[str, str] | None = None
_CONFIG_NAMES = ("affiliate.json", "config.json")
_PLACEHOLDERS = {
    "",
    "YOUR_APPLICATION_ID",
    "YOUR_APP_ID",
    "YOUR_AFFILIATE_ID",
    "YOUR_ACCESS_KEY",
    "PLACEHOLDER",
    "XXX",
    "changeme",
}


def affiliate_settings() -> dict[str, str]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    data: dict[str, str] = {
        "amazon_tag": os.environ.get("MANGA_CHECKER_AMAZON_TAG", "").strip(),
        "rakuten_affiliate_id": (
            os.environ.get("MANGA_CHECKER_RAKUTEN_AFFILIATE_ID")
            or os.environ.get("RAKUTEN_AFFILIATE_ID")
            or ""
        ).strip(),
        "rakuten_application_id": (
            os.environ.get("MANGA_CHECKER_RAKUTEN_APPLICATION_ID")
            or os.environ.get("RAKUTEN_APPLICATION_ID")
            or os.environ.get("RAKUTEN_APP_ID")
            or ""
        ).strip(),
        "rakuten_access_key": (
            os.environ.get("MANGA_CHECKER_RAKUTEN_ACCESS_KEY")
            or os.environ.get("RAKUTEN_ACCESS_KEY")
            or ""
        ).strip(),
    }
    for name in _CONFIG_NAMES:
        path = Path(name)
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            data["amazon_tag"] = _pick(payload, data["amazon_tag"], "amazon_tag")
            data["rakuten_affiliate_id"] = _pick(
                payload,
                data["rakuten_affiliate_id"],
                "rakuten_affiliate_id",
                "affiliateId",
                "affiliate_id",
            )
            data["rakuten_application_id"] = _pick(
                payload,
                data["rakuten_application_id"],
                "rakuten_application_id",
                "applicationId",
                "application_id",
            )
            data["rakuten_access_key"] = _pick(
                payload,
                data["rakuten_access_key"],
                "rakuten_access_key",
                "accessKey",
                "access_key",
            )
        break
    _CACHE = data
    return data


def rakuten_application_id() -> str:
    value = affiliate_settings().get("rakuten_application_id") or ""
    return "" if value.strip() in _PLACEHOLDERS else value.strip()


def rakuten_affiliate_id() -> str:
    value = affiliate_settings().get("rakuten_affiliate_id") or ""
    return "" if value.strip() in _PLACEHOLDERS else value.strip()


def rakuten_access_key() -> str:
    value = affiliate_settings().get("rakuten_access_key") or ""
    return "" if value.strip() in _PLACEHOLDERS else value.strip()


def _pick(payload: dict, current: str, *keys: str) -> str:
    for key in keys:
        raw = payload.get(key)
        if raw is None:
            continue
        text = str(raw).strip()
        if text and text not in _PLACEHOLDERS:
            return text
    return current
