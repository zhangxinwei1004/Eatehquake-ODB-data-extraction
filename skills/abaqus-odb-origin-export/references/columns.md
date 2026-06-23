# Column Reference

Use N-m-kg-s units.

## Time History Columns

| Column | Meaning |
| --- | --- |
| 时间_s | Time in seconds |
| 塔顶位移_m | Average top U1 displacement |
| 底部位移_m | Base RP U1 displacement |
| 塔顶相对位移_m | `塔顶位移_m - 底部位移_m` |
| 塔顶加速度_m_s2 | Average top A1 acceleration |
| 底部加速度_m_s2 | Base RP A1 acceleration |
| 底部剪力_RF1_N | Base RP RF1 |
| 底部剪力_RF1_kN | `底部剪力_RF1_N / 1000` |
| 底部弯矩_RM1_N_m | Base RP RM1 |
| 底部倾覆弯矩_RM2_N_m | Base RP RM2 |
| 底部弯矩_RM3_N_m | Base RP RM3 |
| 底部倾覆弯矩_RM2_kN_m | `底部倾覆弯矩_RM2_N_m / 1000` |
| 底部倾覆弯矩_M_ot_N_m | Same as RM2 overturning moment |
| 底部倾覆弯矩_M_ot_kN_m | `底部倾覆弯矩_M_ot_N_m / 1000` |
| 合成倾覆弯矩_N_m | `sqrt(RM1^2 + RM2^2)` |
| 合成倾覆弯矩_kN_m | `合成倾覆弯矩_N_m / 1000` |

## Summary Metrics

Use maximum absolute value while preserving the signed value at the peak time.

- 最大输入加速度
- 最大塔顶相对位移
- 最大塔顶加速度
- 最大底部剪力
- 最大底部倾覆弯矩
- 最大合成倾覆弯矩
- 塔顶加速度放大系数_eta_a
- 抗倾覆安全系数_K
