import os
import unittest

from database import CSDL
from tests.helpers import CoDB


class TestThem(CoDB):
    def test_tu_cap_khoa_chinh(self):
        self.db.them("PHONGBAN", {"TenPB": "Nhân sự"})
        self.assertEqual(self.db["PHONGBAN"]["MaPB"].tolist(), [1, 2, 3])

    def test_chuan_hoa_check(self):
        self.assertEqual(self.db["NHANVIEN"]["GioiTinh"].tolist(), ["Nam", "Nữ"])

    def test_ten_Na_khong_bi_coi_la_null(self):
        self.assertEqual(self.db["NHANVIEN"]["HoTen"].tolist()[1], "Na")

    def test_loi_khong_them_gi_ca(self):
        truoc = len(self.db["NHANVIEN"])
        with self.assertRaises(ValueError) as cm:
            self.db.them("NHANVIEN", [{"HoTen": "Hợp lệ", "MaPB": 1},
                                      {"HoTen": "Sai FK", "MaPB": 99},
                                      {"HoTen": "Sai giới tính", "GioiTinh": "x"},
                                      {"HoTen": "Lương âm", "LuongCoBan": -1}])
        msg = str(cm.exception)
        self.assertIn("dòng 1", msg)
        self.assertIn("dòng 2", msg)
        self.assertIn("dòng 3", msg)
        self.assertEqual(len(self.db["NHANVIEN"]), truoc)

    def test_thieu_not_null(self):
        with self.assertRaises(ValueError):
            self.db.them("NHANVIEN", {"LuongCoBan": 1})

    def test_trung_khoa_chinh_va_unique(self):
        with self.assertRaises(ValueError):
            self.db.them("NHANVIEN", {"MaNV": 1, "HoTen": "Trùng"})
        with self.assertRaises(ValueError):
            self.db.them("PHONGBAN", {"TenPB": "Kế toán"})
        with self.assertRaises(ValueError):                      # trùng ngay trong lô thêm
            self.db.them("PHONGBAN", [{"TenPB": "Mới"}, {"TenPB": "Mới"}])

    def test_unique_chamcong(self):
        dong = {"MaNV": 1, "MaCa": 1, "NgayChamCong": "2026-11-02"}
        self.db.them("BANGCHAMCONG", dong)
        with self.assertRaises(ValueError):
            self.db.them("BANGCHAMCONG", dong)

    def test_thang_ngoai_khoang(self):
        with self.assertRaises(ValueError):
            self.db.them("BANGLUONG", {"MaNV": 1, "Thang": 13, "Nam": 2026})

    def test_bang_khong_ton_tai(self):
        with self.assertRaises(KeyError):
            self.db.them("KHONGCO", {})

    def test_them_nhan_vien_tu_tao_dong_luong(self):
        self.assertEqual(sorted(self.db["BANGLUONG"]["MaNV"].tolist()), [1, 2])
        self.db.them("NHANVIEN", {"HoTen": "Mới", "MaPB": 1})
        self.assertEqual(sorted(self.db["BANGLUONG"]["MaNV"].tolist()), [1, 2, 3])


class TestSua(CoDB):
    def test_sua_cung_bang(self):
        n = self.db.sua("NHANVIEN", "ChucVu", "Trưởng phòng", "HoTen", "Na")
        self.assertEqual(n, 1)
        self.assertEqual(self.db["NHANVIEN"]["ChucVu"].tolist()[1], "Trưởng phòng")

    def test_sua_qua_fk(self):
        n = self.db.sua("NHANVIEN", "ChucVu", "KT", "TenPB", "Kế toán", bang_loc="PHONGBAN")
        self.assertEqual(n, 1)
        self.assertEqual(self.db["NHANVIEN"]["ChucVu"].tolist()[0], "KT")

    def test_khong_co_dong_thoa(self):
        with self.assertRaises(ValueError):
            self.db.sua("NHANVIEN", "ChucVu", "x", "HoTen", "Không có")

    def test_khong_sua_cot_tu_tinh(self):
        with self.assertRaises(ValueError):
            self.db.sua("BANGLUONG", "LuongThucNhan", 1, "MaNV", 1)

    def test_sai_rang_buoc_giu_nguyen(self):
        with self.assertRaises(ValueError):
            self.db.sua("NHANVIEN", "GioiTinh", "xyz", "MaNV", 1)
        self.assertEqual(self.db["NHANVIEN"]["GioiTinh"].tolist()[0], "Nam")

    def test_chan_sua_khoa_dang_duoc_tham_chieu(self):
        with self.assertRaises(ValueError):
            self.db.sua("NHANVIEN", "MaNV", 10, "MaNV", 1)

    def test_dieu_kien_trong(self):
        with self.assertRaises(ValueError):
            self.db.sua("NHANVIEN", "ChucVu", "x", "HoTen", "")


class TestXoa(CoDB):
    def test_xoa_theo_cot_va_bang_kem_xoa_luong(self):
        kq = self.db.xoa("Na", "HoTen", "NHANVIEN")
        self.assertEqual(kq, {"NHANVIEN": 1, "BANGLUONG": 1})
        self.assertEqual(self.db["NHANVIEN"]["MaNV"].tolist(), [1])

    def test_chan_xoa_cha_con_con(self):
        with self.assertRaises(ValueError) as cm:
            self.db.xoa(None, None, "PHONGBAN")
        self.assertIn("NHANVIEN", str(cm.exception))
        self.assertEqual(len(self.db["PHONGBAN"]), 2)

    def test_xoa_ca_bang_con(self):
        self.db.them("PHUCAP_THUONGPHAT", {"MaNV": 1, "Loai": "Phạt", "SoTien": 1, "NgayApDung": "2026-11-01"})
        self.assertEqual(self.db.xoa(None, None, "PHUCAP_THUONGPHAT"), {"PHUCAP_THUONGPHAT": 1})

    def test_khong_khop(self):
        with self.assertRaises(ValueError):
            self.db.xoa("Không có", "HoTen", "NHANVIEN")

    def test_thieu_tham_so(self):
        with self.assertRaises(ValueError):
            self.db.xoa()
        with self.assertRaises(ValueError):
            self.db.xoa(None, "HoTen")

    def test_cot_khong_thuoc_bang(self):
        with self.assertRaises(ValueError):
            self.db.xoa("x", "Khong", "NHANVIEN")


class TestLuuCSV(CoDB):
    def test_ghi_va_doc_lai(self):
        self.assertTrue(os.path.exists(os.path.join(self.thu_muc, "luong.csv")))
        db2 = CSDL(thu_muc=self.thu_muc)
        for ten in self.db.bang:
            self.assertEqual(len(db2[ten]), len(self.db[ten]), ten)
        self.assertEqual(db2["NHANVIEN"]["HoTen"].tolist(), ["Nguyễn Văn An", "Na"])

    def test_loi_khong_ghi_csv(self):
        duong = os.path.join(self.thu_muc, "phongban.csv")
        with open(duong, encoding="utf-8-sig") as f:
            truoc = f.read()
        with self.assertRaises(ValueError):
            self.db.them("PHONGBAN", {"TenPB": "Kế toán"})
        with open(duong, encoding="utf-8-sig") as f:
            self.assertEqual(f.read(), truoc)

    def test_csv_sua_tay_bang_excel_van_doc_duoc(self):
        duong = os.path.join(self.thu_muc, "nhanvien.csv")
        with open(duong, encoding="utf-8-sig") as f:
            noi_dung = f.read().replace("Nguyễn Văn An", "Nguyễn Văn Ân")
        with open(duong, "w", encoding="utf-8-sig") as f:
            f.write(noi_dung)
        self.assertEqual(CSDL(thu_muc=self.thu_muc)["NHANVIEN"]["HoTen"].tolist()[0], "Nguyễn Văn Ân")

    def test_thu_muc_rong_tao_bang_rong(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(len(CSDL(thu_muc=t)["NHANVIEN"]), 0)


if __name__ == "__main__":
    unittest.main()
