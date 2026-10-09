from math import ceil, inf
from time import perf_counter

from ai.brains import Brain
from ai.common import manhattan, path_cost
from core.entities import Shipper
from core.metrics import Metrics
from core.sensing import sense, with_halo
from core.world import World


class Simulation:
    def __init__(self, config, brain='astar_tick'):
        self.config = config
        self.world = World(config)
        self.shipper = Shipper(self.world.start)
        self.brain = Brain(brain, config.rows, config.cols)
        self.known = {cell: inf for cell in self.world.walls}
        self.visible = set()
        self.metrics = Metrics()
        self.tick = 0
        self.current = None
        self.stage = 'idle'
        self.finished = False
        self.last_processed = 0
        self.last_ms = 0
        self._orders_update()
        _, self.visible = sense(self.world, self.shipper.pos, config.sensing_radius, self.known)

    @property
    def goal(self):
        if self.current is None:
            return None
        return self.current.pickup if self.stage == 'pickup' else self.current.dropoff

    def set_brain(self, name):
        self.brain = Brain(name, self.config.rows, self.config.cols)

    def _orders_update(self):
        active_count = sum(o.status in ('pending', 'picked') for o in self.world.orders)
        for order in self.world.orders:
            if order.status == 'scheduled' and order.release_tick <= self.tick and active_count < 3:
                order.status = 'pending'
                active_count += 1
            if order.status in ('pending', 'picked', 'scheduled') and self.tick > order.deadline + self.config.cancellation_grace:
                order.status = 'cancelled'
                self.shipper.score -= 50
                if self.current is order:
                    self.current, self.stage = None, 'idle'
        if self.current and self.shipper.pos == self.goal and self.shipper.cooldown == 0:
            if self.stage == 'pickup':
                self.current.status = 'picked'
                self.stage = 'dropoff'
            else:
                self.current.status = 'delivered'
                self.current.delivered_tick = self.tick
                late = max(0, self.tick - self.current.deadline)
                self.shipper.score += max(10, 100 - 2 * late)
                self.current, self.stage = None, 'idle'
        if self.current is None:
            pending = [o for o in self.world.orders if o.status == 'pending']
            if pending:
                self.current = min(pending, key=lambda o: (manhattan(self.shipper.pos, o.pickup), o.id))
                self.stage = 'pickup'

    def step(self):
        if self.finished:
            return
        self.tick += 1
        old_npcs = set(self.world.traffic.positions)
        self.world.advance(self.tick)
        if self.shipper.pos in set(self.world.traffic.positions) - old_npcs:
            self.metrics.npc_contacts += 1
            self.shipper.score -= 30
        _, self.visible = sense(self.world, self.shipper.pos, self.config.sensing_radius, self.known)
        self._orders_update()
        self.last_processed = 0
        self.last_ms = 0
        if self.goal is not None:
            costs = with_halo(self.world, self.known, self.visible, self.shipper.pos) if self.brain.name == 'dstar_halo' else dict(self.known)
            costs[self.shipper.pos] = max(1, self.world.terrain_cost(self.shipper.pos))
            if costs[self.shipper.pos] == inf:
                costs[self.shipper.pos] = 1
            t0 = perf_counter()
            nxt = self.brain.plan(self.shipper.pos, self.goal, costs)
            self.last_ms = (perf_counter() - t0) * 1000
            self.last_processed = self.brain.last_result.processed
            self.metrics.states_processed += self.last_processed
            self.metrics.planning_ms += self.last_ms
            self.metrics.replans += int(self.brain.replanned)
            self.metrics.path_changes += int(self.brain.path_changed)
            if self.shipper.cooldown > 0:
                self.shipper.cooldown -= 1
                self.metrics.waits += 1
            elif nxt is None:
                self.metrics.waits += 1
            elif self.world.cost_at(nxt) == inf:
                self.metrics.blocked_attempts += 1
                self.metrics.waits += 1
            else:
                actual_cost = self.world.terrain_cost(nxt)
                self.shipper.pos = nxt
                self.shipper.steps += 1
                self.shipper.travel_cost += actual_cost
                self.shipper.cooldown = ceil(actual_cost) - 1
                self.shipper.score -= int(actual_cost > 1)
                self.brain.on_move(nxt)
        else:
            self.metrics.waits += 1
        self._orders_update()
        remaining = path_cost(self.brain.path, self.brain.costs)
        self.metrics.records.append({'tick': self.tick, 'brain': self.brain.name,
                                     'row': self.shipper.pos[0], 'col': self.shipper.pos[1],
                                     'goal': str(self.goal), 'states_processed': self.last_processed,
                                     'planning_ms': self.last_ms, 'remaining_cost': remaining,
                                     'steps': self.shipper.steps, 'travel_cost': self.shipper.travel_cost,
                                     'blocked_attempts': self.metrics.blocked_attempts,
                                     'npc_contacts': self.metrics.npc_contacts})
        self.finished = self.tick >= self.config.max_ticks or all(
            o.status in ('delivered', 'cancelled') for o in self.world.orders)

    def summary(self):
        orders = self.world.orders
        delivered = sum(o.status == 'delivered' for o in orders)
        on_time = sum(o.delivered_tick is not None and o.delivered_tick <= o.deadline for o in orders)
        return {'seed': self.config.seed, 'density': self.config.density,
                'npc_count': self.config.npc_count, 'radius': self.config.sensing_radius,
                'brain': self.brain.name, 'ticks': self.tick, 'orders': len(orders),
                'delivered': delivered, 'on_time': on_time, 'on_time_rate': on_time / len(orders),
                'cancelled': sum(o.status == 'cancelled' for o in orders),
                'unfinished': sum(o.status not in ('delivered', 'cancelled') for o in orders),
                'steps': self.shipper.steps, 'travel_cost': self.shipper.travel_cost,
                'score': self.shipper.score, 'states_processed': self.metrics.states_processed,
                'planning_ms': self.metrics.planning_ms,
                'mean_planning_ms_per_tick': self.metrics.planning_ms / max(1, self.tick),
                'replans': self.metrics.replans, 'path_changes': self.metrics.path_changes,
                'blocked_attempts': self.metrics.blocked_attempts,
                'npc_contacts': self.metrics.npc_contacts, 'waits': self.metrics.waits}
