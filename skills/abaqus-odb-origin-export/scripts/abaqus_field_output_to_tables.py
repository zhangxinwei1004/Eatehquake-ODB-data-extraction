from __future__ import print_function

import csv
import math
import os
import traceback

from abaqus import session


ODB_NAME_CONTAINS = "EI01g-1"
STEP_NAME = "EQ"
REQUESTED_TOP_SET = "TOP_NODE"
TOP_SET_FALLBACK = "TATONG-SHANG"
BASE_SET_CANDIDATES = ["BASE_RP", "RP-1", "ASSEMBLY_DIBU_REFERENCE_POINT"]
OUT_DIR = r"E:\Codex\Codex+abaqus\EQ"
OUTPUT_PREFIX = ODB_NAME_CONTAINS

TIME_HISTORY_COLUMNS = [
    "时间_s",
    "塔顶位移_m",
    "底部位移_m",
    "塔顶相对位移_m",
    "塔顶加速度_m_s2",
    "底部加速度_m_s2",
    "底部剪力_RF1_N",
    "底部剪力_RF1_kN",
    "底部弯矩_RM1_N_m",
    "底部倾覆弯矩_RM2_N_m",
    "底部弯矩_RM3_N_m",
    "底部倾覆弯矩_RM2_kN_m",
    "底部倾覆弯矩_M_ot_N_m",
    "底部倾覆弯矩_M_ot_kN_m",
    "合成倾覆弯矩_N_m",
    "合成倾覆弯矩_kN_m",
]
SUMMARY_COLUMNS = ["统计项目", "数值", "时间_s", "单位"]


def find_target_odb():
    for key, odb in session.odbs.items():
        path = getattr(odb, "path", key)
        if ODB_NAME_CONTAINS.lower() in ("%s %s" % (key, path)).lower():
            return key, odb
    print("Target ODB containing '%s' was not found." % ODB_NAME_CONTAINS)
    print("Currently open ODBs:")
    for key, odb in session.odbs.items():
        print("  %s" % getattr(odb, "path", key))
    raise RuntimeError("Target ODB not open")


def print_available_names(odb):
    print("Available Step names: %s" % ", ".join(odb.steps.keys()))
    print("Available rootAssembly node set names: %s" % ", ".join(odb.rootAssembly.nodeSets.keys()))


def pick_node_set(odb, requested, fallback, role):
    sets = odb.rootAssembly.nodeSets
    if requested in sets:
        print("%s node set: using requested '%s'" % (role, requested))
        return sets[requested], requested
    print("%s requested node set '%s' not found." % (role, requested))
    print_available_names(odb)
    if fallback in sets:
        print("%s node set: using fallback '%s'" % (role, fallback))
        return sets[fallback], fallback
    raise RuntimeError("%s node set not found: requested '%s', fallback '%s'" % (role, requested, fallback))


def pick_first_node_set(odb, candidates, role):
    sets = odb.rootAssembly.nodeSets
    for name in candidates:
        if name in sets:
            print("%s node set: using '%s'" % (role, name))
            return sets[name], name
    print("%s node set candidates not found: %s" % (role, ", ".join(candidates)))
    print_available_names(odb)
    raise RuntimeError("%s node set not found" % role)


def require_field(frame, name, frame_index):
    if name not in frame.fieldOutputs:
        raise RuntimeError("Frame %d missing Field Output '%s'" % (frame_index, name))
    return frame.fieldOutputs[name]


def component_average(field_output, region, component_index, label):
    values = field_output.getSubset(region=region).values
    if not values:
        raise RuntimeError("No Field Output values for %s" % label)
    total = 0.0
    for value in values:
        total += float(value.data[component_index])
    return total / float(len(values))


def update_peak(peaks, key, value, time_s):
    if key not in peaks or abs(value) > abs(peaks[key][0]):
        peaks[key] = (value, time_s)


def write_summary_csv(path, rows):
    with open(path, "wb") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def try_write_xlsx(path, time_csv_path, summary_rows):
    try:
        from openpyxl import Workbook
    except Exception as exc:
        print("openpyxl unavailable in Abaqus Python; CSV files are available. %s" % exc)
        return False

    wb = Workbook()
    ws = wb.active
    ws.title = "Time_History"
    with open(time_csv_path, "rb") as f:
        for row in csv.reader(f):
            ws.append(row)
    ws2 = wb.create_sheet("Summary")
    ws2.append(SUMMARY_COLUMNS)
    for row in summary_rows:
        ws2.append([row[col] for col in SUMMARY_COLUMNS])
    wb.save(path)
    return True


def main():
    key, odb = find_target_odb()
    print("Using ODB: %s" % getattr(odb, "path", key))
    if STEP_NAME not in odb.steps:
        print("Requested Step '%s' not found." % STEP_NAME)
        print_available_names(odb)
        raise RuntimeError("Step not found: %s" % STEP_NAME)

    top_set, top_name = pick_node_set(odb, REQUESTED_TOP_SET, TOP_SET_FALLBACK, "TOP")
    base_set, base_name = pick_first_node_set(odb, BASE_SET_CANDIDATES, "BASE")
    print("Final node set mapping: TOP=%s, BASE=%s" % (top_name, base_name))

    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    time_csv_path = os.path.join(OUT_DIR, OUTPUT_PREFIX + "_Time_History.csv")
    summary_csv_path = os.path.join(OUT_DIR, OUTPUT_PREFIX + "_Summary.csv")
    xlsx_path = os.path.join(OUT_DIR, OUTPUT_PREFIX + "_postprocess_results.xlsx")

    step = odb.steps[STEP_NAME]
    peaks = {}
    max_abs_a_base = 0.0

    with open(time_csv_path, "wb") as f:
        writer = csv.DictWriter(f, fieldnames=TIME_HISTORY_COLUMNS)
        writer.writeheader()
        for frame_index, frame in enumerate(step.frames):
            u_field = require_field(frame, "U", frame_index)
            a_field = require_field(frame, "A", frame_index)
            rf_field = require_field(frame, "RF", frame_index)
            rm_field = require_field(frame, "RM", frame_index)

            time_s = float(frame.frameValue)
            u_top = component_average(u_field, top_set, 0, "U1 top")
            u_base = component_average(u_field, base_set, 0, "U1 base")
            a_top = component_average(a_field, top_set, 0, "A1 top")
            a_base = component_average(a_field, base_set, 0, "A1 base")
            rf1 = component_average(rf_field, base_set, 0, "RF1 base")
            rm1 = component_average(rm_field, base_set, 0, "RM1 base")
            rm2 = component_average(rm_field, base_set, 1, "RM2 base")
            rm3 = component_average(rm_field, base_set, 2, "RM3 base")
            m_resultant = math.sqrt(rm1 * rm1 + rm2 * rm2)
            u_rel = u_top - u_base

            writer.writerow({
                "时间_s": time_s,
                "塔顶位移_m": u_top,
                "底部位移_m": u_base,
                "塔顶相对位移_m": u_rel,
                "塔顶加速度_m_s2": a_top,
                "底部加速度_m_s2": a_base,
                "底部剪力_RF1_N": rf1,
                "底部剪力_RF1_kN": rf1 / 1000.0,
                "底部弯矩_RM1_N_m": rm1,
                "底部倾覆弯矩_RM2_N_m": rm2,
                "底部弯矩_RM3_N_m": rm3,
                "底部倾覆弯矩_RM2_kN_m": rm2 / 1000.0,
                "底部倾覆弯矩_M_ot_N_m": rm2,
                "底部倾覆弯矩_M_ot_kN_m": rm2 / 1000.0,
                "合成倾覆弯矩_N_m": m_resultant,
                "合成倾覆弯矩_kN_m": m_resultant / 1000.0,
            })

            update_peak(peaks, "最大塔顶相对位移", u_rel, time_s)
            update_peak(peaks, "最大塔顶加速度", a_top, time_s)
            update_peak(peaks, "最大底部剪力", rf1, time_s)
            update_peak(peaks, "最大底部倾覆弯矩", rm2, time_s)
            update_peak(peaks, "最大合成倾覆弯矩", m_resultant, time_s)
            if abs(a_base) > max_abs_a_base:
                max_abs_a_base = abs(a_base)
            if frame_index % 100 == 0:
                print("Processed frame %d / %d" % (frame_index + 1, len(step.frames)))

    eta_a = ""
    if max_abs_a_base > 0.0:
        eta_a = abs(peaks["最大塔顶加速度"][0]) / max_abs_a_base
    summary_rows = [
        {"统计项目": "最大塔顶相对位移", "数值": peaks["最大塔顶相对位移"][0], "时间_s": peaks["最大塔顶相对位移"][1], "单位": "m"},
        {"统计项目": "最大塔顶加速度", "数值": peaks["最大塔顶加速度"][0], "时间_s": peaks["最大塔顶加速度"][1], "单位": "m/s^2"},
        {"统计项目": "最大底部剪力", "数值": peaks["最大底部剪力"][0], "时间_s": peaks["最大底部剪力"][1], "单位": "N"},
        {"统计项目": "最大底部倾覆弯矩", "数值": peaks["最大底部倾覆弯矩"][0], "时间_s": peaks["最大底部倾覆弯矩"][1], "单位": "N*m"},
        {"统计项目": "最大合成倾覆弯矩", "数值": peaks["最大合成倾覆弯矩"][0], "时间_s": peaks["最大合成倾覆弯矩"][1], "单位": "N*m"},
        {"统计项目": "塔顶加速度放大系数_eta_a", "数值": eta_a, "时间_s": "", "单位": "-"},
    ]
    write_summary_csv(summary_csv_path, summary_rows)
    wrote_xlsx = try_write_xlsx(xlsx_path, time_csv_path, summary_rows)

    print("Wrote CSV: %s" % time_csv_path)
    print("Wrote CSV: %s" % summary_csv_path)
    if wrote_xlsx:
        print("Wrote Excel: %s" % xlsx_path)
    for row in summary_rows:
        print("%s = %s at time_s=%s %s" % (row["统计项目"], row["数值"], row["时间_s"], row["单位"]))


try:
    main()
except Exception:
    traceback.print_exc()
    raise
