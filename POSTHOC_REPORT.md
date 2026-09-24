# Báo cáo hậu kiểm (post hoc) — sau protocol v0.4

> **Nhãn bắt buộc khi viết bài:** mọi kết quả trong file này là **hậu kiểm**. Chúng được thực hiện sau khi đã biết kết quả chính và không có trong protocol đã khóa. Chúng dùng để tạo giả thuyết và gợi ý triển khai, không để xác nhận.

- **Code:** `notebooks/05_posthoc.py`.
- **Kết quả:** `posthoc_out/posthoc_results.json`, `posthoc_out/PH2_dca.csv`.
- **Hình:** `figures/fig3_*`, `figures/fig4_*`.
- **Nguyên tắc:** file đã khóa không bị sửa. Các mô hình mới trong PH-1b dùng đúng quy trình tuning đã định trước (lưới C, log loss có trọng số, GroupKFold theo PSU, chỉ trên P). CI dùng JK2 trên L (15 strata).

## PH-1. Khối nhân trắc quyết định hiệu năng (HbA1c ≥6,5%)

### PH-1a. Tách mức mất Brier skill theo khối (dự đoán đã lưu, không huấn luyện lại)

| Khối bị thiếu | Mất skill — M-AUG [CI 95%] | Mất skill — M-PS [CI 95%] |
|---|---|---|
| B1 nhân trắc | **0,024 [0,006; 0,043]** | **0,024 [0,007; 0,042]** |
| B2 huyết áp | 0,001 [−0,004; 0,006] | 0,002 [−0,003; 0,006] |
| B3 tiền sử | −0,003 [−0,008; 0,002] | −0,003 [−0,008; 0,001] |
| B4 lối sống/KT–XH | 0,001 [−0,005; 0,007] | −0,002 [−0,007; 0,003] |
| B1 − trung bình (B2, B3, B4) | 0,024 [0,006; 0,043] | 0,025 [0,007; 0,044] |
| Tỷ lệ skill ở S0 do B1 đóng góp | **68% [45%; 91%]** | **69% [42%; 96%]** |

**Kết luận:** chỉ riêng khối nhân trắc đã chiếm khoảng 2/3 khả năng dự báo. Thiếu huyết áp, tiền sử hay lối sống không làm mất skill đo được.

### PH-1b. Thiếu một phần nhân trắc — mô hình con LR mới, huấn luyện trên P, đánh giá trên L

| Nguồn thông tin nhân trắc | Brier skill [CI 95%] | AUROC [CI 95%] | Phần skill thu hồi so với "không có nhân trắc" |
|---|---|---|---|
| Đủ: cân, thước đo chiều cao, thước dây (S0) | 0,035 [0,014; 0,056] | 0,811 [0,764; 0,859] | 100% (mốc) |
| **Không có thước dây** (cân + chiều cao đo) | 0,033 [0,014; 0,053] | 0,806 [0,763; 0,849] | **93% [66%; 120%]** |
| **Cân nặng/chiều cao tự khai**, không đo gì | 0,033 [0,009; 0,056] | 0,795 [0,746; 0,845] | **91% [61%; 121%]** |
| Không có nhân trắc (S1) | 0,011 [0,000; 0,022] | 0,729 [0,678; 0,781] | 0% (mốc) |

- Chênh lệch so với đủ dữ liệu:
  - Không có thước dây: 0,002 [−0,005; 0,008].
  - Tự khai: 0,002 [−0,004; 0,008].
- Tương quan giữa BMI đo và BMI tự khai ở L: r = 0,96.
- Tỷ lệ thiếu dữ liệu tự khai ở L: khoảng 1%.

**Hàm ý triển khai:** một công cụ **chỉ gồm bảng hỏi**, có hỏi cân nặng và chiều cao tự khai, giữ được khoảng 90% hiệu năng của bản đo đầy đủ. Vì vậy công cụ sàng lọc trực tuyến hoặc tự đánh giá tại nhà là khả thi.

**Lưu ý:** cả hai mô hình mới chọn C = 1,0 (biên trên của lưới), như M-PS (D-45). Tự khai trong NHANES được thu trong phỏng vấn có người hỏi; tự khai ngoài thực tế có thể sai lệch nhiều hơn.

## PH-2. Nhãn HbA1c ≥5,7% (tiền ĐTĐ hoặc ĐTĐ chưa chẩn đoán)

- L có 1.474 sự kiện; tỷ lệ có trọng số 26,7%.
- Ngưỡng mô hình chọn trên OOF của P tại độ nhạy 80%: M-AUG 0,244; M-PS 0,240.
- Điểm Bang dùng điểm cắt **≥4**, là điểm cắt chính Bang 2009 đề xuất cho nhãn gộp này (không chọn lại).

| Chỉ số trên L (S0) | M-AUG | M-PS | Điểm Bang ≥4 |
|---|---|---|---|
| Brier skill | 0,177 [0,149; 0,205] | 0,178 [0,150; 0,205] | — |
| AUROC | **0,775 [0,753; 0,796]** | 0,775 [0,754; 0,796] | 0,727 [0,700; 0,754] |
| Độ nhạy | 0,81 [0,78; 0,84] | 0,81 [0,79; 0,84] | 0,76 [0,72; 0,80] |
| Độ đặc hiệu | 0,60 [0,57; 0,63] | 0,60 [0,58; 0,63] | 0,60 [0,57; 0,63] |
| PPV | 0,43 [0,39; 0,46] | 0,43 [0,40; 0,46] | 0,41 [0,38; 0,44] |
| Tỷ lệ chuyển xét nghiệm | 51% | 51% | 49% |

**So sánh ghép cặp với điểm Bang:**
- Cùng tỷ lệ chuyển xét nghiệm như Bang ≥4 (49%): mô hình có độ nhạy **cao hơn 4,6 điểm % [2,1; 7,1]**.
- Net benefit, M-AUG − Bang ≥4:

| Ngưỡng | Chênh lệch [CI 95%] |
|---|---|
| 10% | +0,030 [0,017; 0,043] |
| 20% | +0,018 [0,008; 0,028] |
| 30% | +0,022 [0,012; 0,032] |
| 40% | +0,046 [0,032; 0,061] |

- Với ngưỡng 20–50%, mô hình hơn cả chiến lược "xét nghiệm tất cả" (Hình 4).

**Khi thiếu nhân trắc (S1):**
- M-BASE mất 0,064 [0,044; 0,085] skill.
- M-AUG hơn M-BASE 0,025 [0,008; 0,043].
- M-AUG vẫn có skill 0,139 và AUROC 0,748, **vẫn hơn điểm Bang có đủ thông tin** (0,727).

## Cách viết trong bài (đề xuất)
- Phần Kết quả: tách mục "Phân tích hậu kiểm". Mở đầu bằng câu: "Các phân tích sau không được định trước trong protocol và mang tính khám phá."
- Phần Bàn luận:
  - PH-1 là thông điệp thực tiễn chính: nhân trắc > mọi khối khác; cân nặng và chiều cao tự khai là đủ.
  - PH-2 cho thấy tín hiệu mạnh hơn nhiều ở nhãn tiền ĐTĐ + ĐTĐ, và lợi thế nhất quán so với điểm Bang.
