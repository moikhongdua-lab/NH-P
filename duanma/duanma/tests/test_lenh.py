import unittest

from hamtinhtoan import sua, them, xoa, truyvan
from tests.helpers import CoDB


class TestSuaLenh(CoDB):
    def test_gia_tri_moi_khong_nhay_chua_chu_thanh(self):
        sua.thuc_thi(self.db, "sửa HoTen khi MaNV = 1 thành Thanh Tùng")
        self.assertEqual(self.db["NHANVIEN"]["HoTen"].tolist()[0], "Thanh Tùng")

    def test_gia_tri_cu_trong_nhay_chua_chu_thanh(self):
        self.db.them("NHANVIEN", {"HoTen": "Lê Thành", "MaPB": 1})
        sua.thuc_thi(self.db, "sửa ChucVu khi HoTen = 'Lê Thành' thành Trưởng nhóm")
        self.assertEqual(self.db["NHANVIEN"]["ChucVu"].tolist()[-1], "Trưởng nhóm")

    def test_cu_phap_sai(self):
        for lenh in ("xóa X", "sửa", "sửa A khi", "sửa  khi MaNV = 1 thành 2",
                     "sửa HoTen khi MaNV > 1 thành X", "sửa HoTen khi MaNV = 1"):
            with self.assertRaises(ValueError, msg=lenh):
                sua.thuc_thi(self.db, lenh)

    def test_viet_hoa_va_dau(self):
        sua.thuc_thi(self.db, "SỬA LuongCoBan KHI HoTen = 'Na' THÀNH 700000")
        self.assertEqual(self.db["NHANVIEN"]["LuongCoBan"].tolist()[1], 700000)


class TestThemLenh(CoDB):
    def test_them_mot_dong(self):
        bang, _ = them.thuc_thi(self.db, "thêm 'Tùng' vào HoTen; thêm '100000' vào LuongCoBan; thêm 'Nam' vào GioiTinh")
        self.assertEqual(bang, "NHANVIEN")
        self.assertEqual(self.db["NHANVIEN"]["HoTen"].tolist()[-1], "Tùng")

    def test_nhieu_bang_khac_nhau(self):
        with self.assertRaises(ValueError):
            them.thuc_thi(self.db, "thêm 'A' vào HoTen; thêm 'B' vào TenPB")

    def test_cot_tu_tinh(self):
        with self.assertRaises(ValueError):
            them.thuc_thi(self.db, "thêm '5' vào LuongThucNhan")

    def test_nhap_hai_lan_mot_cot(self):
        with self.assertRaises(ValueError):
            them.thuc_thi(self.db, "thêm 'A' vào HoTen; thêm 'B' vào HoTen")

    def test_cu_phap_sai(self):
        for lenh in ("", "thêm", "sửa 'a' vào HoTen", "thêm 'a' HoTen", "thêm 'a' vào"):
            with self.assertRaises(ValueError, msg=lenh):
                them.thuc_thi(self.db, lenh)

    def test_cot_khong_ton_tai(self):
        with self.assertRaises(ValueError):
            them.thuc_thi(self.db, "thêm 'a' vào KhongCo")

    def test_dau_cham_phay_trong_nhay(self):
        them.thuc_thi(self.db, "thêm 'A; B' vào HoTen")
        self.assertEqual(self.db["NHANVIEN"]["HoTen"].tolist()[-1], "A; B")


class TestXoaLenh(CoDB):
    def test_ten_Na_xoa_duoc(self):
        xoa.thuc_thi(self.db, "xóa: 'Na', HoTen, NHANVIEN")
        self.assertEqual(self.db["NHANVIEN"]["HoTen"].tolist(), ["Nguyễn Văn An"])

    def test_bo_trong_cot(self):
        xoa.thuc_thi(self.db, "xóa: 'Na', , NHANVIEN")
        self.assertEqual(len(self.db["NHANVIEN"]), 1)

    def test_nhan_biet_phan_khi_it_hon_3(self):
        self.assertEqual(xoa.phan_tich(self.db, "xóa: 'Na', NHANVIEN"), ("Na", None, "NHANVIEN"))

    def test_loi(self):
        for lenh in ("xóa:", "xóa: a, b, c, d", "sửa: 'a'", "xóa: 'a', HoTen, KHONGCO"):
            with self.assertRaises(ValueError, msg=lenh):
                xoa.thuc_thi(self.db, lenh)


class TestTruyVan(CoDB):
    def q(self, s):
        return truyvan.thuc_thi(self.db, s)[0]

    def test_in_loc_ghep(self):
        kq = self.q("in(loc(ghep(NHANVIEN, BANGLUONG), HoTen == 'na'), HoTen, LuongThucNhan)")
        self.assertEqual(list(kq), ["HoTen", "LuongThucNhan"])
        self.assertEqual(kq["HoTen"], ["Na"])

    def test_dau_phay_cuoi(self):
        self.assertEqual(self.q("in(NHANVIEN, HoTen, )")["HoTen"], ["Nguyễn Văn An", "Na"])
        self.assertEqual(list(self.q("in(NHANVIEN, )")), list(self.db["NHANVIEN"].columns))

    def test_bi_danh(self):
        kq = self.q("dem(NHANVIEN, GioiTinh, as='SoNguoi')")
        self.assertEqual(kq, {"GioiTinh": ["Nam", "Nữ"], "SoNguoi": [1, 1]})
        kq = self.q("tong(NHANVIEN, LuongCoBan, as=Tong)")
        self.assertEqual(kq, {"Tong": [1100000.0]})

    def test_bi_danh_trung_ten_cot_khac(self):
        with self.assertRaises(ValueError):
            self.q("dem(NHANVIEN, GioiTinh, as='GioiTinh')")

    def test_gom_tong_nhom(self):
        kq = self.q("tong(gom(NHANVIEN, MaPB), LuongCoBan)")
        self.assertEqual(kq["Tong_LuongCoBan"], [500000.0, 600000.0])

    def test_nhom_ngoai_cung_duoc_gop_lai(self):
        self.assertEqual(len(self.q("gom(NHANVIEN, MaPB)")["MaNV"]), 2)

    def test_sap_xep_va_top(self):
        self.assertEqual(self.q("top(NHANVIEN, LuongCoBan, 1)")["HoTen"], ["Na"])
        self.assertEqual(self.q("sap_xep(NHANVIEN, LuongCoBan, giam)")["MaNV"], [2, 1])

    def test_ghep_trai(self):
        self.assertEqual(len(self.q("ghep(NHANVIEN, BANGCHAMCONG, MaNV, trai)")["MaNV"]), 2)
        self.assertEqual(len(self.q("ghep(NHANVIEN, BANGCHAMCONG, trai)")["MaNV"]), 2)   # bỏ trống cột
        self.assertEqual(len(self.q("ghep(NHANVIEN, BANGCHAMCONG)")["MaNV"]), 0)         # inner: chưa có chấm công

    def test_cot_khong_dau_va_ten_bang_ngan(self):
        self.assertEqual(len(self.q("in(nhanvien, hoten)")["HoTen"]), 2)
        self.assertEqual(len(self.q("luong")["MaNV"]), 2)

    def test_buoc_tinh_trong_ra_ngoai(self):
        _, buoc = truyvan.thuc_thi(self.db, "in(loc(NHANVIEN, LuongCoBan > 1), HoTen)")
        self.assertEqual(len(buoc), 2)
        self.assertTrue(buoc[0].startswith("loc("))

    def test_loi(self):
        for s in ("", "xyz(NHANVIEN)", "KHONGCO", "in(NHANVIEN, KhongCo)", "gom(NHANVIEN, MaPB)x",
                  "top(NHANVIEN, LuongCoBan, abc)", "top(NHANVIEN, LuongCoBan, -1)",
                  "sap_xep(NHANVIEN, MaNV, lung)", "in(gom(NHANVIEN, MaPB), HoTen)",
                  "tong(NHANVIEN, HoTen)", "loc(NHANVIEN)", "in(NHANVIEN"):
            with self.assertRaises(ValueError, msg=s):
                self.q(s)

    def test_khong_thay_doi_du_lieu(self):
        truoc = self.db["NHANVIEN"].copy()
        self.q("loc(NHANVIEN, MaNV > 0)")
        self.assertTrue(truoc.equals(self.db["NHANVIEN"]))


if __name__ == "__main__":
    unittest.main()
