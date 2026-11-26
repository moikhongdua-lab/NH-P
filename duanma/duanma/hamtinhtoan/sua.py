"""Dịch và thực thi lệnh SỬA.
Cú pháp:  sửa <cột cần sửa> khi <cột điều kiện> = '<giá trị cũ>' thành <giá trị mới>
Ví dụ:    sửa LuongCoBan khi HoTen = 'Thanh Tùng' thành 100000
Giá trị mới không cần dấu nháy (sửa HoTen khi MaNV = 1 thành Thanh Tùng chạy được).
Giá trị điều kiện nên đặt trong nháy nếu có chứa chữ "thành".
"""
from database.map_dulieu.map import tim_cot_hoac_loi, chon_cap_cot
from hamtinhtoan.cu_phap import bo_tu_lenh, tim_tu, tach_dieu_kien, bo_nhay
from ham_cac_phuong_thuc import strip

CU_PHAP = "sửa <cột cần sửa> khi <cột điều kiện> = '<giá trị cũ>' thành <giá trị mới>"
VI_DU = "sửa LuongCoBan khi HoTen = 'Thanh Tùng' thành 100000"


def phan_tich(lenh):
    con = bo_tu_lenh(lenh, "sua")
    if con is None:
        raise ValueError(f"Lệnh sửa phải bắt đầu bằng 'sửa'.\nCú pháp: {CU_PHAP}")
    i_khi = tim_tu(con, "khi")
    if i_khi < 0:
        raise ValueError(f"Thiếu từ khóa 'khi' hoặc 'thành'.\nCú pháp: {CU_PHAP}")
    sau_khi = i_khi + 3
    j = tim_tu(con[sau_khi:], "thanh")               # chữ 'thành' ĐẦU TIÊN sau 'khi'
    if j < 0:
        raise ValueError(f"Thiếu từ khóa 'khi' hoặc 'thành'.\nCú pháp: {CU_PHAP}")
    i_thanh = sau_khi + j
    
    # Thay .strip() -> strip()
    cot_dich = strip(con[:i_khi])
    dieu_kien = strip(con[sau_khi:i_thanh])
    moi = strip(con[i_thanh + 5:])
    
    if not cot_dich:
        raise ValueError(f"Chưa ghi cột cần sửa.\nCú pháp: {CU_PHAP}")
    cot_loc, phep, gt_loc = tach_dieu_kien(dieu_kien)
    if phep != "==":
        raise ValueError("Điều kiện của lệnh sửa chỉ dùng dấu '='")
    return cot_dich, cot_loc, bo_nhay(gt_loc)[0], bo_nhay(moi)[0]


def thuc_thi(db, lenh):
    """Trả về (tên bảng đã sửa, thông điệp). Lỗi thì ném ValueError."""
    cot_dich, cot_loc, gt_loc, gt_moi = phan_tich(lenh)
    ds_a = tim_cot_hoac_loi(db.dm, cot_dich)
    ds_b = tim_cot_hoac_loi(db.dm, cot_loc)
    (bang_a, cot_a), (bang_b, cot_b) = chon_cap_cot(db.dm, ds_a, ds_b)
    n = db.sua(bang_a, cot_a, gt_moi, cot_b, gt_loc, bang_loc=bang_b)
    return bang_a, f"Đã sửa {n} dòng: {bang_a}.{cot_a} → {gt_moi!r} (khi {bang_b}.{cot_b} = {gt_loc!r})"