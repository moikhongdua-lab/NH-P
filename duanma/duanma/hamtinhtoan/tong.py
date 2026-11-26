from hamtinhtoan.co_ban import la_trong, kiem_cot
from hamtinhtoan.gom_nhom import GomNhom
from ham_cac_phuong_thuc import isinstance_


def tong_va_dem(ds):
    """(tổng, số ô có giá trị) của một list. Ô trống bị bỏ qua."""
    t = 0
    n = 0
    for v in ds:
        if not la_trong(v):
            try:
                t += v
            except TypeError:
                raise ValueError("Cột không phải kiểu số nên không tính tổng được") from None
            n += 1
    return t, n


def tong(x, cot):
    """x là bảng  -> bảng 1 dòng {Tong_<cột>: [tổng]}
       x là GomNhom -> mỗi nhóm một dòng {<cột gom>: [...], Tong_<cột>: [...]}"""
    ten = "Tong_" + cot
    
    # Thay isinstance -> isinstance_
    if isinstance_(x, GomNhom):
        kiem_cot(x.mau, cot)
        kq = {x.cot_nhom: [], ten: []}
        for k in x.khoa:
            t, n = tong_va_dem(x.nhom[k][cot])
            kq[x.cot_nhom].append(k)
            if n > 0:
                kq[ten].append(t)
            else:
                kq[ten].append(None)
        return kq
        
    kiem_cot(x, cot)
    t, n = tong_va_dem(x[cot])
    if n > 0:
        return {ten: [t]}
    return {ten: [None]}