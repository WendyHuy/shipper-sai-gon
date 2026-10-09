# 🛵 Shipper Sài Gòn — MVP 0.1.1

Game giao hàng và bàn thí nghiệm tìm đường trong thành phố động, triển khai từ kế hoạch trong `docs/shipper_game_design.md`.

**Đọc `PROJECT_STATE.md` trước khi tiếp tục phát triển.** File này giữ yêu cầu, quyết định, trạng thái và việc tiếp theo; `CHANGELOG.md` ghi các mốc đã hoàn tất.

## Chạy trên Windows / Visual Studio Code

1. Cài Python 3.10 trở lên. Giải nén bộ mã nguồn.
2. Trong VS Code, chọn **File → Open Folder** và mở thư mục `shipper-game` (nơi có `main.py` và `requirements.txt`).
3. Mở **Terminal → New Terminal**, chạy từng dòng:

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Các lệnh sử dụng trực tiếp Python trong môi trường, không cần activate. Nếu máy không có lệnh `py`, thay hai lệnh đầu bằng `python --version` và `python -m venv .venv`.

Nếu báo thiếu `requirements.txt`, terminal đang sai thư mục: mở thư mục con `shipper-game`, không mở thư mục ngoài của file ZIP. Sau khi cài xong, có thể bấm `start_windows.bat` để chạy.

Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

## Chơi và demo

Trong màn hình cài đặt, chọn seed, số xe, tầm nhìn, số đơn, mật độ nhà, giới hạn tick và bộ não. Bấm **Bắt đầu giao hàng**. Chương trình tự chọn đơn có điểm nhận gần nhất theo Manhattan, đi lấy hàng rồi giao.

| Điều khiển | Chức năng |
|---|---|
| Space | Tạm dừng / tiếp tục; từ cài đặt thì bắt đầu |
| 1 | A* mỗi tick — S1 |
| 2 | A* khi cần — S2 |
| 3 | D* Lite — S3 |
| 4 | D* Lite + halo — S4 |
| 5 / 6 / 7 | BFS / Greedy / Weighted A* |
| V | Ô vừa được xử lý |
| T | Làm mờ vùng ngoài tầm nhìn |
| R | Chơi lại cùng seed và cấu hình |
| + / − | Tốc độ 1×, 2×, 4×, 8× |
| Esc | Về cài đặt |
| Chuột trái vào đường | Thêm / gỡ vật cản thủ công |
| Chuột phải vào đường | Bật / tắt kẹt xe cost 5 |

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
