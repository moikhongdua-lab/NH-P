"""Nơi dựng và giữ các bảng. Mọi bảng là pandas.DataFrame trong self.bang.

Dữ liệu được lưu thành file CSV cạnh file mã nguồn của bảng (database/bang/<tên>.csv).
Mọi thao tác ghi (them / sua / xoa / tao_luong_thang) chạy như một giao dịch:
lỗi ở đâu thì trả bảng về trạng thái cũ và KHÔNG ghi CSV; thành công mới ghi.
"""
import functools
import os
from datetime import date
from pathlib import Path

import pandas as pd

from database.schema import SCHEMA
from database.kieu_dl import ep_kieu, tao_bang_rong, la_null, ep_gia_tri
from database.map_dulieu.map import tao_data_map, tim_ket_noi
from database.bang.chamcong import cap_nhat_cong
from database.bang.luong import tinh_luong

import os
from datetime import date
import pandas as pd
from database.schema import SCHEMA
from database.kieu_dl import ep_kieu, tao_bang_rong, la_null, ep_gia_tri
from database.map_dulieu.map import tao_data_map, tim_ket_noi
from database.bang.chamcong import cap_nhat_cong
from database.bang.luong import tinh_luong
from ham_cac_phuong_thuc import enumerate_, _upper, _casefold, strip, isspace, isinstance_

THU_MUC = os.path.join(os.path.dirname(__file__), "bang")
TEN_FILE = {"PHONGBAN": "phongban", "NHANVIEN": "nhanvien", "CALAMVIEC": "calamviec", "BANGCHAMCONG": "chamcong", "PHUCAP_THUONGPHAT": "phucap_thuongphat", "BANGLUONG": "luong"}

def giao_dich(ham):
    def boc(self, *a, **kw):
        if self._dang_chay:
            return ham(self, *a, **kw)
        chup = {}
        for k in self.bang:
            chup[k] = self.bang[k]
        self._dang_chay = True
        try:
            kq = ham(self, *a, **kw)
            self.luu()
            return kq
        except Exception:
            self.bang = chup
            raise
        finally:
            self._dang_chay = False
    boc.__name__ = ham.__name__
    return boc

class CSDL:
    def __init__(self, thu_muc=None):
        self.thu_muc = thu_muc if thu_muc else THU_MUC
        self.bang = {}
        for ten in SCHEMA:
            self.bang[ten] = tao_bang_rong(ten)
        self.dm = tao_data_map()
        self._dang_chay = False
        self.doc()

    def _csv(self, ten: str) -> str:
        return os.path.join(self.thu_muc, TEN_FILE[ten] + ".csv")

    def luu(self) -> None:
        if not os.path.exists(self.thu_muc):
            os.makedirs(self.thu_muc)
        for ten in self.bang:
            dich = self._csv(ten)
            tam = dich + ".tmp"
            self.bang[ten].to_csv(tam, index=False, encoding="utf-8-sig")
            os.replace(tam, dich)

    def doc(self) -> None:
        for ten in SCHEMA:
            f = self._csv(ten)
            if os.path.exists(f):
                df = pd.read_csv(f, dtype=str, keep_default_na=False, encoding="utf-8-sig")
                if len(df) > 0:
                    self.bang[ten] = ep_kieu(ten, df)
        self.tinh_lai()

    def _ten(self, ten: str) -> str:
        ten = _upper(ten)
        if ten not in self.bang:
            ds_ten = ""
            for k in self.bang:
                ds_ten += k + ", "
            raise KeyError(f"Không có bảng {ten}. Các bảng: {ds_ten}")
        return ten

    def lay_bang(self, ten: str) -> pd.DataFrame:
        return self.bang[self._ten(ten)]

    @giao_dich
    def them(self, ten: str, du_lieu) -> None:
        ten = self._ten(ten)
        s = SCHEMA[ten]
        if isinstance_(du_lieu, dict):
            du_lieu = [du_lieu]
        moi = du_lieu.copy() if isinstance_(du_lieu, pd.DataFrame) else pd.DataFrame(du_lieu)
        cot_bo = []
        for c in s.get("derived", []):
            if c in moi.columns:
                cot_bo.append(c)
        if len(cot_bo) > 0:
            moi = moi.drop(columns=cot_bo)
        moi = moi.reset_index(drop=True)
        moi = ep_kieu(ten, moi)
        self._pk_tu_dong(ten, moi)
        self._kiem_tra(ten, moi)
        cu = self.bang[ten]
        self.bang[ten] = moi if cu.empty else pd.concat([cu, moi], ignore_index=True)
        self.tinh_lai()
        if ten == "NHANVIEN":
            thang, nam = self.thang_hien_tai()
            self.tao_luong_thang(thang, nam)

    @staticmethod
    def thang_hien_tai():
        h = date.today()
        return h.month, h.year

    def _pk_tu_dong(self, ten: str, moi: pd.DataFrame) -> None:
        pk = SCHEMA[ten]["pk"]
        if len(pk) != 1 or SCHEMA[ten]["cols"][pk[0]] != "int":
            return
        cot = pk[0]
        da_co = []
        v1 = self.bang[ten][cot].max()
        v2 = moi[cot].max()
        if not la_null(v1):
            da_co.append(v1)
        if not la_null(v2):
            da_co.append(v2)
        tiep = 0
        if len(da_co) > 0:
            max_val = da_co[0]
            for x in da_co:
                if x > max_val:
                    max_val = x
            tiep = int(max_val)
        for i in moi.index[moi[cot].isna()]:
            tiep += 1
            moi.loc[i, cot] = tiep

    def _kiem_tra(self, ten: str, moi: pd.DataFrame, cu: pd.DataFrame = None, hanh_dong: str = "thêm") -> None:
        s = SCHEMA[ten]
        loi = []
        cu = self.bang[ten] if cu is None else cu
        cot_kt = []
        for c in s["pk"]:
            if c not in cot_kt:
                cot_kt.append(c)
        for c in s.get("notnull", []):
            if c not in cot_kt:
                cot_kt.append(c)
        for cot in cot_kt:
            for i in moi.index[moi[cot].isna()]:
                loi.append(f"  dòng {i}: cột {cot} không được để trống")
        for cot in s.get("check", {}):
            cho_phep = s["check"][cot]
            ban_do = {}
            for x in cho_phep:
                ban_do[_casefold(x)] = x
            for i in moi.index[moi[cot].notna()]:
                gt = moi.at[i, cot]
                if _casefold(gt) in ban_do:
                    moi.at[i, cot] = ban_do[_casefold(gt)]
                else:
                    loi.append(f"  dòng {i}: {cot}={gt!r} không hợp lệ, chỉ nhận {cho_phep}")
        for cot in s.get("khoang", {}):
            lo, hi = s["khoang"][cot]
            for i in moi.index[moi[cot].notna()]:
                v = moi.at[i, cot]
                if (lo is not None and v < lo) or (hi is not None and v > hi):
                    loi.append(f"  dòng {i}: {cot}={v} ngoài khoảng [{lo}, {hi}]")
        bo_cot_kt = [(s["pk"], "khóa chính")]
        for u in s.get("unique", []):
            bo_cot_kt.append((u, "unique"))
        for bo_cot, nhan in bo_cot_kt:
            trung = self._tim_trung(cu, moi, bo_cot)
            for i in trung:
                loi.append(f"  dòng {i}: trùng {nhan} {bo_cot}")
        for cot in s["fk"]:
            bang_cha, cot_cha = s["fk"][cot]
            cha = {}
            for x in self.bang[bang_cha][cot_cha].dropna().tolist():
                cha[x] = True
            for i in moi.index[moi[cot].notna()]:
                if moi.at[i, cot] not in cha:
                    loi.append(f"  dòng {i}: {cot}={moi.at[i, cot]} không có trong {bang_cha}.{cot_cha}")
        if len(loi) > 0:
            chuoi_loi = ""
            for l in loi:
                chuoi_loi += "\n" + l
            if hanh_dong == "thêm":
                raise ValueError(f"Không thêm được vào {ten}:" + chuoi_loi)
            else:
                raise ValueError(f"Không {hanh_dong} được {ten}:" + chuoi_loi)

    @staticmethod
    def _tim_trung(cu: pd.DataFrame, moi: pd.DataFrame, cols: list) -> list:
        da_co = {}
        cu_sub = cu[cols].dropna()
        for i in cu_sub.index:
            khoa = []
            for c in cols:
                khoa.append(cu_sub.at[i, c])
            da_co[tuple(khoa)] = True
        thay = {}
        trung = []
        for i in moi.index:
            khoa = []
            has_null = False
            for c in cols:
                val = moi.at[i, c]
                if la_null(val):
                    has_null = True
                    break
                khoa.append(val)
            if has_null:
                continue
            khoa_tuple = tuple(khoa)
            if khoa_tuple in da_co or khoa_tuple in thay:
                trung.append(i)
            thay[khoa_tuple] = True
        return trung

    def tinh_lai(self) -> None:
        b = self.bang
        b["BANGCHAMCONG"] = cap_nhat_cong(b["BANGCHAMCONG"], b["CALAMVIEC"])
        b["BANGLUONG"] = tinh_luong(b["BANGLUONG"], b["BANGCHAMCONG"], b["NHANVIEN"], b["PHUCAP_THUONGPHAT"])

    @giao_dich
    def tao_luong_thang(self, thang: int, nam: int) -> None:
        luong = self.bang["BANGLUONG"]
        da_co = {}
        loc = luong.loc[(luong["Thang"] == thang) & (luong["Nam"] == nam)]
        for ma in loc["MaNV"].tolist():
            da_co[ma] = True
        ds = []
        for ma in self.bang["NHANVIEN"]["MaNV"].tolist():
            if ma not in da_co:
                ds.append({"MaNV": ma, "Thang": thang, "Nam": nam})
        if len(ds) > 0:
            self.them("BANGLUONG", ds)

    @giao_dich
    def sua(self, ten: str, cot_dich: str, gia_tri_moi, cot_loc: str, gia_tri_loc, bang_loc: str = None) -> int:
        ten = self._ten(ten)
        bang_loc = self._ten(bang_loc) if bang_loc else ten
        s = SCHEMA[ten]
        for c in s.get("derived", []):
            if c == cot_dich:
                raise ValueError(f"Cột {cot_dich} là cột tự tính, không sửa tay được")
        gt_loc = ep_gia_tri(SCHEMA[bang_loc]["cols"][cot_loc], gia_tri_loc, cot_loc)
        if gt_loc is None:
            raise ValueError("Giá trị điều kiện không được để trống")
        tbl_loc = self.bang[bang_loc]
        khop = []
        for i, v in enumerate_(tbl_loc[cot_loc].tolist()):
            if not la_null(v) and v == gt_loc:
                khop.append(i)
        if bang_loc == ten:
            dong_sua = khop
        else:
            cot_a, cot_b = tim_ket_noi(self.dm, ten, bang_loc)
            khoa = {}
            for i in khop:
                khoa[tbl_loc[cot_b].tolist()[i]] = True
            dong_sua = []
            for i, v in enumerate_(self.bang[ten][cot_a].tolist()):
                if not la_null(v) and v in khoa:
                    dong_sua.append(i)
        if len(dong_sua) == 0:
            raise ValueError(f"Không có dòng nào thỏa điều kiện {bang_loc}.{cot_loc} = {gia_tri_loc!r}")
        gt_moi = ep_gia_tri(s["cols"][cot_dich], gia_tri_moi, cot_dich)
        cand = self.bang[ten].copy()
        gia_tri = cand[cot_dich].tolist()
        khoa_cu = {}
        for i in dong_sua:
            if not la_null(gia_tri[i]) and gia_tri[i] != gt_moi:
                khoa_cu[gia_tri[i]] = True
            gia_tri[i] = gt_moi
        cand[cot_dich] = gia_tri
        cand = ep_kieu(ten, cand)
        self._kiem_tra(ten, cand, cu=tao_bang_rong(ten), hanh_dong="sửa")
        loi = self._kiem_con(ten, cot_dich, khoa_cu)
        if len(loi) > 0:
            chuoi_loi = ""
            for l in loi:
                chuoi_loi += "\n" + l
            raise ValueError(f"Không sửa được {ten}.{cot_dich} vì đang được bảng khác tham chiếu:" + chuoi_loi)
        self.bang[ten] = cand
        self.tinh_lai()
        return len(dong_sua)

    @giao_dich
    def xoa(self, gia_tri=None, cot: str = None, bang: str = None) -> dict:
        bang = self._ten(bang) if bang else None
        co_gt = not la_null(gia_tri)
        if not co_gt and cot is None and bang is None:
            raise ValueError("Cần ít nhất một trong ba: giá trị, cột, bảng")
        if not co_gt and cot is not None:
            raise ValueError("Chưa hỗ trợ xóa theo cột mà không có giá trị. Hãy thêm giá trị cần xóa.")
        xoa_idx = {}
        if not co_gt:
            n = len(self.bang[bang])
            if n > 0:
                ds_idx = []
                for i in range(n):
                    ds_idx.append(i)
                xoa_idx[bang] = ds_idx
        else:
            ds_bang = [bang] if bang else list(self.bang)
            for b in ds_bang:
                cols = SCHEMA[b]["cols"]
                if cot is not None and cot not in cols:
                    if bang:
                        raise ValueError(f"Bảng {b} không có cột {cot}")
                    continue
                dong = {}
                ds_cot = [cot] if cot else list(cols)
                for c in ds_cot:
                    try:
                        gt = ep_gia_tri(cols[c], gia_tri, c)
                    except ValueError:
                        if cot:
                            raise
                        continue
                    for i, v in enumerate_(self.bang[b][c].tolist()):
                        if not la_null(v) and v == gt:
                            dong[i] = True
                if len(dong) > 0:
                    ds_dong = []
                    for k in dong:
                        ds_dong.append(k)
                    xoa_idx[b] = ds_dong
        if len(xoa_idx) == 0:
            raise ValueError("Không có dòng nào khớp để xóa")
        if "NHANVIEN" in xoa_idx:
            ma = {}
            for i in xoa_idx["NHANVIEN"]:
                ma[self.bang["NHANVIEN"]["MaNV"].tolist()[i]] = True
            them_luong = []
            for i, v in enumerate_(self.bang["BANGLUONG"]["MaNV"].tolist()):
                if not la_null(v) and v in ma:
                    them_luong.append(i)
            if len(them_luong) > 0:
                if "BANGLUONG" not in xoa_idx:
                    xoa_idx["BANGLUONG"] = []
                for idx in them_luong:
                    da_co = False
                    for x in xoa_idx["BANGLUONG"]:
                        if x == idx:
                            da_co = True
                            break
                    if not da_co:
                        xoa_idx["BANGLUONG"].append(idx)
                xoa_idx["BANGLUONG"].sort()
        loi = []
        for b in xoa_idx:
            idx = xoa_idx[b]
            ds_cot_cha = []
            for k in self.dm["ket_noi"]:
                if k[2] == b:
                    if k[3] not in ds_cot_cha:
                        ds_cot_cha.append(k[3])
            for cot_cha in ds_cot_cha:
                khoa = {}
                for i in idx:
                    val = self.bang[b][cot_cha].tolist()[i]
                    if not la_null(val):
                        khoa[val] = True
                ds_loi = self._kiem_con(b, cot_cha, khoa, bo_qua=xoa_idx)
                for l in ds_loi:
                    loi.append(l)
        if len(loi) > 0:
            chuoi_loi = ""
            for l in loi:
                chuoi_loi += "\n" + l
            raise ValueError("Không xóa được vì còn dữ liệu đang tham chiếu tới:" + chuoi_loi)
        kq = {}
        for b in xoa_idx:
            idx = xoa_idx[b]
            self.bang[b] = self.bang[b].drop(index=idx).reset_index(drop=True)
            kq[b] = len(idx)
        self.tinh_lai()
        return kq

    def _kiem_con(self, cha: str, cot_cha: str, khoa: dict, bo_qua: dict = None) -> list:
        loi = []
        for t in SCHEMA:
            s = SCHEMA[t]
            for cot in s["fk"]:
                b, c = s["fk"][cot]
                if b == cha and c == cot_cha:
                    bo = {}
                    if bo_qua is not None and t in bo_qua:
                        for x in bo_qua[t]:
                            bo[x] = True
                    dem = 0
                    for i, v in enumerate_(self.bang[t][cot].tolist()):
                        if i not in bo and not la_null(v) and v in khoa:
                            dem += 1
                    if dem > 0:
                        loi.append(f"  bảng {t} còn {dem} dòng tham chiếu tới {cha}.{cot_cha}")
        return loi