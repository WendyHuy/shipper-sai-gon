import unittest
from dataclasses import replace
from math import inf

from ai.brains import BRAIN_NAMES
from ai.common import manhattan
from config import Config
from core.simulation import Simulation
from core.sensing import sense


class SimulationTests(unittest.TestCase):
    def test_seed_reproducible_except_runtime(self):
        cfg = Config(rows=12, cols=12, npc_count=5, max_ticks=100)
        for brain in BRAIN_NAMES:
            a, b = Simulation(cfg, brain), Simulation(cfg, brain)
            while not a.finished:
                a.step()
                b.step()
            excluded = {'planning_ms', 'mean_planning_ms_per_tick'}
            self.assertEqual({k: v for k, v in a.summary().items() if k not in excluded},
                             {k: v for k, v in b.summary().items() if k not in excluded})
            for ra, rb in zip(a.metrics.records, b.metrics.records):
                self.assertEqual({k: v for k, v in ra.items() if k != 'planning_ms'},
                                 {k: v for k, v in rb.items() if k != 'planning_ms'})

    def test_environment_identical_across_brains(self):
        cfg = Config(rows=12, cols=12, npc_count=10, max_ticks=80)
        a, b = Simulation(cfg, 'astar_tick'), Simulation(cfg, 'dstar_halo')
        for _ in range(80):
            a.step()
            b.step()
            self.assertEqual(a.world.traffic.positions, b.world.traffic.positions)
            self.assertEqual(a.world.events, b.world.events)

    def test_sensing_does_not_reveal_remote_changes(self):
        sim = Simulation(Config(rows=12, cols=12, npc_count=0))
        remote = (11, 11)
        sim.world.manual_blocks.add(remote)
        sense(sim.world, (0, 0), 3, sim.known)
        self.assertNotEqual(sim.known.get(remote, 1), inf)
        sense(sim.world, remote, 3, sim.known)
        sense(sim.world, (11, 10), 3, sim.known)
        self.assertEqual(sim.known[remote], inf)

    def test_1000_ticks_no_invalid_agent_step(self):
        cfg = Config(rows=15, cols=15, npc_count=20, max_ticks=1000,
                     order_count=25, deadline_per_order=1000, cancellation_grace=1000)
        for brain in ('astar_tick', 'dstar', 'dstar_halo'):
            sim = Simulation(cfg, brain)
            for _ in range(1000):
                old = sim.shipper.pos
                sim.step()
                if sim.shipper.pos != old:
                    self.assertEqual(manhattan(old, sim.shipper.pos), 1)
                    self.assertLess(sim.world.cost_at(sim.shipper.pos), inf)
                self.assertEqual(len(sim.world.traffic.positions), len(set(sim.world.traffic.positions)))
                if sim.brain.planner:
                    self.assertLessEqual(len(sim.brain.planner.active), cfg.rows * cfg.cols)

    def test_brain_switch_preserves_game(self):
        sim = Simulation(Config(npc_count=0))
        for _ in range(5):
            sim.step()
        world, pos, tick = sim.world, sim.shipper.pos, sim.tick
        sim.set_brain('dstar')
        self.assertIs(sim.world, world)
        self.assertEqual((sim.shipper.pos, sim.tick), (pos, tick))
        sim.step()


if __name__ == '__main__':
    unittest.main()
