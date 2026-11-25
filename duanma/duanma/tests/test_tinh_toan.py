import unittest

from hamtinhtoan.loc import loc_o
from hamtinhtoan.ghep_bang import ghep_bang
from hamtinhtoan.sap_xep import sap_xep
from hamtinhtoan.gom_nhom import gom_nhom, gop_lai
from hamtinhtoan.dem import dem
from hamtinhtoan.tong import tong
from hamtinhtoan.tinh_chung_binh import tinh_chung_binh
from hamtinhtoan.top_x import top_x

B = {"Ten": ["An", "Binh", "Chi", "Dung"], "Luong": [100, 200, 300, None], "Gt": ["Nam", "Nữ", "nam", None]}


class TestLoc(unittest.TestCase):
    def test_lon_hon(self):
        self.assertEqual(loc_o(B, "Luong", "> 150")["Ten"], ["Binh", "Chi"])

    def test_o_trong_khong_thoa(self):
        self.assertEqual(loc_o(B, "Luong", "!= 100")["Ten"], ["Binh", "Chi"])

    def test_chuoi_khong_phan_biet_hoa_thuong(self):
        self.assertEqual(loc_o(B, "Gt", "== Nam")["Ten"], ["An", "Chi"])

    def test_cot_toan_trong_ra_bang_rong(self):
        kq = loc_o({"A": [None, None]}, "A", "> 1")
        self.assertEqual(kq, {"A": []})

    def test_gia_tri_khong_phai_so(self):
        with self.assertRaises(ValueError):
            loc_o(B, "Luong", "> abc")

    def test_cot_khong_ton_tai(self):
        with self.assertRaises(ValueError):
            loc_o(B, "Khong", "> 1")

    def test_phep_toan_sai(self):
        with self.assertRaises(ValueError):
            loc_o(B, "Luong", "abc")


class TestGhep(unittest.TestCase):
    A = {"Ma": [1, 2, None, 4], "Ten": ["a", "b", "c", "d"]}
    C = {"Ma": [1, 1, 2, None], "Ten": ["x", "y", "z", "w"]}

    def test_inner_mot_nhieu_va_khoa_trong(self):
        kq = ghep_bang(self.A, self.C, "Ma")
        self.assertEqual(kq["Ma"], [1, 1, 2])
        self.assertEqual(kq["Ten_2"], ["x", "y", "z"])

    def test_left_giu_dong_khong_khop(self):
        kq = ghep_bang(self.A, self.C, "Ma", "left")
        self.assertEqual(kq["Ten"], ["a", "a", "b", "c", "d"])
        self.assertEqual(kq["Ten_2"], ["x", "y", "z", None, None])

    def test_cot2_khac_ten(self):
        kq = ghep_bang({"A": [1, 2]}, {"B": [2], "V": ["p"]}, "A", cot2="B")
        self.assertEqual(kq, {"A": [2], "B": [2], "V": ["p"]})

    def test_kieu_ghep_sai(self):
        with self.assertRaises(ValueError):
            ghep_bang(self.A, self.C, "Ma", "right")


class TestSapXep(unittest.TestCase):
    def test_tang_va_o_trong_cuoi(self):
        kq = sap_xep({"X": [3, None, 1, 2]}, "X")
        self.assertEqual(kq["X"], [1, 2, 3, None])

    def test_giam(self):
        self.assertEqual(sap_xep({"X": [3, None, 1, 2]}, "X", True)["X"], [3, 2, 1, None])

    def test_on_dinh(self):
        kq = sap_xep({"K": [1, 1, 1], "V": ["a", "b", "c"]}, "K")
        self.assertEqual(kq["V"], ["a", "b", "c"])

    def test_bang_rong(self):
        self.assertEqual(sap_xep({"X": []}, "X"), {"X": []})

    def test_lan_kieu(self):
        with self.assertRaises(ValueError):
            sap_xep({"X": [1, "a"]}, "X")


class TestGomDemTong(unittest.TestCase):
    T = {"Nhom": ["a", "b", "a", None, "b"], "So": [1, 2, 3, 9, None]}

    def test_gom_bo_khoa_trong(self):
        g = gom_nhom(self.T, "Nhom")
        self.assertEqual(g.khoa, ["a", "b"])
        self.assertEqual(gop_lai(g)["So"], [1, 3, 2, None])

    def test_dem_nhom(self):
        g = gom_nhom(self.T, "Nhom")
        self.assertEqual(dem(g)["SoLuong"], [2, 2])
        self.assertEqual(dem(g, "So")["Dem_So"], [2, 1])        # ô trống không đếm

    def test_dem_bang(self):
        self.assertEqual(dem(self.T), {"SoLuong": [5]})
        self.assertEqual(dem(self.T, "Nhom"), {"Nhom": ["a", "b"], "SoLuong": [2, 2]})

    def test_tong_va_trung_binh(self):
        g = gom_nhom(self.T, "Nhom")
        self.assertEqual(tong(g, "So")["Tong_So"], [4, 2])
        self.assertEqual(tinh_chung_binh(g, "So")["TB_So"], [2.0, 2.0])
        self.assertEqual(tong(self.T, "So"), {"Tong_So": [15]})

    def test_nhom_toan_trong_ra_none(self):
        g = gom_nhom({"N": ["a"], "S": [None]}, "N")
        self.assertEqual(tong(g, "S")["Tong_S"], [None])
        self.assertEqual(tinh_chung_binh(g, "S")["TB_S"], [None])

    def test_tong_cot_chu(self):
        with self.assertRaises(ValueError):
            tong({"X": ["a", "b"]}, "X")


class TestTop(unittest.TestCase):
    T = {"X": [5, 1, 9, 3]}

    def test_top_2(self):
        self.assertEqual(top_x(self.T, "X", 2)["X"], [9, 5])

    def test_top_0_va_vuot_so_dong(self):
        self.assertEqual(top_x(self.T, "X", 0)["X"], [])
        self.assertEqual(len(top_x(self.T, "X", 99)["X"]), 4)

    def test_x_am(self):
        with self.assertRaises(ValueError):
            top_x(self.T, "X", -1)


if __name__ == "__main__":
    unittest.main()
