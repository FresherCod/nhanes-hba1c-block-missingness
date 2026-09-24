# Protocol v0.2 — CHƯA KHÓA

Tên làm việc: *Huấn luyện chịu thiếu theo khối cho mô hình sàng lọc HbA1c đạt ngưỡng từ biến không xét nghiệm: kiểm định theo thời gian trên NHANES 2017–2020 → 2021–2023*

- Phiên bản: 0.2 (2026-09-24). v0.1 = các thiết kế rải rác trong [TĐ]/[KT]/[LR].
- Mọi thay đổi so với v0.1 được ghi trong `decision_log.md` (D-01 đến D-21).
- Nhãn `[CHƯA CHỐT]` = thiếu nguồn, thiếu dữ liệu hoặc cần người duyệt quyết định. `[AUDIT]` = sẽ được xác nhận bằng `notebooks/01_data_audit`.
- **Protocol chỉ khóa khi các cổng G1–G5 (mục 12) đã đạt và Vincent đã ký các dòng trong decision log.**

---

## 1. Câu hỏi chính (một câu)

Ở người trưởng thành NHANES không tự báo cáo chẩn đoán ĐTĐ, khi phát triển mô hình trên 2017–03/2020 và đánh giá trên 2021–2023, **huấn luyện có che khối biến (block-masking augmentation)** có cho dự đoán HbA1c ≥ 6,5% tốt hơn **cùng mô hình không che** hay không, đo bằng Brier score có trọng số khảo sát, khi các khối thông tin bị thiếu lúc sử dụng?

## 2. So sánh chính (một so sánh)

| | |
|---|---|
| Can thiệp | LightGBM + block-masking augmentation (M-AUG) |
| Đối chứng | LightGBM cùng siêu tham số, cùng biến, không augmentation, xử lý NaN tự nhiên (M-BASE) |
| Estimand chính | Δ = Brierʷ(M-AUG) − Brierʷ(M-BASE) trên L, **lấy trung bình không trọng số qua các kịch bản thiếu S1–S5** (mục 6) |
| Điều kiện phụ bắt buộc | Ở S0 (đủ dữ liệu), M-AUG không được kém hơn M-BASE quá biên δ. δ = `[CHƯA CHỐT]`, đề nghị 0,002 Brier; phải chốt trước khi chạy L |
| Diễn giải | Δ < 0 và CI 95% không chứa 0 → M-AUG tốt hơn. CI chứa 0 → không có bằng chứng khác biệt; báo cáo đúng như vậy |

Mọi so sánh khác là **phụ/thăm dò**: ADA score, LR, mô hình con theo mẫu thiếu, huấn luyện có trọng số, hiệu chuẩn lại, từng kịch bản riêng lẻ, phân nhóm.

## 3. Cohort và nhãn

**Dữ liệu:** P = NHANES 2017–03/2020 (tệp tiền đại dịch, gồm cả người tham gia chu kỳ 2017–2018). L = NHANES 08/2021–08/2023. **Không dùng tệp chu kỳ J (2017–2018) riêng lẻ.**

**Cùng một hàm dựng cohort áp dụng cho cả P và L:**

| Bước | Tiêu chí | Nguồn biến |
|---|---|---|
| C1 | Có trong DEMO | DEMO |
| C2 | Tuổi ≥ 20 (D-18) | RIDAGEYR |
| C3 | Đã khám MEC | RIDSTATR = 2 |
| C4 | Có LBXGH | GHB |
| C5 | Trọng số nhãn > 0 | P: WTMECPRP; L: WTPH2YR (D-05) `[AUDIT]` |
| C6 | Không có thai | loại RIDEXPRG = 1 |
| C7 | Không tự báo cáo chẩn đoán ĐTĐ | loại DIQ010 ∈ {1, 7, 9} và DIQ010 thiếu `[CHƯA CHỐT]` (D-22); DIQ010 = 3 giữ lại `[CHƯA CHỐT]` (D-04) |
| C8 | Không dùng thuốc uống hạ đường huyết | loại DIQ070 = 1, nếu câu hỏi được hỏi cho người chưa chẩn đoán `[AUDIT]` |

**Loại trừ bằng domain:** khi tính chỉ số có trọng số và phương sai, giữ nguyên cấu trúc strata/PSU của toàn mẫu.

**Nhãn:**
- Nhãn chính: y = 1{LBXGH ≥ 6,5}.
- Nhãn dự phòng, kích hoạt theo cổng G2 (D-03): 1{LBXGH ≥ 5,7}.
- Tên gọi trong bài: "HbA1c đạt ngưỡng ĐTĐ ở người chưa được chẩn đoán". Một lần đo không phải là chẩn đoán (NIDDK).
- Độ nhạy nhãn ở L: ngưỡng 6,35 và 6,65 (D-06, lệch thiết bị G8/D-100 khoảng 2,3%) `[CHƯA CHỐT]`.

## 4. Biến dự báo (chỉ không xét nghiệm)

`[AUDIT]` cho mọi biến: có mặt ở cả P và L, mã thiếu, phân phối.

| Khối | Biến | Mã NHANES (P / L) | Dẫn xuất | Có thể che? |
|---|---|---|---|---|
| Lõi | Tuổi, giới, chủng tộc | RIDAGEYR, RIAGENDR, RIDRETH3 | Tuổi top-code ở 80 | Không |
| B1 Nhân trắc đo | Cân nặng, chiều cao, BMI, vòng eo | BMXWT, BMXHT, BMXBMI, BMXWAIST | WHtR = BMXWAIST / BMXHT (tính theo từng người) | Có |
| B2 Huyết áp đo | HA tâm thu, tâm trương | BPXOSY1–3, BPXODI1–3 | Trung bình các lần đo hợp lệ | Có |
| B3 Tiền sử tự báo cáo | Từng được báo THA; tiền sử gia đình ĐTĐ; ĐTĐ thai kỳ (nữ) | BPQ020; MCQ300C; RHQ162 `[CHƯA CHỐT: có ở L?]` | Nam → ĐTĐ thai kỳ = 0 | Có |
| B4 Lối sống và KT–XH | Hút thuốc; ngồi tĩnh tại; thể lực giải trí; PIR; học vấn | SMQ020, SMQ040; PAD680; PAQ650/PAQ665 (P) ↔ PAD790Q/PAD810Q (L); INDFMPIR; DMDEDUC2 | Hút thuốc: không bao giờ / đã bỏ / hiện tại. Thể lực: có/không `[CHƯA CHỐT]` (D-19) | Có |

> **Cập nhật sau audit lần 1 (chờ duyệt, chưa áp dụng):**
> - MCQ300C và RHQ162 không có ở L → đề xuất B3 chỉ còn BPQ020 (D-25).
> - Biến thể lực không tương đương giữa P và L → đề xuất bỏ LTPA_ANY (D-24).
> - ADA đổi thành bản rút gọn (D-26).
>
> Bảng trên giữ nguyên cho đến khi Vincent duyệt.

**Cấm dùng làm biến dự báo (D-17):**
- Mọi LBX*/LBD* (xét nghiệm).
- DIQ*: chỉ dùng để xác định cohort.
- BPQ080 (từng được báo cholesterol cao), BPQ090D, BPQ100D (thuốc hạ mỡ).
- Thuốc hạ áp.
- DIQ160 (tiền ĐTĐ), DIQ180 (thử máu 3 năm qua).
- Cả nhóm RXQ*.
- Rượu (ALQ): **không dùng** ở v0.2 vì bảng hỏi đổi qua các chu kỳ; có thể thêm lại nếu audit cho thấy hài hòa được.

## 5. Chia dữ liệu

- **Phát triển:** toàn bộ cohort P.
- **Chọn siêu tham số** bằng GroupKFold 5 fold trên P, nhóm = (SDMVSTRA, SDMVPSU) (D-13).
- **Dự đoán OOF trên P** dùng cho hiệu chuẩn lại và chọn ngưỡng.
- **Kiểm định theo thời gian:** L chỉ được chạm tới **một lần**, sau khi code, siêu tham số, ngưỡng và bộ hiệu chuẩn lại đã đóng băng (có commit hash và mã băm file cấu hình).
- **Tuning (D-21):** trước khi qua cổng chỉ dùng tham số mặc định cố định. Sau cổng: lưới ≤ 12 cấu hình (num_leaves {7, 15, 31} × min_child_samples {20, 50} × learning_rate {0,05, 0,1}), 300 vòng, early stopping trong fold. **Cùng lưới cho M-AUG và M-BASE.**
- **Seed:** 5 seed cố định (0–4). Báo cáo trung bình và phạm vi qua seed.

## 6. Kịch bản thiếu

**Khi đánh giá (tất định):** mỗi kịch bản áp dụng cho toàn bộ tập L.

| ID | Khối bị thiếu | Tình huống triển khai |
|---|---|---|
| S0 | Không | Đủ dữ liệu |
| S1 | B1 | Không có cân và thước |
| S2 | B2 | Không có máy đo huyết áp |
| S3 | B3 | Không trả lời phần tiền sử |
| S4 | B4 | Không trả lời phần lối sống và thu nhập |
| S5 | B1 + B2 | Chỉ có bảng hỏi |
| S6 (phụ, không dùng khi huấn luyện) | B3 + B4 | Kiểm tra mẫu thiếu chưa thấy khi huấn luyện |
| S7 (phụ) | B4 thiếu với xác suất phụ thuộc học vấn/tuổi (MAR) | `[CHƯA CHỐT]` công thức xác suất |

- **Thiếu tự nhiên:** giá trị thiếu sẵn có trong NHANES được giữ nguyên ở mọi kịch bản và được báo cáo riêng `[AUDIT]`.
- **Augmentation khi huấn luyện (M-AUG):**
  - Chỉ làm **bên trong fold train, sau khi chia**.
  - Mỗi dòng train được thêm k = 1 bản sao, gán ngẫu nhiên một mẫu thiếu thuộc {S1…S5}.
  - Bản sao mang cùng mã nhóm với dòng gốc.
  - Có biến chỉ báo "khối bị thiếu" cho B1–B4 `[CHƯA CHỐT: k và có dùng biến chỉ báo hay không]`.
- **Công bằng giữa hai nhánh:** M-BASE nhận cùng biến chỉ báo khối (bằng 0 khi huấn luyện). Mô hình con theo mẫu thiếu là đối chứng mạnh, dùng làm phân tích phụ.

## 7. Hiệu chuẩn

- **Kết quả chính:** dự đoán thô của từng mô hình, không hiệu chuẩn lại.
- **Hiệu chuẩn lại (phụ, D-12):** hồi quy logistic của y theo logit(p̂), fit trên OOF của P, áp cho L. Không dùng isotonic.
- **Cập nhật trên L (phụ):** chia đôi L theo PSU trong strata; fit trên một nửa, đánh giá trên nửa còn lại.
- **Báo cáo theo từng kịch bản** S0–S5, có trọng số:
  - calibration-in-the-large (intercept khi slope cố định = 1);
  - calibration slope;
  - đường cong hiệu chuẩn làm trơn (loess có trọng số);
  - ICI;
  - O/E có trọng số.
- **Diễn giải lệch intercept ở L:** so với thay đổi tỷ lệ nhãn có trọng số giữa P và L, để tách thay đổi tỷ lệ hiện mắc thực sự khỏi lỗi của mô hình.

## 8. Chỉ số

| Loại | Chỉ số (đều có trọng số khảo sát trên L) |
|---|---|
| Chính | Brier score |
| Phân biệt | AUROC, AUPRC |
| Hiệu chuẩn | Intercept, slope, ICI, O/E |
| Tại ngưỡng | Độ nhạy, độ đặc hiệu, PPV, NPV, tỷ lệ phải chuyển xét nghiệm HbA1c. Ngưỡng chọn trên OOF của P tại độ nhạy 80% `[CHƯA CHỐT]` (D-15) |
| Lợi ích | Net benefit trên khoảng ngưỡng 1–10% `[CHƯA CHỐT: khoảng ngưỡng cần lý do]` |
| Mô tả | Tỷ lệ nhãn có trọng số ở P và L; so sánh phân phối biến P → L |

## 9. Độ bất định

- **Tập L:** tạo replicate weights JK2. Với mỗi stratum h, một replicate gán PSU thứ nhất trọng số ×2 và PSU còn lại ×0. SE = √Σ(θ_r − θ̂)². CI 95% dùng phân vị t với df = số strata − 0 (≈ 15) `[AUDIT: số strata/PSU]`.
- **Hiệu (Δ):** tính **ghép cặp** trong từng replicate.
- **Bất định do huấn luyện:** mô hình cố định sau huấn luyện trên P, nên CI chỉ phản ánh bất định lấy mẫu của L. Biến thiên do seed báo cáo riêng (5 seed). Đây là giới hạn phải nêu trong bài.
- **Nhiều phép thử:** chỉ estimand chính có diễn giải xác nhận. Mọi phân tích khác báo cáo ước lượng + CI, gắn nhãn thăm dò, không dùng p-value để kết luận.

## 10. Trọng số khảo sát

| Mục đích | P | L |
|---|---|---|
| Nhãn HbA1c / đánh giá | WTMECPRP `[AUDIT]` | WTPH2YR `[AUDIT]` |
| Thiết kế | SDMVSTRA, SDMVPSU | SDMVSTRA, SDMVPSU |

- Huấn luyện chính **không trọng số**; huấn luyện có trọng số là phân tích phụ (D-08).
- Không trim trọng số ở phân tích chính. Báo cáo hệ số biến thiên và tỷ số max/trung vị của trọng số `[AUDIT]`.
- Không gộp P và L thành một mẫu, nên không cần hệ số quy đổi.

## 11. Kiểm tra rò rỉ (tự động hóa trong code, fail = dừng)

| ID | Kiểm tra |
|---|---|
| K1 | Không có SEQN chung giữa P và L; không nạp tệp chu kỳ J |
| K2 | Danh sách biến ∩ danh sách cấm (mục 4) = ∅; không biến nào có tiền tố LBX/LBD/DIQ/RXQ |
| K3 | Augmentation chạy sau khi chia fold; mọi bản sao có cùng nhóm với dòng gốc; không nhóm nào vừa ở train vừa ở validation |
| K4 | Imputer và scaler nằm trong pipeline, fit chỉ trên chỉ số train |
| K5 | Hiệu chuẩn lại và ngưỡng chỉ fit trên OOF của P. File dự đoán L được tạo **một lần** và ghi mã băm vào log |
| K6 | Hoán vị nhãn trên P: AUROC OOF phải ≈ 0,5 (ngoài khoảng 0,45–0,55 → điều tra) |
| K7 | Không biến đơn lẻ nào có AUROC > 0,85 trên P; nếu có → điều tra định nghĩa biến |
| K8 | Cohort P và L được dựng bằng cùng một hàm và cùng tham số |

## 12. Cổng, tiêu chí dừng và đổi hướng

| Cổng | Điều kiện đạt | Nếu không đạt |
|---|---|---|
| G1 Toàn vẹn dữ liệu | Tải đủ các tệp; SEQN duy nhất trong mỗi tệp; biến trọng số và thiết kế có mặt | Sửa trước khi làm bất cứ việc gì khác |
| G2 Số sự kiện | L có ≥ 100 sự kiện (không trọng số) cho nhãn 6,5% | Chuyển nhãn chính sang 5,7% theo D-03. Nếu cả 5,7% cũng <100 → dừng, xem lại thiết kế |
| G3 Hài hòa biến | Mọi biến lõi, B1, B2 có ở cả P và L cùng định nghĩa; mỗi khối B3, B4 còn ≥ 1 biến hài hòa được | Bỏ biến không hài hòa được (ghi log); nếu cả khối mất → bỏ kịch bản tương ứng |
| G4 Tính mới | Đã đọc tay [NG-BBD] và các bài trong T-3, có log tìm kiếm T-2; không bài nào đã làm đồng thời: chưa chẩn đoán + kiểm định theo thời gian + thiếu theo khối | Nếu đã có: đổi khung thành nghiên cứu lặp lại/kiểm định độc lập, hoặc chọn câu hỏi khác; ghi log |
| G5 Ký duyệt | Các dòng `CHƯA CHỐT` quan trọng (D-04, D-15, δ, D-19) đã có quyết định | Không chạy L |

**Sau khi chạy (định trước, không đổi sau khi thấy kết quả):**
- Nếu M-BASE gần như không giảm hiệu năng khi thiếu khối (Brierʷ(S1…S5) − Brierʷ(S0) < δ), câu hỏi augmentation không còn quan trọng thực tiễn → báo cáo là phát hiện âm tính, **không thêm phương pháp mới** để "cứu" kết quả.
- Không thêm mô hình, biến hay kịch bản ngoài protocol nếu chưa có dòng mới trong decision log. Mọi thứ thêm sau khi chạy L phải gắn nhãn hậu kiểm (post hoc).

## 13. Giới hạn suy rộng (viết sẵn)

- Chỉ đại diện dân số Hoa Kỳ không sống trong cơ sở tập trung.
- Nhãn dựa trên một lần đo HbA1c; HbA1c có thể sai ở người có biến thể hemoglobin, thiếu máu thiếu sắt hoặc bệnh thận (NIDDK).
- L không oversample theo chủng tộc/thu nhập, nên ước lượng phân nhóm kém chính xác.
- Thiếu dữ liệu mô phỏng không đồng nghĩa với cơ chế thiếu thực tế.
- Không suy ra được cho quần thể Việt Nam.
