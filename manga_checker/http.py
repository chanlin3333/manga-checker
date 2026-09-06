"""requests の SSL 検証設定。

Windows や社内プロキシ環境では、OS の証明書ストアが Python に渡らず
CERTIFICATE_VERIFY_FAILED になることがあります。

優先順:
1. --insecure / 環境変数 MANGA_CHECKER_SSL_VERIFY=0 なら verify=False
2. それ以外は certifi の CA バンドルを使う
3. それでも SSL エラーなら、一度だけ verify=False にフォールバック
"""

from __future__ import annotations

import os
import warnings

import certifi
import requests
from requests.adapters import HTTPAdapter
from urllib3.exceptions import InsecureRequestWarning

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_insecure_override: bool | None = None
_fallback_warned = False


def configure_ssl(*, insecure: bool | None = None) -> None:
    """main.py の --insecure から呼び出す。"""
    global _insecure_override
    _insecure_override = insecure


def ssl_verify_setting() -> bool | str:
    if _insecure_override is True:
        return False
    if _insecure_override is False:
        return certifi.where()

    raw = os.environ.get("MANGA_CHECKER_SSL_VERIFY", "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return certifi.where()
    return certifi.where()


class _SslFallbackAdapter(HTTPAdapter):
    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        global _fallback_warned
        try:
            return super().send(
                request,
                stream=stream,
                timeout=timeout,
                verify=verify,
                cert=cert,
                proxies=proxies,
            )
        except requests.exceptions.SSLError:
            if verify is False:
                raise
            if not _fallback_warned:
                warnings.warn(
                    "SSL証明書の検証に失敗したため、verify=False で再試行します。"
                    "恒久対応する場合は python main.py --insecure を使ってください。",
                    InsecureRequestWarning,
                    stacklevel=2,
                )
                _fallback_warned = True
            return super().send(
                request,
                stream=stream,
                timeout=timeout,
                verify=False,
                cert=cert,
                proxies=proxies,
            )


def make_session(*, extra_headers: dict[str, str] | None = None) -> requests.Session:
    verify = ssl_verify_setting()
    if verify is False:
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    session = requests.Session()
    session.verify = verify
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        }
    )
    if extra_headers:
        session.headers.update(extra_headers)
    adapter = _SslFallbackAdapter()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
