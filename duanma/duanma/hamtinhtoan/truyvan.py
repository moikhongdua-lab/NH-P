"""Dịch và thực thi câu truy vấn TÌM KIẾM."""
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

# Import các hàm tự chế
from ham_cac_phuong_thuc import strip, isinstance_, startswith, _casefold, find, isspace

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

# ================= CÁC HÀM PHỤ TRỢ (Tự viết) =================

def _join(ds, ky_tu_noi):
    """Giống "ky_tu_noi".join(ds)"""
    kq = ""
    for i in range(do_dai(ds)):
        if i > 0:
            kq += ky_tu_noi
        kq += ds[i]
    return kq

def _rfind(s, ky_tu):
    """Giống s.rfind(ky_tu)"""
    kq = -1
    for i in range(do_dai(s)):
        if s[i] == ky_tu:
            kq = i
    return kq

def _thay_the(s, cu, moi):
    """Giống s.replace(cu, moi)"""
    kq = ""
    i = 0
    while i < do_dai(s):
        if s[i:i+do_dai(cu)] == cu:
            kq += moi
            i += do_dai(cu)
        else:
            kq += s[i]
            i += 1
    return kq

def _bo_khoang_trang(s):
    """Bỏ toàn bộ khoảng trắng trong chuỗi"""
    kq = ""
    for ch in s:
        if not isspace(ch):
            kq += ch
    return kq

def _tach_lan_dau(s, ky_tu):
    """Tách chuỗi tại vị trí xuất hiện ĐẦU TIÊN của ky_tu"""
    for i in range(do_dai(s)):
        if s[i] == ky_tu:
            return s[:i], s[i+1:]
    return s, ""

# =============================================================

class _NguCanh:
    def __init__(self, db):
        self.db = db
        self.dm = db.dm
        self.nhat_ky = []


def _mo_ta(kq):
    if isinstance_(kq, GomNhom):
        return str(do_dai(kq.khoa)) + " nhóm theo " + kq.cot_nhom
    return str(so_hang(kq)) + " dòng × " + str(do_dai(kq)) + " cột"


def _so_tham_so(a, tu, den, cu_phap):
    n = do_dai(a)
    if not (tu <= n <= den):
        raise ValueError("Sai số tham số.\nCú pháp: " + cu_phap)


def _bang_tu(nc, text):
    kq = _tinh(nc, text)
    if isinstance_(kq, GomNhom):
        raise ValueError("'gom' cho ra các nhóm; hãy dùng dem / tong / tinh_chung_binh để tính trên nhóm "
                         "(hoặc để gom ở ngoài cùng).")
    return kq


def _cot_trong(bang, text):
    t = bo_nhay(text)[0]
    if "." in t:
        i = _rfind(t, ".")
        t = t[i+1:]
    k = chuan_ten(t)
    for c in bang:
        if chuan_ten(c) == k:
            return c
    ds_cot = []
    for c in bang:
        ds_cot.append(c)
    raise ValueError("Không có cột " + str(text) + ". Các cột hiện có: " + _join(ds_cot, ", "))


def _h_in(nc, a):
    _so_tham_so(a, 1, 99, CU_PHAP_HAM["in"])
    x = _bang_tu(nc, a[0])
    if do_dai(a) == 1:
        return x
    kq = {}
    for i in range(1, do_dai(a)):
        c = _cot_trong(x, a[i])
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
    
    # Copy list a
    ds_a = []
    for v in a:
        ds_a.append(v)
    a = ds_a
    
    if do_dai(a) == 3 and chuan_ten(a[2]) in ("trai", "left"):
        a = a[:2] + [""] + a[2:]
        
    kieu = "inner"
    if do_dai(a) == 4:
        if chuan_ten(a[3]) not in ("trai", "left"):
            raise ValueError("Tham số thứ 4 của ghep chỉ nhận 'trai' (giữ mọi dòng bảng 1)")
        kieu = "left"
        
    cot1 = None
    cot2 = None
    if do_dai(a) >= 3 and strip(a[2]):
        cot1 = a[2]
        cot2 = a[2]
    elif _la_ten_bang(nc, a[0]) and _la_ten_bang(nc, a[1]):
        noi = tim_ket_noi(nc.dm, tim_bang(nc.dm, a[0]), tim_bang(nc.dm, a[1]))
        if noi is not None:
            cot1 = noi[0]
            cot2 = noi[1]
            
    x = _bang_tu(nc, a[0])
    y = _bang_tu(nc, a[1])
    
    if cot1 is None:
        chung = []
        for c in x:
            for c2 in y:
                if c == c2:
                    chung.append(c)
                    break
        if do_dai(chung) != 1:
            raise ValueError("Không tự dò được cột nối (hai bảng không có kết nối FK trực tiếp hoặc có nhiều "
                             "cột chung). Hãy ghi rõ: ghep(bảng1, bảng2, cột)")
        cot1 = chung[0]
        cot2 = chung[0]
    else:
        cot1 = _cot_trong(x, cot1)
        cot2 = _cot_trong(y, cot2)
    return ghep_bang(x, y, cot1, kieu, cot2)


def _h_gom(nc, a):
    _so_tham_so(a, 2, 2, CU_PHAP_HAM["gom"])
    x = _bang_tu(nc, a[0])
    return gom_nhom(x, _cot_trong(x, a[1]))


def _bang_hoac_nhom(nc, text):
    kq = _tinh(nc, text)
    mau = kq.mau if isinstance_(kq, GomNhom) else kq
    return kq, mau


def _h_dem(nc, a):
    _so_tham_so(a, 1, 2, CU_PHAP_HAM["dem"])
    x, mau = _bang_hoac_nhom(nc, a[0])
    cot = None
    if do_dai(a) == 2:
        cot = _cot_trong(mau, a[1])
    return dem(x, cot)


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
    if do_dai(a) == 3:
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
        n = int(strip(a[2]))
    except ValueError:
        raise ValueError("x trong top(...) phải là số nguyên, nhận được " + str(a[2])) from None
    return top_x(x, _cot_trong(x, a[1]), n)


HAM = {
    "in": _h_in, "loc": _h_loc, "loc_o": _h_loc, "ghep": _h_ghep, "ghep_bang": _h_ghep,
    "gom": _h_gom, "gom_nhom": _h_gom, "dem": _h_dem, "tong": _h_tong,
    "tinh_chung_binh": _h_tb, "trung_binh": _h_tb, "tb": _h_tb,
    "sap_xep": _h_sap_xep, "sx": _h_sap_xep, "top": _h_top, "top_x": _h_top,
}
HAM_CO_BI_DANH = ("dem", "tong", "tinh_chung_binh", "trung_binh", "tb")


def _tach_bi_danh(tham_so):
    n = do_dai(tham_so)
    if n > 0:
        cuoi = tham_so[n-1]
        khong_khoang = _bo_khoang_trang(cuoi)
        khong_khoang_thuong = _casefold(khong_khoang)
        if startswith(khong_khoang_thuong, "as="):
            phan_sau = _tach_lan_dau(cuoi, "=")[1]
            ten = bo_nhay(phan_sau)[0]
            if not ten:
                raise ValueError("as= chưa có tên. Ví dụ: as='SoNguoi'")
            
            ds_moi = []
            for i in range(n - 1):
                ds_moi.append(tham_so[i])
            return ds_moi, ten
    return tham_so, None


def _doi_ten_cot_cuoi(kq, ten):
    cuoi = None
    for c in kq:
        cuoi = c  # lấy phần tử cuối
        
    if ten != cuoi and ten in kq:
        raise ValueError("Tên cột " + str(ten) + " đã có trong kết quả")
        
    kq_moi = {}
    for c in kq:
        if c == cuoi:
            kq_moi[ten] = kq[c]
        else:
            kq_moi[c] = kq[c]
    return kq_moi


def _tinh(nc, s):
    s = strip(s)
    if not s:
        raise ValueError("Có một tham số đang để trống")
        
    p = find(che(s, False), "(")
    if p > 0 and tim_ngoac_dong(s, p) == do_dai(s) - 1:
        ten = chuan_ten(s[:p])
        ten = _thay_the(ten, " ", "_")
        
        if ten not in HAM:
            ds_ham = []
            for k in CU_PHAP_HAM:
                ds_ham.append(k)
            raise ValueError("Không có hàm " + str(strip(s[:p])) + ". Các hàm: " + _join(ds_ham, ", "))
            
        trong = s[p + 1:-1]
        
        tham_so = []
        if strip(trong):
            for t in tach(trong, ","):
                tham_so.append(strip(t))
                
        n_ts = do_dai(tham_so)
        if n_ts > 0 and tham_so[n_ts - 1] == "":
            ds_moi = []
            for i in range(n_ts - 1):
                ds_moi.append(tham_so[i])
            tham_so = ds_moi
            
        bi_danh = None
        if ten in HAM_CO_BI_DANH:
            tham_so, bi_danh = _tach_bi_danh(tham_so)
            
        kq = HAM[ten](nc, tham_so)
        if bi_danh:
            kq = _doi_ten_cot_cuoi(kq, bi_danh)
            
        chuoi_log = s
        if do_dai(s) > 90:
            chuoi_log = s[:87] + "..."
        nc.nhat_ky.append(chuoi_log + "   →   " + _mo_ta(kq))
        return kq
        
    b = tim_bang(nc.dm, s)
    if b is None:
        ds_bang = []
        for b2 in nc.dm["bang"]:
            ds_bang.append(b2)
        raise ValueError("Không hiểu " + str(s) + ": không phải tên bảng hay hàm. Các bảng: " + _join(ds_bang, ", "))
    return doc_bang(nc.db.bang[b])


def thuc_thi(db, truy_van):
    nc = _NguCanh(db)
    kq = _tinh(nc, truy_van)
    if isinstance_(kq, GomNhom):
        kq = gop_lai(kq)
    return kq, nc.nhat_ky