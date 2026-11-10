import math
import pygame

from ai.brains import BRAIN_NAMES, LABELS
from ai.common import manhattan, path_cost, neighbors4

BG = (12, 18, 28)
PANEL = (20, 30, 44)
PANEL_HEADER = (27, 40, 58)
TEXT = (230, 238, 246)
MUTED = (140, 156, 175)
LIME = (191, 242, 103)
BLUE = (70, 190, 255)
ORANGE = (255, 150, 55)
RED = (245, 80, 95)
ROAD_BASE = (38, 48, 60)
ROAD_LINE = (235, 205, 95)
SIDEWALK = (54, 68, 82)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font_name = pygame.font.match_font('segoeui,dejavusans,arial,tahoma')
        self.fonts = {}
        self.buttons = []
        self.map_origin = (32, 96)
        self.cell_size = 24
        self.path_anim_offset = 0.0

    def text(self, text, pos, size=18, color=TEXT, bold=False, shadow=False):
        key = (size, bold)
        if key not in self.fonts:
            self.fonts[key] = pygame.font.Font(self.font_name, size)
            self.fonts[key].set_bold(bold)
        font = self.fonts[key]
        if shadow:
            s_surf = font.render(str(text), True, (10, 14, 20))
            self.screen.blit(s_surf, (pos[0] + 1, pos[1] + 1))
        surface = font.render(str(text), True, color)
        self.screen.blit(surface, pos)
        return surface.get_width()

    def box(self, rect, color=PANEL, radius=12, border_color=None, border_width=1):
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)
        if border_color:
            pygame.draw.rect(self.screen, border_color, rect, border_width, border_radius=radius)

    def button(self, action, label, rect, active=False, primary=False, color_override=None):
        rect = pygame.Rect(rect)
        if color_override:
            col = color_override
        elif active or primary:
            col = LIME
        else:
            col = (34, 48, 66)
        if rect.collidepoint(pygame.mouse.get_pos()) and not (active or primary):
            col = (48, 68, 92)
        self.box(rect, col, 8)
        txt_color = (12, 20, 31) if (active or primary) else TEXT
        self.text(label, (rect.x + 12, rect.y + 8), 15, txt_color, active or primary)
        self.buttons.append((rect, action))

    def action_at(self, pos):
        return next((action for rect, action in reversed(self.buttons) if rect.collidepoint(pos)), None)

    def begin(self):
        self.screen.fill(BG)
        self.buttons = []
        # Header phong cách Sài Gòn hiện đại
        self.text('SHIPPER SÀI GÒN 2D', (32, 18), 28, LIME, True, shadow=True)
        self.text('Game Giao Hàng & Bàn Thí Nghiệm AI • Thành Phố Động 60 FPS', (34, 56), 14, MUTED)

    def draw_setup(self, config, brain, mode='ai'):
        self.begin()
        self.box((32, 95, 595, 595), border_color=(35, 52, 72))
        self.text('Thiết lập chuyến giao hàng', (58, 115), 23, TEXT, True)
        fields = [
            ('seed', 'Seed bản đồ', config.seed),
            ('npc_count', 'Số xe NPC', config.npc_count),
            ('sensing_radius', 'Tầm nhìn radar (ô)', config.sensing_radius),
            ('order_count', 'Số đơn hàng', config.order_count),
            ('density', 'Mật độ nhà phố', f'{config.density:.0%}'),
            ('max_ticks', 'Giới hạn tick', config.max_ticks)
        ]
        for i, (field, label, value) in enumerate(fields):
            y = 165 + i * 52
            self.text(label, (60, y + 8), 16, MUTED)
            self.text(value, (340, y + 6), 19, TEXT, True)
            self.button(('adjust', field, -1), '−', (450, y, 48, 36))
            self.button(('adjust', field, 1), '+', (510, y, 48, 36))

        # Nút chọn chế độ chơi ngay từ đầu
        self.text('Chế độ chơi:', (60, 492), 16, MUTED)
        self.button(('mode', 'ai'), '🤖 AI Tự Lái (Autopilot)', (175, 486, 210, 36), mode == 'ai')
        self.button(('mode', 'manual'), '🎮 Lái Tay (WASD)', (395, 486, 175, 36), mode == 'manual')

        self.button('start', '▶ BẮT ĐẦU GIAO HÀNG', (60, 545, 275, 46), primary=True)
        self.button('compare', '📊 SO SÁNH 7 BỘ NÃO', (60, 605, 275, 42))

        # Panel bên phải: Chọn não AI
        self.box((652, 95, 595, 595), border_color=(35, 52, 72))
        self.text('Chọn bộ não AI dẫn đường', (680, 115), 23, TEXT, True)
        for i, name in enumerate(BRAIN_NAMES):
            self.button(('brain', name), f'{i + 1}   {LABELS[name]}',
                        (680, 165 + i * 46, 537, 38), name == brain)

        self.text('Cùng một bản đồ • Cùng chuỗi giao thông và sự kiện động.', (680, 505), 15, MUTED)
        self.text('Thuật toán tự phát triển Lab 1–4; hiển thị đường dẫn GPS trực quan.', (680, 532), 14, MUTED)
        self.text('Phím: Space (Chạy/Dừng) • M (Chuyển Lái Tay / AI) • H (Còi bim bim)', (680, 565), 14, BLUE)
        self.text('Phím: 1–7 (Đổi Não) • W (Thời Tiết) • S (Âm Thanh) • Esc (Cài đặt)', (680, 595), 14, BLUE)

        self.text('Bản quyền © Shipper Sài Gòn • Đồ họa 2D & Thuật toán tìm đường tối ưu', (32, 720), 13, MUTED)

    def cell_rect(self, cell):
        r, c = cell
        return pygame.Rect(self.map_origin[0] + c * self.cell_size,
                           self.map_origin[1] + r * self.cell_size,
                           self.cell_size, self.cell_size)

    def center(self, cell):
        return self.cell_rect(cell).center

    def grid_cell(self, point, world):
        c = (point[0] - self.map_origin[0]) // self.cell_size
        r = (point[1] - self.map_origin[1]) // self.cell_size
        return (r, c) if 0 <= r < world.rows and 0 <= c < world.cols else None

    # --- HỆ THỐNG VẼ ĐỒ HỌA 2D CHI TIẾT ---

    def draw_road_cell(self, cell, world, cost):
        """Vẽ mặt đường đô thị Sài Gòn với vạch tim đường và vỉa hè."""
        rect = self.cell_rect(cell)
        r, c = cell

        # Màu nền đường theo tình trạng giao thông
        if math.isinf(cost):
            base_col = (130, 45, 60)   # Chặn hoàn toàn / Tai nạn
        elif cost >= 5:
            base_col = (165, 88, 38)   # Kẹt xe nặng
        elif cost > 1:
            base_col = (128, 85, 45)   # Đông đúc
        else:
            base_col = ROAD_BASE       # Bình thường

        pygame.draw.rect(self.screen, base_col, rect)

        # Viền vỉa hè nếu tiếp giáp nhà
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (nr, nc) in world.walls or nr < 0 or nr >= world.rows or nc < 0 or nc >= world.cols:
                if dr == -1:
                    pygame.draw.line(self.screen, SIDEWALK, rect.topleft, rect.topright, 2)
                elif dr == 1:
                    pygame.draw.line(self.screen, SIDEWALK, rect.bottomleft, rect.bottomright, 2)
                elif dc == -1:
                    pygame.draw.line(self.screen, SIDEWALK, rect.topleft, rect.bottomleft, 2)
                elif dc == 1:
                    pygame.draw.line(self.screen, SIDEWALK, rect.topright, rect.bottomright, 2)

        # Vạch kẻ tim đường vàng đứt nét
        cx, cy = rect.center
        if cost <= 3:
            # Ngang
            if (r, c - 1) not in world.walls and (r, c + 1) not in world.walls:
                pygame.draw.line(self.screen, (220, 185, 75), (cx - 4, cy), (cx + 4, cy), 1)
            # Dọc
            if (r - 1, c) not in world.walls and (r + 1, c) not in world.walls:
                pygame.draw.line(self.screen, (220, 185, 75), (cx, cy - 4), (cx, cy + 4), 1)

        # Nếu là ô chướng ngại vật nhân tạo hoặc tai nạn (Lô cốt đường)
        if cell in world.manual_blocks or math.isinf(cost):
            self.draw_construction_barrier(rect)

    def draw_construction_barrier(self, rect):
        """Vẽ rào chắn lô cốt công trình sọc vàng - đen."""
        barr_rect = rect.inflate(-6, -6)
        pygame.draw.rect(self.screen, (30, 30, 30), barr_rect, border_radius=2)
        # Sọc vàng cảnh báo
        for i in range(0, barr_rect.width + barr_rect.height, 8):
            start = (barr_rect.x + i, barr_rect.y)
            end = (barr_rect.x, barr_rect.y + i)
            pygame.draw.line(self.screen, (245, 200, 30), start, end, 2)
        pygame.draw.rect(self.screen, (240, 60, 60), barr_rect, 1, border_radius=2)
        # Đèn chớp đỏ vàng
        pygame.draw.circle(self.screen, (255, 60, 60), (barr_rect.x + 4, barr_rect.y + 4), 2)
        pygame.draw.circle(self.screen, (255, 210, 40), (barr_rect.right - 4, barr_rect.y + 4), 2)

    def draw_building(self, cell):
        """Vẽ nhà phố Sài Gòn (mái tôn, bồn nước, ban công)."""
        rect = self.cell_rect(cell)
        # Bóng đổ nhẹ góc đông nam
        pygame.draw.rect(self.screen, (10, 16, 24), rect.move(2, 2), border_radius=3)
        # Khối tường nhà
        pygame.draw.rect(self.screen, (50, 65, 82), rect, border_radius=3)
        # Mái nhà tông màu ngói xám / xanh rêu
        roof_rect = rect.inflate(-4, -4)
        pygame.draw.rect(self.screen, (68, 86, 105), roof_rect, border_radius=2)
        # Bồn nước inox tròn trên mái
        cx, cy = roof_rect.center
        pygame.draw.circle(self.screen, (170, 195, 215), (cx - 3, cy - 3), 3)
        pygame.draw.circle(self.screen, (220, 240, 255), (cx - 4, cy - 4), 1)
        # Ô cửa thông gió / ban công nhỏ
        pygame.draw.rect(self.screen, (40, 52, 66), (cx + 1, cy + 1, 4, 4))

    def draw_pickup_store(self, cell, active=False, radar_phase=0.0):
        """Vẽ quán cà phê / quán ăn Sài Gòn (Điểm lấy hàng)."""
        rect = self.cell_rect(cell)
        cx, cy = rect.center

        # Radar sóng tỏa ra nếu là đơn đang chờ đến lấy
        if active:
            rad = int(8 + 14 * radar_phase)
            alpha = int(220 * (1.0 - radar_phase))
            radar_surf = pygame.Surface((rad * 2 + 4, rad * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(radar_surf, (255, 200, 60, alpha), (rad + 2, rad + 2), rad, 2)
            self.screen.blit(radar_surf, (cx - rad - 2, cy - rad - 2))

        # Mái bạt sọc vàng - cam của quán
        store_rect = rect.inflate(-4, -4)
        pygame.draw.rect(self.screen, (245, 175, 45), store_rect, border_radius=4)
        # Sọc mái bạt
        for offset in range(-store_rect.width // 2, store_rect.width // 2, 4):
            pygame.draw.line(self.screen, (220, 95, 30),
                             (cx + offset, store_rect.top), (cx + offset, store_rect.bottom), 2)
        # Biển hiệu tròn chữ P
        pygame.draw.circle(self.screen, (25, 35, 45), (cx, cy), 7)
        self.text('P', (cx - 4, cy - 6), 11, (255, 215, 60), True)

    def draw_customer_house(self, cell, active=False, delivered=False, radar_phase=0.0):
        """Vẽ nhà khách hàng (Mái ngói, cửa, đèn, hiệu ứng radar)."""
        rect = self.cell_rect(cell)
        cx, cy = rect.center

        # Radar xanh lá hướng dẫn khi là đích giao hiện tại
        if active:
            rad = int(8 + 16 * radar_phase)
            alpha = int(230 * (1.0 - radar_phase))
            radar_surf = pygame.Surface((rad * 2 + 4, rad * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(radar_surf, (191, 242, 103, alpha), (rad + 2, rad + 2), rad, 2)
            self.screen.blit(radar_surf, (cx - rad - 2, cy - rad - 2))

        col_base = (35, 58, 48) if active else ((45, 60, 52) if delivered else (40, 55, 48))
        pygame.draw.rect(self.screen, col_base, rect.inflate(-2, -2), border_radius=4)

        # Mái ngói hình tam giác
        roof_color = LIME if active else ((120, 145, 115) if delivered else (150, 205, 135))
        pygame.draw.polygon(self.screen, roof_color,
                            [(cx, cy - 10), (cx - 9, cy - 2), (cx + 9, cy - 2)])
        # Thân nhà
        pygame.draw.rect(self.screen, roof_color, (cx - 7, cy - 2, 14, 11), border_radius=2)
        # Cửa nhà
        pygame.draw.rect(self.screen, (25, 40, 32), (cx - 2, cy + 2, 4, 7))
        # Đèn hiên nhà ấm áp
        pygame.draw.circle(self.screen, (255, 240, 150), (cx + 4, cy), 2)

        if active:
            pygame.draw.rect(self.screen, LIME, rect.inflate(2, 2), 2, border_radius=6)

    def draw_shipper(self, x, y, angle=0, score_boost=False):
        """Vẽ xe máy Shipper Sài Gòn (Top-down motorcycle sprite 60 FPS)."""
        # Ánh đèn pha phía trước xe (Headlight glow cone)
        rad_angle = math.radians(angle)
        dx = -math.sin(rad_angle)
        dy = -math.cos(rad_angle)
        cone_length = 26
        spread = 0.55
        p1 = (x, y)
        p2 = (x + (dx * math.cos(spread) - dy * math.sin(spread)) * cone_length,
              y + (dx * math.sin(spread) + dy * math.cos(spread)) * cone_length)
        p3 = (x + (dx * math.cos(-spread) - dy * math.sin(-spread)) * cone_length,
              y + (dx * math.sin(-spread) + dy * math.cos(-spread)) * cone_length)

        light_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(light_surf, (255, 250, 180, 55), [p1, p2, p3])
        self.screen.blit(light_surf, (0, 0))

        # Tạo surface xe để xoay mượt mà
        surf_size = 32
        m_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        scx, scy = surf_size // 2, surf_size // 2

        # Bánh trước & bánh sau (Màu lốp đen)
        pygame.draw.rect(m_surf, (15, 15, 15), (scx - 2, scy - 12, 4, 7), border_radius=2)
        pygame.draw.rect(m_surf, (15, 15, 15), (scx - 2, scy + 5, 4, 7), border_radius=2)

        # Khung xe máy (Bạc / Xám đen)
        pygame.draw.rect(m_surf, (50, 60, 70), (scx - 3, scy - 8, 6, 16), border_radius=3)
        # Ghi đông tay lái
        pygame.draw.line(m_surf, (180, 190, 200), (scx - 7, scy - 7), (scx + 7, scy - 7), 2)
        # Hai gương chiếu hậu tròn
        pygame.draw.circle(m_surf, (200, 220, 240), (scx - 8, scy - 8), 1)
        pygame.draw.circle(m_surf, (200, 220, 240), (scx + 8, scy - 8), 1)

        # Nón bảo hiểm Shipper (Màu xanh lá thương hiệu công nghệ)
        pygame.draw.circle(m_surf, (35, 180, 85), (scx, scy - 2), 5)
        # Kính nón bảo hiểm
        pygame.draw.line(m_surf, (230, 245, 255), (scx - 3, scy - 4), (scx + 3, scy - 4), 2)

        # Thùng giao hàng phía sau xe (Delivery box màu cam nổi bật)
        box_col = ORANGE if not score_boost else (255, 220, 60)
        pygame.draw.rect(m_surf, box_col, (scx - 5, scy + 3, 10, 8), border_radius=2)
        pygame.draw.rect(m_surf, (240, 240, 240), (scx - 3, scy + 5, 6, 4), border_radius=1)

        # Xoay surface theo hướng di chuyển
        rotated = pygame.transform.rotate(m_surf, -angle)
        rot_rect = rotated.get_rect(center=(int(x), int(y)))
        self.screen.blit(rotated, rot_rect)

    def draw_npc(self, x, y, angle=0, npc_type='motor'):
        """Vẽ NPC giao thông (Xe máy, ô tô, taxi, xe tải nhỏ)."""
        surf_size = 32
        n_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        scx, scy = surf_size // 2, surf_size // 2

        if npc_type == 'car':
            # Ô tô sedan đỏ / xám
            pygame.draw.rect(n_surf, (215, 65, 75), (scx - 6, scy - 12, 12, 24), border_radius=4)
            # Kính xe trước & sau
            pygame.draw.rect(n_surf, (150, 205, 240), (scx - 4, scy - 6, 8, 4), border_radius=1)
            pygame.draw.rect(n_surf, (150, 205, 240), (scx - 4, scy + 4, 8, 3), border_radius=1)
            # Đèn trước vàng, đèn sau đỏ
            pygame.draw.circle(n_surf, (255, 240, 160), (scx - 4, scy - 11), 1)
            pygame.draw.circle(n_surf, (255, 240, 160), (scx + 4, scy - 11), 1)
        elif npc_type == 'taxi':
            # Taxi vàng rực
            pygame.draw.rect(n_surf, (245, 195, 35), (scx - 6, scy - 12, 12, 24), border_radius=4)
            # Bảng taxi nóc xe
            pygame.draw.rect(n_surf, (20, 20, 20), (scx - 3, scy - 1, 6, 3), border_radius=1)
            # Kính xe
            pygame.draw.rect(n_surf, (140, 195, 230), (scx - 4, scy - 7, 8, 4), border_radius=1)
        else:
            # Xe máy người dân
            pygame.draw.rect(n_surf, (20, 20, 20), (scx - 2, scy - 10, 4, 6), border_radius=2)
            pygame.draw.rect(n_surf, (20, 20, 20), (scx - 2, scy + 4, 4, 6), border_radius=2)
            pygame.draw.rect(n_surf, (70, 80, 90), (scx - 3, scy - 7, 6, 14), border_radius=3)
            # Người lái nón bảo hiểm đỏ
            pygame.draw.circle(n_surf, (235, 75, 75), (scx, scy - 1), 4)

        rotated = pygame.transform.rotate(n_surf, -angle)
        rot_rect = rotated.get_rect(center=(int(x), int(y)))
        self.screen.blit(rotated, rot_rect)

    def draw_path(self, path, costs):
        """Vẽ đường dẫn GPS phát sáng chuyển động nhịp nhàng như Google Maps."""
        if not path or len(path) < 2:
            return
        points = [self.center(cell) for cell in path]

        # 1. Đường phát sáng mờ nền (Ambient Cyan Glow)
        glow_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        pygame.draw.lines(glow_surf, (60, 180, 255, 60), False, points, 7)
        self.screen.blit(glow_surf, (0, 0))

        # 2. Đường chính (Core GPS Route Line)
        pygame.draw.lines(self.screen, BLUE, False, points, 3)

        # 3. Các hạt sáng chuyển động dọc tuyến đường (Flowing Dots)
        self.path_anim_offset = (self.path_anim_offset + 0.05) % 1.0
        for i in range(len(points) - 1):
            p_a = points[i]
            p_b = points[i + 1]
            t = (self.path_anim_offset + i * 0.4) % 1.0
            dot_x = p_a[0] + (p_b[0] - p_a[0]) * t
            dot_y = p_a[1] + (p_b[1] - p_a[1]) * t
            pygame.draw.circle(self.screen, (255, 255, 255), (int(dot_x), int(dot_y)), 2)

    def draw_game(self, sim, paused, show_visited, show_sensing, speed,
                  effects=None, control_mode='ai', audio_on=True,
                  shipper_screen_pos=None, npc_screen_positions=None,
                  shipper_angle=0, npc_angles=None):
        """Vẽ toàn bộ game với đồ họa 2D, hiệu ứng và HUD hiện đại."""
        self.begin()
        self.cell_size = min(24, 600 // max(sim.world.rows, sim.world.cols))
        world = sim.world
        radar_p = effects.radar_phase if effects else 0.0

        # Header trạng thái
        mode_label = '🎮 LÁI TAY (MANUAL)' if control_mode == 'manual' else '🤖 TỰ ĐỘNG (AI)'
        status = 'HOÀN THÀNH' if sim.finished else ('TẠM DỪNG' if paused else mode_label)
        status_col = LIME if control_mode == 'ai' else BLUE
        self.text(status, (1020, 24), 16, status_col, True, shadow=True)

        # 1. Vẽ bản đồ nền: Đường phố, Tòa nhà, Lô cốt
        for r in range(world.rows):
            for c in range(world.cols):
                cell = (r, c)
                if cell in world.walls:
                    self.draw_building(cell)
                else:
                    cost = world.terrain_cost(cell)
                    self.draw_road_cell(cell, world, cost)

                # Lớp mờ che vùng ngoài tầm nhìn (Fog of war)
                if show_sensing and cell not in sim.visible and cell not in world.walls:
                    rect = self.cell_rect(cell)
                    fog = pygame.Surface(rect.size, pygame.SRCALPHA)
                    fog.fill((6, 12, 20, 95))
                    self.screen.blit(fog, rect)

        # 2. Vẽ các ô đã xử lý nếu bật 'V'
        if show_visited and hasattr(sim.brain, 'last_result') and sim.brain.last_result:
            for cell in sim.brain.last_result.expanded_cells:
                pygame.draw.circle(self.screen, (185, 135, 240), self.center(cell), 3)

        # 3. Vẽ lộ trình GPS tìm đường
        if sim.brain.path and len(sim.brain.path) > 1:
            self.draw_path(sim.brain.path, sim.brain.costs)

        # 4. Vẽ các điểm nhận hàng (Quán ăn) và giao hàng (Nhà khách)
        for order in sorted(world.orders, key=lambda o: o is sim.current):
            is_active_drop = (order is sim.current and sim.stage == 'dropoff')
            is_active_pick = (order is sim.current and sim.stage == 'pickup')

            self.draw_customer_house(order.dropoff, is_active_drop,
                                     order.status == 'delivered', radar_p)
            if order.status in ('pending', 'picked'):
                if order.status == 'pending':
                    self.draw_pickup_store(order.pickup, is_active_pick, radar_p)

        # 5. Vẽ xe NPC với nội suy tọa độ 60 FPS
        npc_types = ['motor', 'car', 'taxi', 'motor', 'car']
        for i, pos in enumerate(world.traffic.positions):
            if npc_screen_positions and i < len(npc_screen_positions):
                nx, ny = npc_screen_positions[i]
            else:
                nx, ny = self.center(pos)
            n_angle = npc_angles[i] if (npc_angles and i < len(npc_angles)) else 0
            n_type = npc_types[i % len(npc_types)]
            self.draw_npc(nx, ny, n_angle, n_type)

        # 6. Vẽ Shipper với nội suy tọa độ và đèn pha 60 FPS
        if shipper_screen_pos:
            sx, sy = shipper_screen_pos
        else:
            sx, sy = self.center(sim.shipper.pos)
        self.draw_shipper(sx, sy, shipper_angle)

        # Đích đến hiện tại: Hiển thị nhãn nổi bật
        if sim.goal:
            goal_rect = self.cell_rect(sim.goal)
            if sim.stage == 'dropoff' and sim.current:
                label = f'NHÀ KHÁCH #{sim.current.id:02d}'
                lx = min(max(32, goal_rect.x - 40), 480)
                ly = max(95, goal_rect.y - 26)
                self.box((lx - 4, ly - 2, 140, 22), (22, 44, 34), 5, border_color=LIME)
                self.text(label, (lx, ly), 12, LIME, True)

        # 7. Vẽ các hiệu ứng Hạt & Mưa
        if effects:
            effects.draw_particles(self.screen)
            effects.draw_rain(self.screen)
            effects.draw_floating_texts(self.screen, self.font_name)

        # --- GIAO DIỆN HUD BẢNG ĐIỀU KHIỂN (RIGHT PANEL) ---
        self.draw_hud(sim, paused, speed, control_mode, audio_on, effects)

    def draw_hud(self, sim, paused, speed, control_mode, audio_on, effects):
        world = sim.world

        # Panel 1: Thẻ tài xế & Chỉ số chính
        self.box((660, 95, 588, 92), border_color=(35, 52, 70))
        stats = [
            ('ĐIỂM THƯỞNG', f'{sim.shipper.score}', LIME),
            ('THỜI GIAN', f'{sim.tick}/{sim.config.max_ticks}', TEXT),
            ('ĐƠN ĐÃ GIAO', f"{sum(o.status == 'delivered' for o in world.orders)}/{len(world.orders)}", BLUE),
            ('TỐC ĐỘ', f'{speed}×', TEXT)
        ]
        for i, (label, value, col) in enumerate(stats):
            self.text(label, (678 + i * 142, 108), 12, MUTED, True)
            self.text(value, (678 + i * 142, 134), 22, col, True)

        # Thanh tiến độ Deadline của đơn hàng hiện tại
        if sim.current and sim.current.status in ('pending', 'picked'):
            total_time = sim.current.deadline - sim.current.release_tick
            rem_time = max(0, sim.current.deadline - sim.tick)
            ratio = min(1.0, max(0.0, rem_time / max(1, total_time)))
            bar_col = LIME if ratio > 0.4 else (ORANGE if ratio > 0.15 else RED)
            bar_w = int(552 * ratio)
            pygame.draw.rect(self.screen, (30, 42, 54), (678, 168, 552, 6), border_radius=3)
            pygame.draw.rect(self.screen, bar_col, (678, 168, bar_w, 6), border_radius=3)

        # Panel 2: Bộ não AI
        self.box((660, 196, 588, 205), border_color=(35, 52, 70))
        self.text('BỘ NÃO AI DẪN ĐƯỜNG', (679, 208), 13, MUTED, True)
        for i, name in enumerate(BRAIN_NAMES):
            col, row = i % 2, i // 2
            self.button(('brain', name), f'{i + 1}  {LABELS[name]}',
                        (677 + col * 282, 235 + row * 38, 272, 32), sim.brain.name == name)

        # Panel 3: Phân tích thuật toán & Hiệu năng
        self.box((660, 410, 588, 142), border_color=(35, 52, 70))
        remaining = path_cost(sim.brain.path, sim.brain.costs)
        fields = [
            ('Cost còn lại', '∞' if math.isinf(remaining) else f'{remaining:.0f}'),
            ('States / tick', sim.last_processed),
            ('Plan / tick', f'{sim.last_ms:.3f} ms'),
            ('Tổng states', sim.metrics.states_processed),
            ('Lần lập lại', sim.metrics.replans),
            ('Chặn / Tiếp xúc', f'{sim.metrics.blocked_attempts} / {sim.metrics.npc_contacts}')
        ]
        for i, (label, value) in enumerate(fields):
            col, row = i % 3, i // 3
            x0, y0 = 678 + col * 188, 424 + row * 58
            self.text(label, (x0, y0), 12, MUTED)
            self.text(str(value), (x0, y0 + 19), 19, BLUE, True)

        # Panel 4: Danh sách đơn hàng
        self.box((660, 560, 588, 98), border_color=(35, 52, 70))
        if sim.current:
            if sim.stage == 'pickup':
                heading = f'ĐẾN QUÁN LẤY ĐƠN #{sim.current.id:02d} (Biểu tượng P)'
            else:
                heading = f'GIAO ĐẾN NHÀ KHÁCH #{sim.current.id:02d}'
            h_col = LIME
        else:
            heading = 'CHỜ PHÂN PHỐI ĐƠN HÀNG MỚI'
            h_col = MUTED
        self.text(heading, (678, 570), 13, h_col, True)

        translations = {
            'scheduled': 'chưa mở', 'pending': 'chờ lấy', 'picked': 'đang giao',
            'delivered': 'đã giao', 'cancelled': 'đã hủy'
        }
        displayed = [sim.current] if sim.current else []
        displayed += [o for o in world.orders if o is not sim.current]
        for i, order in enumerate(displayed[:3]):
            st_text = translations.get(order.status, order.status)
            color = LIME if order is sim.current else TEXT
            self.text(f'#{order.id:02d}  •  {st_text}  •  hạn chót tick {order.deadline}',
                      (678, 594 + i * 19), 13, color)

        # Hàng nút điều khiển tương tác bên dưới
        self.button('pause', '▶ Tiếp tục' if paused else '⏸ Tạm dừng', (660, 668, 105, 34))
        self.button('toggle_mode', '🎮 Lái tay' if control_mode == 'ai' else '🤖 Tự lái',
                    (772, 668, 100, 34), color_override=(55, 90, 120))
        self.button('honk', '📢 Còi xe', (879, 668, 85, 34), color_override=(110, 75, 45))
        self.button('audio', '🔊 Bật' if audio_on else '🔇 Tắt', (971, 668, 75, 34))
        rain_on = effects.rain_enabled if effects else False
        self.button('weather', '🌧 Mưa' if rain_on else '☀ Nắng', (1053, 668, 85, 34))
        self.button('setup', '⚙ Cài đặt', (1145, 668, 102, 34))

        # Ghi chú hướng dẫn phím tắt dưới chân màn hình
        self.text('Phím: [M] Đổi Lái tay / Tự lái • [H] Bấm còi • [WASD/Mũi tên] Lái xe • [V] States • [T] Tầm nhìn',
                  (32, 708), 12, MUTED)
        self.text('Chuột trái: Thêm/Xóa lô cốt • Chuột phải: Tạo điểm kẹt xe • [+/-] Tốc độ • [R] Chơi lại',
                  (32, 728), 12, MUTED)

    def draw_compare(self, rows, done, total, error):
        self.begin()
        self.box((32, 95, 1216, 595), border_color=(35, 52, 72))
        self.text('So sánh 7 bộ não AI • Cùng seed, cùng xe NPC và sự kiện', (58, 118), 24, TEXT, True)
        self.text(f'{done}/{total} lượt hoàn tất' if not error else error, (58, 160), 16, BLUE)

        headers = [
            ('BỘ NÃO', 58), ('ĐÃ GIAO', 380), ('ĐÚNG HẠN', 510),
            ('TỔNG STATES', 660), ('PLAN (ms)', 860), ('COST ĐÃ ĐI', 1040)
        ]
        for label, x in headers:
            self.text(label, (x, 210), 13, MUTED, True)

        for i, record in enumerate(rows[-7:]):
            y = 252 + i * 46
            if i % 2 == 0:
                self.box((49, y - 6, 1180, 40), (26, 38, 52), 6)
            values = [
                (LABELS.get(record['brain'], record['brain']), 58),
                (f"{record['delivered']}/{record['orders']}", 380),
                (f"{record['on_time_rate']:.0%}", 510),
                (record['states_processed'], 660),
                (f"{record['planning_ms']:.2f}", 860),
                (f"{record['travel_cost']:.0f}", 1040)
            ]
            for value, x in values:
                self.text(str(value), (x, y), 15, TEXT)

        self.text('Kiểm nghiệm học thuật khách quan; chi phí di chuyển khớp theo cùng trạng thái.', (58, 625), 14, MUTED)
        self.button('setup', '⮌ Về cài đặt', (58, 650, 150, 36))
