from hamtinhtoan.co_ban import la_trong, so_hang, do_dai, kiem_cot
from hamtinhtoan.gom_nhom import GomNhom


def dem(x, cot=None):
    """Đếm.
    dem(GomNhom)        -> số dòng của từng nhóm
    dem(GomNhom, cot)   -> số ô không trống của `cot` trong từng nhóm
    dem(bảng)           -> tổng số dòng
    dem(bảng, cot)      -> mỗi giá trị khác nhau của `cot` xuất hiện bao nhiêu lần
    Ô trống ở cột đếm bị bỏ qua (như COUNT(cột) trong SQL)."""
    if isinstance(x, GomNhom):
        if cot is None:
            kq = {x.cot_nhom: [], "SoLuong": []}
            for k in x.khoa:
                kq[x.cot_nhom].append(k)
                kq["SoLuong"].append(so_hang(x.nhom[k]))
            return kq
        kiem_cot(x.mau, cot)
        kq = {x.cot_nhom: [], "Dem_" + cot: []}
        for k in x.khoa:
            n = 0
            for v in x.nhom[k][cot]:
                if not la_trong(v):
                    n += 1
            kq[x.cot_nhom].append(k)
            kq["Dem_" + cot].append(n)
        return kq

    if cot is None:
        return {"SoLuong": [so_hang(x)]}
    kiem_cot(x, cot)
    gia_tri = []
    so_lan = []
    vi_tri = {}
    for v in x[cot]:
        if la_trong(v):
            continue
        if v in vi_tri:
            so_lan[vi_tri[v]] += 1
        else:
            vi_tri[v] = do_dai(gia_tri)
            gia_tri.append(v)
            so_lan.append(1)
    return {cot: gia_tri, "SoLuong": so_lan}
