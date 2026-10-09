# 🛵 Shipper Sài Gòn – Tài liệu thiết kế game

> Game mô phỏng nhân viên giao hàng tự tìm đường trong thành phố có **kẹt xe, tai nạn và xe cộ di chuyển liên tục**.
> Điểm nhấn: người chơi (và báo cáo) so sánh các "bộ não" AI từ Lab 1–4: **BFS, Greedy, A\*, Weighted A\*, D\* Lite**.

---

## 1. Tổng quan

### 1.1. Mục tiêu dự án
- Trả lời câu hỏi của giảng viên: *khi chướng ngại vật di chuyển liên tục thì mô hình tìm đường hoạt động ra sao?*
- Biến kiến thức Lab 1–4 thành sản phẩm chạy được, có số liệu thực nghiệm.
- Vừa là game chơi được, vừa là **bàn thí nghiệm** (chạy tự động không giao diện để lấy số liệu).

### 1.2. Hai chế độ chính
| Chế độ | Mô tả | Dùng để |
|---|---|---|
| **Play (Game)** | Có giao diện, đơn hàng, điểm số, chọn "bộ não" | Demo, trình bày |
| **Benchmark (Lab)** | Chạy headless, cố định seed, xuất CSV | Viết báo cáo |

### 1.3. Ánh xạ Lab → game
| Lab | Thuật toán | Vai trò trong game |
|---|---|---|
| Lab 1 | BFS | Kiểm tra bản đồ sinh ra có đi được không (`is_reachable`); "bộ não" mức thấp nhất (không có thông tin, không xét chi phí) |
| Lab 2 | Greedy-Manhattan | Bộ não "liều": nhanh, hay đi vòng; chọn đơn gần nhất tiếp theo |
| Lab 3 | A\*, Weighted A\* | Bộ não tối ưu cho bản đồ tĩnh; Weighted A\* cho chế độ "giao gấp" |
| Lab 4 | D\* Lite | Bộ não thích nghi, sửa đường khi môi trường đổi |

---

## 2. Công nghệ đề xuất

| Thành phần | Lựa chọn | Lý do |
|---|---|---|
| Ngôn ngữ | Python 3.10+ | Lab đã viết bằng Python, tái sử dụng code |
| Giao diện game | **pygame** | Vòng lặp game, vẽ lưới, bắt phím/chuột dễ |
| Biểu đồ kết quả | matplotlib + pandas | Giống các Lab |
| Cấu hình | file `config.py` hoặc JSON | Đổi tham số không sửa code |
| Quản lý mã | GitHub | Làm nhóm, nộp bài |

> Nếu muốn nhanh hơn: dùng `matplotlib.animation` thay pygame (ít tương tác hơn). Tài liệu này giả định dùng pygame.

---

## 3. Thiết kế giao diện (UI)

### 3.1. Bố cục màn hình chính (1280×720)

```
┌──────────────────────────────────────────────────────────────┬───────────────────┐
│  THANH TRÊN: Điểm | Thời gian | Đơn còn lại | Tốc độ (1x/2x)│                   │
├──────────────────────────────────────────────────────────────┤   BẢNG ĐIỀU KHIỂN │
│                                                              │                   │
│                                                              │  Chọn bộ não:     │
│                       LƯỚI BẢN ĐỒ 25×25                      │  ( ) BFS          │
│                    (mỗi ô 24×24 px = 600px)                  │  ( ) Greedy       │
│                                                              │  (•) A*           │
│                                                              │  ( ) Weighted A*  │
│                                                              │  ( ) D* Lite      │
│                                                              │                   │
│                                                              │  Số xe NPC: [20]  │
│                                                              │  Tầm nhìn:  [5]   │
│                                                              │  [Bắt đầu][Dừng]  │
│                                                              │  [Reset][Seed]    │
├──────────────────────────────────────────────────────────────┤                   │
│  HUD SỐ LIỆU: Cost còn lại | States processed | Replan (ms)  │  Danh sách đơn    │
│  Số lần replan | Va chạm | Quãng đường đã đi                 │                   │
└──────────────────────────────────────────────────────────────┴───────────────────┘
```

### 3.2. Các màn hình
1. **Menu chính**: Chơi, Benchmark, Hướng dẫn, Thoát.
2. **Màn hình cài đặt trận**: chọn mật độ nhà (15% / 20%), số xe NPC, số đơn, seed, bộ não.
3. **Màn hình chơi** (mục 3.1).
4. **Màn hình kết quả**: điểm, bảng chỉ số, nút "Chơi lại" / "Đổi bộ não chơi lại cùng seed".
5. **Màn hình so sánh**: chạy cùng seed với nhiều bộ não, hiện bảng + biểu đồ cột.

### 3.3. Quy ước hiển thị

| Đối tượng | Màu / hình | Ghi chú |
|---|---|---|
| Ô đường thường | Xám nhạt | cost = 1 |
| Nhà / tòa nhà | Đen hoặc xám đậm | Obstacle tĩnh |
| Shipper | Chấm xanh dương (có mũi tên hướng) | Agent |
| Quán (điểm nhận) | Ô vàng, ký hiệu 🍜 | Pickup |
| Nhà khách (điểm giao) | Ô xanh lá, ký hiệu 🏠 | Dropoff |
| Xe NPC | Ô đỏ | Chướng ngại di động |
| Kẹt xe | Ô cam (đậm dần theo cost) | cost 3–8 |
| Tai nạn / ngập | Ô đỏ sẫm có dấu ✖ | Chặn tạm thời |
| Vùng nguy hiểm (halo) | Viền đỏ nhạt quanh xe | cost cao quanh NPC |
| Tầm nhìn shipper | Vòng tròn/ô sáng bán kính r | Chỉ thấy thay đổi trong vùng này |
| Đường đi dự kiến | Đường xanh đậm | Path hiện tại |
| Ô đã được xử lý | Chấm mờ (bật bằng phím `V`) | Trực quan hóa "states processed" |

> **Mẹo cho demo:** bật phím `V` để thấy A\* tô sáng cả vùng rộng mỗi lần replan, còn D\* Lite chỉ tô vùng nhỏ quanh chỗ bị đổi. Đây là hình ảnh thuyết phục nhất cho báo cáo.

### 3.4. Điều khiển
| Phím / chuột | Chức năng |
|---|---|
| `Space` | Tạm dừng / tiếp tục |
| `1`–`5` | Đổi bộ não ngay trong lúc chơi |
| `+` / `-` | Tăng / giảm tốc độ mô phỏng |
| `V` | Bật/tắt hiển thị ô đã xử lý |
| `T` | Bật/tắt hiển thị tầm nhìn |
| `R` | Reset cùng seed |
| Click chuột trái vào ô | Đặt/xóa vật cản thủ công (để demo cho giảng viên) |
| Click chuột phải vào ô | Đặt ô kẹt xe (cost cao) |

> Tính năng click đặt vật cản rất hữu ích khi thuyết trình: giảng viên tự chặn đường và xem shipper phản ứng.

---

## 4. Thế giới game

### 4.1. Bản đồ
- Lưới **25×25**, 4 hướng, mỗi bước cơ bản cost = 1 (giống Lab 4).
- Nhà cố định: sinh ngẫu nhiên theo `density` + `seed` (dùng lại `generate_obstacles` Lab 3), **bắt buộc kiểm tra reachable bằng BFS** (Lab 1).
- Nâng cấp tùy chọn: dùng layout dạng "khu phố" (các khối chữ nhật + đường ngang dọc) thay vì chấm ngẫu nhiên để giống thành phố hơn.

### 4.2. Mô hình chi phí (`cost_map`)
Mỗi ô có chi phí để **đi vào** ô đó:

| Trạng thái ô | Cost |
|---|---|
| Đường thường | 1 |
| Kẹt xe nhẹ / vừa / nặng | 3 / 5 / 8 |
| Halo quanh xe NPC | 4 |
| Tai nạn, ngập, nhà, xe NPC đang đứng | ∞ (chặn) |

### 4.3. Shipper (agent)
- Mỗi tick đi tối đa 1 ô.
- Có `sensing_radius` (mặc định 5): chỉ cập nhật thông tin các ô nằm trong bán kính này (khoảng cách Manhattan).
- Có trạng thái: `ĐI_NHẬN`, `ĐI_GIAO`, `NHÀN_RỖI`.

### 4.4. Đơn hàng
```
Order { id, pickup_cell, dropoff_cell, deadline_tick, reward, status }
```
- Sinh theo thời gian, tối đa N đơn cùng lúc (mặc định 3).
- Shipper chọn đơn theo **nearest-neighbor** (tham lam kiểu Lab 2) dùng khoảng cách Manhattan, hoặc dùng cost A\* thật giữa các điểm (chính xác hơn, tốn hơn).

### 4.5. Xe NPC (chướng ngại di động)
| Kiểu | Hành vi | Mục đích thí nghiệm |
|---|---|---|
| `RandomWalker` | Mỗi tick đi ngẫu nhiên 1 ô hợp lệ (hoặc đứng yên) | Môi trường nhiễu |
| `Patrol` | Chạy vòng theo lộ trình cố định | Dự đoán được → đẩy cost trước |
| `Chaser` | Đi về phía shipper (Manhattan, hoặc dùng A\* nhẹ) | Kịch bản khó nhất, "CSGT đuổi" |

Quy tắc: NPC không đi vào nhà, không đi vào cùng ô với NPC khác.

### 4.6. Sự kiện môi trường
- **Kẹt xe**: xuất hiện ngẫu nhiên tại 1 ô, lan sang vài ô kề (cost giảm dần theo khoảng cách), biến mất sau 20–60 tick.
- **Tai nạn / ngập**: chặn hẳn 1–3 ô trong 15–40 tick, sau đó mở lại (unblock event của Lab 4).
- Giờ cao điểm (tùy chọn): tần suất kẹt xe tăng gấp đôi trong một khoảng thời gian.

---

## 5. Kiến trúc AI

### 5.1. Interface chung cho mọi "bộ não"
Để so sánh công bằng, tất cả bộ não dùng chung một interface:

```python
class Brain:
    name = "base"

    def reset(self, world, start, goal):
        """Khởi tạo lúc bắt đầu một đơn / một chặng."""

    def on_changes(self, changed_cells):
        """Nhận danh sách ô vừa đổi trong tầm nhìn: [(cell, new_cost), ...]"""

    def next_step(self, pos):
        """Trả về ô kế tiếp và ghi lại metrics của lần plan này."""

    # metrics sau mỗi tick
    states_processed = 0
    replan_ms = 0.0
```

### 5.2. Bốn chiến lược cần cài đặt và so sánh

| # | Chiến lược | Khi nào replan | Đặc điểm |
|---|---|---|---|
| S1 | **A\* replan mỗi tick** | Luôn luôn | Baseline ngây thơ, chính xác, tốn nhất |
| S2 | **A\* replan khi cần** | Chỉ khi đường hiện tại bị chặn / cost đổi trên đường | Rẻ hơn, phản ứng muộn |
| S3 | **D\* Lite + tầm nhìn giới hạn** | Mỗi tick, chỉ cập nhật ô trong bán kính r | Đúng tinh thần Lab 4 |
| S4 | **D\* Lite + halo nguy hiểm** | Như S3 + cost cao quanh xe NPC | Né từ xa, ít va chạm |

Hai bộ não bổ sung để minh họa Lab 1, 2: **BFS** (bỏ qua cost, chỉ đếm bước) và **Greedy-Manhattan**.

### 5.3. Sửa `DStarLite` của Lab 4 để hỗ trợ cost thay đổi

Lab 4 để `cost()` luôn bằng 1.0. Cần đổi sang tra `cost_map`:

```python
class DStarLiteDyn(DStarLite):
    def __init__(self, rows, cols, obstacles, start, goal):
        super().__init__(rows, cols, obstacles, start, goal)
        self.cost_map = {}            # {cell: cost vào ô đó}

    def cost(self, u, v):
        if u in self.obstacles or v in self.obstacles:
            return INF
        # Lưu ý: nên bỏ kiểm tra set(neighbors4(...)) của bản Lab
        # vì tạo set mới mỗi lần gọi -> rất chậm khi chạy nhiều tick
        return self.cost_map.get(v, 1.0)

    def change_cost(self, cell, new_cost):
        if new_cost == 1.0:
            self.cost_map.pop(cell, None)
        else:
            self.cost_map[cell] = new_cost
        # cost phụ thuộc ô đích -> các ô kề (predecessor) phải tính lại rhs
        for u in neighbors4(cell, self.rows, self.cols):
            self.update_vertex(u)
        self.update_vertex(cell)
```

Nhớ hai điều dễ sai:
1. Mỗi khi shipper **bước một ô**, gọi `move_start(new_pos)` để cập nhật `km`. Quên bước này, key sai và đường đi có thể không tối ưu.
2. Khi **đổi goal** (giao xong đơn này sang đơn khác), nên **khởi tạo lại** `DStarLite` vì D\* Lite tìm ngược từ goal.

### 5.4. Cảm biến (sensing)
Chỉ những ô trong bán kính r mới được "báo" cho planner:

```python
def sense(world, agent_pos, radius, known_state):
    changes = []
    for cell in cells_within(agent_pos, radius):
        true_cost = world.cost_at(cell)          # kể cả NPC, kẹt xe, tai nạn
        if known_state.get(cell, 1.0) != true_cost:
            known_state[cell] = true_cost
            changes.append((cell, true_cost))
    return changes
```
- Ô ngoài tầm nhìn: shipper vẫn tin thông tin cũ (có thể sai) → đây là tính "thực tế" của bài toán, giống robot thật.
- Với A\*: truyền `known_state` làm bản đồ để tính lại.

### 5.5. Dự đoán xe NPC (tùy chọn nâng cao)
- Với `Patrol`: biết lộ trình nên đẩy cost vào ô xe **sắp tới** trong 2–3 tick tới.
- Với `RandomWalker` / `Chaser`: dùng halo bán kính 1 quanh xe.

---

## 6. Vòng lặp game

```python
while running:
    handle_input()
    if not paused:
        tick += 1

        # 1. Môi trường cập nhật
        for npc in npcs: npc.step(world)
        world.update_events(tick)          # kẹt xe, tai nạn xuất hiện/biến mất

        # 2. Shipper cảm nhận
        changes = sense(world, shipper.pos, radius, known_state)

        # 3. Cập nhật planner
        brain.on_changes(changes)

        # 4. Lập kế hoạch + đo
        t0 = perf_counter()
        nxt = brain.next_step(shipper.pos)
        metrics.log(tick, brain.states_processed,
                    (perf_counter() - t0) * 1000)

        # 5. Di chuyển + kiểm tra
        if nxt is None:
            shipper.wait()
        elif world.is_blocked(nxt):         # NPC vừa bước vào ô này
            shipper.wait(); metrics.collisions += 1
        else:
            shipper.move(nxt); brain.on_move(nxt)

        # 6. Xử lý đơn hàng
        orders.update(shipper, tick)

    render()           # chỉ vẽ nếu không chạy headless
    clock.tick(FPS)
```

Điểm quan trọng: **đo thời gian chỉ bao quanh bước plan**, không tính vẽ hình (giống nguyên tắc benchmark công bằng ở Lab 1 và 3).

---

## 7. Danh sách tính năng

### 7.1. Bắt buộc (MVP)
- [ ] Sinh bản đồ 25×25 theo seed, kiểm tra reachable
- [ ] Vẽ lưới, shipper, quán, nhà khách, đường đi dự kiến
- [ ] Shipper tự đi bằng A\* trên bản đồ tĩnh
- [ ] Xe NPC kiểu `RandomWalker`
- [ ] Sự kiện kẹt xe (đổi cost) và tai nạn (block/unblock)
- [ ] D\* Lite có `cost_map` + `move_start`
- [ ] Tầm nhìn giới hạn
- [ ] HUD: cost còn lại, states processed, replan ms
- [ ] Đổi bộ não bằng phím số
- [ ] Nhiều đơn hàng + điểm số
- [ ] Chế độ benchmark headless xuất CSV

### 7.2. Nên có
- [ ] `Patrol` và `Chaser`
- [ ] Halo nguy hiểm quanh xe
- [ ] Click chuột đặt vật cản / kẹt xe lúc đang chạy
- [ ] Hiển thị ô đã xử lý (phím `V`)
- [ ] Màn hình so sánh nhiều bộ não cùng seed
- [ ] Replay lại trận bằng log

### 7.3. Có thì tốt
- [ ] Weighted A\* cho "đơn giao gấp"
- [ ] Giờ cao điểm
- [ ] Âm thanh, hiệu ứng
- [ ] Chế độ 2 người: người chơi tự điều khiển shipper vs AI
- [ ] Bản đồ khu vực VLU (dùng graph của Lab 1) làm map đặc biệt

---

## 8. Hệ thống điểm

| Sự kiện | Điểm |
|---|---|
| Giao đúng hạn | +100 |
| Giao trễ | +100 − 2×(số tick trễ), tối thiểu 10 |
| Mỗi tick đi trong ô kẹt xe | −1 |
| Va chạm xe NPC | −30 |
| Giao nhanh hơn dự tính (cost thực < cost ước tính ban đầu) | +20 |
| Đơn hết hạn không giao | −50 |

Điểm chỉ phục vụ phần game. **Báo cáo khoa học dùng các chỉ số kỹ thuật ở mục 9**, không dùng điểm game (vì điểm có yếu tố chủ quan).

---

## 9. Thiết kế thực nghiệm (cho báo cáo)

### 9.1. Biến thí nghiệm
| Biến | Giá trị |
|---|---|
| Số xe NPC | 5, 10, 20, 40 |
| Kiểu NPC | Random, Patrol, Chaser |
| Bộ não | S1, S2, S3, S4 (+ BFS, Greedy làm đối chứng) |
| Bán kính tầm nhìn | 3, 5, 8 |
| Mật độ nhà | 15%, 20% |
| Seed | 10 seed cố định |
| Độ dài trận | 300 tick hoặc đến khi giao xong 5 đơn |

### 9.2. Chỉ số
| Chỉ số | Cách đo |
|---|---|
| Tỷ lệ giao thành công | số đơn giao đúng hạn / tổng đơn |
| Số va chạm | đếm khi bước vào ô bị chiếm |
| Quãng đường thực tế | tổng cost các bước shipper đã đi |
| Tổng states processed | cộng dồn mọi lần plan |
| Replan time TB mỗi tick (ms) | trung bình `perf_counter` |
| Số lần đổi đường | số lần path mới khác path cũ |
| Replanning gain (%) | `100 × (T_A* − T_D*) / T_A*` (công thức Lab 4) |

### 9.3. Biểu đồ nên có
1. Cột: states processed theo bộ não, mỗi nhóm là một số lượng xe.
2. Đường: replan time theo số xe (tìm **điểm giao nhau** giữa A\* và D\* Lite).
3. Cột: số va chạm, S3 vs S4 (halo có hiệu quả không).
4. Hộp (box plot): phân bố path cost trên 10 seed.

### 9.4. Giả thuyết cần kiểm chứng
- **H1**: Khi ít xe, D\* Lite xử lý ít state hơn A\* replan mỗi tick.
- **H2**: Khi nhiều xe (thay đổi lớn mỗi tick), lợi thế của D\* Lite giảm, có thể thua A\* replan khi cần.
- **H3**: Tầm nhìn giới hạn giúp D\* Lite lấy lại lợi thế vì số ô cập nhật mỗi tick giảm.
- **H4**: Halo giảm va chạm nhưng tăng quãng đường đi.
- **H5**: Greedy đi nhanh nhưng va chạm và đi vòng nhiều hơn A\*.

> Kết quả không như giả thuyết cũng **tốt** cho báo cáo, miễn là bạn giải thích được bằng cơ chế (g/rhs, số ô inconsistent, overhead của heap).

---

## 10. Cấu trúc thư mục

```
shipper-game/
├── README.md
├── requirements.txt          # pygame, pandas, matplotlib
├── main.py                   # menu + vòng lặp game
├── config.py                 # tham số mặc định
├── core/
│   ├── world.py              # grid, cost_map, sự kiện kẹt xe/tai nạn
│   ├── entities.py           # Shipper, Order
│   ├── npc.py                # RandomWalker, Patrol, Chaser
│   ├── sensing.py            # cảm biến bán kính r
│   └── metrics.py            # ghi chỉ số mỗi tick
├── ai/
│   ├── common.py             # reconstruct_path, manhattan, heuristics
│   ├── bfs_dfs.py            # Lab 1
│   ├── greedy.py             # Lab 2
│   ├── astar.py              # Lab 3 (A*, Weighted A*, Dijkstra)
│   ├── dstar_lite.py         # Lab 4 + cost_map
│   └── brains.py             # S1..S4 theo interface Brain
├── ui/
│   ├── renderer.py           # vẽ lưới, entity, overlay
│   ├── hud.py                # bảng số liệu
│   └── menu.py               # menu, cài đặt, kết quả
├── experiments/
│   ├── run_benchmark.py      # headless, seed cố định, xuất CSV
│   └── plot_results.py       # vẽ biểu đồ từ CSV
├── results/                  # CSV, hình
└── tests/
    ├── test_validate_path.py
    └── test_dstar_vs_astar.py
```

---

## 11. Kiểm thử

| Kiểm thử | Mục đích |
|---|---|
| `validate_path` trên mọi path | Path không đi qua obstacle, nối đúng start–goal (Lab 1) |
| D\* Lite vs A\* trên cùng snapshot | Cost phải bằng nhau (Lab 4, bài tập 4) |
| Chạy 2 lần cùng seed | Kết quả metrics giống hệt (tái lập được) |
| Goal không reachable | Không crash, trả về "không có đường" |
| Block ô start/goal bởi NPC | Shipper chờ, không lỗi |
| Chạy 1000 tick headless | Không rò bộ nhớ, không treo |

Lỗi hay gặp:
- Quên `move_start()` → D\* Lite đi sai đường.
- Dùng `visited` đơn giản cho A\* với cost thay đổi → mất đường tốt (Lab 3 đã cảnh báo).
- Đo runtime lẫn thời gian vẽ → số liệu sai.
- NPC và shipper dùng chung bộ sinh số ngẫu nhiên → đổi bộ não làm đổi hành vi NPC, so sánh không công bằng. **Mỗi thành phần dùng `random.Random(seed + offset)` riêng**, và nên ghi trước toàn bộ quỹ đạo NPC rồi phát lại để mọi bộ não gặp đúng cùng một môi trường.

---

## 12. Kế hoạch thực hiện (4–5 tuần)

| Tuần | Công việc | Sản phẩm |
|---|---|---|
| 1 | Dựng world + renderer, sinh map, shipper đi bằng A\* trên map tĩnh | Demo shipper đi từ quán tới khách |
| 2 | NPC (3 kiểu), kẹt xe, tai nạn, tầm nhìn, HUD cơ bản | Môi trường động chạy được |
| 3 | Tích hợp `DStarLiteDyn`, interface `Brain`, 4 chiến lược, halo | Đổi bộ não bằng phím số |
| 4 | Đơn hàng, điểm số, menu, màn hình kết quả, click đặt vật cản | Game hoàn chỉnh |
| 5 | Benchmark headless, biểu đồ, viết báo cáo, quay video demo | Báo cáo + repo GitHub |

Nếu làm nhóm, gợi ý chia việc:
- **A**: world, NPC, sự kiện, sensing
- **B**: AI (brains, D\* Lite, benchmark)
- **C**: UI (renderer, HUD, menu)
- **D**: thực nghiệm, biểu đồ, báo cáo

Làm một mình: bỏ mục 7.3, bỏ `Chaser`, chỉ giữ S1, S3, S4, và rút benchmark còn 5 seed.

---

## 13. Dàn ý báo cáo

1. **Giới thiệu**: bài toán đường đi trong môi trường động, động lực smart transportation.
2. **Cơ sở lý thuyết**: tóm tắt BFS/DFS, Greedy, A\*, D\* Lite (g, rhs, key).
3. **Mô hình hóa game**: lưới, cost_map, NPC, sensing.
4. **Thiết kế hệ thống**: kiến trúc, interface Brain, vòng lặp game.
5. **Thực nghiệm**: biến, chỉ số, giả thuyết H1–H5.
6. **Kết quả và thảo luận**: bảng, biểu đồ, giải thích cơ chế, điểm giao nhau.
7. **Hạn chế**: bản đồ nhỏ, NPC đơn giản, tầm nhìn mô phỏng.
8. **Hướng phát triển**: dự đoán quỹ đạo NPC, learned heuristic, nhiều shipper.

---

## 14. Rủi ro và cách xử lý

| Rủi ro | Cách xử lý |
|---|---|
| Code D\* Lite của Lab chạy chậm khi nhiều tick | Bỏ `set(neighbors4())` trong `cost()`, giới hạn kích thước heap, dọn entry stale định kỳ |
| NPC chặn kín đường khiến shipper kẹt mãi | Đặt timeout chờ, cho phép đơn bị hủy, ghi nhận là "thất bại do tắc" |
| Số liệu dao động giữa các lần chạy | Cố định seed, lặp 5 lần runtime, báo cáo trung bình |
| Quá nhiều tính năng, không kịp hạn | Chốt MVP ở mục 7.1 trước, các mục sau chỉ làm khi còn thời gian |
| Pygame chậm khi vẽ nhiều | Vẽ lưới tĩnh vào một surface cache, chỉ vẽ lại ô đổi |

---

## 15. Tài liệu tham khảo (từ 4 lab)

- Lab 1: BFS/DFS, `validate_path`, nguyên tắc benchmark công bằng
- Lab 2: Greedy Best-First, heuristic Manhattan/Euclidean, noisy heuristic
- Lab 3: A\*, `best_g`, stale entry, Weighted A\*, optimality gap
- Lab 4: D\* Lite, g/rhs, priority key, `change_cell`, `move_start`, Replanning gain
