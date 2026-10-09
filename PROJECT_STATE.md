# Shipper Sài Gòn — hồ sơ tiếp tục dự án

Cập nhật: 09/10/2026. Tài liệu chuẩn: `docs/shipper_game_design.md` do người dùng cung cấp.

## Yêu cầu đã xác nhận
- Cập nhật 0.1.1: đích giao là nhà người đặt hàng; hiện biểu tượng nhà và đánh dấu nhà khách hiện tại.
- Bắt đầu triển khai kế hoạch đính kèm, dùng Python 3.10+ và Pygame.
- Giữ tiến độ, quyết định và công việc tiếp theo trong file để tiếp tục giữa các phiên.
- MVP gồm world 25×25, A*, NPC, sự kiện động, D* Lite, sensing, HUD, đổi brain, đơn hàng và CSV headless.

## Trạng thái hiện tại
- [x] Đọc toàn bộ kế hoạch.
- [x] Tạo hồ sơ dự án và quy tắc tiếp tục.
- [x] Cài đặt MVP 0.1: world, 7 brain, sensing, halo, NPC, traffic/accident, đơn hàng và điểm.
- [x] Giao diện cài đặt, chơi/HUD và so sánh cùng seed; điều khiển chuột/phím.
- [x] Headless CSV, benchmark game và benchmark cùng snapshot, biểu đồ pilot.
- [x] 9 bài unittest đạt; D* Lite khớp Dijkstra qua 1.000 lượt cập nhật.
- [x] Kiểm tra 1.000 tick cho S1/S3/S4; seed/RNG và sensing.
- [x] Render và kiểm tra giao diện cài đặt/game/so sánh.
- [x] Bản 0.1.1: hiện nhà khách làm đích giao; render kiểm tra và 9 bài kiểm thử chạy lại đều đạt.
- [x] Chạy pilot 84 lượt, 11 snapshot A*/D* Lite cost khớp.
- [x] Đóng gói bộ mã nguồn, hồ sơ, kế hoạch và kết quả pilot để giao người dùng.
- [ ] Báo cáo học thuật, biểu đồ đầy đủ, video demo và đưa code lên repository GitHub người dùng chọn.

## Quyết định kỹ thuật
- Điểm `dropoff` biểu diễn ô cửa nhà khách, là ô tiếp cận được; nhà tĩnh khác là chướng ngại. Nhà khách hiện bằng biểu tượng mái/cửa, viền và nhãn khi đang giao.
- Thuật toán tự cài; không dùng hàm tìm đường có sẵn.
- Chi phí là chi phí đi vào ô, >= 1; Manhattan nhất quán với lưới 4 hướng.
- D* Lite giữ g/rhs và queue với một entry logic cho mỗi node; cập nhật cả predecessor hình học khi block/unblock.
- Biết nhà tĩnh từ đầu; chỉ biết thay đổi động trong tầm nhìn. S4 thêm halo vào bản đồ nhận thức.
- NPC có RNG riêng, không phụ thuộc vị trí shipper trong benchmark RandomWalker. Các brain gặp cùng chuỗi môi trường.
- Runtime đo thực không thể giống hệt giữa hai lần cùng seed. Kiểm tra tái lập loại runtime khỏi phép so sánh.
- Khi định đi vào ô đang bị chặn, xe chờ; ghi `blocked_attempts`, không gọi đó là va chạm vật lý.
- A* khi cần bám chính sách S2 trong kế hoạch; cost giảm ngoài path có thể tạo đường tốt hơn mà S2 chưa tìm lại.
- Thay goal thì reset D* Lite. Thay brain giữ world, đơn hàng và bản đồ nhận thức.
- Chi phí c khi đi vào ô dẫn tới ceil(c)-1 tick chờ; nhận/giao sau khi chờ xong. Deadline phụ thuộc tick mô phỏng.
- NPC không nhìn shipper nên có thể đi vào ô shipper. `npc_contacts` đếm tiếp xúc này; agent có thể rời ô đang đứng. Không có vật lý liên tục.
- Metadata CSV ghi rõ gain của cả trận khác gain A*/D* Lite trên cùng snapshot.

## Kết quả pilot và điều cần kiểm chứng thêm
84 lượt = 3 seed × 2 mức NPC (5/20) × 7 brain × 2 lần lặp; density 15%, radius 5, tối đa 300 tick.
Trong pilot, D* Lite xử lý ít node hơn S1 nhưng tổng runtime cao hơn S1. Đây là bằng chứng cần đo overhead, không phải lỗi tối ưu đường. S4 có ít NPC contacts hơn S3 trong pilot. Chưa đủ để kết luận H1–H5 với toàn bộ cấu hình.
Các file `results/pilot_benchmark.csv`, `.json`, `.png`, `snapshots.csv` giữ số liệu thực.

## Backlog theo thứ tự đề xuất
1. Người dùng chạy trên Windows, xác nhận giao diện và điều khiển; sửa lỗi nếu có.
2. Chọn repository GitHub đích và đưa code lên sau khi đích được xác nhận.
3. Thêm Patrol/Chaser và replay môi trường có log đầy đủ; không để Chaser làm sai phép so sánh cùng môi trường.
4. Benchmark đủ mật độ 15/20%, NPC 5/10/20/40, radius 3/5/8, 10 seed, 5 repeats; phân tích cùng snapshot và kết quả giao hàng riêng.
5. Báo cáo Word, biểu đồ theo H1–H5 và kịch bản/video demo.
6. Tùy chọn: thưởng +20 theo ước tính, giờ cao điểm, âm thanh, hai người, map VLU.

## Giới hạn đã biết
- Bản đồ lưới mô phỏng; chưa là bản đồ đường phố thực.
- S2 có thể giữ đường chưa tối ưu sau cost giảm ngoài path.
- Giao diện Windows chưa kiểm tra trực tiếp trên máy người dùng; đã render Pygame ở môi trường kiểm tra.
- Chưa cài Patrol/Chaser, replay, physics hoặc phát hiện va chạm giữa hai frame.
- Thuật toán lập kế hoạch theo snapshot nhận thức, chưa dự đoán thời gian/quỹ đạo NPC.
- HUD/menu gom trong `ui/app.py`, `ui/renderer.py`; khác chia file đề xuất nhưng giữ chức năng.

## Cách tiếp tục
1. Đọc `PROJECT_STATE.md`, `CHANGELOG.md`, `README.md` và kế hoạch gốc.
2. Chạy `python -m unittest discover -s tests -v`.
3. Đọc hạn chế/tồn đọng trước khi mở rộng. Cập nhật hồ sơ sau mỗi mốc đã kiểm tra.
4. Dùng bản mã nguồn mới nhất; cập nhật và lưu bộ mã nguồn cùng hồ sơ sau mỗi mốc. Không tuyên bố nhớ vĩnh viễn chỉ bằng ngữ cảnh trò chuyện.

## Quyền truy cập và lưu trữ
GitHub plugin đã sẵn sàng. Chưa có repository đích do người dùng chọn; chưa ghi lên tài khoản GitHub.
