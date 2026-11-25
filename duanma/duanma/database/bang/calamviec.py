# Ca ngày: 07:00 - 16:00.  Ca đêm: 19:00 - 05:00 (GioKetThuc < GioBatDau => ca qua đêm).
SCHEMA_CALAMVIEC = {
    "CALAMVIEC": {
        "cols": {"MaCa": "int", "TenCa": "str", "GioBatDau": "time",
                 "GioKetThuc": "time", "HeSoCa": "float"},
        "pk": ["MaCa"],
        "fk": {},
        "notnull": ["TenCa", "HeSoCa"],
        "khoang": {"HeSoCa": (0, None)},
    },
}
