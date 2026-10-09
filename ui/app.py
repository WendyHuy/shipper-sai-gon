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
from ui.renderer import Renderer


def run_app(config, brain='astar_tick', screenshot=None, screenshot_ticks=70):
    pygame.init()
    screen = pygame.display.set_mode((1280, 760))
    pygame.display.set_caption('Shipper Sài Gòn • AI Lab 1–4')
    renderer = Renderer(screen)
    clock = pygame.time.Clock()
    sim = Simulation(config, brain)
    state = 'play' if screenshot else 'setup'
    paused, show_visited, show_sensing = False, False, True
    speed = 1
    accumulator = 0
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

    while running:
        elapsed = clock.tick(60) / 1000
        actions = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    actions.append('setup')
                elif event.key == pygame.K_SPACE:
                    actions.append('pause' if state == 'play' else 'start')
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                action = renderer.action_at(event.pos)
                if action and event.button == 1:
                    actions.append(action)
                elif state == 'play':
                    cell = renderer.grid_cell(event.pos, sim.world)
                    if cell is not None and cell != sim.shipper.pos:
                        if event.button == 1:
                            sim.world.toggle_block(cell)
                        elif event.button == 3:
                            sim.world.toggle_congestion(cell)
        for action in actions:
            if action in ('start', 'reset'):
                try:
                    sim = Simulation(config, brain)
                    state, paused, accumulator = 'play', False, 0
                    note = ''
                except ValueError as exc:
                    note = str(exc)
            elif action == 'pause' and state == 'play':
                paused = not paused
            elif action == 'setup':
                state = 'setup'
            elif action == 'compare':
                if worker is None or not worker.is_alive():
                    compare_rows, compare_done, compare_error = [], 0, ''
                    while not mailbox.empty():
                        mailbox.get_nowait()
                    worker = threading.Thread(target=compare_job, args=(config,), daemon=True)
                    worker.start()
                state = 'compare'
            elif isinstance(action, tuple) and action[0] == 'brain':
                brain = action[1]
                sim.set_brain(brain)
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
        while not mailbox.empty():
            message = mailbox.get_nowait()
            if message[0] == 'progress':
                compare_done, compare_total = message[1:3]
                compare_rows.append(message[3])
            elif message[0] == 'error':
                compare_error = message[1]
        if state == 'play' and not paused and not sim.finished:
            accumulator += elapsed * speed
            while accumulator >= 0.12 and not sim.finished:
                sim.step()
                accumulator -= 0.12
        if screenshot:
            while sim.tick < screenshot_ticks and not sim.finished:
                sim.step()
            show_visited = True
        if state == 'setup':
            renderer.draw_setup(config, brain)
            if note:
                renderer.text(note, (34, 690), 14, (255, 125, 125))
        elif state == 'compare':
            renderer.draw_compare(compare_rows, compare_done, compare_total, compare_error)
        else:
            renderer.draw_game(sim, paused, show_visited, show_sensing, speed)
        pygame.display.flip()
        if screenshot:
            Path(screenshot).parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(screen, screenshot)
            running = False
    pygame.quit()
