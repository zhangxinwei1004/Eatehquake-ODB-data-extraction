---
name: abaqus-odb-origin-export
description: Extract earthquake dynamic analysis time-history data from already-open Abaqus/CAE ODB files through Abaqus MCP using read-only Field Output access, export Chinese-header Excel/CSV postprocessing tables, and convert those tables into Origin-ready CSV/XLSX plotting data. Use when the user asks to process Abaqus ODB seismic results, TOP_NODE/BASE_RP or fallback node sets, U/A/RF/RM field outputs, postprocess_results.xlsx, Origin_export, UTF-8-SIG CSVs, Chinese engineering headers, or Origin plotting data for displacement, acceleration, base shear, and overturning moment.
---

# Abaqus ODB Origin Export

Use this skill for two linked workflows:

1. Read an already-open Abaqus/CAE ODB through Abaqus MCP, using Field Output only, and export time-history and summary tables.
2. Convert the exported `postprocess_results.xlsx` into Origin-ready CSV and workbook files.

## Safety Rules

- Treat Abaqus as read-only unless the user explicitly requests otherwise.
- Do not modify models, materials, loads, boundary conditions, meshes, sets, jobs, or CAE files.
- Do not save CAE files.
- Do not submit jobs.
- Do not use History Output for this workflow; read `U`, `A`, `RF`, and `RM` from each Frame Field Output.
- If a required Step or node set is absent, print available Step names and node set names before stopping or choosing a user-approved fallback.
- Do not delete or overwrite existing result folders when organizing outputs.

## Output Organization

Place final generated files under:

`E:\Codex\对话内容`

Create one subfolder per processed dataset or ODB name. For example:

- `EI01g`
- `EI02g`
- `EI025g`

If the target folder already exists, do not delete it and do not merge into it unless the user explicitly asks. Instead, create the next available suffix:

- `EI01g-1`
- `EI01g-2`
- `EI01g-3`

Keep related files together in that dataset folder, such as postprocess Excel/CSV files, Origin CSV files, `Origin_plot_data.xlsx`, and Summary files.

## Abaqus ODB Extraction

Use `scripts/abaqus_field_output_to_tables.py` as the Abaqus-kernel script. It is meant to be executed inside Abaqus/CAE, for example through `mcp__abaqus_mcp_server.execute_script`.

Before execution, set these constants at the top of the script or patch a task copy:

- `ODB_NAME_CONTAINS`: target ODB name fragment, for example `EI01g-1`.
- `OUT_DIR`: output directory. Prefer an ASCII path when running inside Abaqus Python 2.
- `TOP_SET_FALLBACK`: default `TATONG-SHANG`.
- `BASE_SET_CANDIDATES`: default `BASE_RP`, `RP-1`, then `ASSEMBLY_DIBU_REFERENCE_POINT`.
- `M_CAPACITY_KN_M`: optional overturning capacity for Origin comparison workflows.

The script prioritizes:

- Top node set: `TOP_NODE`, then fallback `TATONG-SHANG`.
- Base RP node set: `BASE_RP`, then `RP-1`, then `ASSEMBLY_DIBU_REFERENCE_POINT`.
- Step: `EQ`.

Generated time-history columns use Chinese headers and N-m-kg-s units:

- `时间_s`
- `塔顶位移_m`
- `底部位移_m`
- `塔顶相对位移_m`
- `塔顶加速度_m_s2`
- `底部加速度_m_s2`
- `底部剪力_RF1_N`
- `底部剪力_RF1_kN`
- `底部弯矩_RM1_N_m`
- `底部倾覆弯矩_RM2_N_m`
- `底部弯矩_RM3_N_m`
- `底部倾覆弯矩_RM2_kN_m`
- `底部倾覆弯矩_M_ot_N_m`
- `底部倾覆弯矩_M_ot_kN_m`
- `合成倾覆弯矩_N_m`
- `合成倾覆弯矩_kN_m`

## Origin Export

Use `scripts/origin_export_from_postprocess_excel.py` for normal Python environments with `openpyxl`.

Inputs:

- Default: `postprocess_results.xlsx`
- Required sheet: `Time_History`
- Header names must match the Chinese columns above. The script can derive kN shear/moment columns from N columns when needed.

Outputs in `Origin_export/`:

- `Fig1_ElCentro_input_acceleration.csv`
- `Fig2_top_relative_displacement.csv`
- `Fig3_top_base_acceleration_comparison.csv`
- `Fig4_base_shear_time_history.csv`
- `Fig5_base_overturning_moment.csv`
- `Fig6_overturning_moment_vs_capacity.csv`
- `Summary.csv`
- `Origin_plot_data.xlsx`

All CSV files must be written with `utf-8-sig` encoding so Origin opens Chinese headers correctly.

## Validation Checklist

After running either workflow, report:

- Input ODB or Excel path.
- Sheet or Step used.
- Node set mapping used.
- Output file paths.
- Row/frame count.
- Peak values and times.
- Whether `M_capacity_kN_m` was set; if zero, report `未设置抗倾覆能力`.

If Python is unavailable in the user environment, still provide the script and use available local tools to generate equivalent output only when that does not modify the source Excel or Abaqus model.
