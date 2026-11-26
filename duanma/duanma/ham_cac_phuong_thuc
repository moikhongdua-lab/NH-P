def isspace(ch):
    """ kiểm tra một ký tự có phải khoảng trắng."""
    if ch == " ":
        return True
    if ch == "\t":
        return True
    if ch == "\n":
        return True
    if ch == "\r":
        return True
    if ch == "\f":
        return True
    if ch == "\v":
        return True
    return False


def strip(s):
    """ bỏ khoảng trắng ở cả hai đầu."""
    n = len(s)
    # tìm vị trí ký tự KHÔNG-trắng đầu tiên
    dau = n
    for i in range(n):
        if not _la_khoang_trang(s[i]):
            dau = i
            break
    # tìm vị trí sau ký tự KHÔNG-trắng cuối cùng
    cuoi = 0
    for i in range(n - 1, -1, -1):
        if not _la_khoang_trang(s[i]):
            cuoi = i + 1
            break
    if dau >= cuoi:
        return ""
    return s[dau:cuoi]


def lstrip(s):
    """bỏ khoảng trắng ở đầu trái."""
    n = len(s)
    dau = n
    for i in range(n):
        if not _la_khoang_trang(s[i]):
            dau = i
            break
    return s[dau:]


def find(s, chuoi_con, bat_dau=0):
    """ trả vị trí đầu tiên hoặc -1 nếu không thấy."""
    n = len(s)
    m = len(chuoi_con)
    if m == 0:
        if bat_dau <= n:
            return bat_dau
        return -1
    for i in range(bat_dau, n - m + 1):
        if s[i:i + m] == chuoi_con:
            return i
    return -1


def startswith(s, tien_to):
    """ kiểm tra s có bắt đầu bằng tien_to không."""
    if len(tien_to) > len(s):
        return False
    for i in range(len(tien_to)):
        if s[i] != tien_to[i]:
            return False
    return True

def enumerate_(ds):
    kq = []
    i = 0
    for v in ds:
        cap = (i, v)
        kq = kq + [cap]
        i = i + 1
    return kq
    # hamtinhtoan/co_ban.py — thêm vào cuối file

def isinstance_(obj, lop):
    """Giống isinstance(obj, lop) — dùng type + __mro__ + for/if/len."""
    hang_ke_thua = type(obj).__mro__
    for i in range(len(hang_ke_thua)):
        if hang_ke_thua[i] is lop:
            return True
    return False
    
def _casefold(s):
    kq = ""
    for ch in s:
        if 65 <= ord(ch) <= 90:  # 'A' to 'Z'
            kq += chr(ord(ch) + 32)
        else:
            kq += ch
    return kq