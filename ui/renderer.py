import math

import pygame

from ai.brains import BRAIN_NAMES, LABELS
from ai.common import manhattan, path_cost


BG = (12, 20, 31)
PANEL = (22, 33, 47)
TEXT = (227, 235, 243)
MUTED = (145, 161, 179)
LIME = (191, 242, 103)
BLUE = (91, 186, 255)
ORANGE = (244, 153, 61)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.font_name = pygame.font.match_font('segoeui,dejavusans,arial')
        self.fonts = {}
        self.buttons = []
        self.map_origin = (32, 100)
        self.cell_size = 24

    def text(self, text, pos, size=18, color=TEXT, bold=False):
        key = size, bold
        if key not in self.fonts:
            self.fonts[key] = pygame.font.Font(self.font_name, size)
            self.fonts[key].set_bold(bold)
        surface = self.fonts[key].render(str(text), True, color)
        self.screen.blit(surface, pos)
        return surface.get_width()

    def box(self, rect, color=PANEL, radius=14):
        pygame.draw.rect(self.screen, color, rect, border_radius=radius)

    def button(self, action, label, rect, active=False, primary=False):
        rect = pygame.Rect(rect)
        color = LIME if active or primary else (35, 50, 69)
        if rect.collidepoint(pygame.mouse.get_pos()) and not (active or primary):
            color = (48, 68, 90)
        self.box(rect, color, 9)
        self.text(label, (rect.x + 13, rect.y + 9), 16, BG if active or primary else TEXT,
                  active or primary)
        self.buttons.append((rect, action))

    def action_at(self, pos):
        return next((action for rect, action in reversed(self.buttons) if rect.collidepoint(pos)), None)

    def begin(self):
        self.screen.fill(BG)
        self.buttons = []
        self.text('SHIPPER SÀI GÒN', (32, 22), 30, LIME, True)
        self.text('Tìm đường thông minh • Thành phố luôn chuyển động', (34, 63), 16, MUTED)

    def draw_setup(self, config, brain):
        self.begin()
        self.box((32, 113, 595, 568))
        self.text('Thiết lập chuyến giao hàng', (58, 134), 25, TEXT, True)
        fields = [('seed', 'Seed bản đồ', config.seed), ('npc_count', 'Số xe NPC', config.npc_count),
                  ('sensing_radius', 'Tầm nhìn (ô)', config.sensing_radius),
                  ('order_count', 'Số đơn hàng', config.order_count),
                  ('density', 'Mật độ nhà', f'{config.density:.0%}'),
                  ('max_ticks', 'Giới hạn tick', config.max_ticks)]
        for i, (field, label, value) in enumerate(fields):
            y = 191 + i * 55
            self.text(label, (60, y + 9), 18, MUTED)
            self.text(value, (350, y + 8), 20, TEXT, True)
            self.button(('adjust', field, -1), '−', (460, y, 50, 38))
            self.button(('adjust', field, 1), '+', (524, y, 50, 38))
        self.button('start', 'BẮT ĐẦU GIAO HÀNG', (60, 548, 280, 47), primary=True)
        self.button('compare', 'SO SÁNH CÙNG SEED', (60, 610, 280, 43))
        self.box((652, 113, 595, 568))
        self.text('Chọn bộ não AI', (680, 137), 25, TEXT, True)
        for i, name in enumerate(BRAIN_NAMES):
            self.button(('brain', name), f'{i + 1}   {LABELS[name]}', (680, 191 + i * 48, 537, 39), name == brain)
        self.text('Cùng một bản đồ. Cùng chuỗi xe và sự kiện.', (680, 560), 17, MUTED)
        self.text('Tự cài thuật toán từ Lab 1–4; không dùng API bản đồ.', (680, 590), 16, MUTED)
        self.text('Phím Space: chạy / dừng • Esc: trở về cài đặt', (680, 623), 16, BLUE)
        self.text('MVP 0.1.1 • Python + Pygame • Seed tái lập được, runtime có dao động', (32, 719), 15, MUTED)

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

    def customer_house(self, cell, active=False, delivered=False):
        rect = self.cell_rect(cell)
        x, y = rect.center
        color = LIME if active else ((115, 137, 111) if delivered else (145, 191, 128))
        pygame.draw.rect(self.screen, (32, 55, 46), rect.inflate(-2, -2), border_radius=4)
        pygame.draw.polygon(self.screen, color, [(x, y - 9), (x - 9, y - 1), (x + 9, y - 1)])
        pygame.draw.rect(self.screen, color, (x - 7, y - 1, 14, 10), border_radius=1)
        pygame.draw.rect(self.screen, (25, 47, 42), (x - 2, y + 3, 4, 6))
        pygame.draw.rect(self.screen, TEXT, (x + 3, y + 1, 3, 3))
        if active:
            pygame.draw.rect(self.screen, LIME, rect.inflate(2, 2), 2, border_radius=5)

    def draw_game(self, sim, paused, show_visited, show_sensing, speed):
        self.begin()
        self.cell_size = min(24, 600 // max(sim.world.rows, sim.world.cols))
        status = 'HOÀN THÀNH' if sim.finished else ('TẠM DỪNG' if paused else 'ĐANG GIAO')
        self.text(status, (1020, 28), 17, LIME, True)
        world = sim.world
        for r in range(world.rows):
            for c in range(world.cols):
                cell = r, c
                rect = self.cell_rect(cell)
                cost = world.terrain_cost(cell)
                if cell in world.walls:
                    color = (46, 62, 77)
                elif math.isinf(cost):
                    color = (125, 47, 64)
                elif cost > 1:
                    color = (163, 92, 36) if cost >= 5 else (126, 88, 46)
                else:
                    color = (67, 83, 97)
                pygame.draw.rect(self.screen, color, rect.inflate(-1, -1), border_radius=3)
                if cell in world.walls:
                    pygame.draw.rect(self.screen, (66, 83, 98), rect.inflate(-8, -8), 1, border_radius=2)
                if show_sensing and cell not in sim.visible and cell not in world.walls:
                    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                    overlay.fill((8, 16, 28, 78))
                    self.screen.blit(overlay, rect)
        if show_visited:
            for cell in sim.brain.last_result.expanded_cells:
                pygame.draw.circle(self.screen, (177, 130, 222), self.center(cell), 3)
        if sim.brain.path and len(sim.brain.path) > 1:
            pygame.draw.lines(self.screen, BLUE, False, [self.center(cell) for cell in sim.brain.path], 3)
        for order in sorted(world.orders, key=lambda o: o is sim.current):
            active_home = order is sim.current and sim.stage == 'dropoff'
            self.customer_house(order.dropoff, active_home, order.status == 'delivered')
            if order.status in ('pending', 'picked'):
                if order.status == 'pending':
                    rect = self.cell_rect(order.pickup).inflate(-7, -7)
                    pygame.draw.rect(self.screen, (244, 200, 86), rect, border_radius=4)
                    self.text('P', (rect.x + 3, rect.y - 2), 12, BG, True)
        for npc in world.traffic.positions:
            rect = self.cell_rect(npc).inflate(-8, -6)
            pygame.draw.rect(self.screen, (242, 99, 112), rect, border_radius=4)
            pygame.draw.rect(self.screen, (89, 38, 52), (rect.x + 3, rect.y + 3, rect.width - 6, 4), border_radius=1)
        x, y = self.center(sim.shipper.pos)
        pygame.draw.circle(self.screen, BG, (x, y), 12)
        pygame.draw.circle(self.screen, BLUE, (x, y), 9)
        pygame.draw.polygon(self.screen, TEXT, [(x, y - 5), (x - 4, y + 4), (x + 4, y + 4)])
        if sim.goal:
            pygame.draw.rect(self.screen, TEXT, self.cell_rect(sim.goal).inflate(-2, -2), 2, border_radius=5)
            if sim.stage == 'dropoff':
                rect = self.cell_rect(sim.goal)
                label = f'NHÀ KHÁCH #{sim.current.id:02d}'
                label_x = min(max(32, rect.x - 48), 480)
                label_y = max(100, rect.y - 28)
                self.box((label_x - 4, label_y - 2, 150, 24), (24, 45, 37), 5)
                self.text(label, (label_x, label_y), 13, LIME, True)
        self.box((660, 100, 588, 90))
        stats = [('ĐIỂM', sim.shipper.score), ('TICK', f'{sim.tick}/{sim.config.max_ticks}'),
                 ('ĐÃ GIAO', f"{sum(o.status == 'delivered' for o in world.orders)}/{len(world.orders)}"), ('TỐC ĐỘ', f'{speed}×')]
        for i, (label, value) in enumerate(stats):
            self.text(label, (678 + i * 142, 114), 12, MUTED, True)
            self.text(value, (678 + i * 142, 141), 24, LIME if i == 0 else TEXT, True)
        self.box((660, 204, 588, 214))
        self.text('BỘ NÃO AI', (679, 218), 14, MUTED, True)
        for i, name in enumerate(BRAIN_NAMES):
            col, row = i % 2, i // 2
            self.button(('brain', name), f'{i + 1}  {LABELS[name]}',
                        (677 + col * 282, 248 + row * 39, 272, 33), sim.brain.name == name)
        self.box((660, 432, 588, 149))
        remaining = path_cost(sim.brain.path, sim.brain.costs)
        fields = [('Cost còn lại', '∞' if math.isinf(remaining) else f'{remaining:.0f}'),
                  ('States / tick', sim.last_processed), ('Plan / tick', f'{sim.last_ms:.3f} ms'),
                  ('Tổng states', sim.metrics.states_processed), ('Lần lập lại', sim.metrics.replans),
                  ('Bị chặn / tiếp xúc', f'{sim.metrics.blocked_attempts} / {sim.metrics.npc_contacts}')]
        for i, (label, value) in enumerate(fields):
            col, row = i % 3, i // 3
            x0, y0 = 678 + col * 188, 449 + row * 63
            self.text(label, (x0, y0), 13, MUTED)
            self.text(value, (x0, y0 + 22), 21, BLUE, True)
        self.box((660, 595, 588, 104))
        heading = f'ĐÍCH: NHÀ KHÁCH #{sim.current.id:02d}' if sim.current and sim.stage == 'dropoff' else 'ĐƠN HÀNG • ĐẾN QUÁN NHẬN HÀNG'
        self.text(heading, (678, 604), 13, LIME if sim.stage == 'dropoff' else MUTED, True)
        translations = {'scheduled': 'chưa mở', 'pending': 'chờ nhận', 'picked': 'đang giao',
                        'delivered': 'đã giao', 'cancelled': 'đã hủy'}
        displayed = [sim.current] if sim.current else []
        displayed += [o for o in world.orders if o is not sim.current]
        for i, order in enumerate(displayed[:3]):
            self.text(f'#{order.id:02d}   {translations[order.status]}   |   hạn tick {order.deadline}',
                      (678, 630 + i * 20), 14, LIME if order is sim.current else TEXT)
        self.text('P: quán   Nhà xanh: khách đặt hàng   Xe đỏ: NPC   Cam: kẹt xe', (32, 708), 13, MUTED)
        self.button('pause', 'Tiếp tục' if paused else 'Tạm dừng', (661, 712, 116, 34))
        self.button('reset', 'Reset', (786, 712, 85, 34))
        self.button('setup', 'Cài đặt', (880, 712, 95, 34))
        self.button('compare', 'So sánh', (984, 712, 116, 34))
        self.text('Space • 1–7 • V • T • R • +/−', (32, 738), 12, MUTED)

    def draw_compare(self, rows, done, total, error):
        self.begin()
        self.box((32, 112, 1216, 575))
        self.text('So sánh bộ não • cùng seed, cùng xe và sự kiện', (58, 133), 25, TEXT, True)
        self.text(f'{done}/{total} lượt hoàn tất' if not error else error, (58, 179), 18, BLUE)
        headers = [('BỘ NÃO', 58), ('ĐÃ GIAO', 404), ('ĐÚNG HẠN', 539), ('TỔNG STATES', 691), ('PLAN (ms)', 894), ('COST ĐÃ ĐI', 1058)]
        for label, x in headers:
            self.text(label, (x, 239), 14, MUTED, True)
        for i, record in enumerate(rows[-7:]):
            y = 286 + i * 47
            if i % 2 == 0:
                self.box((49, y - 8, 1180, 42), (28, 42, 57), 6)
            values = [(LABELS[record['brain']], 58), (f"{record['delivered']}/{record['orders']}", 404),
                      (f"{record['on_time_rate']:.0%}", 539), (record['states_processed'], 691),
                      (f"{record['planning_ms']:.2f}", 894), (f"{record['travel_cost']:.0f}", 1058)]
            for value, x in values:
                self.text(value, (x, y), 16, TEXT)
        self.text('Pilot trong game; không kết luận D* Lite luôn nhanh hơn. Runtime có dao động.', (58, 638), 16, MUTED)
        self.button('setup', 'Về cài đặt', (32, 713, 180, 40))
