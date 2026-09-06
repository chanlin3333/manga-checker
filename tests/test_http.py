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

    def test_env_disables_verify(self) -> None:
        http_mod.configure_ssl(insecure=None)
        with patch.dict(os.environ, {"MANGA_CHECKER_SSL_VERIFY": "0"}):
            self.assertIs(ssl_verify_setting(), False)


if __name__ == "__main__":
    unittest.main()
