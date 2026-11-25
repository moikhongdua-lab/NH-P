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

THU_MUC = Path(__file__).parent / "bang"
# tên bảng -> tên file (không phải bảng nào cũng trùng tên file .py)
TEN_FILE = {"PHONGBAN": "phongban", "NHANVIEN": "nhanvien", "CALAMVIEC": "calamviec",
            "BANGCHAMCONG": "chamcong", "PHUCAP_THUONGPHAT": "phucap_thuongphat",
            "BANGLUONG": "luong"}


def giao_dich(ham):
    """Chụp lại trạng thái; lỗi -> hoàn tác; lệnh ngoài cùng thành công -> ghi CSV."""
    @functools.wraps(ham)
    def boc(self, *a, **kw):
        if self._dang_chay:                 # lời gọi lồng nhau: để lệnh ngoài cùng lo
            return ham(self, *a, **kw)
        chup = dict(self.bang)              # các DataFrame không bị sửa tại chỗ nên chụp nông là đủ
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
    return boc


class CSDL:
    def __init__(self, thu_muc=None):
        self.thu_muc = Path(thu_muc) if thu_muc else THU_MUC
        self.bang = {ten: tao_bang_rong(ten) for ten in SCHEMA}
        self.dm = tao_data_map()          # data map: đường kết nối giữa các bảng
        self._dang_chay = False
        self.doc()

    # ---------- lưu / đọc CSV ----------
    def _csv(self, ten: str) -> Path:
        return self.thu_muc / (TEN_FILE[ten] + ".csv")

    def luu(self) -> None:
        """Ghi mọi bảng ra CSV (ghi file tạm rồi thay, tránh file hỏng giữa chừng)."""
        self.thu_muc.mkdir(parents=True, exist_ok=True)
        for ten, df in self.bang.items():
            dich = self._csv(ten)
            tam = dich.with_name(dich.name + ".tmp")
            df.to_csv(tam, index=False, encoding="utf-8-sig")     # utf-8-sig để Excel đọc đúng tiếng Việt
            os.replace(tam, dich)

    def doc(self) -> None:
        """Đọc CSV (nếu có) vào bảng. Người dùng có thể mở bằng Excel, sửa tay rồi lưu."""
        for ten in SCHEMA:
            f = self._csv(ten)
            if f.exists():
                df = pd.read_csv(f, dtype=str, keep_default_na=False, encoding="utf-8-sig")
                if len(df):
                    self.bang[ten] = ep_kieu(ten, df)
        self.tinh_lai()

    # ---------- truy cập ----------
    def _ten(self, ten: str) -> str:
        ten = ten.upper()
        if ten not in self.bang:
            raise KeyError(f"Không có bảng {ten}. Các bảng: {list(self.bang)}")
        return ten

    def __getitem__(self, ten: str) -> pd.DataFrame:
        return self.bang[self._ten(ten)]

    # ---------- thêm dữ liệu ----------
    @giao_dich
    def them(self, ten: str, du_lieu) -> None:
        """Thêm 1 dòng (dict), nhiều dòng (list[dict]) hoặc DataFrame.
        Có lỗi ở bất kỳ dòng nào thì KHÔNG thêm gì cả (giống transaction).
        Thêm nhân viên mới thì tự tạo dòng lương của tháng hiện tại cho nhân viên đó."""
        ten = self._ten(ten)
        s = SCHEMA[ten]
        if isinstance(du_lieu, dict):
            du_lieu = [du_lieu]
        moi = du_lieu.copy() if isinstance(du_lieu, pd.DataFrame) else pd.DataFrame(du_lieu)
        moi = moi.drop(columns=[c for c in s.get("derived", []) if c in moi.columns])
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
        """pk số nguyên đơn bị bỏ trống thì tự cấp (max + 1)."""
        pk = SCHEMA[ten]["pk"]
        if len(pk) != 1 or SCHEMA[ten]["cols"][pk[0]] != "int":
            return
        cot = pk[0]
        da_co = [x for x in (self.bang[ten][cot].max(), moi[cot].max()) if not la_null(x)]
        tiep = int(max(da_co)) if da_co else 0
        for i in moi.index[moi[cot].isna()]:
            tiep += 1
            moi.loc[i, cot] = tiep

    # ---------- kiểm tra ràng buộc ----------
    def _kiem_tra(self, ten: str, moi: pd.DataFrame, cu: pd.DataFrame = None, hanh_dong: str = "thêm") -> None:
        s, loi = SCHEMA[ten], []
        cu = self.bang[ten] if cu is None else cu

        for cot in dict.fromkeys(s["pk"] + s.get("notnull", [])):
            for i in moi.index[moi[cot].isna()]:
                loi.append(f"  dòng {i}: cột {cot} không được để trống")

        for cot, cho_phep in s.get("check", {}).items():
            ban_do = {x.casefold(): x for x in cho_phep}
            for i in moi.index[moi[cot].notna()]:
                gt = moi.at[i, cot]
                if gt.casefold() in ban_do:
                    moi.at[i, cot] = ban_do[gt.casefold()]      # chuẩn hóa 'nam' -> 'Nam'
                else:
                    loi.append(f"  dòng {i}: {cot}={gt!r} không hợp lệ, chỉ nhận {cho_phep}")

        for cot, (lo, hi) in s.get("khoang", {}).items():
            for i in moi.index[moi[cot].notna()]:
                v = moi.at[i, cot]
                if (lo is not None and v < lo) or (hi is not None and v > hi):
                    loi.append(f"  dòng {i}: {cot}={v} ngoài khoảng [{lo}, {hi}]")

        for bo_cot, nhan in [(s["pk"], "khóa chính")] + [(u, "unique") for u in s.get("unique", [])]:
            for i in self._tim_trung(cu, moi, bo_cot):
                loi.append(f"  dòng {i}: trùng {nhan} {bo_cot}")

        for cot, (bang_cha, cot_cha) in s["fk"].items():
            cha = set(self.bang[bang_cha][cot_cha].dropna().tolist())
            for i in moi.index[moi[cot].notna()]:
                if moi.at[i, cot] not in cha:
                    loi.append(f"  dòng {i}: {cot}={moi.at[i, cot]} không có trong {bang_cha}.{cot_cha}")

        if loi:
            raise ValueError(f"Không {hanh_dong} được {'vào ' if hanh_dong == 'thêm' else ''}{ten}:\n" + "\n".join(loi))

    @staticmethod
    def _tim_trung(cu: pd.DataFrame, moi: pd.DataFrame, cols: list) -> list:
        """Dòng của `moi` trùng với bảng cũ hoặc trùng nhau. Bộ khóa có NA không tính là trùng (như SQL)."""
        da_co = set(cu[cols].dropna().itertuples(index=False, name=None))
        thay, trung = set(), []
        for i, khoa in zip(moi.index, moi[cols].itertuples(index=False, name=None)):
            if any(la_null(x) for x in khoa):
                continue
            if khoa in da_co or khoa in thay:
                trung.append(i)
            thay.add(khoa)
        return trung

    # ---------- tính toán tự động ----------
    def tinh_lai(self) -> None:
        """Chấm công -> Cong (cần ca làm) -> BANGLUONG (cần công, phụ cấp/thưởng phạt, lương cơ bản)."""
        b = self.bang
        b["BANGCHAMCONG"] = cap_nhat_cong(b["BANGCHAMCONG"], b["CALAMVIEC"])
        b["BANGLUONG"] = tinh_luong(b["BANGLUONG"], b["BANGCHAMCONG"],
                                    b["NHANVIEN"], b["PHUCAP_THUONGPHAT"])

    @giao_dich
    def tao_luong_thang(self, thang: int, nam: int) -> None:
        """Tạo dòng lương tháng này cho mọi nhân viên chưa có (số liệu tự tính)."""
        luong = self.bang["BANGLUONG"]
        da_co = set(luong.loc[(luong["Thang"] == thang) & (luong["Nam"] == nam), "MaNV"].tolist())
        ds = [{"MaNV": ma, "Thang": thang, "Nam": nam}
              for ma in self.bang["NHANVIEN"]["MaNV"].tolist() if ma not in da_co]
        if ds:
            self.them("BANGLUONG", ds)

    # ---------- sửa ----------
    @giao_dich
    def sua(self, ten: str, cot_dich: str, gia_tri_moi, cot_loc: str, gia_tri_loc, bang_loc: str = None) -> int:
        """Sửa `cot_dich` của `ten` thành gia_tri_moi, ở các dòng có `cot_loc` = gia_tri_loc.
        `cot_loc` có thể ở bảng khác nếu hai bảng nối trực tiếp bằng FK. Trả về số dòng sửa.
        Có lỗi thì không sửa gì cả."""
        ten = self._ten(ten)
        bang_loc = self._ten(bang_loc) if bang_loc else ten
        s = SCHEMA[ten]
        if cot_dich in s.get("derived", []):
            raise ValueError(f"Cột {cot_dich} là cột tự tính, không sửa tay được")

        gt_loc = ep_gia_tri(SCHEMA[bang_loc]["cols"][cot_loc], gia_tri_loc, cot_loc)
        if gt_loc is None:
            raise ValueError("Giá trị điều kiện không được để trống")
        tbl_loc = self.bang[bang_loc]
        khop = [i for i, v in enumerate(tbl_loc[cot_loc].tolist()) if not la_null(v) and v == gt_loc]

        if bang_loc == ten:
            dong_sua = khop
        else:                                           # nối qua FK: lấy khóa của các dòng khớp
            cot_a, cot_b = tim_ket_noi(self.dm, ten, bang_loc)
            khoa = {tbl_loc[cot_b].tolist()[i] for i in khop}
            dong_sua = [i for i, v in enumerate(self.bang[ten][cot_a].tolist()) if not la_null(v) and v in khoa]
        if not dong_sua:
            raise ValueError(f"Không có dòng nào thỏa điều kiện {bang_loc}.{cot_loc} = {gia_tri_loc!r}")

        gt_moi = ep_gia_tri(s["cols"][cot_dich], gia_tri_moi, cot_dich)
        cand = self.bang[ten].copy()
        gia_tri = cand[cot_dich].tolist()
        khoa_cu = set()
        for i in dong_sua:
            if not la_null(gia_tri[i]) and gia_tri[i] != gt_moi:
                khoa_cu.add(gia_tri[i])
            gia_tri[i] = gt_moi
        cand[cot_dich] = gia_tri
        cand = ep_kieu(ten, cand)
        self._kiem_tra(ten, cand, cu=tao_bang_rong(ten), hanh_dong="sửa")      # kiểm tra lại cả bảng sau khi sửa
        loi = self._kiem_con(ten, cot_dich, khoa_cu)
        if loi:
            raise ValueError(f"Không sửa được {ten}.{cot_dich} vì đang được bảng khác tham chiếu:\n" + "\n".join(loi))

        self.bang[ten] = cand
        self.tinh_lai()
        return len(dong_sua)

    # ---------- xóa ----------
    @giao_dich
    def xoa(self, gia_tri=None, cot: str = None, bang: str = None) -> dict:
        """Xóa dòng. Cần ít nhất 1 trong 3 (giá trị, cột, bảng):
          giá trị + cột + bảng : xóa dòng của bảng có cột = giá trị
          giá trị + bảng       : xóa dòng của bảng có BẤT KỲ cột nào = giá trị
          giá trị + cột        : xóa dòng có cột = giá trị ở MỌI bảng có cột đó
          chỉ giá trị          : xóa dòng có bất kỳ ô nào = giá trị ở mọi bảng
          chỉ bảng             : xóa toàn bộ dòng của bảng
        Dòng cha đang được bảng con tham chiếu thì bị chặn (như ON DELETE RESTRICT),
        riêng BANGLUONG là bảng tự tính nên xóa nhân viên sẽ xóa luôn các dòng lương của họ.
        Trả về {bảng: số dòng đã xóa}."""
        bang = self._ten(bang) if bang else None
        co_gt = not la_null(gia_tri)
        if not co_gt and cot is None and bang is None:
            raise ValueError("Cần ít nhất một trong ba: giá trị, cột, bảng")
        if not co_gt and cot is not None:
            raise ValueError("Chưa hỗ trợ xóa theo cột mà không có giá trị. Hãy thêm giá trị cần xóa.")

        xoa_idx = {}
        if not co_gt:                                    # chỉ bảng
            n = len(self.bang[bang])
            if n:
                xoa_idx[bang] = list(range(n))
        else:
            for b in ([bang] if bang else list(self.bang)):
                cols = SCHEMA[b]["cols"]
                if cot is not None and cot not in cols:
                    if bang:
                        raise ValueError(f"Bảng {b} không có cột {cot}")
                    continue
                dong = set()
                for c in ([cot] if cot else list(cols)):
                    try:
                        gt = ep_gia_tri(cols[c], gia_tri, c)
                    except ValueError:
                        if cot:
                            raise
                        continue                         # tìm khắp nơi: cột khác kiểu thì bỏ qua
                    for i, v in enumerate(self.bang[b][c].tolist()):
                        if not la_null(v) and v == gt:
                            dong.add(i)
                if dong:
                    xoa_idx[b] = sorted(dong)
        if not xoa_idx:
            raise ValueError("Không có dòng nào khớp để xóa")

        if "NHANVIEN" in xoa_idx:                        # lương là bảng tự tính: xóa theo nhân viên
            ma = {self.bang["NHANVIEN"]["MaNV"].tolist()[i] for i in xoa_idx["NHANVIEN"]}
            them_luong = [i for i, v in enumerate(self.bang["BANGLUONG"]["MaNV"].tolist())
                          if not la_null(v) and v in ma]
            if them_luong:
                xoa_idx["BANGLUONG"] = sorted(set(xoa_idx.get("BANGLUONG", [])) | set(them_luong))

        loi = []
        for b, idx in xoa_idx.items():                   # chặn xóa dòng cha còn dòng con
            for cot_cha in {c for _, _, cha, c in self.dm["ket_noi"] if cha == b}:
                khoa = {self.bang[b][cot_cha].tolist()[i] for i in idx}
                khoa = {k for k in khoa if not la_null(k)}
                loi += self._kiem_con(b, cot_cha, khoa, bo_qua=xoa_idx)
        if loi:
            raise ValueError("Không xóa được vì còn dữ liệu đang tham chiếu tới:\n" + "\n".join(loi))

        for b, idx in xoa_idx.items():
            self.bang[b] = self.bang[b].drop(index=idx).reset_index(drop=True)
        self.tinh_lai()
        return {b: len(idx) for b, idx in xoa_idx.items()}

    def _kiem_con(self, cha: str, cot_cha: str, khoa: set, bo_qua: dict = None) -> list:
        """Các bảng con còn dòng tham chiếu tới `khoa` của cha.cot_cha (không tính dòng sắp bị xóa)."""
        loi = []
        for t, s in SCHEMA.items():
            for cot, (b, c) in s["fk"].items():
                if b == cha and c == cot_cha:
                    bo = set((bo_qua or {}).get(t, []))
                    dem = sum(1 for i, v in enumerate(self.bang[t][cot].tolist())
                              if i not in bo and not la_null(v) and v in khoa)
                    if dem:
                        loi.append(f"  bảng {t} còn {dem} dòng tham chiếu tới {cha}.{cot_cha}")
        return loi
