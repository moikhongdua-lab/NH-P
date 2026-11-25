import unittest

from database.bang.chamcong import so_gio_lam, tinh_cong, la_ca_dem
from tests.helpers import CoDB


class TestChamCong(unittest.TestCase):
    def test_ca_ngay_du_8h(self):
        self.assertEqual(tinh_cong("08:00", "16:00", 1.0), 1.0)

    def test_nua_ngay(self):
        self.assertEqual(tinh_cong("08:00", "12:00", 1.0), 0.5)

    def test_tang_ca(self):          # 9h: 1 + 1/8*1.5
        self.assertEqual(tinh_cong("07:00", "16:00", 1.0), 1.1875)

    def test_he_so_ca_khong_nhan_voi_gio_tang_ca(self):
        self.assertEqual(tinh_cong("19:00", "05:00", 1.2, ca_dem=True), 1.575)

    def test_nhan_biet_ca_dem(self):
        self.assertTrue(la_ca_dem("19:00", "05:00"))
        self.assertFalse(la_ca_dem("07:00", "16:00"))
        self.assertFalse(la_ca_dem(None, "05:00"))

    def test_thieu_gio_ra_la_none(self):
        self.assertIsNone(tinh_cong("08:00", None, 1.0))
        self.assertIsNone(so_gio_lam(None, None))

    def test_gio_ra_som_hon_vao_o_ca_ngay_bao_loi(self):
        with self.assertRaises(ValueError):
            so_gio_lam("16:00", "08:00", ca_dem=False)

    def test_gio_vao_bang_gio_ra_bao_loi(self):
        with self.assertRaises(ValueError):
            so_gio_lam("08:00", "08:00", ca_dem=True)

    def test_vuot_gio_toi_da(self):
        with self.assertRaises(ValueError):
            so_gio_lam("05:00", "23:00")

    def test_he_so_trong_la_none(self):
        self.assertIsNone(tinh_cong("08:00", "16:00", None))


class TestLuong(CoDB):
    def setUp(self):
        super().setUp()
        d = self.db
        d.them("BANGCHAMCONG", [
            {"MaNV": 1, "MaCa": 1, "GioVaoThucTe": "08:00", "GioRaThucTe": "16:00", "NgayChamCong": "2026-11-02"},
            {"MaNV": 1, "MaCa": 2, "GioVaoThucTe": "19:00", "GioRaThucTe": "05:00", "NgayChamCong": "03/11/2026"},
            {"MaNV": 2, "MaCa": 1, "GioVaoThucTe": "08:00", "GioRaThucTe": None, "NgayChamCong": "2026-11-02"}])
        d.them("PHUCAP_THUONGPHAT", [
            {"MaNV": 1, "Loai": "thưởng", "SoTien": 200000, "NgayApDung": "2026-11-10"},
            {"MaNV": 1, "Loai": "Phạt", "SoTien": 50000, "NgayApDung": "2026-11-12"},
            {"MaNV": 1, "Loai": "Phạt", "SoTien": 99999, "NgayApDung": "2026-10-12"}])    # tháng khác

    def luong(self, ma):
        b = self.db["BANGLUONG"]
        return b[b["MaNV"] == ma].iloc[0]

    def test_luong_nv1(self):
        r = self.luong(1)
        self.assertEqual(r["TongCong"], 2.575)
        self.assertEqual(r["LuongThucNhan"], 500000 * 2.575 - 50000 + 200000)

    def test_dong_thieu_gio_khong_tinh_cong(self):
        self.assertEqual(self.luong(2)["TongCong"], 0.0)

    def test_cong_tu_tinh_khong_nhap_tay(self):
        self.db.them("BANGCHAMCONG", {"MaNV": 2, "MaCa": 2, "GioVaoThucTe": "19:00", "GioRaThucTe": "05:00",
                                      "NgayChamCong": "2026-11-03", "Cong": 999})
        self.assertFalse(self.db["BANGCHAMCONG"]["Cong"].fillna(0).eq(999).any())

    def test_gio_sai_bi_chan_va_hoan_tac(self):
        so_dong = len(self.db["BANGCHAMCONG"])
        with self.assertRaises(ValueError):
            self.db.them("BANGCHAMCONG", {"MaNV": 2, "MaCa": 1, "GioVaoThucTe": "16:00",
                                          "GioRaThucTe": "08:00", "NgayChamCong": "2026-11-04"})
        self.assertEqual(len(self.db["BANGCHAMCONG"]), so_dong)

    def test_sua_luong_co_ban_cap_nhat_luong(self):
        self.db.sua("NHANVIEN", "LuongCoBan", 1000000, "MaNV", 1)
        self.assertEqual(self.luong(1)["LuongThucNhan"], 1000000 * 2.575 - 50000 + 200000)


if __name__ == "__main__":
    unittest.main()
