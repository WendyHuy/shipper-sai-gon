import math
import random
import pygame


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size', 'fade')

    def __init__(self, x, y, vx, vy, life, color, size=3, fade=True):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.fade = fade

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return self.life > 0

    def draw(self, screen):
        ratio = max(0.0, self.life / self.max_life)
        alpha = int(255 * ratio) if self.fade else 255
        radius = max(1, int(self.size * (0.4 + 0.6 * ratio)))
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        c = self.color
        surf_color = (c[0], c[1], c[2], alpha) if len(c) == 3 else (c[0], c[1], c[2], int(c[3] * ratio))
        pygame.draw.circle(surf, surf_color, (radius, radius), radius)
        screen.blit(surf, (self.x - radius, self.y - radius))


class FloatingText:
    __slots__ = ('text', 'x', 'y', 'vy', 'life', 'max_life', 'color', 'size', 'font_name')

    def __init__(self, text, x, y, color=(191, 242, 103), size=18, life=1.4, vy=-32):
        self.text = text
        self.x = x
        self.y = y
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size

    def update(self, dt):
        self.life -= dt
        self.y += self.vy * dt
        return self.life > 0

    def draw(self, screen, font):
        ratio = max(0.0, self.life / self.max_life)
        alpha = int(255 * min(1.0, ratio * 1.5))
        txt_surf = font.render(self.text, True, self.color)
        txt_surf.set_alpha(alpha)
        rect = txt_surf.get_rect(center=(int(self.x), int(self.y)))
        # Hiệu ứng viền bóng đen (drop shadow)
        shadow_surf = font.render(self.text, True, (10, 15, 22))
        shadow_surf.set_alpha(int(alpha * 0.7))
        screen.blit(shadow_surf, (rect.x + 2, rect.y + 2))
        screen.blit(txt_surf, rect)


class EffectManager:
    """Quản lý các hiệu ứng hạt, khói xe, thời tiết mưa và chữ nổi động."""
    def __init__(self):
        self.particles = []
        self.floating_texts = []
        self.rain_drops = []
        self.rain_enabled = False
        self.radar_phase = 0.0
        self.fonts = {}

    def get_font(self, font_name, size):
        key = (font_name, size)
        if key not in self.fonts:
            self.fonts[key] = pygame.font.Font(font_name, size)
            self.fonts[key].set_bold(True)
        return self.fonts[key]

    def add_smoke(self, x, y, vx=0, vy=0):
        """Khói thải pô xe khi di chuyển."""
        for _ in range(2):
            life = random.uniform(0.3, 0.6)
            size = random.uniform(2.5, 4.5)
            # Khói mờ xám
            col = random.randint(180, 220)
            self.particles.append(Particle(
                x + random.uniform(-2, 2),
                y + random.uniform(-2, 2),
                vx * 0.2 + random.uniform(-10, 10),
                vy * 0.2 + random.uniform(-10, 10),
                life, (col, col, col, 140), size
            ))

    def add_sparks(self, x, y, color=(255, 220, 80), count=16):
        """Tia lửa ăn mừng khi giao hàng thành công."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 120)
            life = random.uniform(0.4, 0.8)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                life, color, size=random.uniform(2.5, 4.0)
            ))

    def add_bump_effect(self, x, y):
        """Bụi va quẹt khi xe tiếp xúc NPC."""
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(25, 75)
            life = random.uniform(0.2, 0.45)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                life, (242, 99, 112, 190), size=random.uniform(2, 3.5)
            ))

    def add_floating_text(self, text, x, y, color=(191, 242, 103), size=18):
        self.floating_texts.append(FloatingText(text, x, y, color=color, size=size))

    def init_rain(self, width, height, density=120):
        self.rain_drops = []
        for _ in range(density):
            self.rain_drops.append([
                random.uniform(0, width),
                random.uniform(0, height),
                random.uniform(300, 500),  # tốc độ rơi vy
                random.uniform(8, 16),     # chiều dài giọt mưa
            ])

    def toggle_rain(self, width, height):
        self.rain_enabled = not self.rain_enabled
        if self.rain_enabled and not self.rain_drops:
            self.init_rain(width, height)
        return self.rain_enabled

    def update(self, dt, width, height):
        # 1. Hạt
        self.particles = [p for p in self.particles if p.update(dt)]
        # 2. Chữ nổi
        self.floating_texts = [t for t in self.floating_texts if t.update(dt)]
        # 3. Radar phase
        self.radar_phase = (self.radar_phase + dt * 2.0) % 1.0
        # 4. Mưa
        if self.rain_enabled:
            for drop in self.rain_drops:
                drop[0] -= 70 * dt  # xiên sang trái nhẹ theo gió
                drop[1] += drop[2] * dt
                if drop[1] > height:
                    drop[1] = random.uniform(-30, 0)
                    drop[0] = random.uniform(0, width + 50)
                if drop[0] < -20:
                    drop[0] = width + random.uniform(0, 20)

    def draw_particles(self, screen):
        for p in self.particles:
            p.draw(screen)

    def draw_floating_texts(self, screen, font_name):
        for t in self.floating_texts:
            font = self.get_font(font_name, t.size)
            t.draw(screen, font)

    def draw_rain(self, screen):
        if not self.rain_enabled:
            return
        rain_color = (180, 215, 255, 90)
        rain_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for x, y, _, length in self.rain_drops:
            pygame.draw.line(rain_surf, rain_color, (x, y), (x - length * 0.3, y + length), 1)
        screen.blit(rain_surf, (0, 0))
