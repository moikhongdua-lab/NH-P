from hamtinhtoan.co_ban import la_trong, do_dai, chon_hang, kiem_cot


def _tron(trai, phai, khoa, giam):
    """Trộn hai danh sách chỉ số đã xếp. Ổn định: bằng nhau thì giữ thứ tự cũ."""
    kq = []
    i = 0
    j = 0
    nt = do_dai(trai)
    np_ = do_dai(phai)
    while i < nt and j < np_:
        a = khoa[trai[i]]
        b = khoa[phai[j]]
        if giam:
            lay_phai = b > a
        else:
            lay_phai = b < a
        if lay_phai:
            kq.append(phai[j])
            j += 1
        else:
            kq.append(trai[i])
            i += 1
    while i < nt:
        kq.append(trai[i])
        i += 1
    while j < np_:
        kq.append(phai[j])
        j += 1
    return kq


def _sap_chi_so(ds, khoa, giam):
    """Merge sort các chỉ số theo khoa[chỉ số]."""
    n = do_dai(ds)
    if n <= 1:
        return ds
    giua = n // 2
    return _tron(_sap_chi_so(ds[:giua], khoa, giam),
                 _sap_chi_so(ds[giua:], khoa, giam), khoa, giam)


def sap_xep(bang, cot, giam=False):
    """Sắp xếp các dòng theo cột `cot` (tăng dần, hoặc giảm dần nếu giam=True).
    Ô trống luôn nằm cuối."""
    kiem_cot(bang, cot)
    khoa = bang[cot]
    co_gia_tri = []
    trong = []
    i = 0
    for v in khoa:
        if la_trong(v):
            trong.append(i)
        else:
            co_gia_tri.append(i)
        i += 1
    try:
        da_xep = _sap_chi_so(co_gia_tri, khoa, giam)
    except TypeError:
        raise ValueError(f"Cột {cot} lẫn nhiều kiểu dữ liệu nên không sắp xếp được") from None
    for i in trong:
        da_xep.append(i)
    return chon_hang(bang, da_xep)
