"""Dịch và thực thi câu truy vấn TÌM KIẾM.

Câu truy vấn là các hàm lồng nhau, tính từ ngoặc trong ra ngoài:
    in(loc(ghep(NHANVIEN, BANGLUONG), HoTen == 'Thanh Tùng'), HoTen, LuongThucNhan)

Hàm:  in, loc, ghep, gom, dem, tong, tinh_chung_binh, sap_xep, top
Cho phép dấu phẩy cuối:  in(NHANVIEN, HoTen, )
Đặt tên cột kết quả:     dem(NHANVIEN, GioiTinh, as='SoNguoi')   (dùng được với dem, tong, tinh_chung_binh)
"""
from database.map_dulieu.map import tim_bang, tim_ket_noi, chuan_ten
from hamtinhtoan.co_ban import doc_bang, so_hang, do_dai
from hamtinhtoan.cu_phap import che, tach, tim_ngoac_dong, tach_dieu_kien, bo_nhay
from hamtinhtoan.gom_nhom import GomNhom, gom_nhom, gop_lai
from hamtinhtoan.dem import dem
from hamtinhtoan.tong import tong
from hamtinhtoan.tinh_chung_binh import tinh_chung_binh
from hamtinhtoan.sap_xep import sap_xep
from hamtinhtoan.top_x import top_x
from hamtinhtoan.loc import loc_o
from hamtinhtoan.ghep_bang import ghep_bang

CU_PHAP_HAM = {
    "in":              "in(bảng, cột1, cột2, ...)       chọn các cột để in (chỉ ghi bảng = in tất cả)",
    "loc":             "loc(bảng, cột > giá trị)         lọc ô; phép toán: > < >= <= == !=",
    "ghep":            "ghep(bảng1, bảng2[, cột][, trai])  nối theo quy tắc '='; để trống cột = tự dò theo kết nối FK",
    "gom":             "gom(bảng, cột)                   gom các dòng cùng giá trị ở cột",
    "dem":             "dem(bảng[, cột][, as='tên']) hoặc dem(gom(...)[, cột])  đếm số phần tử cùng giá trị / đếm theo nhóm",
    "tong":            "tong(bảng, cột[, as='tên']) hoặc tong(gom(...), cột)",
    "tinh_chung_binh": "tinh_chung_binh(bảng, cột[, as='tên']) hoặc tinh_chung_binh(gom(...), cột)",
    "sap_xep":         "sap_xep(bảng, cột[, giam])       mặc định tăng dần",
    "top":             "top(bảng, cột, x)                x dòng lớn nhất của cột",
}


class _NguCanh:
    def __init__(self, db):
        self.db = db
        self.dm = db.dm
        self.nhat_ky = []          # thứ tự các bước đã tính (trong ra ngoài)


def _mo_ta(kq):
    if isinstance(kq, GomNhom):
        return f"{do_dai(kq.khoa)} nhóm theo {kq.cot_nhom}"
    return f"{so_hang(kq)} dòng × {do_dai(kq)} cột"


def _so_tham_so(a, tu, den, cu_phap):
    if not (tu <= len(a) <= den):
        raise ValueError(f"Sai số tham số.\nCú pháp: {cu_phap}")


def _bang_tu(nc, text):
    kq = _tinh(nc, text)
    if isinstance(kq, GomNhom):
        raise ValueError("'gom' cho ra các nhóm; hãy dùng dem / tong / tinh_chung_binh để tính trên nhóm "
                         "(hoặc để gom ở ngoài cùng).")
    return kq


def _cot_trong(bang, text):
    t = bo_nhay(text)[0]
    if "." in t:
        t = t[t.rfind(".") + 1:]
    k = chuan_ten(t)
    for c in bang:
        if chuan_ten(c) == k:
            return c
    raise ValueError(f"Không có cột {text!r}. Các cột hiện có: " + ", ".join(bang))


def _h_in(nc, a):
    _so_tham_so(a, 1, 99, CU_PHAP_HAM["in"])
    x = _bang_tu(nc, a[0])
    if len(a) == 1:
        return x
    kq = {}
    for t in a[1:]:
        c = _cot_trong(x, t)
        kq[c] = x[c]
    return kq


def _h_loc(nc, a):
    _so_tham_so(a, 2, 2, CU_PHAP_HAM["loc"])
    x = _bang_tu(nc, a[0])
    cot, phep, gt = tach_dieu_kien(a[1])
    return loc_o(x, _cot_trong(x, cot), phep + " " + gt)


def _la_ten_bang(nc, text):
    return "(" not in text and tim_bang(nc.dm, text) is not None


def _h_ghep(nc, a):
    _so_tham_so(a, 2, 4, CU_PHAP_HAM["ghep"])
    a = list(a)
    if len(a) == 3 and chuan_ten(a[2]) in ("trai", "left"):     # ghep(A, B, trai): bỏ trống cột
        a.insert(2, "")
    kieu = "inner"
    if len(a) == 4:
        if chuan_ten(a[3]) not in ("trai", "left"):
            raise ValueError("Tham số thứ 4 của ghep chỉ nhận 'trai' (giữ mọi dòng bảng 1)")
        kieu = "left"
    cot1 = cot2 = None
    if len(a) >= 3 and a[2].strip():
        cot1 = cot2 = a[2]
    elif _la_ten_bang(nc, a[0]) and _la_ten_bang(nc, a[1]):       # dò theo kết nối FK trong data map
        noi = tim_ket_noi(nc.dm, tim_bang(nc.dm, a[0]), tim_bang(nc.dm, a[1]))
        if noi is not None:
            cot1, cot2 = noi
    x = _bang_tu(nc, a[0])
    y = _bang_tu(nc, a[1])
    if cot1 is None:                                              # cuối cùng: cột chung duy nhất
        chung = [c for c in x if c in y]
        if len(chung) != 1:
            raise ValueError("Không tự dò được cột nối (hai bảng không có kết nối FK trực tiếp hoặc có nhiều "
                             "cột chung). Hãy ghi rõ: ghep(bảng1, bảng2, cột)")
        cot1 = cot2 = chung[0]
    else:
        cot1, cot2 = _cot_trong(x, cot1), _cot_trong(y, cot2)
    return ghep_bang(x, y, cot1, kieu, cot2)


def _h_gom(nc, a):
    _so_tham_so(a, 2, 2, CU_PHAP_HAM["gom"])
    x = _bang_tu(nc, a[0])
    return gom_nhom(x, _cot_trong(x, a[1]))


def _bang_hoac_nhom(nc, text):
    kq = _tinh(nc, text)
    return kq, (kq.mau if isinstance(kq, GomNhom) else kq)


def _h_dem(nc, a):
    _so_tham_so(a, 1, 2, CU_PHAP_HAM["dem"])
    x, mau = _bang_hoac_nhom(nc, a[0])
    return dem(x, _cot_trong(mau, a[1]) if len(a) == 2 else None)


def _h_tong(nc, a):
    _so_tham_so(a, 2, 2, CU_PHAP_HAM["tong"])
    x, mau = _bang_hoac_nhom(nc, a[0])
    return tong(x, _cot_trong(mau, a[1]))


def _h_tb(nc, a):
    _so_tham_so(a, 2, 2, CU_PHAP_HAM["tinh_chung_binh"])
    x, mau = _bang_hoac_nhom(nc, a[0])
    return tinh_chung_binh(x, _cot_trong(mau, a[1]))


def _h_sap_xep(nc, a):
    _so_tham_so(a, 2, 3, CU_PHAP_HAM["sap_xep"])
    x = _bang_tu(nc, a[0])
    giam = False
    if len(a) == 3:
        chieu = chuan_ten(a[2])
        if chieu in ("giam", "desc"):
            giam = True
        elif chieu not in ("tang", "asc"):
            raise ValueError("Tham số thứ 3 của sap_xep chỉ nhận 'tang' hoặc 'giam'")
    return sap_xep(x, _cot_trong(x, a[1]), giam)


def _h_top(nc, a):
    _so_tham_so(a, 3, 3, CU_PHAP_HAM["top"])
    x = _bang_tu(nc, a[0])
    try:
        n = int(a[2].strip())
    except ValueError:
        raise ValueError(f"x trong top(...) phải là số nguyên, nhận được {a[2]!r}") from None
    return top_x(x, _cot_trong(x, a[1]), n)


HAM = {
    "in": _h_in, "loc": _h_loc, "loc_o": _h_loc, "ghep": _h_ghep, "ghep_bang": _h_ghep,
    "gom": _h_gom, "gom_nhom": _h_gom, "dem": _h_dem, "tong": _h_tong,
    "tinh_chung_binh": _h_tb, "trung_binh": _h_tb, "tb": _h_tb,
    "sap_xep": _h_sap_xep, "sx": _h_sap_xep, "top": _h_top, "top_x": _h_top,
}
HAM_CO_BI_DANH = ("dem", "tong", "tinh_chung_binh", "trung_binh", "tb")


def _tach_bi_danh(tham_so):
    """Lấy tham số cuối dạng as='tên' ra khỏi danh sách. -> (tham số còn lại, tên hoặc None)."""
    if tham_so and tham_so[-1].replace(" ", "").lower().startswith("as="):
        ten = bo_nhay(tham_so[-1].split("=", 1)[1])[0]
        if not ten:
            raise ValueError("as= chưa có tên. Ví dụ: as='SoNguoi'")
        return tham_so[:-1], ten
    return tham_so, None


def _doi_ten_cot_cuoi(kq, ten):
    cuoi = list(kq)[-1]
    if ten != cuoi and ten in kq:
        raise ValueError(f"Tên cột {ten!r} đã có trong kết quả")
    return {(ten if c == cuoi else c): kq[c] for c in kq}


def _tinh(nc, s):
    """Tính một biểu thức: lời gọi hàm (tính các tham số bên trong trước) hoặc tên bảng."""
    s = s.strip()
    if not s:
        raise ValueError("Có một tham số đang để trống")
    p = che(s, False).find("(")
    if p > 0 and tim_ngoac_dong(s, p) == len(s) - 1:
        ten = chuan_ten(s[:p]).replace(" ", "_")
        if ten not in HAM:
            raise ValueError(f"Không có hàm {s[:p].strip()!r}. Các hàm: " + ", ".join(CU_PHAP_HAM))
        trong = s[p + 1:-1]
        tham_so = [t.strip() for t in tach(trong, ",")] if trong.strip() else []
        if tham_so and tham_so[-1] == "":                 # cho phép dấu phẩy cuối: in(NHANVIEN, )
            tham_so.pop()
        bi_danh = None
        if ten in HAM_CO_BI_DANH:
            tham_so, bi_danh = _tach_bi_danh(tham_so)
        kq = HAM[ten](nc, tham_so)
        if bi_danh:
            kq = _doi_ten_cot_cuoi(kq, bi_danh)
        nc.nhat_ky.append(f"{s if len(s) <= 90 else s[:87] + '...'}   →   {_mo_ta(kq)}")
        return kq
    b = tim_bang(nc.dm, s)
    if b is None:
        raise ValueError(f"Không hiểu {s!r}: không phải tên bảng hay hàm. Các bảng: " + ", ".join(nc.dm["bang"]))
    return doc_bang(nc.db.bang[b])


def thuc_thi(db, truy_van):
    """Trả về (bảng kết quả dạng dict các list, danh sách các bước tính trong ra ngoài).
    Lỗi thì ném ValueError."""
    nc = _NguCanh(db)
    kq = _tinh(nc, truy_van)
    if isinstance(kq, GomNhom):
        kq = gop_lai(kq)
    return kq, nc.nhat_ky
