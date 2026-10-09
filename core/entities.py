from dataclasses import dataclass


@dataclass
class Order:
    id: int
    pickup: tuple
    dropoff: tuple  # Ô cửa nhà người đặt hàng: shipper được phép đến để giao.
    release_tick: int
    deadline: int
    status: str = 'scheduled'
    delivered_tick: int | None = None


@dataclass
class Shipper:
    pos: tuple
    steps: int = 0
    travel_cost: float = 0
    score: int = 0
    cooldown: int = 0
