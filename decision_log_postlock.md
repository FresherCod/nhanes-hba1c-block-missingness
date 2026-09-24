# Nhật ký sau khóa (protocol v0.4)

Các file đã khóa (`decision_log.md`, `protocol_v0.4.md`, code, mô hình) **không được sửa** sau khóa. Mọi ghi chép sau khóa nằm ở file này.

| ID | Thời điểm | Sự kiện |
|---|---|---|
| PL-01 | 2026-09-24 10:56:12 | Tạo `LOCK_protocol_v0.4.json` |
| PL-02 | 2026-09-24 10:56:22–10:57:54 | Chạy giai đoạn B trên L **một lần**; exit 0; mã băm dự đoán `f329876fe924d91f9a0c31c3d62f3743256111232681bbca56c87d8fd8f14361` |
| PL-03 | 2026-09-24 | Kiểm lại mã băm sau khi chạy: mọi file khóa khớp |
| PL-04 | 2026-09-24 | Kết quả chính: Δ = −0,0006 [−0,0023; 0,0012] → tương đương thực tế theo quy tắc định trước. Báo cáo: `RESULTS_protocol_v0.4.md` |
| PL-05 | 2026-09-24 | Chưa có phân tích hậu kiểm nào. Mọi phân tích thêm từ đây phải gắn nhãn "hậu kiểm" |
| PL-06 | 2026-09-24 | Vincent yêu cầu 2 phân tích **hậu kiểm** để tăng sức nặng bài báo. Thực hiện `notebooks/05_posthoc.py`: PH-1 (vai trò khối nhân trắc; mô hình con mới "không thước dây" và "cân/đo tự khai", tải thêm P_WHQ/WHQ_L từ CDC); PH-2 (nhãn ≥5,7: ngưỡng từ OOF của P, so với điểm Bang ≥4 theo Bang 2009, net benefit). File khóa không bị sửa |
| PL-07 | 2026-09-24 | Kết quả hậu kiểm: `POSTHOC_REPORT.md`. Tạo 4 hình (`notebooks/06_figures.py`, `figures/`). Hình 3–4 ghi rõ "hậu kiểm" |
| PL-08 | 2026-09-24 | Chọn tạp chí Health Information Science and Systems (Vincent). Viết bản thảo tiếng Anh `manuscript/manuscript_HISS.docx` (+ .md nguồn), hình `manuscript/figures/Fig1–4` (TIFF 600 dpi, PDF, PNG; không có tiêu đề trong hình theo hướng dẫn tác giả), `cover_letter.docx`. Số liệu lấy trực tiếp từ `final_out/` và `posthoc_out/`; không phân tích mới |
| PL-09 | 2026-09-24 | Đưa code lên GitHub (private): https://github.com/FresherCod/nhanes-hba1c-block-missingness ; kiểm LOCK trên bản clone: khớp. Viết lại bản thảo theo văn phong học thuật (bỏ gạch đầu dòng, văn xuôi), định dạng bản nộp (TNR 12, dãn đôi, đánh số dòng liên tục, số trang, bảng 3 đường kẻ); đổi thứ tự hình (Fig. 1 = so sánh chính). Không đổi số liệu |
| PL-10 | 2026-09-24 | Điền thông tin tác giả (Phuc Dinh Truong, nghiên cứu độc lập, Cam Ranh, Khánh Hòa; ORCID 0009-0008-2149-478X), các mục khai báo, lời cảm ơn; đổi sang ngôi thứ nhất số ít. Claude **không** đứng tên tác giả (Springer: LLM không đạt tiêu chuẩn tác giả); việc dùng AI được khai báo trong Methods và Acknowledgements |
| PL-11 | 2026-09-24 | Repo GitHub chuyển sang Public (Vincent yêu cầu; đã quét: không có email/token). Bắt đầu nộp medRxiv (bản nháp MEDRXIV/2026/363865: mới lưu chuyên ngành Health Informatics + tiêu đề) rồi **dừng theo yêu cầu của tác giả, chưa nộp**. Sửa định dạng: căn đều hai bên, bảng căn trái, lặp hàng tiêu đề bảng |
