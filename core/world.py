from math import inf
from random import Random

from ai.common import neighbors4
from core.entities import Order
from core.npc import RandomTraffic


def reachable_cells(rows, cols, walls, start):
    queue = [start]
    seen = {start}
    for u in queue:
        for v in neighbors4(u, rows, cols):
            if v not in seen and v not in walls:
                seen.add(v)
                queue.append(v)
    return seen


class World:
    def __init__(self, config):
        self.config = config
        self.rows, self.cols = config.rows, config.cols
        self.start = (0, 0)
        cells = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        map_rng = Random(config.seed + 101)
        candidates = [c for c in cells if c != self.start]
        wall_count = int(len(cells) * config.density)
        for _ in range(200):
            walls = set(map_rng.sample(candidates, wall_count))
            component = reachable_cells(self.rows, self.cols, walls, self.start)
            if len(component) >= (len(cells) - wall_count) * 0.8:
                self.walls = walls
                break
        else:
            raise ValueError('Không sinh được bản đồ đủ liên thông; hãy đổi seed/mật độ.')
        order_rng = Random(config.seed + 1009)
        roads = sorted(component - {self.start})
        if len(roads) < 2:
            raise ValueError('Bản đồ thiếu điểm nhận/giao.')
        self.orders = []
        for i in range(config.order_count):
            pickup, dropoff = order_rng.sample(roads, 2)
            release = i * 25
            self.orders.append(Order(i + 1, pickup, dropoff, release,
                                     release + config.deadline_per_order))
        reserved = {self.start} | {o.pickup for o in self.orders} | {o.dropoff for o in self.orders}
        spawn_cells = sorted(component - reserved)
        if config.npc_count > len(spawn_cells):
            raise ValueError(f'Bản đồ chỉ đủ chỗ khởi tạo {len(spawn_cells)} xe NPC.')
        spawn_rng = Random(config.seed + 2001)
        self.traffic = RandomTraffic(self.rows, self.cols, self.walls,
                                     spawn_rng.sample(spawn_cells, config.npc_count), config.seed)
        self.event_rng = Random(config.seed + 3001)
        self.roads = sorted(component)
        self.events = []
        self.manual_blocks = set()
        self.manual_costs = {}
        self.event_log = []
        self.tick = 0

    def advance(self, tick):
        self.tick = tick
        self.traffic.step()
        self.events = [e for e in self.events if e['expires'] > tick]
        if tick % self.config.event_interval == 0:
            cell = self.event_rng.choice(self.roads)
            blocked = self.event_rng.random() < 0.35
            cost = inf if blocked else self.event_rng.choice((3, 5, 8))
            affected = [cell]
            if not blocked:
                affected += [v for v in neighbors4(cell, self.rows, self.cols)
                             if v not in self.walls]
            expires = tick + self.event_rng.randint(15, 40)
            event = {'cells': affected, 'cost': cost, 'expires': expires, 'tick': tick}
            self.events.append(event)
            self.event_log.append(event)

    def terrain_cost(self, cell):
        if cell in self.walls or cell in self.manual_blocks:
            return inf
        cost = self.manual_costs.get(cell, 1)
        for event in self.events:
            if cell in event['cells']:
                cost = max(cost, event['cost'])
        return cost

    def cost_at(self, cell):
        if cell in self.traffic.positions:
            return inf
        return self.terrain_cost(cell)

    def toggle_block(self, cell):
        if cell in self.manual_blocks:
            self.manual_blocks.remove(cell)
        elif cell not in self.walls:
            self.manual_blocks.add(cell)

    def toggle_congestion(self, cell):
        if cell not in self.walls:
            if cell in self.manual_costs:
                del self.manual_costs[cell]
            else:
                self.manual_costs[cell] = 5
