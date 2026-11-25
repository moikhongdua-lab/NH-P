import tempfile
import unittest

from database import CSDL


class CoDB(unittest.TestCase):
    """Mỗi test có một CSDL riêng ghi vào thư mục tạm (không đụng CSV thật)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.thu_muc = self._tmp.name
        self.db = CSDL(thu_muc=self.thu_muc)
        self.db.thang_hien_tai = lambda: (11, 2026)
        d = self.db
        d.them("PHONGBAN", [{"TenPB": "Kế toán"}, {"TenPB": "Kỹ thuật"}])
        d.them("CALAMVIEC", [
            {"MaCa": 1, "TenCa": "Ca ngày", "GioBatDau": "07:00", "GioKetThuc": "16:00", "HeSoCa": 1.0},
            {"MaCa": 2, "TenCa": "Ca đêm", "GioBatDau": "19:00", "GioKetThuc": "05:00", "HeSoCa": 1.2}])
        d.them("NHANVIEN", [
            {"MaNV": 1, "HoTen": "Nguyễn Văn An", "GioiTinh": "nam", "LuongCoBan": 500000, "MaPB": 1},
            {"MaNV": 2, "HoTen": "Na", "GioiTinh": "Nữ", "LuongCoBan": 600000, "MaPB": 2}])
