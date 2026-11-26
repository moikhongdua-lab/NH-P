"""Dịch và thực thi lệnh XÓA.
Cú pháp:  xóa: '<giá trị>', <cột>, <bảng>      (cần ít nhất 1 trong 3, phần bỏ trống để trống giữa hai dấu phẩy)
Ví dụ:    xóa: '100000', LuongCoBan, NHANVIEN     xóa các dòng của NHANVIEN có LuongCoBan = 100000
          xóa: 'Thanh Tùng', , NHANVIEN           xóa dòng của NHANVIEN có BẤT KỲ ô nào = 'Thanh Tùng'
          xóa: , , PHUCAP_THUONGPHAT              xóa toàn bộ dòng của bảng
"""
from database.map_dulieu.map import tim_bang, tim_cot, tim_cot_hoac_loi
from hamtinhtoan.cu_phap import bo_tu_lenh, tach, bo_nhay
from hamtinhtoan.co_ban import do_dai
from ham_cac_phuong_thuc import strip

CU_PHAP = "xóa: '<giá trị>', <cột>, <bảng>   (cần ít nhất 1 trong 3)"
VI_DU = "xóa: 'Thanh Tùng', HoTen, NHANVIEN"


def phan_tich(db, lenh):
    """-> (giá trị | None, tên cột | None, tên bảng | None)"""
    con = bo_tu_lenh(lenh, "xoa")
    if con is None:
        raise ValueError(f"Lệnh xóa phải bắt đầu bằng 'xóa'.\nCú pháp: {CU_PHAP}")
        
    phan = []
    for p in tach(con, ","):
        phan.append(strip(p))      # Thay .strip() và List Comprehension
        
    if do_dai(phan) > 3:           # Thay len() bằng do_dai()
        raise ValueError(f"Chỉ có tối đa 3 phần (giá trị, cột, bảng), cách nhau bằng dấu phẩy.\nCú pháp: {CU_PHAP}")
        
    gia_tri = None
    cot = None
    bang = None
    
    if do_dai(phan) == 3:          # Thay len() bằng do_dai()
        gt = phan[0]
        c = phan[1]
        b = phan[2]
        
        # Thay toán tử 3 ngôi (if else) bằng if thường
        if gt:
            gia_tri = bo_nhay(gt)[0]
        if c:
            cot = c
        if b:
            bang = b
    else:                          # ít hơn 3 phần: nhận biết từng phần theo nội dung
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
            # Thay join() bằng vòng for nối chuỗi
            ds_bang = []
            for b2 in db.dm['bang']:
                ds_bang.append(b2)
            chuoi_bang = ""
            for i in range(do_dai(ds_bang)):
                if i > 0:
                    chuoi_bang += ", "
                chuoi_bang += ds_bang[i]
            raise ValueError(f"Không có bảng {bang!r}. Các bảng: {chuoi_bang}")
        bang = b
        
    if cot is not None:
        ds = tim_cot_hoac_loi(db.dm, cot, bang)
        cot = ds[0][1]
        
    ket_qua = db.xoa(gia_tri, cot, bang)
    
    # Thay join(), items(), Generator Expression bằng vòng for
    chi_tiet = ""
    dau_tien = True
    for b in ket_qua:
        if not dau_tien:
            chi_tiet += ", "
        chi_tiet += f"{b}: {ket_qua[b]} dòng"
        dau_tien = False
        
    # Thay next(iter()) để lấy phần tử đầu tiên
    bang_dau_tien = None
    for b in ket_qua:
        bang_dau_tien = b
        break
        
    return bang_dau_tien, f"Đã xóa ({chi_tiet})"