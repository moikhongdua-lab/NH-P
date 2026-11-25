"""Dịch và thực thi lệnh THÊM.
Cú pháp:  thêm '<giá trị>' vào <cột>; thêm '<giá trị>' vào <cột>; ...
Các giá trị trong cùng một lần nhập nằm chung MỘT dòng mới (thêm ở cuối bảng).
Ví dụ:    thêm 'Tùng' vào HoTen; thêm '100000' vào LuongCoBan
"""
from database.map_dulieu.map import tim_cot_hoac_loi
from database.schema import SCHEMA
from hamtinhtoan.cu_phap import bo_tu_lenh, tim_tu, tach, bo_nhay

CU_PHAP = "thêm '<giá trị>' vào <cột>; thêm '<giá trị>' vào <cột>; ..."
VI_DU = "thêm 'Tùng' vào HoTen; thêm '100000' vào LuongCoBan; thêm 'Nam' vào GioiTinh"


def phan_tich(lenh):
    """-> [(tên cột gõ, giá trị)]"""
    cac_cau = []
    for cau in tach(lenh.strip(), ";"):
        if cau.strip():
            cac_cau.append(cau.strip())
    if not cac_cau:
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
        cot = con[i_vao + 3:].strip()
        if not cot:
            raise ValueError(f"Câu {cau!r} chưa ghi tên cột.\nCú pháp: {CU_PHAP}")
        kq.append((cot, bo_nhay(con[:i_vao])[0]))
    return kq


def thuc_thi(db, lenh):
    """Trả về (tên bảng, thông điệp). Lỗi thì ném ValueError."""
    cac = phan_tich(lenh)
    chung = None                                        # bảng chứa được TẤT CẢ các cột đã nhập
    ung_vien = []
    for cot, _ in cac:
        ds = tim_cot_hoac_loi(db.dm, cot)
        ung_vien.append(ds)
        bang_cua_cot = {b for b, _ in ds}
        chung = bang_cua_cot if chung is None else chung & bang_cua_cot
    if not chung:
        raise ValueError("Các cột thuộc những bảng khác nhau nên không nằm chung một dòng được. "
                         "Mỗi lần nhập chỉ thêm vào một bảng.")
    if len(chung) > 1:
        raise ValueError("Chưa rõ thêm vào bảng nào (cột có ở nhiều bảng): " + ", ".join(sorted(chung))
                         + ". Hãy viết dạng BANG.cot.")
    bang = next(iter(chung))
    dong = {}
    for (cot, gt), ds in zip(cac, ung_vien):
        cot_that = [c for b, c in ds if b == bang][0]
        if cot_that in SCHEMA[bang].get("derived", []):
            raise ValueError(f"Cột {cot_that} là cột tự tính, không nhập tay được")
        if cot_that in dong:
            raise ValueError(f"Cột {cot_that} bị nhập hai lần trong cùng một dòng")
        dong[cot_that] = gt
    db.them(bang, dong)
    return bang, f"Đã thêm 1 dòng vào {bang}: " + ", ".join(f"{c} = {v!r}" for c, v in dong.items())
