import pandas as pd
from database.kieu_dl import ep_kieu, parse_time, la_null

GIO_CHUAN = 8.0        # 1 công = 8 giờ
HE_SO_TANG_CA = 1.5    # giờ vượt 8h; KHÔNG nhân HeSoCa
GIO_TOI_DA = 16        # làm quá số giờ này một ca => coi là nhập sai, báo lỗi

SCHEMA_CHAMCONG = {
    "BANGCHAMCONG": {
        "cols": {"MaCC": "int", "MaNV": "int", "MaCa": "int",
                 "GioVaoThucTe": "time", "GioRaThucTe": "time",
                 "NgayChamCong": "date", "Cong": "float"},
        "pk": ["MaCC"],
        "fk": {"MaNV": ("NHANVIEN", "MaNV"), "MaCa": ("CALAMVIEC", "MaCa")},
        "notnull": ["MaNV", "MaCa", "NgayChamCong"],   # giờ vào/ra được phép trống (quên chấm)
        "unique": [["MaNV", "MaCa", "NgayChamCong"]],
        "derived": ["Cong"],                            # tự tính, không cho nhập tay
    },
}


def _phut(t: str) -> float:
    h, m, s = (int(x) for x in t.split(":"))
    return h * 60 + m + s / 60


def la_ca_dem(bat_dau, ket_thuc) -> bool:
    """Ca qua đêm: giờ kết thúc nhỏ hơn giờ bắt đầu (vd 19:00 -> 05:00)."""
    bd, kt = parse_time(bat_dau), parse_time(ket_thuc)
    if bd is None or kt is None:
        return False
    return _phut(kt) < _phut(bd)


def so_gio_lam(vao, ra, ca_dem: bool = False) -> float | None:
    """Số giờ làm. Thiếu giờ vào/ra -> None.
    Giờ vào = giờ ra, hoặc ra < vào ở ca không phải ca đêm, hoặc quá GIO_TOI_DA -> ValueError."""
    vao, ra = parse_time(vao), parse_time(ra)
    if vao is None or ra is None:
        return None
    p_vao, p_ra = _phut(vao), _phut(ra)
    if p_ra == p_vao:
        raise ValueError(f"giờ vào và giờ ra trùng nhau ({vao}), cần người kiểm tra lại")
    if p_ra < p_vao:
        if not ca_dem:
            raise ValueError(f"giờ ra {ra} sớm hơn giờ vào {vao} nhưng ca này không phải ca đêm")
        p_ra += 24 * 60
    gio = (p_ra - p_vao) / 60
    if gio > GIO_TOI_DA:
        raise ValueError(f"làm {gio:.1f} giờ (vào {vao}, ra {ra}) vượt {GIO_TOI_DA} giờ, cần kiểm tra lại")
    return gio


def tinh_cong(vao, ra, he_so, ca_dem: bool = False) -> float | None:
    """giờ <= 8: giờ/8 * HeSoCa;  giờ > 8: 1*HeSoCa + (giờ-8)/8 * 1.5."""
    gio = so_gio_lam(vao, ra, ca_dem)
    if gio is None or la_null(he_so):
        return None
    he_so = float(he_so)
    if gio <= GIO_CHUAN:
        return round(gio / GIO_CHUAN * he_so, 4)
    return round(he_so + (gio - GIO_CHUAN) / GIO_CHUAN * HE_SO_TANG_CA, 4)


def cap_nhat_cong(chamcong: pd.DataFrame, calamviec: pd.DataFrame) -> pd.DataFrame:
    """Tính lại cột Cong cho toàn bộ BANGCHAMCONG. Gom hết lỗi giờ rồi báo một lần."""
    ca = {}
    for ma, hs, bd, kt in zip(calamviec["MaCa"], calamviec["HeSoCa"],
                              calamviec["GioBatDau"], calamviec["GioKetThuc"]):
        ca[int(ma)] = (hs, la_ca_dem(bd, kt))

    chamcong = chamcong.copy()
    cong, loi = [], []
    for ma_cc, vao, ra, ma_ca, ngay in zip(chamcong["MaCC"], chamcong["GioVaoThucTe"],
                                           chamcong["GioRaThucTe"], chamcong["MaCa"],
                                           chamcong["NgayChamCong"]):
        he_so, dem = ca.get(int(ma_ca), (None, False))
        try:
            cong.append(tinh_cong(vao, ra, he_so, dem))
        except ValueError as e:
            loi.append(f"  chấm công MaCC={ma_cc} (ngày {str(ngay)[:10]}): {e}")
            cong.append(None)
    if loi:
        raise ValueError("Giờ chấm công không hợp lệ:\n" + "\n".join(loi))
    chamcong["Cong"] = cong
    return ep_kieu("BANGCHAMCONG", chamcong)
