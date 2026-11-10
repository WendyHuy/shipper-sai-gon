import math
import numpy as np
import pygame


class AudioManager:
    """Hệ thống âm thanh kỹ thuật số procedural đa âm sắc cho Shipper Sài Gòn."""
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.enabled = True
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=sample_rate, size=-16, channels=2, buffer=512)
            self._generate_sounds()
        except Exception as exc:
            print(f"[Audio] Mixer không khả dụng: {exc}")
            self.enabled = False

    def _make_sound(self, samples):
        """Chuyển numpy float array [-1.0, 1.0] thành Pygame Sound Stereo 16-bit."""
        int16_samples = np.int16(np.clip(samples, -1.0, 1.0) * 32767)
        stereo_samples = np.column_stack((int16_samples, int16_samples))
        return pygame.sndarray.make_sound(stereo_samples)

    def _generate_sounds(self):
        sr = self.sample_rate

        # 1. Nhận đơn hàng (Pickup ting-ting: 880Hz -> 1320Hz arpeggio)
        dur1 = 0.16
        t1 = np.linspace(0, dur1, int(sr * dur1), False)
        env1 = np.exp(-12 * t1)
        freq1 = np.where(t1 < 0.08, 880, 1320)
        s1 = 0.45 * np.sin(2 * np.pi * freq1 * t1) * env1
        self.sounds['pickup'] = self._make_sound(s1)

        # 2. Giao hàng thành công (Success chord: C5 523Hz + E5 659Hz + G5 784Hz + C6 1046Hz)
        dur2 = 0.38
        t2 = np.linspace(0, dur2, int(sr * dur2), False)
        env2 = np.exp(-6 * t2)
        s2 = 0.25 * (
            np.sin(2 * np.pi * 523.25 * t2) +
            np.sin(2 * np.pi * 659.25 * t2) +
            np.sin(2 * np.pi * 783.99 * t2) +
            0.6 * np.sin(2 * np.pi * 1046.50 * t2)
        ) * env2
        self.sounds['delivery'] = self._make_sound(s2)

        # 3. Tiếng còi xe máy Sài Gòn (Horn bim-bim: 440Hz + 554Hz)
        dur3 = 0.18
        t3 = np.linspace(0, dur3, int(sr * dur3), False)
        env3 = np.ones_like(t3)
        # Làm fade in và fade out nhẹ cho âm không bị nổ click
        attack = int(sr * 0.015)
        decay = int(sr * 0.03)
        env3[:attack] = np.linspace(0, 1, attack)
        env3[-decay:] = np.linspace(1, 0, decay)
        s3 = 0.35 * (np.sin(2 * np.pi * 440 * t3) + 0.85 * np.sin(2 * np.pi * 554 * t3)) * env3
        self.sounds['honk'] = self._make_sound(s3)

        # 4. Va quẹt NPC / chướng ngại vật (Bump / Thud: 140Hz giảm nhanh về 40Hz)
        dur4 = 0.15
        t4 = np.linspace(0, dur4, int(sr * dur4), False)
        freq4 = np.linspace(160, 40, len(t4))
        env4 = np.exp(-18 * t4)
        noise = (np.random.rand(len(t4)) * 2 - 1) * 0.2
        s4 = (0.5 * np.sin(2 * np.pi * freq4 * t4) + noise) * env4
        self.sounds['bump'] = self._make_sound(s4)

        # 5. Cảnh báo trễ giờ / Hủy đơn (Alert buzz)
        dur5 = 0.25
        t5 = np.linspace(0, dur5, int(sr * dur5), False)
        env5 = np.exp(-8 * t5)
        s5 = 0.3 * np.sign(np.sin(2 * np.pi * 220 * t5)) * env5
        self.sounds['alert'] = self._make_sound(s5)

        # 6. Đổi thuật toán / click nhẹ
        dur6 = 0.04
        t6 = np.linspace(0, dur6, int(sr * dur6), False)
        env6 = np.exp(-35 * t6)
        s6 = 0.25 * np.sin(2 * np.pi * 900 * t6) * env6
        self.sounds['click'] = self._make_sound(s6)

    def play(self, name):
        """Phát âm thanh theo tên nếu bật âm thanh."""
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def toggle(self):
        """Bật / tắt âm thanh."""
        self.enabled = not self.enabled
        return self.enabled
