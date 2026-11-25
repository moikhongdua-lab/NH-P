# Quản lý nhân sự - chấm công - lương

Python + pandas + Streamlit. Dữ liệu lưu thành CSV cạnh file mã nguồn của từng bảng
(ví dụ `database/bang/luong.py` + `database/bang/luong.csv`).

## Chạy
```
pip install -r requirements.txt
streamlit run giaodien/app.py
```
## Test (không cần cài thêm gì)
```
python -m unittest discover -s tests -t .
```
Cũng chạy được bằng `pytest` nếu bạn đã cài.

## Cấu trúc
```
database/
  csdl.py            CSDL: them / sua / xoa, ràng buộc, giao dịch, đọc-ghi CSV
  kieu_dl.py         ép kiểu, null, bỏ dấu, đổi giá trị theo kiểu cột
  schema.py          gom schema các bảng
  bang/              <bảng>.py (schema + tính toán) và <bảng>.csv (dữ liệu)
  map_dulieu/map.py  data map: kết nối FK, tra tên bảng/cột
hamtinhtoan/         hàm tính toán thuần (dict các list) + trình dịch lệnh sửa/thêm/xóa/truy vấn
giaodien/app.py      giao diện Streamlit
tests/               unittest
```
## Quy tắc đáng nhớ
- Mọi lệnh ghi là một giao dịch: lỗi thì hoàn tác và KHÔNG ghi CSV.
- Ca ngày 07:00-16:00, ca đêm 19:00-05:00 (ca có giờ kết thúc < giờ bắt đầu là ca đêm).
  Giờ vào = giờ ra, giờ ra < giờ vào ở ca ngày, hoặc làm quá 16 giờ => báo lỗi để người kiểm tra.
- Thêm nhân viên => tự tạo dòng lương của tháng hiện tại. Xóa nhân viên => xóa luôn dòng lương của họ.
- Lương dùng LuongCoBan HIỆN TẠI cho mọi tháng (chủ ý; muốn chốt lương cũ thì thêm cột lưu lương cơ bản vào BANGLUONG).
- Mở CSV bằng Excel sửa tay vẫn đọc lại được (UTF-8 BOM, ngày dd/mm/yyyy hoặc yyyy-mm-dd).
- Chỉ ô trống thật ("" hoặc "null") mới là NULL; tên như "Na" là dữ liệu bình thường.
- Truy vấn: dấu phẩy cuối `in(NHANVIEN, HoTen, )`, đặt tên cột kết quả `dem(NHANVIEN, GioiTinh, as='SoNguoi')`.
