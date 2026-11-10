import math
import os
import queue
import threading
from dataclasses import replace
from pathlib import Path

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame

from ai.brains import BRAIN_NAMES
from core.simulation import Simulation
from experiments.run_benchmark import benchmark
from ui.audio import AudioManager
from ui.effects import EffectManager
from ui.renderer import Renderer


def get_direction_angle(from_cell, to_cell):
    """Tính góc xoay phương tiện (0: lên, 90: phải, 180: xuống, 270: trái)."""
    if not from_cell or not to_cell:
        return 0
    dr = to_cell[0] - from_cell[0]
    dc = to_cell[1] - from_cell[1]
    if dr < 0:
        return 0     # Lên
    if dc > 0:
        return 90    # Phải
    if dr > 0:
        return 180   # Xuống
    if dc < 0:
        return 270   # Trái
    return 0


def lerp_angle(a0, a1, t):
    """Nội suy góc quay mượt mà theo đường ngắn nhất."""
    diff = (a1 - a0 + 180) % 360 - 180
    return (a0 + diff * t) % 360


def run_app(config, brain='astar_tick', screenshot=None, screenshot_ticks=70):
    pygame.init()
    screen = pygame.display.set_mode((1280, 760))
    pygame.display.set_caption('Shipper Sài Gòn 2D • Trò Chơi Giao Hàng & Bàn Thí Nghiệm AI')
    renderer = Renderer(screen)
    clock = pygame.time.Clock()
    audio = AudioManager()
    effects = EffectManager()
    effects.init_rain(1280, 760)

    sim = Simulation(config, brain)
    state = 'play' if screenshot else 'setup'
    control_mode = 'ai'  # 'ai' hoặc 'manual'
    manual_move_queue = None

    paused, show_visited, show_sensing = False, False, True
    speed = 1
    accumulator = 0.0
    tick_duration = 0.12

    # Vị trí phục vụ nội suy chuyển động 60 FPS mượt mà
    prev_shipper_cell = sim.shipper.pos
    curr_shipper_cell = sim.shipper.pos
    shipper_angle = 0
    target_shipper_angle = 0

    prev_npc_cells = list(sim.world.traffic.positions)
    curr_npc_cells = list(sim.world.traffic.positions)
    npc_angles = [0] * len(curr_npc_cells)
    target_npc_angles = [0] * len(curr_npc_cells)

    # Theo dõi trạng thái để kích hoạt âm thanh & chữ nổi
    last_stage = sim.stage
    last_delivered = 0
    last_contacts = 0
    last_cancelled = 0

    mailbox = queue.Queue()
    compare_rows, compare_done, compare_total, compare_error = [], 0, len(BRAIN_NAMES), ''
    worker = None
    running = True
    note = ''

    def compare_job(cfg):
        try:
            benchmark(cfg, [cfg.seed], [cfg.npc_count], output='results/ui_compare.csv',
                      progress=lambda i, n, row: mailbox.put(('progress', i, n, row)))
            mailbox.put(('done',))
        except Exception as exc:
            mailbox.put(('error', str(exc)))

    def apply_honk_horn():
        """Bấm còi bim bim: giải tỏa các xe NPC gần đó."""
        audio.play('honk')
        sx, sy = renderer.center(sim.shipper.pos)
        effects.add_floating_text('📢 BIM BIM!', sx, sy - 20, (255, 230, 80), 16)
        # NPC trong bán kính 2 ô ưu tiên đứng yên
        for i, pos in enumerate(sim.world.traffic.positions):
            if abs(pos[0] - sim.shipper.pos[0]) <= 2 and abs(pos[1] - sim.shipper.pos[1]) <= 2:
                effects.add_floating_text('!', renderer.center(pos)[0], renderer.center(pos)[1] - 12, (255, 100, 100), 12)

    while running:
        dt = clock.tick(60) / 1000.0
        effects.update(dt, 1280, 760)

        actions = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    actions.append('setup')
                elif event.key == pygame.K_SPACE:
                    if state == 'play':
                        actions.append('pause')
                    else:
                        actions.append('start')
                elif event.key == pygame.K_m:
                    actions.append('toggle_mode')
                elif event.key == pygame.K_h:
                    actions.append('honk')
                elif event.key == pygame.K_s:
                    actions.append('audio')
                elif event.key == pygame.K_w and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    # Ctrl+W đóng cửa sổ
                    running = False
                elif event.key == pygame.K_w and control_mode == 'ai':
                    # Phím W khi AI mode: đổi thời tiết
                    actions.append('weather')
                elif pygame.K_1 <= event.key <= pygame.K_7:
                    actions.append(('brain', BRAIN_NAMES[event.key - pygame.K_1]))
                elif event.key == pygame.K_r:
                    actions.append('reset')
                elif event.key == pygame.K_v:
                    show_visited = not show_visited
                elif event.key == pygame.K_t:
                    show_sensing = not show_sensing
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    speed = min(8, speed * 2)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed = max(1, speed // 2)

                # Điều khiển lái thủ công trong chế độ Manual
                if state == 'play' and control_mode == 'manual':
                    if event.key in (pygame.K_UP, pygame.K_w):
                        manual_move_queue = (-1, 0)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        manual_move_queue = (1, 0)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        manual_move_queue = (0, -1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        manual_move_queue = (0, 1)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                action = renderer.action_at(event.pos)
                if action and event.button == 1:
                    actions.append(action)
                elif state == 'play':
                    cell = renderer.grid_cell(event.pos, sim.world)
                    if cell is not None and cell != sim.shipper.pos:
                        if event.button == 1:
                            sim.world.toggle_block(cell)
                            audio.play('click')
                        elif event.button == 3:
                            sim.world.toggle_congestion(cell)
                            audio.play('click')

        # Xử lý các actions
        for action in actions:
            if action in ('start', 'reset'):
                try:
                    sim = Simulation(config, brain)
                    state, paused, accumulator = 'play', False, 0.0
                    prev_shipper_cell = sim.shipper.pos
                    curr_shipper_cell = sim.shipper.pos
                    prev_npc_cells = list(sim.world.traffic.positions)
                    curr_npc_cells = list(sim.world.traffic.positions)
                    npc_angles = [0] * len(curr_npc_cells)
                    target_npc_angles = [0] * len(curr_npc_cells)
                    last_stage = sim.stage
                    last_delivered = 0
                    last_contacts = 0
                    last_cancelled = 0
                    note = ''
                    audio.play('pickup')
                except ValueError as exc:
                    note = str(exc)
            elif action == 'pause' and state == 'play':
                paused = not paused
                audio.play('click')
            elif action == 'setup':
                state = 'setup'
                audio.play('click')
            elif action == 'toggle_mode':
                control_mode = 'manual' if control_mode == 'ai' else 'ai'
                sx, sy = renderer.center(sim.shipper.pos)
                msg = '🎮 CHẾ ĐỘ LÁI TAY (WASD)' if control_mode == 'manual' else '🤖 CHẾ ĐỘ TỰ ĐỘNG AI'
                effects.add_floating_text(msg, sx, sy - 24, (70, 190, 255) if control_mode == 'manual' else (191, 242, 103), 16)
                audio.play('click')
            elif action == 'honk':
                apply_honk_horn()
            elif action == 'audio':
                is_on = audio.toggle()
                audio.play('click')
            elif action == 'weather':
                rain_active = effects.toggle_rain(1280, 760)
                audio.play('click')
            elif action == 'compare':
                if worker is None or not worker.is_alive():
                    compare_rows, compare_done, compare_error = [], 0, ''
                    while not mailbox.empty():
                        mailbox.get_nowait()
                    worker = threading.Thread(target=compare_job, args=(config,), daemon=True)
                    worker.start()
                state = 'compare'
                audio.play('click')
            elif isinstance(action, tuple) and action[0] == 'brain':
                brain = action[1]
                sim.set_brain(brain)
                audio.play('click')
            elif isinstance(action, tuple) and action[0] == 'mode':
                control_mode = action[1]
                audio.play('click')
            elif isinstance(action, tuple) and action[0] == 'adjust':
                _, field, delta = action
                value = getattr(config, field)
                steps = {'npc_count': 5, 'max_ticks': 100, 'density': 0.05}
                lower = {'seed': 0, 'npc_count': 0, 'sensing_radius': 1, 'order_count': 1,
                         'density': 0, 'max_ticks': 100}
                upper = {'seed': 999999, 'npc_count': 100, 'sensing_radius': 25, 'order_count': 25,
                         'density': 0.4, 'max_ticks': 3000}
                value = min(upper[field], max(lower[field], value + delta * steps.get(field, 1)))
                if field == 'density':
                    value = round(value, 2)
                config = replace(config, **{field: value})
                audio.play('click')

        while not mailbox.empty():
            message = mailbox.get_nowait()
            if message[0] == 'progress':
                compare_done, compare_total = message[1:3]
                compare_rows.append(message[3])
            elif message[0] == 'error':
                compare_error = message[1]

        # Logic bước nhảy tick của Game Simulation
        if state == 'play' and not paused and not sim.finished:
            accumulator += dt * speed
            while accumulator >= tick_duration and not sim.finished:
                accumulator -= tick_duration

                # Lưu trạng thái trước tick để nội suy
                prev_shipper_cell = sim.shipper.pos
                prev_npc_cells = list(sim.world.traffic.positions)

                # Nếu ở chế độ Manual: can thiệp hướng đi của shipper
                if control_mode == 'manual' and manual_move_queue:
                    dr, dc = manual_move_queue
                    manual_move_queue = None
                    target_cell = (sim.shipper.pos[0] + dr, sim.shipper.pos[1] + dc)
                    # Kiểm tra ô đích có thể đi vào không
                    if 0 <= target_cell[0] < sim.world.rows and 0 <= target_cell[1] < sim.world.cols:
                        if target_cell not in sim.world.walls and sim.world.cost_at(target_cell) < math.inf:
                            # Override bước đi cho AI não ngầm
                            sim.brain.path = [sim.shipper.pos, target_cell]

                sim.step()

                # Cập nhật trạng thái sau tick
                curr_shipper_cell = sim.shipper.pos
                curr_npc_cells = list(sim.world.traffic.positions)

                # Cập nhật góc quay mục tiêu
                target_shipper_angle = get_direction_angle(prev_shipper_cell, curr_shipper_cell)
                for idx in range(len(curr_npc_cells)):
                    p_pos = prev_npc_cells[idx] if idx < len(prev_npc_cells) else curr_npc_cells[idx]
                    target_npc_angles[idx] = get_direction_angle(p_pos, curr_npc_cells[idx])

                # Sinh khói xe nếu shipper di chuyển
                if prev_shipper_cell != curr_shipper_cell:
                    sx, sy = renderer.center(curr_shipper_cell)
                    effects.add_smoke(sx, sy)

                # --- BẮT SỰ KIỆN PHÁT ÂM THANH & HIỆU ỨNG ---
                delivered_count = sum(o.status == 'delivered' for o in sim.world.orders)
                cancelled_count = sum(o.status == 'cancelled' for o in sim.world.orders)

                # Giao hàng thành công
                if delivered_count > last_delivered:
                    audio.play('delivery')
                    sx, sy = renderer.center(sim.shipper.pos)
                    effects.add_sparks(sx, sy, (255, 225, 75), 20)
                    effects.add_floating_text('+100 GIAO THÀNH CÔNG! 🛵', sx, sy - 24, (191, 242, 103), 18)
                    last_delivered = delivered_count

                # Lấy hàng tại quán
                elif sim.stage == 'dropoff' and last_stage == 'pickup':
                    audio.play('pickup')
                    sx, sy = renderer.center(sim.shipper.pos)
                    effects.add_floating_text('📦 ĐÃ LẤY HÀNG! TIẾN ĐẾN NHÀ KHÁCH', sx, sy - 24, (255, 175, 55), 16)

                # Va quẹt NPC
                if sim.metrics.npc_contacts > last_contacts:
                    audio.play('bump')
                    sx, sy = renderer.center(sim.shipper.pos)
                    effects.add_bump_effect(sx, sy)
                    effects.add_floating_text('-30 VA CHẠM! ⚠️', sx, sy - 22, (245, 80, 95), 17)
                    last_contacts = sim.metrics.npc_contacts

                # Đơn hàng bị hủy do trễ giờ
                if cancelled_count > last_cancelled:
                    audio.play('alert')
                    sx, sy = renderer.center(sim.shipper.pos)
                    effects.add_floating_text('❌ HỦY ĐƠN TRỄ HẠN (-50)', sx, sy - 22, (245, 80, 95), 17)
                    last_cancelled = cancelled_count

                last_stage = sim.stage

        # Screenshot testing mode
        if screenshot:
            while sim.tick < screenshot_ticks and not sim.finished:
                sim.step()
            show_visited = True

        # --- NỘI SUY TỌA ĐỘ VÀ GÓC QUAY 60 FPS CHO CHUYỂN ĐỘNG SIÊU MƯỢT ---
        anim_t = min(1.0, max(0.0, accumulator / max(0.001, tick_duration)))
        # Nội suy vị trí shipper
        p1 = renderer.center(prev_shipper_cell)
        p2 = renderer.center(curr_shipper_cell)
        shipper_screen_pos = (p1[0] + (p2[0] - p1[0]) * anim_t,
                              p1[1] + (p2[1] - p1[1]) * anim_t)
        shipper_angle = lerp_angle(shipper_angle, target_shipper_angle, 0.25)

        # Nội suy vị trí các NPC
        npc_screen_positions = []
        for idx in range(len(curr_npc_cells)):
            np1 = renderer.center(prev_npc_cells[idx] if idx < len(prev_npc_cells) else curr_npc_cells[idx])
            np2 = renderer.center(curr_npc_cells[idx])
            nx = np1[0] + (np2[0] - np1[0]) * anim_t
            ny = np1[1] + (np2[1] - np1[1]) * anim_t
            npc_screen_positions.append((nx, ny))
            npc_angles[idx] = lerp_angle(npc_angles[idx], target_npc_angles[idx], 0.25)

        # --- DỰNG HÌNH THEO TRẠNG THÁI ---
        if state == 'setup':
            renderer.draw_setup(config, brain, control_mode)
            if note:
                renderer.text(note, (34, 690), 14, (255, 120, 120))
        elif state == 'compare':
            renderer.draw_compare(compare_rows, compare_done, compare_total, compare_error)
        else:
            renderer.draw_game(
                sim, paused, show_visited, show_sensing, speed,
                effects=effects, control_mode=control_mode, audio_on=audio.enabled,
                shipper_screen_pos=shipper_screen_pos,
                npc_screen_positions=npc_screen_positions,
                shipper_angle=shipper_angle,
                npc_angles=npc_angles
            )

        pygame.display.flip()

        if screenshot:
            Path(screenshot).parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(screen, screenshot)
            running = False

    pygame.quit()
