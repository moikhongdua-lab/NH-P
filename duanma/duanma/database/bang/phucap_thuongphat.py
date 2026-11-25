LOAI_CONG = ("Thưởng", "Phụ cấp")   # cộng vào lương
LOAI_TRU = ("Phạt",)                # trừ khỏi lương

SCHEMA_PHUCAP_THUONGPHAT = {
    "PHUCAP_THUONGPHAT": {
        "cols": {"MaPC": "int", "MaNV": "int", "Loai": "str", "SoTien": "float",
                 "NgayApDung": "date", "LyDo": "str"},   # NgayApDung để biết thuộc tháng nào
        "pk": ["MaPC"],
        "fk": {"MaNV": ("NHANVIEN", "MaNV")},
        "notnull": ["MaNV", "Loai", "SoTien", "NgayApDung"],
        "check": {"Loai": list(LOAI_CONG + LOAI_TRU)},
        "khoang": {"SoTien": (0, None)},
    },
}
