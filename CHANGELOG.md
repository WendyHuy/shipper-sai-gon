# Nhật ký dự án

## 0.1.1 — 09/10/2026

- Theo yêu cầu người dùng, đích giao hàng thể hiện là nhà của khách đặt hàng.
- Thay ký hiệu D bằng biểu tượng nhà có mái, cửa và cửa sổ. Nhà vẫn hiển thị sau khi giao.
- Nhà khách đang giao có viền nổi bật và nhãn NHÀ KHÁCH #; HUD hiển thị đúng đích giao.
- `dropoff` là ô cửa nhà có thể tiếp cận, phân biệt với ô nhà tĩnh chặn đường. Giữ tọa độ và thuật toán để các kết quả pilot 0.1 vẫn có ý nghĩa.
- Đã render kiểm tra nhà đích/HUD và chạy lại 9 bài kiểm thử: đều đạt.

## 0.1.0 — 09/10/2026

- Giữ bản kế hoạch nguyên văn trong docs/shipper_game_design.md; tạo AGENTS.md, PROJECT_STATE.md và README.md để tiếp tục giữa các phiên.
- Tạo world 25×25 theo seed, BFS kiểm tra thành phần liên thông, đơn hàng theo thời gian và RandomWalker với RNG riêng.
- Tự cài BFS, Greedy, A*, Weighted A*, D* Lite; tích hợp S1–S4, sensing và halo.
- Thêm sự kiện traffic/accident có thời hạn, vật cản/cost thủ công, chi phí di chuyển, deadline và điểm.
- Giao diện Pygame: cài đặt, gameplay/HUD, đổi AI, overlay, pause/reset/speed, danh sách đơn và màn hình so sánh.
- CLI headless, CSV mỗi tick/summary, benchmark nhiều seed/repeat và snapshot benchmark A* vs D* Lite.
- 9 bài unittest đạt; D* Lite đối chiếu Dijkstra trong 1.000 lượt cập nhật; 1.000 tick mô phỏng cho 3 chiến lược chính.
- Render và kiểm tra giao diện cài đặt, game và so sánh.
- Chạy pilot 84 lượt; 11 snapshot có chi phí A*/D* Lite khớp. Biểu đồ pilot đi kèm.
- Tách blocked_attempts khỏi npc_contacts, ghi rõ runtime không tái lập chính xác, gain của cả trận khác gain cùng snapshot.
- Chưa đăng code GitHub; các tính năng ngoài MVP và báo cáo còn trong backlog.
