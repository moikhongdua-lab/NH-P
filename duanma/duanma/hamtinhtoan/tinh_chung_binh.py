from hamtinhtoan.co_ban import kiem_cot
from hamtinhtoan.gom_nhom import GomNhom
from hamtinhtoan.tong import tong_va_dem
from hamtinhtoan.co_ban import kiem_cot, la_trong
from hamtinhtoan.gom_nhom import GomNhom


def tinh_chung_binh(x, cot):
    """Trung bình của cột (bỏ qua ô trống). Cách dùng giống `tong`."""
    ten = "TB_" + cot

    # Có phân nhóm: mỗi nhóm cho ra một dòng trung bình
    if type(x) == GomNhom:
        kiem_cot(x.mau, cot)
        kq = {x.cot_nhom: [], ten: []}
        for i in range(len(x.khoa)):
            k = x.khoa[i]
            ds = x.nhom[k][cot]
            tong = 0
            dem = 0
            for j in range(len(ds)):
                if not la_trong(ds[j]):
                    tong = tong + ds[j]
                    dem = dem + 1
            kq[x.cot_nhom].append(k)
            if dem > 0:
                kq[ten].append(tong / dem)
            else:
                kq[ten].append(None)
        return kq

    # Không phân nhóm: một dòng duy nhất
    kiem_cot(x, cot)
    ds = x[cot]
    tong = 0
    dem = 0
    for j in range(len(ds)):
        if not la_trong(ds[j]):
            tong = tong + ds[j]
            dem = dem + 1
    if dem > 0:
        return {ten: [tong / dem]}
    return {ten: [None]}
