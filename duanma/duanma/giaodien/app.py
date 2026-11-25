"""Giao diện Streamlit.  Chạy từ thư mục gốc dự án:   streamlit run giaodien/app.py

Luồng (theo sơ đồ):  bắt đầu -> đọc CSV & tạo data map -> menu 4 chức năng
  sửa / thêm / xóa : hiện ô nhập + cú pháp -> thực thi -> (lỗi | thành công + bảng sau khi đổi) -> xác nhận -> menu
  tìm kiếm         : ô nhập truy vấn + các hàm có sẵn -> dịch & thực thi -> hiện bảng
Dữ liệu nằm trong database/bang/*.csv và được ghi lại sau mỗi lệnh thành công.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from database import CSDL
from database.kieu_dl import TEN_KIEU
from database.schema import SCHEMA
from hamtinhtoan import sua, them, xoa, truyvan

st.set_page_config(page_title="Quản lý nhân sự - lương", layout="wide")


@st.cache_resource
def lay_csdl():
    """Một đối tượng CSDL dùng chung cho mọi tab trình duyệt (tránh ghi đè CSV của nhau)."""
    return CSDL()


# ---------------------------------------------------------------- trạng thái
db = lay_csdl()
if "trang" not in st.session_state:
    st.session_state.trang = "menu"
    st.session_state.kq = None              # kết quả sửa/thêm/xóa gần nhất
    st.session_state.kq_tim = None          # kết quả tìm kiếm gần nhất


def chuyen(trang):
    st.session_state.trang = trang
    st.rerun()


def _loi(e):
    if isinstance(e, (ValueError, KeyError)):
        return e.args[0] if e.args else str(e)
    return f"Lỗi không mong đợi ({type(e).__name__}): {e}"


# ---------------------------------------------------------------- hiển thị
def _o(v):
    if v is None or v is pd.NA or v is pd.NaT:
        return None
    if isinstance(v, pd.Timestamp):
        return v.strftime("%d/%m/%Y")
    if hasattr(v, "item"):                  # numpy -> python
        v = v.item()
    if isinstance(v, float) and v != v:
        return None
    return v


def hien_bang(bang):
    """DataFrame hoặc dict các list -> bảng trên màn hình (ô trống để trống, ngày dd/mm/yyyy)."""
    cot = bang.columns if isinstance(bang, pd.DataFrame) else bang
    st.dataframe(pd.DataFrame({c: pd.Series([_o(v) for v in bang[c]], dtype=object) for c in cot}))


def hien_luu_y_kieu():
    with st.expander("Cột và kiểu dữ liệu của từng bảng (lưu ý khi nhập)"):
        for ten, s in SCHEMA.items():
            st.markdown(f"**{ten}**")
            dong = []
            for c, k in s["cols"].items():
                ghi_chu = []
                if c in s["pk"]:
                    ghi_chu.append("khóa chính (để trống sẽ tự cấp)")
                if c in s["fk"]:
                    ghi_chu.append("khóa ngoại → %s.%s" % s["fk"][c])
                if c in s.get("derived", []):
                    ghi_chu.append("TỰ TÍNH, không nhập")
                if c in s.get("notnull", []):
                    ghi_chu.append("bắt buộc")
                if c in s.get("check", {}):
                    ghi_chu.append("chỉ nhận: " + ", ".join(s["check"][c]))
                dong.append({"Cột": c, "Kiểu": TEN_KIEU[k], "Ghi chú": "; ".join(ghi_chu)})
            st.table(pd.DataFrame(dong))


# ---------------------------------------------------------------- các trang
def trang_menu():
    st.subheader("Menu")
    cot = st.columns(4)
    nut = [("✏️ Chọn sửa", "sua"), ("➕ Chọn thêm", "them"), ("🗑️ Chọn xóa", "xoa"), ("🔍 Tìm kiếm", "timkiem")]
    for c, (nhan, trang) in zip(cot, nut):
        if c.button(nhan, key="menu_" + trang):
            chuyen(trang)
    st.divider()
    st.caption("Dữ liệu hiện tại (lưu trong database/bang/*.csv)")
    tab = st.tabs(list(db.bang))
    for t, ten in zip(tab, db.bang):
        with t:
            hien_bang(db[ten])


def trang_lenh(key, tieu_de, cu_phap, vi_du, module, can_xac_nhan=False):
    st.subheader(tieu_de)
    st.info("Cú pháp:  " + cu_phap)
    st.code(vi_du, language=None)
    hien_luu_y_kieu()
    lenh = st.text_area("Nhập lệnh", key="lenh_" + key)
    cho_phep = True
    if can_xac_nhan:
        cho_phep = st.checkbox("Tôi hiểu dữ liệu đã xóa không khôi phục được", key="xn_" + key)
    c1, c2 = st.columns(2)
    chay = c1.button("Thực thi", key="chay_" + key, disabled=not cho_phep)
    ve = c2.button("⬅ Về menu", key="ve_" + key)
    if ve:
        chuyen("menu")
    if chay:
        try:
            bang, tb = module.thuc_thi(db, lenh)
            st.session_state.kq = {"ok": True, "thong_diep": tb, "bang": bang}
        except Exception as e:
            st.session_state.kq = {"ok": False, "thong_diep": _loi(e)}
        chuyen("ket_qua")


def trang_ket_qua():
    kq = st.session_state.kq
    if kq is None:
        chuyen("menu")
        return
    if kq["ok"]:
        st.success(kq["thong_diep"])
        st.caption(f"Bảng {kq['bang']} sau khi thay đổi")
        hien_bang(db[kq["bang"]])
    else:
        st.error("Lỗi:\n\n" + str(kq["thong_diep"]).replace("\n", "  \n"))
    if st.button("Xác nhận", key="xac_nhan"):
        chuyen("menu")


HAM_MAU = [
    ("tổng", "tong(gom(BANGCHAMCONG, MaNV), Cong)"),
    ("tính trung bình", "tinh_chung_binh(gom(NHANVIEN, MaPB), LuongCoBan)"),
    ("gom nhóm", "gom(NHANVIEN, MaPB)"),
    ("đếm", "dem(NHANVIEN, GioiTinh, as='SoNguoi')"),
    ("sắp xếp", "sap_xep(NHANVIEN, LuongCoBan, giam)"),
    ("ghép bảng", "ghep(NHANVIEN, BANGLUONG)"),
    ("lọc ô", "loc(NHANVIEN, LuongCoBan > 500000)"),
    ("in", "in(NHANVIEN, HoTen, LuongCoBan)"),
    ("top x", "top(NHANVIEN, LuongCoBan, 2)"),
]


def _chen_mau(mau):
    st.session_state["truy_van"] = mau


def trang_tim_kiem():
    st.subheader("Tìm kiếm")
    st.write("Các hàm có sẵn (bấm để chèn mẫu vào ô nhập):")
    for hang in (HAM_MAU[:5], HAM_MAU[5:]):
        cot = st.columns(5)
        for c, (ten, mau) in zip(cot, hang):
            c.button(ten, key="ham_" + ten, on_click=_chen_mau, args=(mau,))
    st.caption("Các hàm lồng nhau, được tính từ ngoặc trong ra ngoài. Ví dụ:  "
               "in(loc(ghep(NHANVIEN, BANGLUONG), HoTen == 'Thanh Tùng'), HoTen, LuongThucNhan)")
    with st.expander("Cú pháp từng hàm"):
        st.code("\n".join(truyvan.CU_PHAP_HAM.values()), language=None)
    hien_luu_y_kieu()
    st.text_area("Nhập truy vấn", key="truy_van")
    c1, c2 = st.columns(2)
    chay = c1.button("Thực hiện", key="chay_tim")
    ve = c2.button("Xác nhận / về menu", key="ve_tim")
    if ve:
        chuyen("menu")
    if chay:
        try:
            bang, buoc = truyvan.thuc_thi(db, st.session_state["truy_van"])
            st.session_state.kq_tim = {"ok": True, "bang": bang, "buoc": buoc}
        except Exception as e:
            st.session_state.kq_tim = {"ok": False, "thong_diep": _loi(e)}
    kq = st.session_state.kq_tim
    if kq is not None:
        if kq["ok"]:
            st.success("Truy vấn thành công")
            hien_bang(kq["bang"])
            with st.expander("Thứ tự tính (trong ra ngoài)"):
                for i, b in enumerate(kq["buoc"], 1):
                    st.text(f"{i}. {b}")
        else:
            st.error("Lỗi:\n\n" + str(kq["thong_diep"]).replace("\n", "  \n"))


# ---------------------------------------------------------------- điều hướng
st.title("Quản lý nhân sự - chấm công - lương")
trang = st.session_state.trang
if trang == "menu":
    trang_menu()
elif trang == "sua":
    trang_lenh("sua", "Sửa dữ liệu", sua.CU_PHAP, sua.VI_DU, sua)
elif trang == "them":
    trang_lenh("them", "Thêm dữ liệu", them.CU_PHAP, them.VI_DU, them)
elif trang == "xoa":
    trang_lenh("xoa", "Xóa dữ liệu", xoa.CU_PHAP, xoa.VI_DU, xoa, can_xac_nhan=True)
elif trang == "timkiem":
    trang_tim_kiem()
elif trang == "ket_qua":
    trang_ket_qua()
