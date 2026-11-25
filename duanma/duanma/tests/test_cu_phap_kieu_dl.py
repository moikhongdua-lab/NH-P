import unittest

import pandas as pd

from database.kieu_dl import (bo_dau, la_null, parse_time, ep_kieu, ep_gia_tri, doi_theo_mau)
from hamtinhtoan.cu_phap import (tach, tach_dieu_kien, tach_phep_gia_tri, bo_nhay,
                                 bo_tu_lenh, tim_tu, tim_ngoac_dong)


class TestCuPhap(unittest.TestCase):
    def test_tach_bo_qua_nhay_va_ngoac(self):
        self.assertEqual(tach("a, 'b,c', f(x, y), d", ","), ["a", " 'b,c'", " f(x, y)", " d"])

    def test_tach_dieu_kien(self):
        self.assertEqual(tach_dieu_kien("HoTen = 'An'"), ("HoTen", "==", "'An'"))
        self.assertEqual(tach_dieu_kien("L >= 5"), ("L", ">=", "5"))
        self.assertEqual(tach_dieu_kien("T == 'a>b'"), ("T", "==", "'a>b'"))

    def test_dieu_kien_loi(self):
        for s in ("abc", "> 5", "A >"):
            with self.assertRaises(ValueError):
                tach_dieu_kien(s)
        with self.assertRaises(ValueError):
            tach_phep_gia_tri("abc")

    def test_bo_nhay(self):
        self.assertEqual(bo_nhay(" 'ab' "), ("ab", True))
        self.assertEqual(bo_nhay("ab"), ("ab", False))
        self.assertEqual(bo_nhay("“ab”"), ("ab", True))

    def test_bo_tu_lenh(self):
        self.assertEqual(bo_tu_lenh("Thêm: 'a' vào b", "them"), "'a' vào b")
        self.assertEqual(bo_tu_lenh("sửa X khi", "sua"), "X khi")
        self.assertIsNone(bo_tu_lenh("themxyz", "them"))
        self.assertIsNone(bo_tu_lenh("xóa", "them"))

    def test_tim_tu_bo_qua_trong_nhay(self):
        s = "A khi B = 'Thành khi' thành C"
        self.assertEqual(tim_tu(s, "khi"), 2)
        self.assertEqual(tim_tu("x thành y", "thanh"), 2)
        self.assertEqual(tim_tu("thanhxyz", "thanh"), -1)

    def test_ngoac(self):
        self.assertEqual(tim_ngoac_dong("f(a(b))", 1), 6)
        self.assertEqual(tim_ngoac_dong("f(a", 1), -1)


class TestKieuDL(unittest.TestCase):
    def test_bo_dau_giu_do_dai(self):
        for s in ("Thành Đạt", "ữặđĐ", "Nguyễn Văn An", "a\u0301"):
            self.assertEqual(len(bo_dau(s)), len(s))
        self.assertEqual(bo_dau("Thêm Đạt"), "them dat")

    def test_la_null(self):
        for v in (None, "", "  ", pd.NA, float("nan"), pd.NaT, "null"):
            self.assertTrue(la_null(v), v)
        for v in ("Na", "none", "n/a", 0, "0", "An"):
            self.assertFalse(la_null(v), v)

    def test_parse_time(self):
        self.assertEqual(parse_time("8:05"), "08:05:00")
        self.assertIsNone(parse_time(None))
        for s in ("25:00", "8", "ab:cd", "10:60"):
            with self.assertRaises(ValueError):
                parse_time(s)

    def test_ep_gia_tri(self):
        self.assertEqual(ep_gia_tri("int", "5"), 5)
        self.assertEqual(ep_gia_tri("float", "1.5"), 1.5)
        self.assertEqual(ep_gia_tri("date", "15/03/1995"), pd.Timestamp("1995-03-15"))
        self.assertIsNone(ep_gia_tri("int", ""))
        for kieu, v in (("int", "1.5"), ("int", "abc"), ("float", "inf"), ("date", "31/02/2020")):
            with self.assertRaises(ValueError):
                ep_gia_tri(kieu, v, "Cot")

    def test_ep_kieu_gom_loi_va_giu_o_trong(self):
        df = pd.DataFrame([{"MaPB": "x", "TenPB": "A"}, {"MaPB": 2, "TenPB": "B"}])
        with self.assertRaises(ValueError) as cm:
            ep_kieu("PHONGBAN", df)
        self.assertIn("dòng 0", str(cm.exception))
        kq = ep_kieu("PHONGBAN", pd.DataFrame([{"TenPB": "A"}]))
        self.assertTrue(pd.isna(kq.loc[0, "MaPB"]))

    def test_ep_kieu_cot_la(self):
        with self.assertRaises(ValueError):
            ep_kieu("PHONGBAN", pd.DataFrame([{"Lạ": 1}]))

    def test_doi_theo_mau(self):
        self.assertEqual(doi_theo_mau("5", 1), 5.0)
        self.assertEqual(doi_theo_mau("2026-11-02", pd.Timestamp("2026-01-01")), pd.Timestamp("2026-11-02"))
        self.assertEqual(doi_theo_mau("8:00", "07:00:00"), "08:00:00")
        self.assertEqual(doi_theo_mau("An", "Binh"), "An")
        with self.assertRaises(ValueError):
            doi_theo_mau("abc", 1)


if __name__ == "__main__":
    unittest.main()
