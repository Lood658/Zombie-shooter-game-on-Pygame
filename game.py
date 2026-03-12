import pygame
import math
import random

W, H = 960, 540
ARENA_MARGIN = 60


def load_scaled(path, scale=1.0):
    img = pygame.image.load(path).convert_alpha()
    w, h = img.get_size()
    return pygame.transform.scale(img, (int(w * scale), int(h * scale)))


def load_sound(path, volume=1.0):
    try:
        s = pygame.mixer.Sound(path)
        s.set_volume(volume)
        return s
    except Exception:
        return None


class Bullet:
    SPEED = 500

    def __init__(self, x, y, angle, img):
        self.x = x
        self.y = y
        self.angle = angle
        self.vx = math.cos(angle) * self.SPEED
        self.vy = math.sin(angle) * self.SPEED
        self.alive = True
        self.img = pygame.transform.rotate(img, -math.degrees(angle))
        self.radius = 8
        self.prev_x = x
        self.prev_y = y

    def update(self, dt):
        self.prev_x = self.x
        self.prev_y = self.y
        sub_dt = dt / 4
        for _ in range(4):
            self.x += self.vx * sub_dt
            self.y += self.vy * sub_dt
        if not (0 <= self.x <= W and 0 <= self.y <= H):
            self.alive = False

    def draw(self, surf):
        r = self.img.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(self.img, r)


class BloodEffect:
    FRAME_DUR = 0.07

    def __init__(self, x, y, frames):
        self.x = x
        self.y = y
        self.frames = frames
        self.idx = 0
        self.timer = 0
        self.alive = True

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.FRAME_DUR:
            self.timer = 0
            self.idx += 1
            if self.idx >= len(self.frames):
                self.alive = False

    def draw(self, surf):
        if self.alive and self.idx < len(self.frames):
            f = self.frames[self.idx]
            r = f.get_rect(center=(int(self.x), int(self.y)))
            surf.blit(f, r)


class Zombie:
    STATS = {
        "normal": dict(speed=55,  hp=3, radius=20, damage=1, attack_rate=1.2),
        "fast":   dict(speed=110, hp=2, radius=17, damage=1, attack_rate=0.8),
    }
    ATTACK_FRAME_DUR = 0.10
    HIT_FLASH_DUR    = 0.12
    ATTACK_RANGE     = 50

    def __init__(self, x, y, img, attack_frames, ztype="normal"):
        self.x = x
        self.y = y
        self.img = img
        self.attack_frames = attack_frames
        self.angle = 0
        self.alive = True
        self.hit_flash = 0
        self.ztype = ztype
        self.attack_cooldown = 0

        self.is_attacking     = False
        self.attack_idx       = 0
        self.attack_anim_t    = 0

        stats = self.STATS[ztype]
        self.speed       = stats["speed"]
        self.hp          = stats["hp"]
        self.radius      = stats["radius"]
        self.damage      = stats["damage"]
        self.attack_rate = stats["attack_rate"]

    def update(self, dt, px, py):
        zdx = px - self.x
        zdy = py - self.y
        dist = math.hypot(zdx, zdy)

        if dist > 1:
            self.angle = math.atan2(zdy, zdx)
            if not self.is_attacking:
                self.x += (zdx / dist) * self.speed * dt
                self.y += (zdy / dist) * self.speed * dt

        self.x = max(ARENA_MARGIN + 20, min(W - ARENA_MARGIN - 20, self.x))
        self.y = max(ARENA_MARGIN + 20, min(H - ARENA_MARGIN - 20, self.y))

        if self.hit_flash > 0:
            self.hit_flash -= dt
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        if self.is_attacking:
            self.attack_anim_t += dt
            if self.attack_anim_t >= self.ATTACK_FRAME_DUR:
                self.attack_anim_t = 0
                self.attack_idx += 1
                if self.attack_idx >= len(self.attack_frames):
                    self.attack_idx = 0
                    self.is_attacking = False

        if dist < self.ATTACK_RANGE and self.attack_cooldown <= 0:
            self.attack_cooldown = self.attack_rate
            self.is_attacking  = True
            self.attack_idx    = 0
            self.attack_anim_t = 0
            return True

        return False

    def draw(self, surf):
        shadow = pygame.Surface((28, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), (0, 0, 28, 12))
        surf.blit(shadow, (int(self.x) - 14, int(self.y) + 10))

        img = self.img
        if self.hit_flash > 0:
            white = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            white.fill((255, 255, 255, 180))
            img = img.copy()
            img.blit(white, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        rotated = pygame.transform.rotate(img, -math.degrees(self.angle) + 90)
        zr = rotated.get_rect(center=(int(self.x), int(self.y)))
        surf.blit(rotated, zr)

    def draw_attack_overlay(self, surf, px, py):
        if self.is_attacking and self.attack_frames:
            af = self.attack_frames[self.attack_idx]
            ax = int(self.x + (px - self.x) * 0.65)
            ay = int(self.y + (py - self.y) * 0.65)
            rotated = pygame.transform.rotate(af, -math.degrees(self.angle) + 90)
            ar = rotated.get_rect(center=(ax, ay))
            surf.blit(rotated, ar)

    def take_hit(self):
        self.hp -= 1
        self.hit_flash = self.HIT_FLASH_DUR
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def collides_with_bullet(self, bullet):
        steps = 16
        for i in range(steps + 1):
            t = i / steps
            bx = bullet.prev_x + (bullet.x - bullet.prev_x) * t
            by = bullet.prev_y + (bullet.y - bullet.prev_y) * t
            if math.hypot(self.x - bx, self.y - by) < self.radius + bullet.radius:
                return True
        return False


def spawn_wave(wave_num, zombi_img, zombi2_img, attack_frames):
    wave_configs = {
        1: {"normal": 5, "fast": 0},
        2: {"normal": 5, "fast": 3},
    }
    counts = wave_configs.get(wave_num, {"normal": 7, "fast": 5})

    zombies = []
    for ztype, count in counts.items():
        img = zombi_img if ztype == "normal" else zombi2_img
        for _ in range(count):
            while True:
                zx = random.randint(ARENA_MARGIN + 40, W - ARENA_MARGIN - 40)
                zy = random.randint(ARENA_MARGIN + 40, H - ARENA_MARGIN - 40)
                if math.hypot(zx - W // 2, zy - H // 2) > 150:
                    break
            zombies.append(Zombie(zx, zy, img, attack_frames, ztype))
    return zombies


def draw_hud_hp(surf, hp, max_hp, font):
    bar_x, bar_y = 20, 20
    bar_w, bar_h = 160, 18
    pygame.draw.rect(surf, (60, 10, 10), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    fill = max(0, int(bar_w * hp / max_hp))
    if fill > 0:
        color = (220, 50, 50) if hp > max_hp * 0.3 else (255, 80, 0)
        pygame.draw.rect(surf, color, (bar_x, bar_y, fill, bar_h), border_radius=4)
    pygame.draw.rect(surf, (180, 60, 60), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=4)
    label = font.render(f"HP  {hp} / {max_hp}", True, (220, 180, 180))
    surf.blit(label, (bar_x + 4, bar_y + 1))


def load_arena_textures():
    floor_w = W - ARENA_MARGIN * 2
    floor_h = H - ARENA_MARGIN * 2

    def try_load(path, size):
        try:
            img = pygame.image.load(path).convert()
            return pygame.transform.scale(img, size)
        except Exception as e:
            print(f"[arena] {path} не загружен: {e}")
            return None

    side_h = H
    textures = {
        "floor":       try_load("image/bg/floor.png",  (floor_w, floor_h)),
        "wall_top":    try_load("image/bg/wall.png",   (W, ARENA_MARGIN)),
        "wall_left":   try_load("image/bg/walls.png",  (ARENA_MARGIN, side_h)),
        "wall_right":  try_load("image/bg/walls.png",  (ARENA_MARGIN, side_h)),
        "wall_bottom": try_load("image/bg/walls.png",  (W, ARENA_MARGIN)),
    }
    return textures


def draw_arena(screen, textures, anim_time):
    screen.fill((0, 0, 0))

    if textures.get("floor"):
        screen.blit(textures["floor"], (ARENA_MARGIN, ARENA_MARGIN))
    else:
        pygame.draw.rect(screen, (8, 5, 5),
                         (ARENA_MARGIN, ARENA_MARGIN,
                          W - ARENA_MARGIN * 2, H - ARENA_MARGIN * 2))
        for ty in range(ARENA_MARGIN, H - ARENA_MARGIN, 40):
            for tx in range(ARENA_MARGIN, W - ARENA_MARGIN, 40):
                pygame.draw.rect(screen, (18, 12, 14), (tx, ty, 40, 40), 1)

    wall_rects = [
        ("wall_top",    (0, 0)),
        ("wall_left",   (0, 0)),
        ("wall_right",  (W - ARENA_MARGIN, 0)),
        ("wall_bottom", (0, H - ARENA_MARGIN)),
    ]
    fallback_color = (30, 18, 20)
    fallback_rects = [
        (0, 0, W, ARENA_MARGIN),
        (0, 0, ARENA_MARGIN, H),
        (W - ARENA_MARGIN, 0, ARENA_MARGIN, H),
        (0, H - ARENA_MARGIN, W, ARENA_MARGIN),
    ]
    for (key, pos), fb in zip(wall_rects, fallback_rects):
        if textures.get(key):
            screen.blit(textures[key], pos)
        else:
            pygame.draw.rect(screen, fallback_color, fb)

    glow_a = int(60 + 30 * math.sin(anim_time * 1.5))
    gs = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.rect(gs, (180, 30, 30, glow_a),
                     (ARENA_MARGIN, ARENA_MARGIN,
                      W - ARENA_MARGIN * 2, H - ARENA_MARGIN * 2), 2)
    screen.blit(gs, (0, 0))


def run_game(screen, clock, sfx_volume=1.0):

    try:
        walk_frames = [
            load_scaled(f"image/animation_hero/walking-frame{i}.png", scale=0.75)
            for i in range(1, 4)
        ]
        stand_frame = load_scaled("image/animation_hero/stand1-frame1.png", scale=0.75)
    except Exception as e:
        print("Ошибка загрузки героя:", e)
        return "menu"

    try:
        zombi_img  = load_scaled("image/zombi/zombi.png",  scale=0.75)
        zombi2_img = load_scaled("image/zombi/zombi2.png", scale=0.75)
    except Exception as e:
        print("Ошибка загрузки зомби:", e)
        return "menu"

    try:
        attack_frames = [
            load_scaled(f"image/zombi/zombi_attack/att_frame{i}.png", scale=0.75)
            for i in range(1, 4)
        ]
    except Exception as e:
        print("Ошибка загрузки анимации атаки:", e)
        attack_frames = []

    try:
        bullet_img_base = load_scaled("image/cartridge/shoot.png", scale=0.4)
    except Exception as e:
        print("Ошибка загрузки пули:", e)
        return "menu"

    try:
        blood_frames = [
            load_scaled(f"image/animation_blood/blood-frame{i}.png", scale=0.75)
            for i in range(1, 5)
        ]
    except Exception as e:
        print("Ошибка загрузки крови:", e)
        return "menu"

    arena_textures = load_arena_textures()

    snd_shoot     = load_sound("music/effects/eff_hero/shoot_gun.wav",   volume=0.7 * sfx_volume)
    snd_dead_hero = load_sound("music/effects/eff_hero/dead_hero.mp3",   volume=1.0 * sfx_volume)
    snd_attack    = load_sound("music/effects/eff_zombi/attack.mp3",     volume=0.6 * sfx_volume)
    snd_dead_zomb = load_sound("music/effects/eff_zombi/gead_zombi.mp3", volume=0.7 * sfx_volume)

    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load("music/game_mus/game.mp3")
        pygame.mixer.music.play(-1)
    except Exception:
        pass

    try:
        fontS = pygame.font.Font("fonts/UI/lunchds.ttf", 18)
        fontU = pygame.font.Font("fonts/UI/lunchds.ttf", 28)
        fontH = pygame.font.Font("fonts/head/DiscoDuckItalic.otf", 52)
    except Exception:
        fontS = pygame.font.SysFont("Arial", 18)
        fontU = pygame.font.SysFont("Arial", 28)
        fontH = pygame.font.SysFont("Arial", 52, bold=True)

    TOTAL_WAVES = 3
    wave_num    = 1
    zombies     = spawn_wave(wave_num, zombi_img, zombi2_img, attack_frames)
    bullets       = []
    blood_effects = []

    state          = "wave_announce"
    announce_timer = 2.0
    clear_timer    = 0.0
    gameover_timer = 0.0

    px, py         = W // 2, H // 2
    speed          = 180
    angle          = 0
    walk_idx       = 0
    walk_timer     = 0.0
    walk_frame_dur = 0.12
    is_moving      = False
    anim_time      = 0.0
    shoot_cooldown = 0.0
    shoot_rate     = 0.25
    player_hp      = 5
    player_max_hp  = 5
    dmg_flash      = 0.0

    scanline_surf = pygame.Surface((W, H), pygame.SRCALPHA)
    for y in range(0, H, 3):
        pygame.draw.line(scanline_surf, (0, 0, 0, 20), (0, y), (W, y))

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        anim_time      += dt
        shoot_cooldown -= dt
        if dmg_flash > 0:
            dmg_flash -= dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
                return "menu"

        if state == "wave_announce":
            announce_timer -= dt
            if announce_timer <= 0:
                state = "playing"

        elif state == "wave_clear":
            clear_timer -= dt
            if clear_timer <= 0:
                if wave_num >= TOTAL_WAVES:
                    state = "victory"
                else:
                    wave_num += 1
                    zombies = spawn_wave(wave_num, zombi_img, zombi2_img, attack_frames)
                    bullets = []
                    announce_timer = 2.0
                    state = "wave_announce"

        elif state == "gameover":
            gameover_timer -= dt

        elif state == "playing":
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_d] - keys[pygame.K_a])
            dy = (keys[pygame.K_s] - keys[pygame.K_w])
            if dx != 0 and dy != 0:
                dx *= 0.707
                dy *= 0.707

            is_moving = bool(dx or dy)
            px += dx * speed * dt
            py += dy * speed * dt
            px = max(ARENA_MARGIN + 20, min(W - ARENA_MARGIN - 20, px))
            py = max(ARENA_MARGIN + 20, min(H - ARENA_MARGIN - 20, py))

            mx, my = pygame.mouse.get_pos()
            angle = math.atan2(my - py, mx - px)

            if is_moving:
                walk_timer += dt
                if walk_timer >= walk_frame_dur:
                    walk_timer = 0
                    walk_idx = (walk_idx + 1) % len(walk_frames)
            else:
                walk_idx = 0
                walk_timer = 0

            if pygame.mouse.get_pressed()[0] and shoot_cooldown <= 0:
                shoot_cooldown = shoot_rate
                bx = px + math.cos(angle) * 25
                by = py + math.sin(angle) * 25
                bullets.append(Bullet(bx, by, angle, bullet_img_base))
                if snd_shoot:
                    snd_shoot.play()

            for b in bullets:
                b.update(dt)

            for z in zombies:
                if z.update(dt, px, py):
                    player_hp -= z.damage
                    dmg_flash = 0.3
                    if snd_attack:
                        snd_attack.play()
                    if player_hp <= 0:
                        player_hp = 0
                        if snd_dead_hero:
                            snd_dead_hero.play()
                        try:
                            pygame.mixer.music.stop()
                        except Exception:
                            pass
                        state = "gameover"
                        gameover_timer = 3.0

            for b in bullets:
                if not b.alive:
                    continue
                for z in zombies:
                    if z.alive and z.collides_with_bullet(b):
                        b.alive = False
                        if z.take_hit():
                            blood_effects.append(BloodEffect(z.x, z.y, blood_frames))
                            if snd_dead_zomb:
                                snd_dead_zomb.play()
                        break

            for be in blood_effects:
                be.update(dt)

            bullets       = [b  for b  in bullets       if b.alive]
            zombies       = [z  for z  in zombies        if z.alive]
            blood_effects = [be for be in blood_effects  if be.alive]

            if not zombies and state == "playing":
                state = "wave_clear"
                clear_timer = 2.5

        # --- Draw ---
        draw_arena(screen, arena_textures, anim_time)

        for be in blood_effects:
            be.draw(screen)
        for z in zombies:
            z.draw(screen)
        for b in bullets:
            b.draw(screen)

        shadow = pygame.Surface((32, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), (0, 0, 32, 12))
        screen.blit(shadow, (int(px) - 16, int(py) + 10))

        frame = walk_frames[walk_idx] if is_moving else stand_frame
        rotated = pygame.transform.rotate(frame, -math.degrees(angle) - 90)
        screen.blit(rotated, rotated.get_rect(center=(int(px), int(py))))

        for z in zombies:
            z.draw_attack_overlay(screen, px, py)

        if dmg_flash > 0:
            alpha = int(min(120, dmg_flash * 400))
            flash_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            flash_surf.fill((200, 0, 0, alpha))
            screen.blit(flash_surf, (0, 0))

        screen.blit(scanline_surf, (0, 0))
        draw_hud_hp(screen, player_hp, player_max_hp, fontS)

        wave_txt = fontS.render(
            f"WAVE {wave_num} / {TOTAL_WAVES}    enemies: {len(zombies)}",
            True, (160, 80, 80))
        screen.blit(wave_txt, (W // 2 - wave_txt.get_width() // 2, 16))

        hint = fontS.render("BACKSPACE — return to menu", True, (60, 40, 40))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 28))

        if state in ("wave_announce", "wave_clear", "victory", "gameover"):
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            alpha   = {"wave_announce": 120, "wave_clear": 100,
                       "victory": 160, "gameover": 180}[state]
            overlay.fill((0, 0, 0, alpha))
            screen.blit(overlay, (0, 0))

            pulse = 1.0 + 0.05 * math.sin(anim_time * 3)

            if state == "wave_announce":
                pulse = 1.0 + 0.04 * math.sin(anim_time * 6)
                t1 = fontH.render(f"WAVE {wave_num}", True, (255, 180, 0))
                t2 = fontU.render("GET READY",        True, (200, 200, 200))
            elif state == "wave_clear":
                pulse = 1.0
                t1 = fontH.render("WAVE CLEAR!", True, (80, 255, 80))
                t2 = fontU.render("next wave incoming...", True, (180, 180, 180)) \
                     if wave_num < TOTAL_WAVES else None
            elif state == "victory":
                t1 = fontH.render("YOU WIN!", True, (255, 200, 0))
                t2 = fontU.render("BACKSPACE — return to menu", True, (180, 180, 100))
            else:  # gameover
                pulse = 1.0 + 0.06 * math.sin(anim_time * 4)
                t1 = fontH.render("YOU DIED", True, (220, 30, 30))
                t2 = fontU.render("BACKSPACE — return to menu", True, (160, 80, 80))

            t1_scaled = pygame.transform.scale(
                t1, (int(t1.get_width() * pulse), int(t1.get_height() * pulse)))
            screen.blit(t1_scaled, (W // 2 - t1_scaled.get_width() // 2, H // 2 - 60))
            if t2:
                screen.blit(t2, (W // 2 - t2.get_width() // 2, H // 2 + 20))

        pygame.display.flip()