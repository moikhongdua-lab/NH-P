from hamtinhtoan.co_ban import la_trong, so_hang, kiem_cot


def ghep_bang(bang1, bang2, cot, kieu_ghep="inner", cot2=None):
    """Nối hai bảng theo quy tắc  bang1[cot] = bang2[cot2]  (cot2 mặc định cùng tên cot).
    kieu_ghep = "inner": chỉ giữ dòng khớp;  "left": giữ mọi dòng bang1, không khớp thì phần bang2 để trống.
    Khóa trống không bao giờ khớp. Cột trùng tên của bang2 được đổi thành <tên>_2."""
    if cot2 is None:
        cot2 = cot
    if kieu_ghep != "inner" and kieu_ghep != "left":
        raise ValueError("kieu_ghep chỉ nhận 'inner' hoặc 'left'")
    kiem_cot(bang1, cot)
    kiem_cot(bang2, cot2)

    ten_moi = {}                                    # tên cột bang2 trong kết quả
    for c in bang2:
        if c == cot2 and cot2 == cot:
            continue                                # cột khóa trùng tên: giữ một cột
        if c in bang1:
            ten_moi[c] = c + "_2"
        else:
            ten_moi[c] = c

    kq = {}
    for c in bang1:
        kq[c] = []
    for c in ten_moi:
        kq[ten_moi[c]] = []

    chi_muc = {}                                    # khóa -> các dòng của bang2
    n2 = so_hang(bang2)
    j = 0
    while j < n2:
        k = bang2[cot2][j]
        if not la_trong(k):
            if k not in chi_muc:
                chi_muc[k] = []
            chi_muc[k].append(j)
        j += 1

    n1 = so_hang(bang1)
    i = 0
    while i < n1:
        k = bang1[cot][i]
        co_khop = False
        if not la_trong(k) and k in chi_muc:
            for j in chi_muc[k]:
                co_khop = True
                for c in bang1:
                    kq[c].append(bang1[c][i])
                for c in ten_moi:
                    kq[ten_moi[c]].append(bang2[c][j])
        if not co_khop and kieu_ghep == "left":
            for c in bang1:
                kq[c].append(bang1[c][i])
            for c in ten_moi:
                kq[ten_moi[c]].append(None)
        i += 1
    return kq
