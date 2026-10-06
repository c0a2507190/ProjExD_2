import math
import os
import random
import sys
import time
import pygame as pg

WIDTH, HEIGHT = 1100, 650
DELTA = {
    pg.K_UP: (0, -5),
    pg.K_DOWN: (0, +5),
    pg.K_LEFT: (-5, 0),
    pg.K_RIGHT: (+5, 0),
}
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def gameover(screen: pg.Surface) -> None:
    black_out = pg.Surface((WIDTH, HEIGHT))
    black_out.set_alpha(180)
    black_out.fill((0, 0, 0))
    screen.blit(black_out, (0, 0))

    font = pg.font.Font(None, 80)
    txt = font.render("Game Over", True, (255, 255, 255))
    txt_rct = txt.get_rect()
    txt_rct.center = WIDTH // 2, HEIGHT // 2

    kk_img = pg.transform.rotozoom(pg.image.load("fig/8.png"), 0, 0.9)
    kk_rct_l = kk_img.get_rect()
    kk_rct_r = kk_img.get_rect()
    kk_rct_l.center = WIDTH // 2 - 200, HEIGHT // 2
    kk_rct_r.center = WIDTH // 2 + 200, HEIGHT // 2

    screen.blit(txt, txt_rct)
    screen.blit(kk_img, kk_rct_l)
    screen.blit(kk_img, kk_rct_r)
    pg.display.update()

    time.sleep(5)


def init_bb_imgs() -> tuple[list[pg.Surface], list[int]]:
    bb_imgs = []
    bb_accs = [a for a in range(1, 11)]

    for r in range(1, 11):
        bb_img = pg.Surface((20 * r, 20 * r))
        pg.draw.circle(bb_img, (255, 0, 0), (10 * r, 10 * r), 10 * r)
        bb_img.set_colorkey((0, 0, 0))
        bb_imgs.append(bb_img)

    return bb_imgs, bb_accs


def get_kk_imgs() -> dict[tuple[int, int], pg.Surface]:
    img_base = pg.image.load("fig/3.png")
    img_flip = pg.transform.flip(img_base, True, False)

    kk_imgs = {
        (0, 0): pg.transform.rotozoom(img_base, 0, 0.9),
        (-5, 0): pg.transform.rotozoom(img_base, 0, 0.9),
        (-5, -5): pg.transform.rotozoom(img_base, -45, 0.9),
        (0, -5): pg.transform.rotozoom(img_flip, 90, 0.9),
        (+5, -5): pg.transform.rotozoom(img_flip, 45, 0.9),
        (+5, 0): pg.transform.rotozoom(img_flip, 0, 0.9),
        (+5, +5): pg.transform.rotozoom(img_flip, -45, 0.9),
        (0, +5): pg.transform.rotozoom(img_flip, -90, 0.9),
        (-5, +5): pg.transform.rotozoom(img_base, 45, 0.9),
    }
    return kk_imgs


def calc_orientation(
    org: pg.Rect, dst: pg.Rect, current_xy: tuple[float, float]
) -> tuple[float, float]:
    dx = dst.centerx - org.centerx
    dy = dst.centery - org.centery
    norm = math.hypot(dx, dy)

    if norm < 300 or norm == 0:
        return current_xy

    vx = (dx / norm) * math.sqrt(50)
    vy = (dy / norm) * math.sqrt(50)
    return vx, vy


def check_dash(key_lst: pg.key.ScancodeWrapper) -> int:
    if key_lst[pg.K_LSHIFT] or key_lst[pg.K_RSHIFT]:
        return 2
    return 1


def main():
    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))

    bg_img = pg.image.load("fig/pg_bg.jpg")

    kk_imgs = get_kk_imgs()
    kk_img = kk_imgs[(0, 0)]
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200

    bb_imgs, bb_accs = init_bb_imgs()
    bb_img = bb_imgs[0]
    bb_rct = bb_img.get_rect()
    bb_rct.center = (random.randint(0, WIDTH), random.randint(0, HEIGHT))
    vx, vy = +5.0, +5.0

    clock = pg.time.Clock()
    tmr = 0

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return

        if kk_rct.colliderect(bb_rct):
            gameover(screen)
            return

        screen.blit(bg_img, [0, 0])

        idx = min(tmr // 500, 9)
        vx, vy = calc_orientation(bb_rct, kk_rct, (vx, vy))
        avx = vx * bb_accs[idx]
        avy = vy * bb_accs[idx]

        bb_img = bb_imgs[idx]
        center = bb_rct.center
        bb_rct = bb_img.get_rect()
        bb_rct.center = center

        bb_rct.move_ip(avx, avy)
        yoko, tate = check_bound(bb_rct)
        if not yoko:
            vx *= -1
        if not tate:
            vy *= -1
        screen.blit(bb_img, bb_rct)

        key_lst = pg.key.get_pressed()
        speed = check_dash(key_lst)

        sum_mv = [0, 0]
        for key, delta in DELTA.items():
            if key_lst[key]:
                sum_mv[0] += delta[0] * speed
                sum_mv[1] += delta[1] * speed

        kk_rct.move_ip(sum_mv)
        yoko, tate = check_bound(kk_rct)
        if not yoko or not tate:
            kk_rct.move_ip(-sum_mv[0], -sum_mv[1])

        norm_mv = (
            0 if sum_mv[0] == 0 else (sum_mv[0] // abs(sum_mv[0])) * 5,
            0 if sum_mv[1] == 0 else (sum_mv[1] // abs(sum_mv[1])) * 5,
        )
        kk_img = kk_imgs[norm_mv]
        screen.blit(kk_img, kk_rct)

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()