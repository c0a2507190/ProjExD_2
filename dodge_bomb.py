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
    """
    オブジェクトが画面内か画面外かを判定し、真理値タプルを返す[cite: 36]
    引数 obj_rct: こうかとんRectまたは爆弾Rect[cite: 15]
    戻り値: タプル(横方向判定結果, 縦方向判定結果) [画面内:True / 画面外:False][cite: 15]
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def gameover(screen: pg.Surface) -> None:
    """
    追加機能1: こうかとん衝突時にゲームオーバー画面を表示する関数[cite: 25, 29]
    引数 screen: 描画先の画面Surface
    """
    # 1. 画面を半透明黒で暗転[cite: 29]
    black_out = pg.Surface((WIDTH, HEIGHT))
    black_out.set_alpha(180)
    black_out.fill((0, 0, 0))
    screen.blit(black_out, (0, 0))

    # 2. 「Game Over」文字列の生成と配置[cite: 29]
    font = pg.font.Font(None, 80)
    txt = font.render("Game Over", True, (255, 255, 255))
    txt_rct = txt.get_rect()
    txt_rct.center = WIDTH // 2, HEIGHT // 2

    # 3. 泣いているこうかとん（8.png）の配置[cite: 29]
    kk_img = pg.transform.rotozoom(pg.image.load("fig/8.png"), 0, 0.9)
    kk_rct_l = kk_img.get_rect()
    kk_rct_r = kk_img.get_rect()
    kk_rct_l.center = WIDTH // 2 - 200, HEIGHT // 2
    kk_rct_r.center = WIDTH // 2 + 200, HEIGHT // 2

    # 4. 画面への貼り付けと更新[cite: 29]
    screen.blit(txt, txt_rct)
    screen.blit(kk_img, kk_rct_l)
    screen.blit(kk_img, kk_rct_r)
    pg.display.update()

    # 5. 5秒間停止[cite: 29]
    time.sleep(5)


def init_bb_imgs() -> tuple[list[pg.Surface], list[int]]:
    """
    追加機能2: 時間経過に伴い拡大・加速する爆弾Surface群と加速度のリストを生成する関数[cite: 25, 30]
    戻り値: (爆弾Surfaceのリスト, 加速度のリスト) のタプル
    """
    bb_imgs = []
    bb_accs = [a for a in range(1, 11)]  # 加速度 1～10[cite: 30]

    for r in range(1, 11):
        bb_img = pg.Surface((20 * r, 20 * r))
        pg.draw.circle(bb_img, (255, 0, 0), (10 * r, 10 * r), 10 * r)
        bb_img.set_colorkey((0, 0, 0))
        bb_imgs.append(bb_img)

    return bb_imgs, bb_accs


def get_kk_imgs() -> dict[tuple[int, int], pg.Surface]:
    """
    追加機能3: 移動量タプルに対応するこうかとんSurfaceの辞書を生成する関数[cite: 25, 31]
    戻り値: 移動量タプルをキー、回転・反転したこうかとんSurfaceを値とする辞書
    """
    img_base = pg.image.load("fig/3.png")
    img_flip = pg.transform.flip(img_base, True, False)  # 右向き用反転

    kk_imgs = {
        (0, 0): pg.transform.rotozoom(img_base, 0, 0.9),
        (-5, 0): pg.transform.rotozoom(img_base, 0, 0.9),  # 左
        (-5, -5): pg.transform.rotozoom(img_base, -45, 0.9),  # 左上
        (0, -5): pg.transform.rotozoom(img_flip, 90, 0.9),  # 上
        (+5, -5): pg.transform.rotozoom(img_flip, 45, 0.9),  # 右上
        (+5, 0): pg.transform.rotozoom(img_flip, 0, 0.9),  # 右
        (+5, +5): pg.transform.rotozoom(img_flip, -45, 0.9),  # 右下
        (0, +5): pg.transform.rotozoom(img_flip, -90, 0.9),  # 下
        (-5, +5): pg.transform.rotozoom(img_base, 45, 0.9),  # 左下
    }
    return kk_imgs


def calc_orientation(
    org: pg.Rect, dst: pg.Rect, current_xy: tuple[float, float]
) -> tuple[float, float]:
    """
    追加機能4: 爆弾からこうかとんへの追従方向ベクトルを計算する関数[cite: 25, 32]
    引数 org: 爆弾Rect
    引数 dst: こうかとんRect[cite: 32]
    引数 current_xy: 計算前の方向ベクトル (vx, vy)[cite: 32]
    戻り値: 正規化された方向ベクトル (vx, vy)[cite: 32]
    """
    dx = dst.centerx - org.centerx
    dy = dst.centery - org.centery
    norm = math.hypot(dx, dy)

    # 距離が300未満の場合、または距離が0の場合は慣性でそのまま進む[cite: 32]
    if norm < 300 or norm == 0:
        return current_xy

    # ベクトルのノルムが√50になるように正規化[cite: 32]
    vx = (dx / norm) * math.sqrt(50)
    vy = (dy / norm) * math.sqrt(50)
    return vx, vy


def check_dash(key_lst: pg.key.ScancodeWrapper) -> int:
    """
    追加機能5: Shiftキー押下時にダッシュ倍率を返す関数[cite: 25, 39]
    引数 key_lst: pg.key.get_pressed() の戻り値
    戻り値: ダッシュ時の倍率（Shift押下時: 2, 通常時: 1）
    """
    if key_lst[pg.K_LSHIFT] or key_lst[pg.K_RSHIFT]:
        return 2
    return 1


def main():
    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))

    bg_img = pg.image.load("fig/pg_bg.jpg")

    # こうかとん画像の準備[cite: 31]
    kk_imgs = get_kk_imgs()
    kk_img = kk_imgs[(0, 0)]
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200

    # 爆弾画像リストと加速度の準備[cite: 30]
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

        # 衝突判定とゲームオーバー処理[cite: 23, 29]
        if kk_rct.colliderect(bb_rct):
            gameover(screen)
            return

        screen.blit(bg_img, [0, 0])

        # 爆弾の拡大・加速・追従移動処理[cite: 30, 32]
        idx = min(tmr // 500, 9)  # 500フレームごとに拡大・加速[cite: 30]
        vx, vy = calc_orientation(bb_rct, kk_rct, (vx, vy))  # 追従ベクトル算出[cite: 32]
        avx = vx * bb_accs[idx]  # 加速度適用[cite: 30]
        avy = vy * bb_accs[idx]

        bb_img = bb_imgs[idx]
        center = bb_rct.center
        bb_rct = bb_img.get_rect()
        bb_rct.center = center  # 中心座標を維持[cite: 30]

        bb_rct.move_ip(avx, avy)
        yoko, tate = check_bound(bb_rct)
        if not yoko:
            vx *= -1
        if not tate:
            vy *= -1
        screen.blit(bb_img, bb_rct)

        # こうかとんの移動と向きの切替処理[cite: 21, 31]
        key_lst = pg.key.get_pressed()
        speed = check_dash(key_lst)  # 追加機能5: ダッシュ倍率取得

        sum_mv = [0, 0]
        for key, delta in DELTA.items():
            if key_lst[key]:
                sum_mv[0] += delta[0] * speed
                sum_mv[1] += delta[1] * speed

        kk_rct.move_ip(sum_mv)
        yoko, tate = check_bound(kk_rct)
        if not yoko or not tate:
            kk_rct.move_ip(-sum_mv[0], -sum_mv[1])

        # 画像切り替え用の移動量正規化（速度が2倍になっても対応する画像を引く処理）[cite: 31]
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