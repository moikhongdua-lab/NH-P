"""Data map: đọc schema, tạo đường kết nối giữa các bảng (theo FK) và tra cứu tên bảng/cột."""
from database.schema import SCHEMA
from database.kieu_dl import bo_dau

# tên gọi ngắn -> tên bảng thật
ALIAS_BANG = {
    "nhanvien": "NHANVIEN", "phongban": "PHONGBAN",
    "calamviec": "CALAMVIEC", "calam": "CALAMVIEC",
    "chamcong": "BANGCHAMCONG", "bangchamcong": "BANGCHAMCONG",
    "luong": "BANGLUONG", "bangluong": "BANGLUONG",
    "phucap_thuongphat": "PHUCAP_THUONGPHAT", "phucap": "PHUCAP_THUONGPHAT",
    "thuongphat": "PHUCAP_THUONGPHAT",
}


def tao_data_map() -> dict:
    """{'bang': {tên: [cột]}, 'kieu': {tên: {cột: kiểu}},
        'ket_noi': [(bảng con, cột con, bảng cha, cột cha)]}"""
    bang, kieu, ket_noi = {}, {}, []
    for ten, s in SCHEMA.items():
        bang[ten] = list(s["cols"])
        kieu[ten] = dict(s["cols"])
        for cot, (cha, cot_cha) in s["fk"].items():
            ket_noi.append((ten, cot, cha, cot_cha))
    return {"bang": bang, "kieu": kieu, "ket_noi": ket_noi}


def chuan_ten(s: str) -> str:
    return bo_dau(s).strip()


def tim_bang(dm: dict, ten: str):
    """Tên bảng thật hoặc None. Không phân biệt hoa/thường, dấu; nhận cả tên ngắn (luong, chamcong...)."""
    k = chuan_ten(ten)
    for b in dm["bang"]:
        if chuan_ten(b) == k:
            return b
    return ALIAS_BANG.get(k)


def tim_cot(dm: dict, ten: str, bang: str = None) -> list:
    """Danh sách (bảng, cột) khớp tên. Hỗ trợ dạng 'BANG.cot'."""
    ten = ten.strip()
    if "." in ten:
        ten_b, ten = ten.split(".", 1)
        bang = tim_bang(dm, ten_b)
        if bang is None:
            raise ValueError(f"Không có bảng {ten_b!r}. Các bảng: {', '.join(dm['bang'])}")
    k = chuan_ten(ten)
    kq = []
    for b, cols in dm["bang"].items():
        if bang is not None and b != bang:
            continue
        for c in cols:
            if chuan_ten(c) == k:
                kq.append((b, c))
    return kq


def goi_y_cot(dm: dict, ten: str) -> str:
    """Gợi ý các cột có tên gần giống khi gõ sai/gõ tắt."""
    k = chuan_ten(ten.split(".")[-1])
    gan = []
    for b, cols in dm["bang"].items():
        for c in cols:
            if k and k in chuan_ten(c):
                gan.append(f"{b}.{c}")
    return ("Có phải bạn muốn: " + ", ".join(gan)) if gan else "Xem danh sách cột ở phần 'Cột và kiểu dữ liệu'."


def tim_cot_hoac_loi(dm: dict, ten: str, bang: str = None) -> list:
    kq = tim_cot(dm, ten, bang)
    if not kq:
        raise ValueError(f"Không có cột {ten!r}. {goi_y_cot(dm, ten)}")
    return kq


def tim_ket_noi(dm: dict, b1: str, b2: str):
    """(cột của b1, cột của b2) nếu hai bảng nối trực tiếp bằng FK (quy tắc nối '='), ngược lại None."""
    for con, cot_con, cha, cot_cha in dm["ket_noi"]:
        if con == b1 and cha == b2:
            return cot_con, cot_cha
        if con == b2 and cha == b1:
            return cot_cha, cot_con
    return None


def chon_cap_cot(dm: dict, ds_a: list, ds_b: list):
    """Chọn 1 cặp ((bảng, cột) đích, (bảng, cột) điều kiện): ưu tiên cùng bảng, sau đó bảng nối trực tiếp qua FK."""
    cung = [(x, y) for x in ds_a for y in ds_b if x[0] == y[0]]
    if len(cung) == 1:
        return cung[0]
    if len(cung) > 1:
        raise ValueError("Tên cột chưa rõ vì có ở nhiều bảng, hãy viết dạng BANG.cot. Ví dụ: "
                         + ", ".join(f"{x[0]}.{x[1]}" for x, _ in cung))
    noi = [(x, y) for x in ds_a for y in ds_b if tim_ket_noi(dm, x[0], y[0])]
    if len(noi) == 1:
        return noi[0]
    if len(noi) > 1:
        raise ValueError("Có nhiều cách nối bảng, hãy viết dạng BANG.cot cho rõ.")
    raise ValueError("Hai cột thuộc hai bảng không có kết nối (FK) với nhau nên không thể liên kết.")
