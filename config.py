from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    rows: int = 25
    cols: int = 25
    density: float = 0.15
    seed: int = 42
    npc_count: int = 20
    sensing_radius: int = 5
    order_count: int = 5
    max_ticks: int = 300
    event_interval: int = 20
    deadline_per_order: int = 100
    cancellation_grace: int = 100

    def __post_init__(self):
        if self.rows < 3 or self.cols < 3:
            raise ValueError('Bản đồ phải có ít nhất 3×3 ô.')
        if not 0 <= self.density <= 0.4:
            raise ValueError('Mật độ nhà phải nằm trong [0, 0.4].')
        if self.npc_count < 0 or self.sensing_radius < 1:
            raise ValueError('Số NPC >= 0 và bán kính tầm nhìn >= 1.')
        if self.order_count < 1 or self.max_ticks < 1 or self.event_interval < 1:
            raise ValueError('Số đơn, số tick, khoảng sự kiện phải > 0.')
