from hamtinhtoan.co_ban import la_trong, so_hang, bang_rong_giong, kiem_cot


class GomNhom:
    """Kết quả của gom_nhom: các dòng chia theo giá trị của cột `cot_nhom`."""
    def __init__(self, cot_nhom, khoa, nhom, mau):
        self.cot_nhom = cot_nhom
        self.khoa = khoa        # các giá trị nhóm, theo thứ tự xuất hiện
        self.nhom = nhom        # {giá trị nhóm: bảng con}
        self.mau = mau          # bảng rỗng cùng cột (để biết tên cột)


def gom_nhom(bang, cot_nhom):
    """Gom các dòng có cùng giá trị ở cột `cot_nhom`. Dòng có khóa nhóm trống bị bỏ qua."""
    kiem_cot(bang, cot_nhom)
    khoa = []
    nhom = {}
    n = so_hang(bang)
    i = 0
    while i < n:
        k = bang[cot_nhom][i]
        if not la_trong(k):
            if k not in nhom:
                nhom[k] = bang_rong_giong(bang)
                khoa.append(k)
            for c in bang:
                nhom[k][c].append(bang[c][i])
        i += 1
    return GomNhom(cot_nhom, khoa, nhom, bang_rong_giong(bang))


def gop_lai(g):
    """Các nhóm -> một bảng (các dòng cùng nhóm đứng cạnh nhau)."""
    kq = bang_rong_giong(g.mau)
    for k in g.khoa:
        for c in kq:
            for v in g.nhom[k][c]:
                kq[c].append(v)
    return kq
