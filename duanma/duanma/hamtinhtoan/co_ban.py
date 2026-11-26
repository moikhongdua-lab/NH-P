"""Phép cơ bản cho các hàm tính toán, chỉ dùng for / while / if / else.

Bảng trong hàm tính toán là dict các list:  {"tên cột": [giá trị, giá trị, ...]}
Ô trống (null) là None / pd.NA / NaT / NaN.
"""
import pandas as pd


def la_trong(v):
    if v is None:
        return True
    if type(v).__name__ in ("NAType", "NaTType"):
        return True
    if v != v:                      # NaN (float), hoặc giá trị không bằng chính nó
        return True
    return False


def do_dai(ds):
    n = 0
    for _ in ds:
        n += 1
    return n


def so_hang(bang):
    for c in bang:
        return do_dai(bang[c])
    return 0


def bang_rong_giong(bang):
    """Bảng rỗng có cùng tên cột."""
    kq = {}
    for c in bang:
        kq[c] = []
    return kq


def chon_hang(bang, chi_so):
    """Bảng mới gồm các dòng theo đúng thứ tự trong chi_so."""
    kq = bang_rong_giong(bang)
    for i in chi_so:
        for c in bang:
            kq[c].append(bang[c][i])
    return kq


def doc_bang(df):
    """DataFrame -> dict các list (đọc theo vị trí, không phụ thuộc index)."""
    kq = {}
    for c in df.columns:
        kq[c] = []
        for v in df[c]:
            kq[c].append(v)
    return kq


def kiem_cot(bang, cot):
    if cot not in bang:
        raise ValueError(f"Không có cột {cot!r}. Các cột hiện có: " + ", ".join(bang))
