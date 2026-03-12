import pygame
import math
import random

W, H = 960, 540
SCROLL_SPEED = 0.3

rng = random.Random(42)

# === ЗВЁЗДЫ ===
stars = []
for _ in range(200):
    x = rng.randint(0, W)
    y = rng.randint(0, int(H * 0.85))
    size = rng.choice([1, 1, 1, 2, 2, 3])
    brightness = rng.randint(150, 255)
    twinkle_speed = rng.uniform(0.5, 3.0)
    twinkle_offset = rng.uniform(0, math.pi * 2)
    stars.append((x, y, size, brightness, twinkle_speed, twinkle_offset))

# === ТУМАННОСТИ ===
nebulas = []
for _ in range(6):
    nx = rng.randint(50, W - 50)
    ny = rng.randint(30, int(H * 0.7))
    nw = rng.randint(120, 280)
    nh = rng.randint(60, 140)
    color = rng.choice([
        (180, 40, 10),
        (220, 80, 0),
        (150, 20, 20),
        (200, 60, 30),
        (120, 10, 40),
    ])
    alpha = rng.randint(18, 40)
    nebulas.append((nx, ny, nw, nh, color, alpha))

# Пре-рендер туманностей
nebula_surf = pygame.Surface((W, H), pygame.SRCALPHA)
for (nx, ny, nw, nh, color, alpha) in nebulas:
    for layer in range(5):
        lw = nw - layer * 20
        lh = nh - layer * 10
        la = alpha - layer * 3
        if lw > 0 and lh > 0 and la > 0:
            s = pygame.Surface((lw, lh), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (*color, la), (0, 0, lw, lh))
            nebula_surf.blit(s, (nx - lw // 2, ny - lh // 2))

# === ЛИНИЯ ГОРИЗОНТА ===
HORIZON_Y = int(H * 0.78)

# === СИЛУЭТЫ ЗДАНИЙ (статичные, тёмные) ===
def make_skyline(seed, total_w, y_base, min_h, max_h, min_w, max_w):
    r = random.Random(seed)
    buildings = []
    x = 0
    while x < total_w:
        bw = r.randint(min_w, max_w)
        bh = r.randint(min_h, max_h)
        buildings.append((x, bw, bh))
        x += bw + r.randint(0, 4)
    return buildings

SCENE_W = W * 4
skyline_bg = make_skyline(10, SCENE_W, HORIZON_Y, 40, 130, 30, 80)
skyline_fg = make_skyline(20, SCENE_W, HORIZON_Y, 20, 70, 20, 55)

def draw_bg_scene(surf, scroll, t):
    # === ФОНОВЫЙ ГРАДИЕНТ (небо) ===
    for y in range(H):
        ratio = y / H
        if ratio < 0.75:
            sky_ratio = ratio / 0.75
            r = int(8 + 30 * sky_ratio)
            g = int(2 + 5 * sky_ratio)
            b = int(8 + 5 * sky_ratio)
        else:
            ground_ratio = (ratio - 0.75) / 0.25
            r = int(38 + 10 * ground_ratio)
            g = int(7 + 3 * ground_ratio)
            b = int(13 + 5 * ground_ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (W, y))

    # === ТУМАННОСТИ ===
    # Пульсация туманностей
    pulse = 0.85 + 0.15 * math.sin(t * 0.4)
    pulsed = pygame.Surface((W, H), pygame.SRCALPHA)
    pulsed.blit(nebula_surf, (0, 0))
    pulsed.set_alpha(int(200 * pulse))
    surf.blit(pulsed, (0, 0))

    # === ЗВЁЗДЫ ===
    for (sx, sy, size, brightness, ts, to) in stars:
        twinkle = math.sin(t * ts + to)
        alpha = int(brightness * (0.6 + 0.4 * twinkle))
        alpha = max(0, min(255, alpha))
        if size == 1:
            s = pygame.Surface((2, 2), pygame.SRCALPHA)
            s.fill((255, 200, 180, alpha))
            surf.blit(s, (sx, sy))
        elif size == 2:
            s = pygame.Surface((3, 3), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 210, 190, alpha), (1, 1), 1)
            surf.blit(s, (sx - 1, sy - 1))
            # крестик-блик
            blink = pygame.Surface((7, 7), pygame.SRCALPHA)
            pygame.draw.line(blink, (255, 220, 200, alpha // 3), (3, 0), (3, 6))
            pygame.draw.line(blink, (255, 220, 200, alpha // 3), (0, 3), (6, 3))
            surf.blit(blink, (sx - 3, sy - 3))
        else:
            s = pygame.Surface((5, 5), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 220, 200, alpha), (2, 2), 2)
            surf.blit(s, (sx - 2, sy - 2))
            blink = pygame.Surface((11, 11), pygame.SRCALPHA)
            pygame.draw.line(blink, (255, 200, 180, alpha // 2), (5, 0), (5, 10))
            pygame.draw.line(blink, (255, 200, 180, alpha // 2), (0, 5), (10, 5))
            surf.blit(blink, (sx - 5, sy - 5))

    # === ПАДАЮЩАЯ ЗВЕЗДА (редко) ===
    shooting_cycle = 8.0
    phase = t % shooting_cycle
    if phase < 1.2:
        progress = phase / 1.2
        sx1 = int(W * 0.1 + W * 0.6 * progress)
        sy1 = int(H * 0.05 + H * 0.25 * progress)
        tail_len = 60
        sx0 = sx1 - int(tail_len * progress)
        sy0 = sy1 - int(tail_len * 0.4 * progress)
        alpha_shoot = int(255 * (1 - progress))
        if alpha_shoot > 0:
            shoot_s = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.line(shoot_s, (255, 200, 150, alpha_shoot), (sx0, sy0), (sx1, sy1), 2)
            surf.blit(shoot_s, (0, 0))

    # === СИЛУЭТЫ ЗДАНИЙ (дальний план) ===
    for (bx, bw, bh) in skyline_bg:
        rx = int((bx - scroll * 0.2) % SCENE_W)
        for offset in [0, SCENE_W]:
            rrx = rx - offset
            if -100 < rrx < W + 100:
                rect = pygame.Rect(rrx, HORIZON_Y - bh, bw, bh)
                s = pygame.Surface((bw, bh), pygame.SRCALPHA)
                s.fill((15, 5, 10, 200))
                surf.blit(s, (rrx, HORIZON_Y - bh))

    # === ГОРИЗОНТАЛЬНАЯ НЕОНОВАЯ ЛИНИЯ ===
    glow_alpha = int(120 + 60 * math.sin(t * 1.2))
    for thickness, alpha_mult in [(6, 0.2), (3, 0.5), (1, 1.0)]:
        gs = pygame.Surface((W, thickness), pygame.SRCALPHA)
        gs.fill((220, 80, 20, int(glow_alpha * alpha_mult)))
        surf.blit(gs, (0, HORIZON_Y - thickness // 2))

    # === СИЛУЭТЫ ЗДАНИЙ (ближний план) ===
    for (bx, bw, bh) in skyline_fg:
        rx = int((bx - scroll * 0.5) % SCENE_W)
        for offset in [0, SCENE_W]:
            rrx = rx - offset
            if -100 < rrx < W + 100:
                s = pygame.Surface((bw, bh), pygame.SRCALPHA)
                s.fill((8, 3, 6, 230))
                surf.blit(s, (rrx, HORIZON_Y - bh))

    # === ЗЕМЛЯ ===
    ground = pygame.Surface((W, H - HORIZON_Y), pygame.SRCALPHA)
    ground.fill((8, 3, 6))
    surf.blit(ground, (0, HORIZON_Y))

    # Отражение неоновой линии в земле
    for i in range(8):
        ref_alpha = int((80 - i * 10) * (0.7 + 0.3 * math.sin(t * 1.2)))
        if ref_alpha > 0:
            rs = pygame.Surface((W, 2), pygame.SRCALPHA)
            rs.fill((220, 80, 20, ref_alpha))
            surf.blit(rs, (0, HORIZON_Y + i * 5))