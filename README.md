# 🛵 Shipper Sài Gòn 2D — Phiên Bản Hoàn Thiện

Tựa game giao hàng 2D sống động kết hợp bàn thí nghiệm tìm đường AI trong thành phố động Sài Gòn 60 FPS, triển khai từ kế hoạch trong `docs/shipper_game_design.md`.

## 🌟 Điểm nổi bật phiên bản 2D Nâng Cấp

1. **Đồ họa & Khung hình 60 FPS mượt mà (Smooth Sub-grid Interpolation)**:
   - Shipper và xe NPC lướt chuyển động êm ái trên đường phố giữa các tick (không giật nhảy ô).
   - Đèn pha xe máy (Headlight) chiếu quầng sáng rọi đường, xoay góc vào cua mượt mà theo hướng di chuyển.
   - Bản đồ phong cách phố thị Sài Gòn 2D chi tiết: nhà phố ban công bồn nước inox, vỉa hè, vạch kẻ tim đường vàng, vạch qua đường, quán ăn mái bạt sọc đỏ-vàng (P), nhà khách hàng có radar mời gọi.
   - Lô cốt rào chắn công trình đào đường sọc vàng-đen phản quang kèm đèn chớp cảnh báo.

2. **Chế độ Gameplay phong phú**:
   - **Lái thủ công (Manual Mode)**: Người chơi trực tiếp lái xe bằng cụm phím `W/A/S/D` hoặc `Phím mũi tên` để luồn lách qua các ngõ hẻm kẹt xe và né tránh xe NPC.
   - **Dẫn đường GPS thông minh**: Ngay cả khi lái tay, hệ thống AI vẫn chiếu đường GPS phát sáng màu xanh cyan hướng dẫn lộ trình tối ưu như Google Maps / Grab.
   - **Tự động lái (AI Autopilot)**: AI tự tính toán và điều khiển xe đến quán lấy hàng rồi giao tận cửa nhà khách.
   - **Còi xe máy Sài Gòn (Horn)**: Bấm còi `H` hoặc click nút còi "Bim bim!" giải tỏa ùn ứ, nhắc nhở các xe NPC xung quanh dừng lại nhường đường.
   - **Thời tiết động (Weather Rain)**: Hiệu ứng mưa rào nhiệt đới Sài Gòn và khói xe pô xe máy sống động.

3. **Âm thanh Kỹ thuật số Procedural (100% tích hợp sẵn)**:
   - Hệ thống tự tổng hợp sóng âm stereo thời gian thực qua `pygame.mixer` & `numpy`: tiếng nhận đơn ting-ting, chuông giao hàng thành công, tiếng còi xe bim-bim, âm thanh va quẹt và còi báo trễ giờ. Không cần file âm thanh ngoài.

4. **Kiểm thử Thuật toán Toàn diện (16/16 Unit Tests PASS)**:
   - Bộ test suite mở rộng kiểm tra mọi trường hợp góc cạnh: đồ thị cô lập không lối thoát, biên kích thước 3×3 đến 30×30, D* Lite dao động liên tục 150 bước, halo sensing, tính bất biến seed và benchmark.

## Chạy trên Windows / Visual Studio Code

1. Cài Python 3.10 trở lên.
2. Trong VS Code, chọn **File → Open Folder** và mở thư mục `shipper-game`.
3. Mở **Terminal → New Terminal**, chạy:

```powershell
.\.venv\Scripts\python.exe main.py
```

Hoặc nhấp đúp trực tiếp vào file **`start_windows.bat`** để chạy ngay.

## Điều khiển trong Game

| Điều khiển | Chức năng |
|---|---|
| **W / A / S / D** hoặc **Mũi tên** | Lái xe máy shipper di chuyển trong chế độ Lái Tay |
| **M** | Chuyển đổi qua lại giữa **Lái Tay (Manual)** và **Tự Động (AI)** |
| **H** | Bấm còi xe máy Sài Gòn "Bim bim!" giải tỏa ùn ứ |
| **Space** | Tạm dừng / Tiếp tục; Bắt đầu từ màn hình cài đặt |
| **S** | Bật / Tắt âm thanh |
| **W** (ở chế độ AI) | Bật / Tắt thời tiết mưa nhiệt đới Sài Gòn |
| **1 — 7** | Đổi trực tiếp 7 bộ não AI (A*, D* Lite, Halo, BFS, Greedy,...) |
| **+ / −** | Điều chỉnh tốc độ mô phỏng (1×, 2×, 4×, 8×) |
| **V** | Ẩn / hiện các ô trạng thái AI vừa duyệt |
| **T** | Ẩn / hiện lớp mờ sương mù ngoài tầm nhìn |
| **R** | Chơi lại ván đấu cùng seed bản đồ |
| **Esc** | Trở về màn hình Cài đặt cấu hình |
| **Chuột trái vào đường** | Đặt / tháo lô cốt công trình rào chắn đường |
| **Chuột phải vào đường** | Tạo / xóa điểm kẹt xe ùn tắc |

Nhà tĩnh sinh sẵn không bị xóa bằng chuột. Không đặt vật cản ngay dưới shipper. Vật cản ngoài tầm nhìn chỉ được AI phát hiện khi tới gần. Hình vẽ cho người xem thấy toàn bản đồ; lớp làm mờ biểu diễn giới hạn thông tin của shipper.

Ký hiệu **P** là quán nhận hàng; **nhà xanh có mái và cửa** là nhà của người đặt hàng. Nhà đang giao có viền nổi bật và nhãn **NHÀ KHÁCH #**; HUD xác nhận đích này. Shipper đến ô cửa nhà (tọa độ `dropoff`, có thể tiếp cận) để giao, không đi vào ô nhà tĩnh chặn đường. Nhà khách vẫn hiển thị sau khi giao. Xe đỏ là NPC; vùng cam là kẹt xe; vùng đỏ sẫm là tai nạn / vật cản thủ công. Ô viền trắng là đích hiện tại. Chấm tím là trạng thái vừa xử lý. Bản đồ là mô phỏng, không phải bản đồ đường phố Sài Gòn thật.

## AI và chi phí

- Tất cả thuật toán tự cài trong `ai/`, dùng lưới 4 hướng, cost đi vào ô >= 1.
- A* dùng `g + Manhattan`; Weighted A* dùng `g + 1.5 × Manhattan`, không bảo đảm tối ưu.
- BFS tối ưu số bước khi mọi bước đồng chi phí; BFS/Greedy bỏ qua cost khi chọn node, nhưng vẫn báo tổng cost của đường tìm được.
- D* Lite dùng g/rhs, key hai thành phần, `km`, `move_start`, queue lazy với một entry logic mỗi node và dọn heap stale định kỳ. Block/unblock cập nhật cả predecessor hình học, kể cả ô vừa bị chặn.
- Biết nhà tĩnh từ đầu; thông tin NPC/sự kiện cập nhật trong bán kính Manhattan. Ô ngoài tầm nhìn giữ thông tin cũ.
- S4 nâng cost các ô trong tầm nhìn cạnh NPC lên ít nhất 4. Halo là chi phí nhận thức; cost thực di chuyển không tính halo.
- S2 chỉ tính lại nếu path chưa có, goal đổi hoặc cost trên path đổi. Cost giảm ngoài path có thể tạo đường tốt hơn mà S2 chưa phát hiện. Không gọi S2 là tối ưu trên mọi snapshot.
- Mỗi lần đổi điểm nhận/giao, D* Lite được khởi tạo lại. Đổi brain bằng phím giữ nguyên trận.

## Mô phỏng thời gian và điểm

Một tick di chuyển tối đa một ô. Khi đi vào ô cost `c`, shipper tốn thêm `ceil(c)-1` tick chờ để mô phỏng kẹt xe; việc nhận/giao chỉ hoàn tất khi chờ xong. Chi phí di chuyển chốt tại thời điểm đi vào ô. Thời gian mô phỏng độc lập với runtime thực của thuật toán.

Đơn được lên lịch mỗi 25 tick, tối đa 3 đơn đang chờ/đang giao. Hạn giao là release tick + 100 mặc định; quá hạn thêm 100 tick thì hủy. Giao đúng hạn +100; trễ trừ 2 điểm/tick, tối thiểu +10; hủy −50; một bước vào vùng kẹt xe −1; NPC mới đi vào ô shipper −30. Chưa áp dụng thưởng +20 so với ước tính ban đầu trong kế hoạch.

NPC RandomWalker cập nhật trước shipper, không dựa vào brain/vị trí shipper. Nếu NPC đi vào ô shipper đang đứng, đếm `npc_contacts`; shipper được phép rời ô đang đứng nếu ô đích trống. Nếu bước dự định bị chặn, shipper chờ và đếm `blocked_attempts`. Hai chỉ số khác nhau; game chưa có mô hình vật lý hay kiểm tra va chạm liên tục. Vì sensing diễn ra sau NPC và trước shipper, `blocked_attempts` thường bằng 0: đó là hành vi tránh bước vào ô bị chiếm, không chứng minh halo có hiệu quả.

## Chạy headless và lấy CSV

Không cần Pygame, pandas, matplotlib khi chỉ chạy mô phỏng và kiểm thử:

```powershell
.\.venv\Scripts\python.exe main.py --headless --brain dstar --seed 42 --npcs 20 --ticks 300 --output results\episode.csv
.\.venv\Scripts\python.exe -m experiments.run_benchmark --seeds 42 43 44 45 46 --npcs 5 10 20 40 --repeats 5 --output results\benchmark.csv
.\.venv\Scripts\python.exe -m experiments.plot_results results\benchmark.csv --output results\benchmark.png
.\.venv\Scripts\python.exe -m experiments.snapshot_benchmark --events 10
```

Lệnh benchmark chính cũng nhận `--density 0.20`, `--radius 3`, `--ticks`, `--orders`, `--brains`. Chạy riêng từng cấu hình; metadata `.json` giữ cấu hình. Màn hình **So sánh cùng seed** chạy 7 brain trong luồng nền và lưu `results/ui_compare.csv`.

Đã kèm pilot: 3 seed (42–44), 2 số lượng xe (5/20), 7 brain, 2 lần lặp = **84 lượt**, density 15%, radius 5. Pilot chưa thay thế ma trận thực nghiệm H1–H5 trong kế hoạch.

### Đọc số liệu đúng

- `planning_ms`: thời gian thực bao quanh `Brain.plan`; gồm đối chiếu/cập nhật cost, khởi tạo planner khi cần, tìm kiếm và truy vết; không tính world, sensing, di chuyển, vẽ hình.
- `mean_planning_ms_per_tick`: tổng planning time chia số tick thực chạy, kể cả tick nhàn rỗi.
- `states_processed`: node thật sự xử lý; stale entry bị bỏ qua không tính. D* Lite có thể xử lý một node nhiều lần.
- `steps`: số ô đã đi; `travel_cost`: tổng chi phí thực các bước, không gồm chờ và halo.
- `on_time_rate`: giao đúng hạn / toàn bộ đơn dự kiến, không phải giao đúng hạn / chỉ các đơn đã giao.
- Cùng seed giữ nguyên bản đồ, đơn, quỹ đạo RandomWalker và sự kiện. Các RNG tách biệt; thuật toán không tiêu thụ RNG môi trường. Do shipper chọn đường khác nhau, sensing và goal đang xử lý có thể khác nhau.
- Runtime không tái lập chính xác theo seed. Các bài kiểm tra so sánh chỉ số quyết định, loại runtime.
- Trận dừng khi hết tick hoặc mọi đơn đã giao/hủy; luôn xem cột `ticks` khi so tổng công việc.
- `planning_gain_vs_s1_pct` ở benchmark game là chênh lệch **tổng thời gian lập kế hoạch của cả trận** so S1. Không phải lợi ích sửa đường trên cùng snapshot.
- `results/snapshots.csv` mới là phép đối chiếu A*/D* Lite trên cùng start/goal và chuỗi map thay đổi, kiểm tra cost khớp. H1–H5 vẫn là giả thuyết. Không khẳng định D* Lite luôn nhanh hơn.

## Kiểm tra

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

9 bài đã đạt trên Python 3.12/Pygame 2.6.1 trong môi trường kiểm tra: A* tránh chi phí lớn, validation, đích không tới được, block/unblock start/goal, start=goal, D* Lite vs Dijkstra qua 1.000 lượt cập nhật, cùng seed, cùng môi trường giữa brain, sensing, đổi brain và chạy 1.000 tick.

Giao diện cài đặt/game/so sánh đã render và kiểm tra vùng click. Ảnh ở `results/*_preview.png`. Chưa xác minh trực tiếp trên máy Windows của người dùng; làm theo lệnh cài đặt ở trên để chạy tại máy.

## Cấu trúc và việc tiếp theo

`main.py`: CLI; `config.py`: cấu hình; `core/`: world, NPC, orders, sensing, metrics, simulation; `ai/`: thuật toán và brain; `ui/`: Pygame; `experiments/`: benchmark/plot; `tests/`: kiểm thử; `docs/`: kế hoạch gốc; `results/`: pilot, CSV, ảnh.

MVP 0.1 đã có các chức năng mục 7.1. Chưa có Patrol/Chaser, dự đoán quỹ đạo, replay log đầy đủ, giờ cao điểm, âm thanh, chơi hai người, map VLU, báo cáo Word/video. UI renderer/HUD/menu tập trung trong hai module thay vì chia ba file như cây thư mục đề xuất.

Bước tiếp theo: người dùng chạy và góp ý UI/gameplay; sau đó thêm Patrol/Chaser hoặc hoàn thiện ma trận thực nghiệm và báo cáo. Chưa chọn repository GitHub đích; chưa đăng code lên tài khoản.
