from hamtinhtoan.co_ban import la_trong, so_hang, chon_hang, kiem_cot
from hamtinhtoan.cu_phap import tach_phep_gia_tri, bo_nhay
from database.kieu_dl import doi_theo_mau


def loc_o(bang, cot, dieu_kien):
    """Giữ các dòng có ô ở cột `cot` thỏa điều kiện.
    dieu_kien = phép toán + giá trị:  '> 500000', '<= 3', "== Nam", '!= 2026-11-02'.
    Ô trống không bao giờ thỏa điều kiện. So sánh chữ không phân biệt hoa/thường."""
    kiem_cot(bang, cot)
    phep, chuoi = tach_phep_gia_tri(dieu_kien)
    chuoi = bo_nhay(chuoi)[0]

    mau = None
    for v in bang[cot]:
        if not la_trong(v):
            mau = v
            break
    chi_so = []
    if mau is not None:
        try:
            gt = doi_theo_mau(chuoi, mau)
        except ValueError as e:
            raise ValueError(f"Điều kiện trên cột {cot}: {e}") from None
        gt_chu = isinstance(gt, str)
        if gt_chu:
            gt = gt.casefold()
        n = so_hang(bang)
        i = 0
        while i < n:
            v = bang[cot][i]
            if not la_trong(v):
                if gt_chu and isinstance(v, str):
                    v = v.casefold()
                try:
                    if phep == ">":
                        ok = v > gt
                    elif phep == "<":
                        ok = v < gt
                    elif phep == ">=":
                        ok = v >= gt
                    elif phep == "<=":
                        ok = v <= gt
                    elif phep == "==":
                        ok = v == gt
                    else:
                        ok = v != gt
                except TypeError:
                    raise ValueError(f"Không so sánh được cột {cot} với {chuoi!r}") from None
                if ok:
                    chi_so.append(i)
            i += 1
    return chon_hang(bang, chi_so)
