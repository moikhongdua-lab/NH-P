from hamtinhtoan.co_ban import kiem_cot
from hamtinhtoan.gom_nhom import GomNhom
from hamtinhtoan.tong import tong_va_dem


def tinh_chung_binh(x, cot):
    """Trung bình của cột (bỏ qua ô trống). Cách dùng giống `tong`."""
    ten = "TB_" + cot
    if isinstance(x, GomNhom):
        kiem_cot(x.mau, cot)
        kq = {x.cot_nhom: [], ten: []}
        for k in x.khoa:
            t, n = tong_va_dem(x.nhom[k][cot])
            kq[x.cot_nhom].append(k)
            if n > 0:
                kq[ten].append(t / n)
            else:
                kq[ten].append(None)
        return kq
    kiem_cot(x, cot)
    t, n = tong_va_dem(x[cot])
    if n > 0:
        return {ten: [t / n]}
    return {ten: [None]}
