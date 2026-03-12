import sys
import pygame
import random
import math
from bg_scene import draw_bg_scene, SCROLL_SPEED
from game import run_game

scroll = 0.0

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((960, 540))
pygame.display.set_caption("GAME")

try:
    fontH = pygame.font.Font("fonts/head/DiscoDuckItalic.otf", 52)
    fontU = pygame.font.Font("fonts/UI/lunchds.ttf", 36)
    fontSmall = pygame.font.Font("fonts/UI/lunchds.ttf", 22)
    snd_tap = pygame.mixer.Sound("music/effects/eff_tap_menu/tap_button.mp3")
    snd_tap.set_volume(0.8)
except:
    fontH = pygame.font.SysFont("Arial", 52, bold=True)
    fontU = pygame.font.SysFont("Arial", 36)
    fontSmall = pygame.font.SysFont("Arial", 22)
    snd_tap = None

try:
    bg_char = pygame.image.load("image/characters/1.png").convert_alpha()
    char_w, char_h = bg_char.get_size()
    scale = 2.8
    bg_char = pygame.transform.scale(bg_char, (int(char_w * scale), int(char_h * scale)))
except:
    bg_char = None

menu_music_list = [
    "music/menu_mus/menu.mp3",
    "music/menu_mus/menu2.mp3",
]
setting_music_list = [
    "music/settings_mus/set.mp3",
    "music/settings_mus/set2.mp3"
]

try:
    pygame.mixer.music.load(random.choice(menu_music_list))
    pygame.mixer.music.play(-1)
except:
    pass

clock = pygame.time.Clock()
game_state = "menu"

class Particle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.randint(0, 960)
        self.y = random.randint(0, 540)
        self.size = random.uniform(1, 3)
        self.speed = random.uniform(0.2, 0.8)
        self.alpha = random.randint(40, 180)
        self.color = random.choice([
            (220, 30, 30),
            (180, 0, 0),
            (255, 80, 0),
            (200, 200, 200),
        ])

    def update(self):
        self.y -= self.speed
        self.alpha -= 0.3
        if self.y < 0 or self.alpha <= 0:
            self.reset()
            self.y = 540

particles = [Particle() for _ in range(120)]

menu_items = ["PLAY", "SETTINGS", "AUTHORS"]
selected_index = 0
anim_time = 0

music_volume = 1.0
sfx_volume   = 1.0
pygame.mixer.music.set_volume(music_volume ** 2)

scanline_surf = pygame.Surface((960, 540), pygame.SRCALPHA)
for y in range(0, 540, 3):
    pygame.draw.line(scanline_surf, (0, 0, 0, 35), (0, y), (960, y))

easter_egg_active = False
easter_egg_timer = 0
author_appear_time = 0
author_click_counts = {}
author_click_timers = {}

SECTIONS = [
    ("DESIGN", (200, 60, 60),  ["Haidarhan Arman", "Abzalbek Amirlan"]),
    ("CODE",   (60, 140, 255), ["Lood658", "Baisakalov Daniil"]),
]

def get_author_rects():
    rects = {}
    y_pos = 115
    for sec_idx, (role, color, names) in enumerate(SECTIONS):
        y_pos += 32
        for n_idx, name in enumerate(names):
            rects[name] = pygame.Rect(70, y_pos, 420, 38)
            y_pos += 40
        y_pos += 8
    return rects

def change_music(music_list):
    pygame.mixer.music.stop()
    try:
        pygame.mixer.music.load(random.choice(music_list))
        pygame.mixer.music.set_volume(music_volume ** 2)
        pygame.mixer.music.play(-1)
    except:
        pass

def draw_bar(label, value, bar_y, hint_text="< > to adjust   or drag with mouse"):
    bar_x, bar_w, bar_h = 50, 400, 12
    lbl = fontU.render(label, True, (200, 200, 200))
    screen.blit(lbl, (50, bar_y - 55))
    pygame.draw.rect(screen, (40, 20, 20), (bar_x, bar_y, bar_w, bar_h))
    filled_w = int(bar_w * value)
    pygame.draw.rect(screen, (200, 40, 40), (bar_x, bar_y, filled_w, bar_h))
    pygame.draw.rect(screen, (120, 40, 40), (bar_x, bar_y, bar_w, bar_h), 1)
    knob_x = bar_x + filled_w
    pygame.draw.circle(screen, (255, 80, 80),  (knob_x, bar_y + bar_h // 2), 10)
    pygame.draw.circle(screen, (255, 150, 150), (knob_x, bar_y + bar_h // 2), 6)
    pct = fontSmall.render(f"{int(value * 100)}%", True, (255, 100, 100))
    screen.blit(pct, (bar_x + bar_w + 15, bar_y - 4))
    hint = fontSmall.render(hint_text, True, (80, 50, 50))
    screen.blit(hint, (bar_x, bar_y + 25))

def draw_menu(anim_time):
    global scroll, selected_index
    scroll += SCROLL_SPEED
    draw_bg_scene(screen, scroll, anim_time)

    for p in particles:
        p.update()
        s = pygame.Surface((int(p.size * 2), int(p.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*p.color, int(p.alpha)), (int(p.size), int(p.size)), int(p.size))
        screen.blit(s, (int(p.x - p.size), int(p.y - p.size)))

    title_y = 55
    for ox, oy, a in [(-3, 3, 60), (3, 3, 60), (0, 4, 80)]:
        ts = fontH.render("DEAD ROOSTER", True, (180, 0, 0))
        ts.set_alpha(a)
        screen.blit(ts, (40 + ox, title_y + oy))
    title_surf = fontH.render("DEAD ROOSTER", True, (255, 255, 255))
    screen.blit(title_surf, (40, title_y))

    sub_alpha = int(160 + 95 * math.sin(anim_time * 2.5))
    sub_surf = fontSmall.render("PRESS ENTER TO CONFIRM", True, (200, 60, 60))
    sub_surf.set_alpha(sub_alpha)
    screen.blit(sub_surf, (40, title_y + 58))

    btn_x = 50
    btn_start_y = 180
    btn_gap = 80
    mx, my = pygame.mouse.get_pos()

    for i, item in enumerate(menu_items):
        by = btn_start_y + i * btn_gap
        if btn_x <= mx <= btn_x + 300 and by <= my <= by + 50:
            selected_index = i
        is_selected = (i == selected_index)

        if is_selected:
            glow_w = int(260 + 30 * math.sin(anim_time * 4))
            glow_h = 54
            glow_surf = pygame.Surface((glow_w + 40, glow_h + 20), pygame.SRCALPHA)
            for layer in range(5):
                lw = glow_w - layer * 18
                lh = glow_h - layer * 6
                la = 30 - layer * 4
                if lw > 0 and lh > 0:
                    pygame.draw.rect(glow_surf, (220, 0, 0, la),
                                     (20 - layer * 9, 10 - layer * 3, lw, lh))
            pygame.draw.rect(glow_surf, (200, 0, 0, 80), (20, 10, glow_w, glow_h))
            pygame.draw.rect(glow_surf, (255, 60, 60, 40), (20, 10, glow_w, 4))
            screen.blit(glow_surf, (btn_x - 20, by - 10))
            pygame.draw.rect(screen, (255, 30, 30), (btn_x - 18, by + 5, 5, 44))
            scale_factor = 1.0 + 0.04 * math.sin(anim_time * 5)
            text_surf = fontU.render(item, True, (255, 255, 255))
            tw = int(text_surf.get_width() * scale_factor)
            th = int(text_surf.get_height() * scale_factor)
            text_surf = pygame.transform.scale(text_surf, (tw, th))
            screen.blit(text_surf, (btn_x + 10, by + 8))
        else:
            try:
                sf = pygame.font.Font("fonts/UI/lunchds.ttf", 28)
            except:
                sf = pygame.font.SysFont("Arial", 28)
            text_surf = sf.render(item, True, (120, 40, 40))
            screen.blit(text_surf, (btn_x + 10, by + 8))

    if bg_char:
        cx = 960 - bg_char.get_width() + 110
        cy = 540 - bg_char.get_height() + 50
        bob = int(4 * math.sin(anim_time * 2))
        screen.blit(bg_char, (cx, cy + bob))

    screen.blit(scanline_surf, (0, 0))

def setting():
    screen.fill((8, 5, 5))
    screen.blit(scanline_surf, (0, 0))
    s = fontH.render("SETTINGS", True, (255, 255, 255))
    screen.blit(s, (50, 50))
    s2 = fontSmall.render("BACKSPACE — return to menu", True, (150, 50, 50))
    screen.blit(s2, (50, 120))
    draw_bar("MUSIC VOLUME", music_volume, 255)
    draw_bar("SFX VOLUME",   sfx_volume,   400)

def authors():
    global easter_egg_active, easter_egg_timer, author_appear_time
    global author_click_counts, author_click_timers

    screen.fill((8, 5, 5))
    screen.blit(scanline_surf, (0, 0))

    for ox, oy, a in [(-2, 2, 50), (2, 2, 50)]:
        ts = fontH.render("AUTHORS", True, (180, 0, 0))
        ts.set_alpha(a)
        screen.blit(ts, (50 + ox, 30 + oy))
    screen.blit(fontH.render("AUTHORS", True, (255, 255, 255)), (50, 30))

    author_appear_time += 0.016
    y_pos = 115
    mx, my = pygame.mouse.get_pos()

    for sec_idx, (role, color, names) in enumerate(SECTIONS):
        appear_delay = sec_idx * 0.4
        appear_alpha = min(255, int((author_appear_time - appear_delay) * 300))
        if appear_alpha <= 0:
            y_pos += 32 + len(names) * 40 + 8
            continue

        line_w = min(280, int((author_appear_time - appear_delay) * 400))
        if line_w > 0:
            ls = pygame.Surface((line_w, 2), pygame.SRCALPHA)
            ls.fill((*color, appear_alpha))
            screen.blit(ls, (50, y_pos + 12))
        role_surf = fontSmall.render(role, True, color)
        role_surf.set_alpha(appear_alpha)
        screen.blit(role_surf, (50 + line_w + 8, y_pos))
        y_pos += 32

        for n_idx, name in enumerate(names):
            name_delay = appear_delay + 0.2 + n_idx * 0.15
            name_alpha = min(255, int((author_appear_time - name_delay) * 400))
            if name_alpha > 0:
                name_rect = pygame.Rect(70, y_pos, 420, 38)
                is_hovered = name_rect.collidepoint(mx, my)
                clicks = author_click_counts.get(name, 0)

                if is_hovered:
                    hover_s = pygame.Surface((420, 38), pygame.SRCALPHA)
                    hover_s.fill((*color, 25))
                    screen.blit(hover_s, (70, y_pos))

                if clicks >= 5:
                    r = min(255, 180 + clicks * 10)
                    name_color = (r, max(0, 200 - clicks * 20), 0)
                elif is_hovered:
                    name_color = (255, 255, 200)
                else:
                    name_color = (220, 220, 220)

                shake = random.randint(-clicks, clicks) if clicks >= 5 else 0
                offset_x = max(0, int((1.0 - (author_appear_time - name_delay) * 3) * 30))

                name_surf = fontU.render(name, True, name_color)
                name_surf.set_alpha(name_alpha)
                screen.blit(name_surf, (70 - offset_x + shake, y_pos))

                if clicks > 0:
                    cnt_surf = fontSmall.render("x" + str(clicks), True, (255, 80, 80))
                    screen.blit(cnt_surf, (500, y_pos + 8))

            y_pos += 40
        y_pos += 8

    hint = fontSmall.render("click a name...", True, (60, 30, 30))
    screen.blit(hint, (50, 470))

    for name in list(author_click_timers.keys()):
        author_click_timers[name] = author_click_timers.get(name, 0) + 0.016
        if author_click_timers[name] > 4.0:
            author_click_counts[name] = 0
            author_click_timers[name] = 0

    if easter_egg_active:
        easter_egg_timer += 0.016

        overlay = pygame.Surface((960, 540), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(200, int(easter_egg_timer * 300))))
        screen.blit(overlay, (0, 0))

        if easter_egg_timer < 3.5:
            flicker = math.sin(easter_egg_timer * 20)
            if flicker > -0.3:
                try:
                    big_font = pygame.font.Font("fonts/head/DiscoDuckItalic.otf", 120)
                except:
                    big_font = pygame.font.SysFont("Arial", 120, bold=True)

                for goff in [(5, 5), (-5, 5), (5, -5), (-5, -5)]:
                    glow = big_font.render("1488", True, (255, 0, 0))
                    glow.set_alpha(80)
                    screen.blit(glow, (960 // 2 - glow.get_width() // 2 + goff[0],
                                      540 // 2 - glow.get_height() // 2 + goff[1]))

                scale_anim = 1.0 + 0.06 * math.sin(easter_egg_timer * 8)
                main_text = big_font.render("1488", True, (255, 50, 0))
                tw = int(main_text.get_width() * scale_anim)
                th = int(main_text.get_height() * scale_anim)
                main_text = pygame.transform.scale(main_text, (tw, th))
                screen.blit(main_text, (960 // 2 - tw // 2, 540 // 2 - th // 2))

        if easter_egg_timer > 1.5:
            close = fontSmall.render("press any key to close", True, (100, 100, 100))
            close.set_alpha(min(255, int((easter_egg_timer - 1.5) * 200)))
            screen.blit(close, (960 // 2 - close.get_width() // 2, 430))

        if easter_egg_timer > 4.0:
            easter_egg_active = False
            author_click_counts = {}

    screen.blit(fontSmall.render("BACKSPACE — return to menu", True, (80, 40, 40)), (50, 510))

def handle_volume_mouse(mx, my):
    global music_volume, sfx_volume
    bar_x, bar_w = 50, 400
    # Музыка
    if bar_x <= mx <= bar_x + bar_w and 240 <= my <= 270:
        music_volume = max(0.0, min(1.0, (mx - bar_x) / bar_w))
        pygame.mixer.music.set_volume(music_volume ** 2)
    # SFX
    if bar_x <= mx <= bar_x + bar_w and 385 <= my <= 415:
        sfx_volume = max(0.0, min(1.0, (mx - bar_x) / bar_w))
        if snd_tap:
            snd_tap.set_volume(sfx_volume * 0.8)

prev_hovered = -1

running = True
while running:
    dt = clock.tick(60) / 1000.0
    anim_time += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "setting":
                mx, my = pygame.mouse.get_pos()
                handle_volume_mouse(mx, my)

            elif game_state == "menu":
                mx, my = pygame.mouse.get_pos()
                btn_x, btn_start_y, btn_gap = 50, 180, 80
                for i in range(len(menu_items)):
                    by = btn_start_y + i * btn_gap
                    if btn_x <= mx <= btn_x + 300 and by <= my <= by + 50:
                        if snd_tap: snd_tap.play()
                        if i == 0:
                            game_state = "game"
                        elif i == 1:
                            game_state = "setting"
                            change_music(setting_music_list)
                        elif i == 2:
                            game_state = "authors"
                            author_appear_time = 0

            elif game_state == "authors":
                if easter_egg_active:
                    easter_egg_active = False
                    author_click_counts = {}
                else:
                    mx, my = pygame.mouse.get_pos()
                    rects = get_author_rects()
                    for name, rect in rects.items():
                        if rect.collidepoint(mx, my):
                            author_click_counts[name] = author_click_counts.get(name, 0) + 1
                            author_click_timers[name] = 0
                            if author_click_counts[name] >= 7:
                                easter_egg_active = True
                                easter_egg_timer = 0
                            break

        elif event.type == pygame.MOUSEMOTION:
            if game_state == "setting" and pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                handle_volume_mouse(mx, my)
            elif game_state == "menu":
                mx, my = pygame.mouse.get_pos()
                btn_x, btn_start_y, btn_gap = 50, 180, 80
                hovered = -1
                for i in range(len(menu_items)):
                    by = btn_start_y + i * btn_gap
                    if btn_x <= mx <= btn_x + 300 and by <= my <= by + 50:
                        hovered = i
                        break
                if hovered != -1 and hovered != prev_hovered:
                    if snd_tap: snd_tap.play()
                prev_hovered = hovered

        elif event.type == pygame.MOUSEWHEEL:
            if game_state == "menu":
                if snd_tap: snd_tap.play()
                selected_index = (selected_index - event.y) % len(menu_items)

        elif event.type == pygame.KEYDOWN:
            if game_state == "menu":
                if event.key == pygame.K_UP:
                    if snd_tap: snd_tap.play()
                    selected_index = (selected_index - 1) % len(menu_items)
                elif event.key == pygame.K_DOWN:
                    if snd_tap: snd_tap.play()
                    selected_index = (selected_index + 1) % len(menu_items)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if snd_tap: snd_tap.play()
                    if selected_index == 0:
                        game_state = "game"
                    elif selected_index == 1:
                        game_state = "setting"
                        change_music(setting_music_list)
                    elif selected_index == 2:
                        game_state = "authors"
                        author_appear_time = 0

            elif game_state == "setting":
                if event.key == pygame.K_RIGHT:
                    music_volume = min(1.0, music_volume + 0.05)
                    pygame.mixer.music.set_volume(music_volume ** 2)
                elif event.key == pygame.K_LEFT:
                    music_volume = max(0.0, music_volume - 0.05)
                    pygame.mixer.music.set_volume(music_volume ** 2)
                elif event.key == pygame.K_BACKSPACE:
                    if snd_tap: snd_tap.play()
                    game_state = "menu"
                    change_music(menu_music_list)

            elif game_state == "authors":
                if easter_egg_active:
                    easter_egg_active = False
                    author_click_counts = {}
                elif event.key == pygame.K_BACKSPACE:
                    game_state = "menu"
                    author_appear_time = 0
                    author_click_counts = {}
                    change_music(menu_music_list)

            elif game_state == "game":
                if event.key == pygame.K_BACKSPACE:
                    game_state = "menu"
                    change_music(menu_music_list)

    if game_state == "menu":
        draw_menu(anim_time)
    elif game_state == "setting":
        setting()
    elif game_state == "authors":
        authors()
    elif game_state == "game":
        run_game(screen, clock, sfx_volume)
        game_state = "menu"
        try:
            pygame.mixer.music.load(random.choice(menu_music_list))
            pygame.mixer.music.set_volume(music_volume ** 2)
            pygame.mixer.music.play(-1)
        except:
            pass

    pygame.display.flip()

pygame.quit()
sys.exit()