"""Gom schema của tất cả bảng. Thứ tự dict = thứ tự tạo bảng (bảng cha trước, bảng con sau).

Mỗi bảng có:
  cols     : {tên cột: kiểu}  (int | float | str | date | time)
  pk       : danh sách cột khóa chính
  fk       : {cột: (bảng cha, cột cha)}
  notnull  : cột không được trống (pk luôn không được trống)
  unique   : danh sách các bộ cột không được trùng
  check    : {cột: [giá trị cho phép]}
  khoang   : {cột: (min, max)}  (None = không giới hạn)
  derived  : cột tự tính, bị bỏ qua nếu người dùng nhập
"""
from database.bang.phongban import SCHEMA_PHONGBAN
from database.bang.nhanvien import SCHEMA_NHANVIEN
from database.bang.calamviec import SCHEMA_CALAMVIEC
from database.bang.chamcong import SCHEMA_CHAMCONG
from database.bang.phucap_thuongphat import SCHEMA_PHUCAP_THUONGPHAT
from database.bang.luong import SCHEMA_BANGLUONG

SCHEMA: dict = {}
for _s in (SCHEMA_PHONGBAN, SCHEMA_NHANVIEN, SCHEMA_CALAMVIEC, SCHEMA_CHAMCONG,
           SCHEMA_PHUCAP_THUONGPHAT, SCHEMA_BANGLUONG):
    SCHEMA.update(_s)
