"""Đọc/tách câu lệnh của người dùng (không phải hàm tính toán)."""
from database.kieu_dl import bo_dau

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
    for i, ch in enumerate(m):
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
    for i, ch in enumerate(k):
        t += "\0" if m[i] == "\0" else ch
    kq = -1
    pos = t.find(tu)
    while pos >= 0:
        truoc = pos == 0 or t[pos - 1].isspace()
        sau = pos + len(tu) == len(t) or t[pos + len(tu)].isspace()
        if truoc and sau:
            kq = pos
            if not cuoi:
                return kq
        pos = t.find(tu, pos + 1)
    return kq


def bo_nhay(s):
    """('abc' hoặc "abc") -> ('abc', True);  abc -> ('abc', False)."""
    s = s.strip()
    if len(s) >= 2 and s[0] in _NHAY and s[-1] == _NHAY[s[0]]:
        return s[1:-1], True
    return s, False


def bo_tu_lenh(lenh, tu):
    """'Thêm: 'a' vào b' với tu='them' -> "'a' vào b".  Không bắt đầu bằng tu -> None."""
    s = lenh.strip()
    if not bo_dau(s).startswith(tu):
        return None
    phan_con = s[len(tu):]
    if phan_con and not (phan_con[0].isspace() or phan_con[0] == ":"):
        return None
    return phan_con.lstrip(" :\t\r\n")


def tach_dieu_kien(s):
    """"HoTen == 'An'" -> ('HoTen', '==', "'An'"). Nhận > < >= <= == != và =  ('=' được hiểu là '==')."""
    m = che(s, False)
    for i in range(len(m)):
        for p in _PHEP_TOAN:
            if m[i:i + len(p)] == p:
                cot = s[:i].strip()
                gt = s[i + len(p):].strip()
                if not cot or not gt:
                    raise ValueError(f"Điều kiện thiếu cột hoặc giá trị: {s!r}")
                return cot, ("==" if p == "=" else p), gt
    raise ValueError(f"Điều kiện không hợp lệ: {s!r} (ví dụ: LuongCoBan > 500000, HoTen == 'An')")


def tach_phep_gia_tri(s):
    """'> 500000' -> ('>', '500000')."""
    s = s.strip()
    for p in _PHEP_TOAN:
        if s.startswith(p):
            gt = s[len(p):].strip()
            if gt:
                return ("==" if p == "=" else p), gt
    raise ValueError(f"Điều kiện không hợp lệ: {s!r} (ví dụ: '> 500000')")
