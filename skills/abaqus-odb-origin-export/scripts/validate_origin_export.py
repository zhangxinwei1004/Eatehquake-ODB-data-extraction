from __future__ import annotations

import csv
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


TIME = "\u65f6\u95f4_s"
TOP_REL_U = "\u5854\u9876\u76f8\u5bf9\u4f4d\u79fb_m"
TOP_A = "\u5854\u9876\u52a0\u901f\u5ea6_m_s2"
BASE_A = "\u5e95\u90e8\u52a0\u901f\u5ea6_m_s2"
BASE_SHEAR = "\u5e95\u90e8\u526a\u529b_RF1_kN"
BASE_MOT = "\u5e95\u90e8\u503e\u8986\u5f2f\u77e9_M_ot_kN_m"
ITEM = "\u9879\u76ee"
MOMENT = "\u5f2f\u77e9_kN_m"


EXPECTED_FILES: Dict[str, Sequence[str]] = {
    "Fig1_ElCentro_input_acceleration.csv": (TIME, BASE_A),
    "Fig2_top_relative_displacement.csv": (TIME, TOP_REL_U),
    "Fig3_top_base_acceleration_comparison.csv": (TIME, TOP_A, BASE_A),
    "Fig4_base_shear_time_history.csv": (TIME, BASE_SHEAR),
    "Fig5_base_overturning_moment.csv": (TIME, BASE_MOT),
    "Fig6_overturning_moment_vs_capacity.csv": (ITEM, MOMENT),
}


def read_csv(path: Path) -> Tuple[List[str], List[List[str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            headers = next(reader)
        except StopIteration:
            raise RuntimeError("%s is empty" % path)
        return headers, [row for row in reader if row]


def require_number(value: str, path: Path, row_no: int, col_name: str) -> None:
    if value == "":
        raise RuntimeError("%s row %d column '%s' is blank" % (path, row_no, col_name))
    try:
        number = float(value)
    except ValueError:
        raise RuntimeError("%s row %d column '%s' is not numeric: %r" % (path, row_no, col_name, value))
    if math.isnan(number) or math.isinf(number):
        raise RuntimeError("%s row %d column '%s' is not finite: %r" % (path, row_no, col_name, value))


def validate_table(path: Path, headers: Sequence[str], rows: Sequence[Sequence[str]], expected_headers: Sequence[str], expected_rows: Optional[int]) -> None:
    if list(headers) != list(expected_headers):
        raise RuntimeError("%s headers mismatch. expected=%r actual=%r" % (path, list(expected_headers), list(headers)))
    if expected_rows is not None and len(rows) != expected_rows:
        raise RuntimeError("%s row count mismatch. expected=%d actual=%d" % (path, expected_rows, len(rows)))
    for row_index, row in enumerate(rows, start=2):
        if len(row) != len(expected_headers):
            raise RuntimeError("%s row %d has %d columns; expected %d. This often means rows were flattened during export." % (path, row_index, len(row), len(expected_headers)))
        for col_name, value in zip(expected_headers, row):
            if col_name == ITEM:
                if value == "":
                    raise RuntimeError("%s row %d item name is blank" % (path, row_index))
            else:
                require_number(value, path, row_index, col_name)


def validate_origin_export(root: Path) -> None:
    origin_dir = root / "Origin_export"
    if not origin_dir.is_dir():
        raise RuntimeError("Missing Origin_export directory: %s" % origin_dir)

    time_csvs = sorted(root.glob("*_Time_History.csv"))
    expected_rows = None
    if time_csvs:
        _, source_rows = read_csv(time_csvs[0])
        expected_rows = len(source_rows)

    for filename, expected_headers in EXPECTED_FILES.items():
        path = origin_dir / filename
        if not path.is_file():
            raise RuntimeError("Missing Origin CSV: %s" % path)
        headers, rows = read_csv(path)
        expected = None if filename.startswith("Fig6_") else expected_rows
        validate_table(path, headers, rows, expected_headers, expected)

    workbook = origin_dir / "Origin_plot_data.xlsx"
    if not workbook.is_file():
        raise RuntimeError("Missing Origin workbook: %s" % workbook)

    print("Origin export validation passed: %s" % origin_dir)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python validate_origin_export.py <dataset-output-folder>")
    validate_origin_export(Path(sys.argv[1]).resolve())


if __name__ == "__main__":
    main()
