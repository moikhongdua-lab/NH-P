import pandas as pd
from database.kieu_dl import ep_kieu, la_null
from database.bang.phucap_thuongphat import LOAI_CONG, LOAI_TRU

SCHEMA_BANGLUONG = {
    "BANGLUONG": {
        "cols": {"MaLuong": "int", "MaNV": "int", "Thang": "int", "Nam": "int",
                 "TongCong": "float", "TongThuongPhuCap": "float",
                 "TongPhat": "float", "LuongThucNhan": "float"},
        "pk": ["MaLuong"],
        "fk": {"MaNV": ("NHANVIEN", "MaNV")},
        "notnull": ["MaNV", "Thang", "Nam"],
        "unique": [["MaNV", "Thang", "Nam"]],
        "khoang": {"Thang": (1, 12)},
        "derived": ["TongCong", "TongThuongPhuCap", "TongPhat", "LuongThucNhan"],
    },
}


def _thang_nam(cot_ngay: pd.Series, thang: int, nam: int) -> pd.Series:
    return (cot_ngay.dt.month == thang) & (cot_ngay.dt.year == nam)


def tinh_luong(luong, chamcong, nhanvien, phucap) -> pd.DataFrame:
    """TongCong, TongThuongPhuCap, TongPhat, LuongThucNhan cho từng dòng BANGLUONG.

    LuongThucNhan = LuongCoBan * TongCong - TongPhat + TongThuongPhuCap
    (Công NA của dòng chấm công thiếu giờ được bỏ qua; LuongCoBan NA -> LuongThucNhan NA.)
    Lưu ý: dùng LuongCoBan HIỆN TẠI cho mọi tháng.
    """
    luong = luong.copy()
    tong_cong, thuong_pc, phat, thuc_nhan = [], [], [], []
    for ma, thang, nam in zip(luong["MaNV"], luong["Thang"], luong["Nam"]):
        ma, thang, nam = int(ma), int(thang), int(nam)

        cc = chamcong[(chamcong["MaNV"] == ma) & _thang_nam(chamcong["NgayChamCong"], thang, nam)]
        tc = float(cc["Cong"].sum())

        pc = phucap[(phucap["MaNV"] == ma) & _thang_nam(phucap["NgayApDung"], thang, nam)]
        tpc = float(pc.loc[pc["Loai"].isin(LOAI_CONG), "SoTien"].sum())
        tp = float(pc.loc[pc["Loai"].isin(LOAI_TRU), "SoTien"].sum())

        lcb = nhanvien.loc[nhanvien["MaNV"] == ma, "LuongCoBan"]
        lcb = lcb.iloc[0] if len(lcb) else None

        tong_cong.append(round(tc, 4))
        thuong_pc.append(tpc)
        phat.append(tp)
        thuc_nhan.append(None if la_null(lcb) else round(float(lcb) * tc - tp + tpc, 2))

    luong["TongCong"] = tong_cong
    luong["TongThuongPhuCap"] = thuong_pc
    luong["TongPhat"] = phat
    luong["LuongThucNhan"] = thuc_nhan
    return ep_kieu("BANGLUONG", luong)
