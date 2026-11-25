"""Dịch và thực thi lệnh XÓA.
Cú pháp:  xóa: '<giá trị>', <cột>, <bảng>      (cần ít nhất 1 trong 3, phần bỏ trống để trống giữa hai dấu phẩy)
Ví dụ:    xóa: '100000', LuongCoBan, NHANVIEN     xóa các dòng của NHANVIEN có LuongCoBan = 100000
          xóa: 'Thanh Tùng', , NHANVIEN           xóa dòng của NHANVIEN có BẤT KỲ ô nào = 'Thanh Tùng'
          xóa: , , PHUCAP_THUONGPHAT              xóa toàn bộ dòng của bảng
"""
from database.map_dulieu.map import tim_bang, tim_cot, tim_cot_hoac_loi
from hamtinhtoan.cu_phap import bo_tu_lenh, tach, bo_nhay

CU_PHAP = "xóa: '<giá trị>', <cột>, <bảng>   (cần ít nhất 1 trong 3)"
VI_DU = "xóa: 'Thanh Tùng', HoTen, NHANVIEN"


def phan_tich(db, lenh):
    """-> (giá trị | None, tên cột | None, tên bảng | None)"""
    con = bo_tu_lenh(lenh, "xoa")
    if con is None:
        raise ValueError(f"Lệnh xóa phải bắt đầu bằng 'xóa'.\nCú pháp: {CU_PHAP}")
    phan = [p.strip() for p in tach(con, ",")]
    if len(phan) > 3:
        raise ValueError(f"Chỉ có tối đa 3 phần (giá trị, cột, bảng), cách nhau bằng dấu phẩy.\nCú pháp: {CU_PHAP}")
    gia_tri = cot = bang = None
    if len(phan) == 3:                                  # đúng vị trí: giá trị, cột, bảng
        gt, c, b = phan
        gia_tri = bo_nhay(gt)[0] if gt else None
        cot = c or None
        bang = b or None
    else:                                               # ít hơn 3 phần: nhận biết từng phần theo nội dung
        for p in phan:
            if not p:
                continue
            noi_dung, co_nhay = bo_nhay(p)
            if co_nhay:
                if gia_tri is not None:
                    raise ValueError("Có hai giá trị trong lệnh xóa")
                gia_tri = noi_dung
            elif tim_bang(db.dm, p) is not None and bang is None:
                bang = p
            elif tim_cot(db.dm, p) and cot is None:
                cot = p
            elif gia_tri is None:
                gia_tri = noi_dung
            else:
                raise ValueError(f"Không hiểu {p!r}. Cú pháp: {CU_PHAP}")
    if gia_tri is None and cot is None and bang is None:
        raise ValueError(f"Cần ít nhất một trong ba: giá trị, cột, bảng.\nCú pháp: {CU_PHAP}")
    return gia_tri, cot, bang


def thuc_thi(db, lenh):
    """Trả về (tên bảng đầu tiên bị xóa, thông điệp). Lỗi thì ném ValueError."""
    gia_tri, cot, bang = phan_tich(db, lenh)
    if bang is not None:
        b = tim_bang(db.dm, bang)
        if b is None:
            raise ValueError(f"Không có bảng {bang!r}. Các bảng: {', '.join(db.dm['bang'])}")
        bang = b
    if cot is not None:
        ds = tim_cot_hoac_loi(db.dm, cot, bang)
        cot = ds[0][1]
    ket_qua = db.xoa(gia_tri, cot, bang)
    chi_tiet = ", ".join(f"{b}: {n} dòng" for b, n in ket_qua.items())
    return next(iter(ket_qua)), f"Đã xóa ({chi_tiet})"
