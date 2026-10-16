# Addendum hậu khóa, đợt 4 (post hoc, khám phá): mở rộng lưới C trong dữ liệu phát triển

Trạng thái: **ĐÃ CHẠY 2026-10-14 (chủ dự án tự chạy, 145 giây)**. Kế hoạch ở mục 1-6 được viết trước khi chạy (Claude Sonnet 5.5, theo lựa chọn của chủ dự án: "Có, em viết script và addendum") và không đổi. Mục 7 ghi kết quả, Claude đọc từ `posthoc_out/posthoc4_C_grid_*.csv/json`. Không sửa file đã khóa (`LOCK_protocol_v0.4.json`), không đọc cohort L.

## 1. Nguồn gốc câu hỏi
Phản biện nội bộ của chủ dự án (không phải của PLOS), điểm m1: ở các mô hình đã khóa, lưới C = {0,03; 0,1; 0,3; 1} bị chạm biên trên. Số liệu đã lưu (`final_out/tuning_log_P.csv`, kết cục chính, 9 mô hình logistic): 6 mô hình (submodel S1–S6) chọn C = 1, M-AUG và M-BASE chọn C = 0,3; chênh log loss có trọng số giữa C = 0,3 và C = 1 của sáu mô hình đó nhỏ hơn 0,0005. Chưa biết điều gì xảy ra với C > 1.

## 2. Câu hỏi
Trong dữ liệu phát triển (cohort P, kết cục chính HbA1c ≥6,5%), nếu mở rộng lưới C thêm 3, 10, 30, 100 thì: (a) mô hình nào đổi C được chọn; (b) log loss có trọng số tốt lên bao nhiêu so với lưới đã khóa; (c) có mô hình nào vẫn chạm biên mới (C = 100).

## 3. Phương pháp (ghi trước khi chạy)
- Script: `notebooks/10c_posthoc_C_grid_extension.py`. Gọi nguyên hàm `fp.tune()` của bản khóa (cùng GroupKFold(5) theo PSU, cùng log loss có trọng số, cùng các bộ augmentation seed), chỉ đặt `fp.C_GRID = [0,03; 0,1; 0,3; 1; 3; 10; 30; 100]` trong bộ nhớ. Không sửa `src/final_pipeline.py`.
- Chỉ mô hình logistic (LR), kết cục chính 6,5%. Không chạy LightGBM, không chạy kết cục 5,7%.
- Cổng kiểm: log loss ở bốn giá trị C đã khóa phải trùng `final_out/tuning_log_P.csv` (sai lệch tối đa < 1e-8). Không đạt thì script dừng và không ghi kết quả. `LOCK OK` phải in ra trước.
- Đầu ra: `posthoc_out/posthoc4_C_grid_loss.csv` (mọi C, mọi mô hình), `posthoc4_C_grid_summary.csv`, `posthoc4_C_grid.json`.

## 4. Quy tắc báo cáo (cố định trước khi thấy kết quả)
- Báo cáo mọi mô hình: C chọn ở lưới khóa và lưới mở rộng, log loss tại hai lựa chọn, mức cải thiện, số mô hình chạm biên cũ và biên mới.
- Nhãn "post hoc, khám phá, chỉ dữ liệu phát triển". Không dùng để đổi mô hình đã khóa hay các bảng đã báo.
- Nếu có mô hình chọn C > 1: ghi con số vào Limitations và vào S1 File (bảng mới); việc chấm lại M-AUG so với M-PS trên cohort L với C mở rộng là một quyết định riêng của chủ dự án, cần addendum tiếp theo, KHÔNG làm trong đợt này.
- Nếu không mô hình nào đổi lựa chọn: ghi một câu trong Limitations.

## 5. Giới hạn
Chỉ nói về điều chỉnh siêu tham số trong dữ liệu phát triển; không nói gì về kết quả trên cohort L. Log loss trong dữ liệu phát triển là ước lượng OOF, có sai số lấy mẫu.

## 6. Lệnh chạy (chủ dự án tự chạy, terminal tại `D:\NCKH\nhanes_hba1c_block_missingness`)
```
python notebooks/10c_posthoc_C_grid_extension.py
```
Sau khi chạy: dán đầu ra cho Claude để đọc, ghi phần "Kết quả" bên dưới và cập nhật Limitations, S1 File.

## 7. Kết quả (post hoc, khám phá, chỉ dữ liệu phát triển P; chủ dự án chạy, Claude đọc từ file)
- `LOCK OK`. P: n = 6.644, 237 biến cố. Cổng tái lập: sai lệch tối đa giữa log loss tính lại ở 4 giá trị C đã khóa và `final_out/tuning_log_P.csv` là 9,7e-17 (đạt, ngưỡng 1e-8).
- 9 mô hình logistic (M-BASE, M-AUG, submodel S0 đến S6; S0 trùng M-BASE). Ở lưới đã khóa, 6 mô hình chạm biên trên (submodel S1 đến S6 chọn C = 1). Sau khi mở rộng lưới đến C = 100: 8/9 mô hình giữ nguyên C được chọn; chỉ submodel S5 đổi từ C = 1 sang C = 3, log loss có trọng số thấp hơn 0,000019. Không mô hình nào chọn biên mới (C = 100). Mức cải thiện lớn nhất trong 9 mô hình: 0,000019.
- Bảng đầy đủ: S1 File, Table S10 (`manuscript_v3`); nguồn `posthoc_out/posthoc4_C_grid_summary.csv`.
- Đã làm theo quy tắc mục 4: ghi vào Limitations (1 câu), danh sách phân tích post hoc ở Methods 4.9 và S1 File. Không đổi mô hình đã khóa hay bảng đã báo. Cohort L không được chấm lại với lưới mở rộng; đó vẫn là quyết định riêng của chủ dự án (cần addendum khác).
- Giới hạn: log loss OOF trong dữ liệu phát triển có sai số lấy mẫu; kết quả không nói gì về độ chính xác trên cohort L.
