"""Đọc/tách câu lệnh của người dùng (không phải hàm tính toán)."""
from database.kieu_dl import bo_dau

# Import các hàm thay thế phương thức chuỗi từ module riêng.
# Đổi đường dẫn dưới đây cho khớp với file/folder bạn đã tạo.
from ham_cac_phuong_thuc import (
    isspace,
    strip,
    lstrip,
    find,
    startswith,
    enumerate_,
)

_NHAY = {"'": "'", '"': '"', "‘": "’", "“": "”"}      # ký tự mở nháy -> ký tự đóng
_PHEP_TOAN = (">=", "<=", "!=", "==", ">", "<", "=")


def che(s, che_ngoac):
    """Chuỗi cùng độ dài với s; phần trong dấu nháy (và trong ngoặc () nếu che_ngoac) bị thay bằng '\\0'.
    Dùng để tìm dấu phân cách / từ khóa ở cấp ngoài cùng."""
    kq = ""
    dong = None
    sau = 0
    for ch in s:
        if dong is not None:
            kq += "\0"
            if ch == dong:
                dong = None
        elif ch in _NHAY:
            dong = _NHAY[ch]
            kq += "\0"
        elif che_ngoac and ch == "(":
            sau += 1
            kq += "\0"
        elif che_ngoac and ch == ")" and sau > 0:
            sau -= 1
            kq += "\0"
        elif che_ngoac and sau > 0:
            kq += "\0"
        else:
            kq += ch
    return kq


def tach(s, dau):
    """Tách s theo ký tự `dau` ở cấp ngoài cùng (không tách trong nháy hoặc trong ngoặc)."""
    m = che(s, True)
    kq = []
    bat_dau = 0
    for i, ch in enumerate_(m):
        if ch == dau:
            kq.append(s[bat_dau:i])
            bat_dau = i + 1
    kq.append(s[bat_dau:])
    return kq


def tim_ngoac_dong(s, p):
    """Vị trí dấu ')' khớp với '(' ở vị trí p; -1 nếu thiếu."""
    m = che(s, False)
    sau = 0
    for i in range(p, len(m)):
        if m[i] == "(":
            sau += 1
        elif m[i] == ")":
            sau -= 1
            if sau == 0:
                return i
    return -1


def tim_tu(s, tu, cuoi=False):
    """Vị trí từ khóa `tu` (không dấu, chữ thường) đứng riêng giữa khoảng trắng, nằm ngoài dấu nháy.
    cuoi=True: lấy lần xuất hiện cuối. Không có: -1."""
    m = che(s, False)
    k = bo_dau(s)
    t = ""
    for i, ch in enumerate_(k):
        if m[i] == "\0":
            t += "\0"
        else:
            t += ch
    kq = -1
    pos = find(t, tu)
    while pos >= 0:
        truoc = pos == 0 or isspace(t[pos - 1])
        sau = pos + len(tu) == len(t) or isspace(t[pos + len(tu)])
        if truoc and sau:
            kq = pos
            if not cuoi:
                return kq
        pos = find(t, tu, pos + 1)
    return kq


def bo_nhay(s):
    """('abc' hoặc "abc") -> ('abc', True);  abc -> ('abc', False)."""
    s = strip(s)
    if len(s) >= 2 and s[0] in _NHAY and s[-1] == _NHAY[s[0]]:
        return s[1:-1], True
    return s, False


def bo_tu_lenh(lenh, tu):
    """'Thêm: 'a' vào b' với tu='them' -> "'a' vào b".  Không bắt đầu bằng tu -> None."""
    s = strip(lenh)
    if not startswith(bo_dau(s), tu):
        return None
    phan_con = s[len(tu):]
    if phan_con and not (isspace(phan_con[0]) or phan_con[0] == ":"):
        return None
    # bỏ khoảng trắng VÀ dấu ':' ở đầu (giống lstrip(" :\t\r\n"))
    i = 0
    while i < len(phan_con):
        ch = phan_con[i]
        if isspace(ch) or ch == ":":
            i = i + 1
        else:
            break
    return phan_con[i:]


def tach_dieu_kien(s):
    """"HoTen == 'An'" -> ('HoTen', '==', "'An'"). Nhận > < >= <= == != và =  ('=' được hiểu là '==')."""
    m = che(s, False)
    for i in range(len(m)):
        for p in _PHEP_TOAN:
            if m[i:i + len(p)] == p:
                cot = strip(s[:i])
                gt = strip(s[i + len(p):])
                if not cot or not gt:
                    raise ValueError(f"Điều kiện thiếu cột hoặc giá trị: {s!r}")
                return cot, ("==" if p == "=" else p), gt
    raise ValueError(f"Điều kiện không hợp lệ: {s!r} (ví dụ: LuongCoBan > 500000, HoTen == 'An')")


def tach_phep_gia_tri(s):
    """> 500000' -> ('>', '500000')."""
    s = strip(s)
    for p in _PHEP_TOAN:
        if startswith(s, p):
            gt = strip(s[len(p):])
            if gt:
                return ("==" if p == "=" else p), gt
    raise ValueError(f"Điều kiện không hợp lệ: {s!r} (ví dụ: '> 500000')")