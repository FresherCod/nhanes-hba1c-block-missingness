# Addendum hậu kiểm đợt 3 (kế hoạch ghi TRƯỚC khi chạy) — 2026-10-14

Trạng thái: **đã chạy xong (2026-10-14, chủ dự án tự chạy; 10a rồi 10b, 10b mất 98 giây).** Kế hoạch bên dưới được ghi trước khi chạy và không đổi. Kết quả ở cuối file. Ghi bởi Claude Sonnet 5.5 theo lựa chọn của chủ dự án ("mức 2").

## Lý do
PLOS Digital Health từ chối bài (2026-10-13) với hai nhận xét của biên tập viên: (1) trong 5 kịch bản chính, 3 kịch bản bỏ khối ít thông tin, 2 kịch bản đều bỏ nhân trắc, nên kết quả tương đương trung bình nói ít về các kiểu thiếu khác nhau; (2) lợi thế triển khai/bảo trì chưa được đánh giá trực tiếp. Hai phân tích dưới đây nhằm trả lời phần (1) bằng số liệu, phần (2) chỉ ở mức đếm số mô hình và kiểm tra trên đủ các kiểu thiếu.

## Tư cách của phân tích
- **Hậu kiểm (post hoc), thăm dò.** Không thuộc protocol v0.4, không đổi kết quả chính đã khóa (Δ = −0,0006 [−0,0023; 0,0012]) và không thay quy tắc định trước.
- L đã được dùng cho phân tích xác nhận và hai đợt hậu kiểm trước; thêm một lượt nữa làm tăng độ linh hoạt phân tích. Bài phải nói điều này.
- File khóa không được sửa. Mỗi script kiểm `verify_lock` ở đầu; lock lệch thì dừng.
- Biên tương đương ±0,005 chỉ dùng để so sánh với bài chính, không phải quy tắc quyết định mới.

## Điều Claude đã thấy TRƯỚC khi viết kế hoạch (để không giả vờ mù)
- Phần 3A: Claude đã đọc `final_out/L_table_LR_label57.csv` (kết quả định trước, nhãn ≥5,7). Skill M-AUG: S0 0,177; S1 0,139; S2 0,178; S3 0,178; S4 0,167; S5 0,139; S6 0,168. Nghĩa là nhân trắc áp đảo; lối sống/KT-XH (B4) mất khoảng 0,010; B2 và B3 gần như không mất. Phần 3A vì thế không phải thử nghiệm mù; nó bổ sung CI ghép cặp theo từng kịch bản và gom nhóm.
- Phần 3B: chưa thấy số nào.

## Phần 3A — nhãn HbA1c ≥5,7% theo từng kịch bản
Script: `notebooks/10a_posthoc_label57_by_scenario.py`. Chỉ dùng `LR57-AUG/PS/BASE` đã khóa; không huấn luyện lại.
Đầu ra: `posthoc_out/posthoc3a_label57_by_scenario.csv/.json`.
- Brier skill từng kịch bản S0–S6 cho 3 chiến lược; mức mất skill của M-AUG so với S0 (S1…S6).
- M-AUG − M-PS và M-AUG − M-BASE theo từng kịch bản, và trung bình theo nhóm: S1–S5 (đối chiếu Bảng 4 của bản thảo: −0,0015 [−0,0032; 0,0001]), nhóm có B1 (S1, S5), nhóm không B1 (S2, S3, S4). Cách gom nhóm theo khối nhân trắc là hậu kiểm.
- CI: JK2 ghép cặp, t với 15 bậc tự do như bài chính.
- Kiểm tái lập tự động: skill tính lại phải khớp `L_table_LR_label57.csv` (sai lệch < 1e-9), nếu không thì dừng.

## Phần 3B — đủ 15 kiểu thiếu khối (nhãn ≥6,5)
Script: `notebooks/10b_posthoc_all_patterns.py`. Đầu ra: `posthoc_out/posthoc3b_all_patterns.csv/.json`.
- Tập kiểu thiếu: mọi tổ hợp khác rỗng của B1–B4 (15) cộng S0.
- **M-AUG:** mô hình đã khóa (augmentation chỉ thấy S1–S5; 10 kiểu còn lại chưa thấy khi huấn luyện).
- **M-AUG15 (mới):** cùng quy trình M-AUG (logistic spline, 5 seed trung bình, 4 chỉ báo khối) nhưng augmentation bốc đều trong cả 15 kiểu. C chọn bằng OOF GroupKFold(5) theo PSU, log loss có trọng số trung bình trên S0 + 15 kiểu, lưới C của protocol.
- **M-PS16 (mới):** mô hình con "reduced-feature" cho mỗi kiểu (16 mô hình), tuning C đúng quy trình bản khóa.
- **M-BASE:** mô hình đã khóa.
- Mọi mô hình mới huấn luyện CHỈ trên P. L chỉ để chấm điểm.
- Kiểm tái lập: skill M-AUG khóa ở S1–S5 phải khớp bảng khóa (sai lệch < 1e-9, nếu không thì dừng); M-PS16 ở S0–S6 phải trùng mô hình con đã khóa (cảnh báo nếu lệch > 1e-6, ghi vào nhật ký trước khi diễn giải).
- Báo cáo: skill từng kiểu cho 4 mô hình; M-AUG − M-PS16 và M-AUG15 − M-PS16 từng kiểu kèm CI; trung bình theo nhóm (15 kiểu; có B1/không B1; kiểu đã thấy/chưa thấy khi huấn luyện M-AUG); số mô hình (M-AUG 5, M-AUG15 5, M-PS16 16).

## Quy tắc báo cáo (định trước)
1. Báo cáo cả 16 hàng của 3B và cả 7 kịch bản của 3A, kể cả kết quả bất lợi cho M-AUG.
2. Nếu M-AUG khóa kém rõ ở kiểu chưa thấy hoặc M-AUG15 khác M-AUG, nói thẳng trong bài; không đổi tên hay chọn lại mô hình.
3. Không dùng L để chọn siêu tham số, ngưỡng hay mô hình.
4. Bản thảo: thêm bảng vào S1 File (S8 cho 3A, S9 cho 3B) và vài câu ở mục 2.6, ghi "post hoc". Kết luận chính trong tóm tắt chỉ đổi nếu kết quả buộc phải đổi.

## Lệnh chạy (từ thư mục dự án)
```
python notebooks/10a_posthoc_label57_by_scenario.py
python notebooks/10b_posthoc_all_patterns.py
```

## Kết quả (chạy 2026-10-14; số liệu: `posthoc_out/posthoc3a_*` và `posthoc3b_*`, bảng đầy đủ ở S1 File v2, Bảng S8 và S9)

Kiểm tái lập: 10a khớp `L_table_LR_label57.csv` tuyệt đối (sai lệch 0); 10b khớp M-AUG khóa (6,8e-17) và M-PS16 trùng M-PS khóa ở S0-S6 (9,2e-17). LOCK OK ở cả hai script.

### 3A — nhãn >=5,7% (1.474 sự kiện), M-AUG khóa
- Mất skill của M-AUG so với S0 (0,177): thiếu nhân trắc 0,0384 [0,0278; 0,0489]; thiếu lối sống/KT-XH (S4) 0,0097 [0,0037; 0,0157]; S6 0,0086 [0,0020; 0,0151]; thiếu huyết áp -0,0010 và tiền sử -0,0009 (CI chứa 0). Với nhãn này có HAI khối có thông tin: B1 và B4.
- M-AUG - M-PS: S1 -0,0015 [-0,0071; 0,0040]; S4 -0,0041 [-0,0066; -0,0016]; S5 -0,0026 [-0,0071; 0,0019]; S6 -0,0030 [-0,0056; -0,0004]; S2 +0,0003; S3 +0,0002. Trong cả 4 kịch bản có khối có thông tin, không chứng minh được tương đương trong +/-0,005; ở S4 và S6 mô hình con tốt hơn một chút nhưng có ý nghĩa thống kê.
- Trung bình S1-S5: -0,0015 [-0,0032; 0,0001] (khớp Bảng 4). Nhóm có B1 (S1,S5): -0,0021 [-0,0069; 0,0028]; nhóm không B1 (S2-S4): -0,0012 [-0,0025; 0,0001].
- M-AUG - M-BASE: nhóm có B1 +0,0272 [0,0092; 0,0452]; nhóm không B1 +0,0002 [-0,0034; 0,0038].

### 3B — đủ 15 kiểu thiếu (nhãn >=6,5; 128 sự kiện)
- M-AUG khóa - M-PS16, trung bình 15 kiểu: -0,0008 [-0,0024; 0,0008]; 8 kiểu có B1: -0,0009 [-0,0031; 0,0012]; 7 kiểu không B1: -0,0007 [-0,0027; 0,0014]; 5 kiểu đã thấy (S1-S5): -0,0006 [-0,0023; 0,0012] (đúng bằng kết quả chính); 10 kiểu chưa thấy: -0,0009 [-0,0027; 0,0009].
- Từng kiểu: CI trong +/-0,005 ở 10/15 kiểu; vượt biên ở 5 kiểu (B4; B1+B4; B3+B4; B1+B2+B3; cả 4 khối). Kiểu B1+B2+B3: mô hình con tốt hơn 0,0042 [0,0019; 0,0065] (có ý nghĩa thống kê, chưa hiệu chỉnh đa so sánh).
- M-AUG15 (huấn luyện trên cả 15 kiểu) KHÔNG tốt hơn M-AUG khóa: M-AUG15 - M-PS16 trung bình -0,0017 [-0,0027; -0,0006] (hơi kém hơn mô hình con, vẫn trong +/-0,005).
- M-PS16 - M-BASE trung bình 15 kiểu: +0,0070 [0,0044; 0,0097].
- Tuning: C chọn ở biên trên của lưới (C = 1) cho 15/16 mô hình con (S0: 0,3) và cho M-AUG15, cùng giới hạn D-45 của bản khóa.
- Số mô hình: M-AUG 5 (trung bình seed), M-AUG15 5, M-PS16 16.

### Ý nghĩa (nhận xét của Claude; chủ dự án quyết định cách dùng)
- Ủng hộ bài: tương đương trung bình giữ được khi mở rộng sang đủ 15 kiểu, kể cả 10 kiểu M-AUG chưa thấy khi huấn luyện và 8 kiểu thiếu nhân trắc; đây là phần trả lời trực tiếp nhận xét 1 của biên tập viên.
- Bất lợi, phải nói thẳng: 5/15 kiểu vượt biên; với nhãn >=5,7% (có khối lối sống có thông tin) mô hình con tốt hơn M-AUG khoảng 0,003-0,004 khi thiếu khối đó; M-AUG15 không cải thiện. Kết luận 'tương đương' vững nhất cho nhãn chính >=6,5%.
- Lợi thế bảo trì vẫn chưa đo: chỉ có số mô hình (5 so với 16).
- Giới hạn: 128 sự kiện nên CI từng kiểu rộng; 15 so sánh chưa hiệu chỉnh; L đã dùng nhiều lần; C ở biên lưới.
