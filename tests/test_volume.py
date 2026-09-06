import unittest

from manga_checker.volume import is_volume_one


class VolumeOneTests(unittest.TestCase):
    def test_volume_field(self) -> None:
        self.assertTrue(is_volume_one("リベンジアクト", "1"))
        self.assertTrue(is_volume_one("リベンジアクト", "第1巻"))
        self.assertTrue(is_volume_one("リベンジアクト", "１巻"))
        self.assertFalse(is_volume_one("リベンジアクト", "2"))
        self.assertFalse(is_volume_one("蒼き鋼のアルペジオ", "31"))

    def test_title_patterns(self) -> None:
        self.assertTrue(is_volume_one("夜は猫といっしょ(1)"))
        self.assertTrue(is_volume_one("夜は猫といっしょ（１）"))
        self.assertTrue(is_volume_one("魔入りました!入間くん 僕同盟のゲーム道(1)"))
        self.assertTrue(is_volume_one("はじめての冒険 第1巻"))
        self.assertTrue(is_volume_one("はじめての冒険 1巻"))
        self.assertTrue(is_volume_one("Example Vol.1"))
        self.assertTrue(is_volume_one("夜は猫といっしょ 1"))
        self.assertTrue(is_volume_one("夜は猫といっしょ １"))
        self.assertTrue(is_volume_one("夜は猫といっしょ 1 特装版"))
        self.assertTrue(is_volume_one("あっ、悪魔ちゃん 1"))
        self.assertTrue(is_volume_one("ヒトナー 1"))
        self.assertTrue(is_volume_one("ヒトナー １"))
        self.assertTrue(is_volume_one("あっ、悪魔ちゃん　1"))
        self.assertTrue(is_volume_one("ヒトナー　１"))
        self.assertTrue(is_volume_one("ヒトナー 1　続刊"))
        self.assertTrue(is_volume_one("ヒトナー　1 続刊"))
        self.assertTrue(is_volume_one("作品 1:特装版"))
        self.assertFalse(is_volume_one("夜は猫といっしょ(10)"))
        self.assertFalse(is_volume_one("進撃の巨人(11)"))
        self.assertFalse(is_volume_one("進撃の巨人 11巻"))
        self.assertFalse(is_volume_one("進撃の巨人 21巻"))
        self.assertFalse(is_volume_one("1日10分でわかる世界史"))
        self.assertFalse(is_volume_one("あおのたつき", "20"))


if __name__ == "__main__":
    unittest.main()
