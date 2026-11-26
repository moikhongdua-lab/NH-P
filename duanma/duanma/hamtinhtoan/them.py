"""Dịch và thực thi lệnh THÊM.
Cú pháp:  thêm '<giá trị>' vào <cột>; thêm '<giá trị>' vào <cột>; ...
Các giá trị trong cùng một lần nhập nằm chung MỘT dòng mới (thêm ở cuối bảng).
Ví dụ:    thêm 'Tùng' vào HoTen; thêm '100000' vào LuongCoBan
"""
from database.map_dulieu.map import tim_cot_hoac_loi
from database.schema import SCHEMA
from hamtinhtoan.cu_phap import bo_tu_lenh, tim_tu, tach, bo_nhay
from hamtinhtoan.co_ban import do_dai
from ham_cac_phuong_thuc import strip

CU_PHAP = "thêm '<giá trị>' vào <cột>; thêm '<giá trị>' vào <cột>; ..."
VI_DU = "thêm 'Tùng' vào HoTen; thêm '100000' vào LuongCoBan; thêm 'Nam' vào GioiTinh"


def phan_tich(lenh):
    """-> [(tên cột gõ, giá trị)]"""
    cac_cau = []
    
    # Thay lenh.strip() -> strip(lenh)
    for cau in tach(strip(lenh), ";"):
        cau_sach = strip(cau)          # Thay cau.strip() -> strip(cau)
        if cau_sach:
            cac_cau.append(cau_sach)
            
    if do_dai(cac_cau) == 0:
        raise ValueError(f"Lệnh đang trống.\nCú pháp: {CU_PHAP}")
        
    if bo_tu_lenh(cac_cau[0], "them") is None:
        raise ValueError(f"Lệnh thêm phải bắt đầu bằng 'thêm'.\nCú pháp: {CU_PHAP}")
        
    kq = []
    for cau in cac_cau:
        con = bo_tu_lenh(cau, "them")
        if con is None:
            con = cau                                   # các câu sau được bỏ chữ 'thêm'
            
        i_vao = tim_tu(con, "vao", cuoi=True)
        if i_vao < 0:
            raise ValueError(f"Câu {cau!r} thiếu từ khóa 'vào'.\nCú pháp: {CU_PHAP}")
            
        cot = strip(con[i_vao + 3:])     # Thay .strip() -> strip()
        if not cot:
            raise ValueError(f"Câu {cau!r} chưa ghi tên cột.\nCú pháp: {CU_PHAP}")
            
        kq.append((cot, bo_nhay(con[:i_vao])[0]))
    return kq


def thuc_thi(db, lenh):
    """Trả về (tên bảng, thông điệp). Lỗi thì ném ValueError."""
    cac = phan_tich(lenh)
    ung_vien = []
    
    # 1. Lấy danh sách các bảng ứng viên cho từng cột
    for cot, gt in cac:
        ds = tim_cot_hoac_loi(db.dm, cot)
        ung_vien.append(ds)

    # 2. Tìm bảng chung chứa TẤT CẢ các cột (thay cho Set Comprehension & giao &)
    bang_kha_thi = []
    
    # Lấy các bảng từ cột đầu tiên làm mốc
    for b_moc, c_moc in ung_vien[0]:
        hop_le = True
        for i in range(1, do_dai(ung_vien)):
            co_cot = False
            for b2, c2 in ung_vien[i]:
                if b2 == b_moc:
                    co_cot = True
                    break
            if not co_cot:
                hop_le = False
                break
                
        if hop_le:
            # Kiểm tra xem bảng này đã có trong danh sách chưa
            da_co = False
            for b_da_co in bang_kha_thi:
                if b_da_co == b_moc:
                    da_co = True
                    break
            if not da_co:
                bang_kha_thi.append(b_moc)

    # 3. Kiểm tra tính hợp lệ của bảng chung
    if do_dai(bang_kha_thi) == 0:
        raise ValueError("Các cột thuộc những bảng khác nhau nên không nằm chung một dòng được. "
                         "Mỗi lần nhập chỉ thêm vào một bảng.")
                         
    if do_dai(bang_kha_thi) > 1:
        # Tự tạo chuỗi lỗi bằng for (thay vì sorted và join)
        chuoi_loi = "Chưa rõ thêm vào bảng nào (cột có ở nhiều bảng): "
        for i in range(do_dai(bang_kha_thi)):
            if i > 0:
                chuoi_loi += ", "
            chuoi_loi += bang_kha_thi[i]
        raise ValueError(chuoi_loi + ". Hãy viết dạng BANG.cot.")
        
    bang = bang_kha_thi[0]                  # Lấy bảng đầu tiên thay vì next(iter(...))

    # 4. Gom giá trị vào 1 dòng
    dong = {}
    for i in range(do_dai(cac)):
        cot = cac[i][0]
        gt = cac[i][1]
        ds = ung_vien[i]
        
        # Tìm tên cột thực tế trong bảng (thay cho List Comprehension)
        cot_that = None
        for b, c in ds:
            if b == bang:
                cot_that = c
                break
                
        # Kiểm tra cột derived
        derived = SCHEMA[bang].get("derived", [])
        la_derived = False
        for d in derived:
            if d == cot_that:
                la_derived = True
                break
                
        if la_derived:
            raise ValueError(f"Cột {cot_that} là cột tự tính, không nhập tay được")
            
        if cot_that in dong:
            raise ValueError(f"Cột {cot_that} bị nhập hai lần trong cùng một dòng")
            
        dong[cot_that] = gt
        
    db.them(bang, dong)
    
    # 5. Tạo thông báo kết quả (thay cho join và items)
    thong_bao = f"Đã thêm 1 dòng vào {bang}: "
    dau_tien = True
    for k in dong:
        if not dau_tien:
            thong_bao += ", "
        thong_bao += f"{k} = {dong[k]!r}"
        dau_tien = False
        
    return bang, thong_bao