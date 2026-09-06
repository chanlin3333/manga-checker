import os
import unittest
from unittest.mock import patch

import certifi

from manga_checker import http as http_mod
from manga_checker.http import ssl_verify_setting


class SslSettingTests(unittest.TestCase):
    def tearDown(self) -> None:
        http_mod.configure_ssl(insecure=None)
        os.environ.pop("MANGA_CHECKER_SSL_VERIFY", None)

    def test_default_uses_certifi(self) -> None:
        http_mod.configure_ssl(insecure=None)
        os.environ.pop("MANGA_CHECKER_SSL_VERIFY", None)
        self.assertEqual(ssl_verify_setting(), certifi.where())

    def test_insecure_flag(self) -> None:
        http_mod.configure_ssl(insecure=True)
        self.assertIs(ssl_verify_setting(), False)

    def test_insecure_warnings_are_filtered(self) -> None:
        import warnings

        from urllib3.exceptions import InsecureRequestWarning

        from manga_checker.http import _suppress_insecure_warnings

        _suppress_insecure_warnings()
        with warnings.catch_warnings(record=True) as caught:
            warnings.warn("ssl", InsecureRequestWarning)
        self.assertFalse(any(item.category is InsecureRequestWarning for item in caught))


if __name__ == "__main__":
    unittest.main()
