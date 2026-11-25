from hamtinhtoan.co_ban import so_hang, bang_rong_giong, kiem_cot
from hamtinhtoan.sap_xep import sap_xep


def top_x(bang, cot, x):
    """x dòng có giá trị lớn nhất ở cột `cot` (dùng hàm sắp xếp giảm dần)."""
    kiem_cot(bang, cot)
    if x < 0:
        raise ValueError("x phải là số nguyên không âm")
    da_xep = sap_xep(bang, cot, True)
    kq = bang_rong_giong(da_xep)
    n = so_hang(da_xep)
    i = 0
    while i < n and i < x:
        for c in da_xep:
            kq[c].append(da_xep[c][i])
        i += 1
    return kq
