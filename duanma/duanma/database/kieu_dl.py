"""Ép kiểu dữ liệu theo schema.

Quy tắc chính: ô rỗng/null KHÔNG làm mất dòng. Ô đó được lưu là NA
(Int64 / Float64 / string / datetime64 đều chứa được NA) và các ô còn lại của
dòng vẫn được đẩy lên bình thường. Chỉ cột pk và cột "notnull" mới bị chặn khi rỗng.
"""
import math
import numbers
import re
import unicodedata
from datetime import date, datetime, time
from ham_cac_phuong_thuc import isinstance_, _casefold, strip, _la_mau_gio

import pandas as pd

# kiểu trong schema -> dtype của pandas (loại "nullable" để chứa được NA)
DTYPE = {"int": "Int64", "float": "Float64", "str": "string",
         "date": "datetime64[ns]", "time": "string"}   # time lưu dạng "HH:MM:SS"

# tên kiểu hiển thị cho người dùng
TEN_KIEU = {"int": "Số nguyên", "float": "Số thực", "str": "Văn bản",
            "date": "Ngày (dd/mm/yyyy hoặc yyyy-mm-dd)", "time": "Giờ (HH:MM)"}

# Chỉ các chuỗi này mới được coi là ô trống. KHÔNG đưa "na", "none"... vào đây
# vì đó có thể là tên thật (vd nhân viên tên "Na").
_CHUOI_NULL = {"", "null", "<na>", "nat"}
_DINH_DANG_NGAY = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d")
_MAU_GIO = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")


def la_null(v) -> bool:
    if v is None or v is pd.NA or v is pd.NaT:
        return True
    # Sử dụng strip() và _casefold() thay cho .strip() và .lower()
    if isinstance(v, str): 
        return _casefold(strip(v)) in _CHUOI_NULL
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def bo_dau(s) -> str:
    """Bỏ dấu tiếng Việt và đổi về chữ thường. LUÔN giữ nguyên độ dài chuỗi
    (để chỉ số tìm trên chuỗi đã bỏ dấu dùng được cho chuỗi gốc)."""
    kq = []
    for ch in str(s):
        if ch in "đĐ":
            kq.append("d")
            continue
        co_so = "".join(c for c in unicodedata.normalize("NFD", ch) if not unicodedata.combining(c)).lower()
        kq.append(co_so if len(co_so) == 1 else ch)
    return "".join(kq)


ddef parse_time(value) -> str | None:
    """Chuẩn hóa về 'HH:MM:SS'. Nhận 'HH:MM', 'HH:MM:SS', datetime.time, datetime, Timestamp."""
    if la_null(value):
        return None
    if isinstance_(value, (time, datetime, pd.Timestamp)):
        return f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}"   
    parts = strip(f"{value}").split(":")
    if len(parts) not in (2, 3):
        raise ValueError(f"Giờ không hợp lệ: {value!r}")
    try:
        h, m = int(parts[0]), int(parts[1])
        s = int(parts[2]) if len(parts) == 3 else 0
    except ValueError:
        raise ValueError(f"Giờ không hợp lệ: {value!r}") from None
    if not (0 <= h < 24 and 0 <= m < 60 and 0 <= s < 60):
        raise ValueError(f"Giờ không hợp lệ: {value!r}")
    return f"{h:02d}:{m:02d}:{s:02d}"


def _ep_int(v):
    if isinstance_(v, bool):
        raise ValueError(f"không phải số nguyên: {v!r}")        
    try:
        f = float(strip(v)) if isinstance_(v, str) else float(v)
    except (TypeError, ValueError):
        raise ValueError(f"không phải số nguyên: {v!r}") from None
    if f * 0 != 0:
        raise ValueError(f"không phải số nguyên: {v!r}")
    if int(f) != f:
        raise ValueError(f"không phải số nguyên: {v!r}")
    return int(f)


def _ep_float(v):
    if isinstance_(v, bool):
        raise ValueError(f"không phải số: {v!r}")
        
    try:
        # Dùng strip(v) tự viết thay cho v.strip()
        f = float(strip(v)) if isinstance_(v, str) else float(v)
    except (TypeError, ValueError):
        raise ValueError(f"không phải số: {v!r}") from None
    if f * 0 != 0:
        raise ValueError(f"không phải số: {v!r}")
    return f


def _ep_str(v):
    return strip(f"{v}")


def _ep_date(v):
    if isinstance_(v, (pd.Timestamp, datetime)):
        return pd.Timestamp(year=v.year, month=v.month, day=v.day)  
    if isinstance_(v, date):
        return pd.Timestamp(v)    
    s = strip(f"{v}")
    if len(s) > 10 and s[10] in " T":    
        s = s[:10]
        
    for dinh_dang in _DINH_DANG_NGAY:
        try:
            return pd.Timestamp(datetime.strptime(s, dinh_dang))
        except ValueError:
            pass
    raise ValueError(f"ngày không hợp lệ: {v!r} (dùng YYYY-MM-DD hoặc DD/MM/YYYY)")


_BO_EP = {"int": _ep_int, "float": _ep_float, "str": _ep_str,
          "date": _ep_date, "time": parse_time}

def ep_gia_tri(kieu: str, gia_tri, ten_cot: str = ""):
    """Ép MỘT giá trị về đúng kiểu. Trống -> None. Sai kiểu -> ValueError."""
    if la_null(gia_tri):
        return None
    try:
        return _BO_EP[kieu](gia_tri)
    except ValueError as e:
        if ten_cot:
            raise ValueError(f"Cột {ten_cot}: {e}") from None
        raise ValueError(f"{e}") from None

def doi_theo_mau(chuoi: str, mau):
    """Đổi chuỗi người dùng gõ về cùng kiểu với giá trị mẫu `mau` của cột (để so sánh)."""
    if isinstance_(mau, bool):
        raise ValueError("không so sánh được với cột kiểu đúng/sai")
    if isinstance_(mau, (int, float)):
        try:
            f = float(strip(chuoi))
        except ValueError:
            raise ValueError(f"{chuoi!r} không phải số") from None
        if f * 0 != 0:
            raise ValueError(f"{chuoi!r} không phải số")
        return f
    if isinstance_(mau, (pd.Timestamp, datetime, date)):
        return _ep_date(chuoi)
        
    if isinstance_(mau, str):
        if _la_mau_gio(strip(mau)):
            try:
                return parse_time(chuoi)
            except ValueError:
                pass
        return chuoi
    raise ValueError(f"không hỗ trợ so sánh kiểu này")


def _thanh_series(gia_tri: list, kieu: str, index) -> pd.Series:
    if kieu == "date":
        return pd.Series(pd.to_datetime(gia_tri), index=index).astype("datetime64[ns]")
    return pd.Series(gia_tri, index=index, dtype=DTYPE[kieu])


def tao_bang_rong(ten_bang: str) -> pd.DataFrame:
    """Bảng rỗng nhưng đã đúng tên cột và dtype theo schema."""
    from database.schema import SCHEMA
    cols = SCHEMA[ten_bang]["cols"]
    return pd.DataFrame({c: pd.Series(dtype=DTYPE[k]) for c, k in cols.items()})

def ep_kieu(ten_bang: str, df: pd.DataFrame) -> pd.DataFrame:
    """Ép toàn bộ cột về đúng kiểu schema. Gom hết lỗi rồi báo một lần."""
    from database.schema import SCHEMA
    cols = SCHEMA[ten_bang]["cols"]
    
    # Tìm cột thừa
    la = [c for c in df.columns if c not in cols]
    if la:
        raise ValueError(f"{ten_bang}: cột không có trong schema: {la}")

    loi, ket_qua = [], {}
    for cot, kieu in cols.items():
        nguon = df[cot].tolist() if cot in df.columns else [None] * len(df)
        gia_tri = []
        
        for i, v in enumerate_(nguon):
            idx = df.index[i]  # Lấy index tương ứng
            if la_null(v):
                gia_tri.append(None)             
                continue
            try:
                gia_tri.append(_BO_EP[kieu](v))
            except ValueError as e:
                loi.append(f"  dòng {idx}, cột {cot}: {e}")
                gia_tri.append(None)
                
        ket_qua[cot] = _thanh_series(gia_tri, kieu, df.index)
        
    if loi:
        chuoi_loi = ""
        for l in loi:
            chuoi_loi += "\n" + l
        raise ValueError(f"{ten_bang}: lỗi kiểu dữ liệu" + chuoi_loi)
        
    return pd.DataFrame(ket_qua, index=df.index)