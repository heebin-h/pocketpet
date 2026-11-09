# -*- coding: utf-8 -*-
"""
BEATLING Rev A 탁상형 함체 — FreeCAD 파라메트릭 스크립트

실행:
  /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
    /Users/heebiny/diyProj/pocketpet/beatling/hw/cad/beatling_enclosure.py

출력 (OUT_DIR):
  beatling_shell.step / .stl   상부 쉘 (전·후·좌·우·상면, 바닥 개방)
  beatling_base.step  / .stl   바닥판 (보드 스탠드오프 + 캐리어 스탠드오프)
  beatling_assembly.step       조립 확인용 (쉘 + 바닥판 + 보드/스피커 더미)

좌표계: X=폭(왼→오), Y=깊이(전면 y=0 → 후면), Z=높이(바닥 z=0). 단위 mm.
[MEASURE] 표시 값은 실물 실측 후 수정해야 하는 추정값이다.
"""
import os
import sys
import FreeCAD as App
import Part
import Mesh

OUT_DIR = "/Users/heebiny/diyProj/pocketpet/beatling/hw/cad/out"

# ---------------------------------------------------------------- 외형
W, D, H = 100.0, 90.0, 62.0     # 외형
T = 2.4                          # 벽 두께
R_OUT = 6.0                      # 외곽 수직 모서리 R
CLR = 0.2                        # 바닥판-쉘 끼움 공차(편측)

# ---------------------------------------------------------------- ROCK Pi S (공식 product brief Rev1.5 §4)
PCB = 43.2                       # 보드 한 변
PCB_T = 1.6                      # [MEASURE] PCB 두께
HOLE_D = 2.5                     # 장착홀 4x Ø2.5 (brief)
HOLE_INSET = 3.0                 # [MEASURE] 보드 모서리→장착홀 중심 (brief 미기재)
ETH_OVERHANG = 48.0 - 43.2       # brief 도면: 이더넷 잭 돌출 포함 48.0
STANDOFF_H = 6.0
BOARD_X0 = 12.0                  # 보드 좌측 모서리 X (좌후측 코너 보스 회피: 보스 x≤9.9)
BOARD_Y1 = D - T - ETH_OVERHANG  # 보드 후측 모서리 (잭 면이 후면 내벽에 닿도록)
BOARD_Y0 = BOARD_Y1 - PCB
BOARD_Z0 = T + STANDOFF_H        # PCB 하면

# 후면 포트 개구 (이더넷+USB-A 통합 개구) — 위치/크기 [MEASURE]
PORT_W, PORT_H = 40.0, 17.0
PORT_CX = BOARD_X0 + PCB / 2.0   # [MEASURE] 보드 중심 기준 가정
PORT_Z0 = BOARD_Z0 + PCB_T - 0.5

# 전원 입력 USB-C 브레이크아웃 (후면 우측) [MEASURE: 브레이크아웃 모델]
USBC_W, USBC_H = 9.6, 3.8
USBC_CX, USBC_CZ = 82.0, 14.0

# ---------------------------------------------------------------- 전면 (y=0)
OLED_WIN_W, OLED_WIN_H = 24.0, 13.0   # [MEASURE] 0.96" SSD1306 표시영역 ≈21.7x10.9 + 여유
OLED_CX, OLED_CZ = W / 2.0, 44.0
LED_D, LED_CX, LED_CZ = 3.2, W / 2.0 + 20.0, 44.0
BTN_D = 10.5                           # 12x12 택트 + Ø10 캡
BTN_CZ = 20.0
BTN_PITCH = 20.0
BTN_COUNT = 4                          # FEED / PLAY / SLEEP / TALK

# ---------------------------------------------------------------- 상면 (z=H)
ENC_D = 7.2                            # EC11 부싱 M7
ENC_CX, ENC_CY = 75.0, 30.0
ENC_TAB_D, ENC_TAB_OFF = 2.6, 7.8      # [MEASURE] EC11 회전방지 탭 위치

# ---------------------------------------------------------------- 우측면 (x=W) 스피커
SPK_D = 40.0                           # 40mm 4Ω 3W [MEASURE]
SPK_CY, SPK_CZ = 60.0, 34.0
GRILLE_HOLE_D, GRILLE_PITCH = 2.5, 4.5
GRILLE_R = 16.0
SPK_RING_H = 3.0                       # 스피커 고정 링 높이(내벽에서)

# ---------------------------------------------------------------- 좌측면 (x=0)
JACK_D, JACK_CY, JACK_CZ = 6.2, 30.0, 20.0   # 3.5mm PJ-320 계열 [MEASURE]
MIC_D, MIC_CY, MIC_CZ = 2.0, 20.0, 46.0      # 음향 포트 (캡슐 Ø9.7은 내부 부트)
MIC_BOOT_D, MIC_BOOT_ID, MIC_BOOT_H = 13.0, 9.9, 4.0

# ---------------------------------------------------------------- 체결
BOSS_D, BOSS_PILOT = 7.0, 2.5          # M3 셀프탭 파일럿
BOSS_INSET = T + BOSS_D / 2.0 + 0.5
PLATE_SCREW_D = 3.4


def vec(x, y, z):
    return App.Vector(x, y, z)


def rounded_box(w, d, h, r, x=0.0, y=0.0, z=0.0):
    b = Part.makeBox(w, d, h, vec(x, y, z))
    if r > 0:
        edges = [e for e in b.Edges
                 if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 1e-6]
        b = b.makeFillet(r, edges)
    return b


def cyl_x(d, length, x, cy, cz):
    return Part.makeCylinder(d / 2.0, length, vec(x, cy, cz), vec(1, 0, 0))


def cyl_y(d, length, cx, y, cz):
    return Part.makeCylinder(d / 2.0, length, vec(cx, y, cz), vec(0, 1, 0))


def cyl_z(d, length, cx, cy, z):
    return Part.makeCylinder(d / 2.0, length, vec(cx, cy, z), vec(0, 0, 1))


def boss_xy():
    return [(BOSS_INSET, BOSS_INSET), (W - BOSS_INSET, BOSS_INSET),
            (BOSS_INSET, D - BOSS_INSET), (W - BOSS_INSET, D - BOSS_INSET)]


def make_shell():
    outer = rounded_box(W, D, H, R_OUT)
    # 바닥 개방 + 바닥판 수용: 내부 캐비티는 z=-1 부터 H-T 까지
    inner = rounded_box(W - 2 * T, D - 2 * T, H - T + 1.0, max(R_OUT - T, 0.5),
                        T, T, -1.0)
    shell = outer.cut(inner)

    # 코너 보스 (바닥판 위 z=T 부터 천장까지)
    for (bx, by) in boss_xy():
        boss = cyl_z(BOSS_D, H - T - T, bx, by, T)
        shell = shell.fuse(boss)
        shell = shell.cut(cyl_z(BOSS_PILOT, 12.0, bx, by, T - 0.01))

    # 스피커 고정 링 (우측 내벽)
    ring_o = cyl_x(SPK_D + 4.0, SPK_RING_H, W - T - SPK_RING_H, SPK_CY, SPK_CZ)
    ring_i = cyl_x(SPK_D + 0.6, SPK_RING_H + 0.2, W - T - SPK_RING_H - 0.1, SPK_CY, SPK_CZ)
    shell = shell.fuse(ring_o.cut(ring_i))

    # 마이크 부트 (좌측 내벽) — 캡슐 압입 + 개스킷
    boot_o = cyl_x(MIC_BOOT_D, MIC_BOOT_H, T, MIC_CY, MIC_CZ)
    boot_i = cyl_x(MIC_BOOT_ID, MIC_BOOT_H + 0.2, T + 0.6, MIC_CY, MIC_CZ)
    shell = shell.fuse(boot_o.cut(boot_i))

    cuts = []
    # 전면
    cuts.append(Part.makeBox(OLED_WIN_W, T + 2, OLED_WIN_H,
                             vec(OLED_CX - OLED_WIN_W / 2, -1, OLED_CZ - OLED_WIN_H / 2)))
    cuts.append(cyl_y(LED_D, T + 2, LED_CX, -1, LED_CZ))
    x0 = W / 2.0 - BTN_PITCH * (BTN_COUNT - 1) / 2.0
    for i in range(BTN_COUNT):
        cuts.append(cyl_y(BTN_D, T + 2, x0 + i * BTN_PITCH, -1, BTN_CZ))
    # 상면
    cuts.append(cyl_z(ENC_D, T + 2, ENC_CX, ENC_CY, H - T - 1))
    cuts.append(cyl_z(ENC_TAB_D, 1.2 + 1, ENC_CX + ENC_TAB_OFF, ENC_CY, H - T - 1))
    # 우측 그릴 (원 안 격자)
    n = int(GRILLE_R // GRILLE_PITCH)
    for iy in range(-n, n + 1):
        for iz in range(-n, n + 1):
            dy, dz = iy * GRILLE_PITCH, iz * GRILLE_PITCH
            if dy * dy + dz * dz <= GRILLE_R * GRILLE_R:
                cuts.append(cyl_x(GRILLE_HOLE_D, T + 2, W - T - 1, SPK_CY + dy, SPK_CZ + dz))
    # 좌측
    cuts.append(cyl_x(JACK_D, T + 2, -1, JACK_CY, JACK_CZ))
    cuts.append(cyl_x(MIC_D, T + 2 + 0.6, -1, MIC_CY, MIC_CZ))
    # 후면
    cuts.append(Part.makeBox(PORT_W, T + 2, PORT_H,
                             vec(PORT_CX - PORT_W / 2, D - T - 1, PORT_Z0)))
    cuts.append(Part.makeBox(USBC_W, T + 2, USBC_H,
                             vec(USBC_CX - USBC_W / 2, D - T - 1, USBC_CZ - USBC_H / 2)))

    shell = shell.cut(Part.makeCompound(cuts))
    return shell.removeSplitter()


def make_base():
    pw, pd = W - 2 * T - 2 * CLR, D - 2 * T - 2 * CLR
    plate = rounded_box(pw, pd, T, max(R_OUT - T - CLR, 0.5), T + CLR, T + CLR, 0.0)

    # 보드 스탠드오프
    for hx in (BOARD_X0 + HOLE_INSET, BOARD_X0 + PCB - HOLE_INSET):
        for hy in (BOARD_Y0 + HOLE_INSET, BOARD_Y0 + PCB - HOLE_INSET):
            so = cyl_z(5.0, STANDOFF_H, hx, hy, T)
            so = so.cut(cyl_z(2.1, STANDOFF_H + 1, hx, hy, T + 0.6))  # M2.5 셀프탭 파일럿
            plate = plate.fuse(so)

    # 캐리어(만능기판 40x24) 스탠드오프 — 전면-우측 영역
    car_x0, car_y0, car_w, car_d = 52.0, 13.0, 40.0, 24.0
    for cx in (car_x0 + 2.5, car_x0 + car_w - 2.5):
        for cy in (car_y0 + 2.5, car_y0 + car_d - 2.5):
            so = cyl_z(5.0, 5.0, cx, cy, T)
            so = so.cut(cyl_z(2.1, 6.0, cx, cy, T + 0.6))
            plate = plate.fuse(so)

    # 코너 체결 홀 (카운터보어)
    for (bx, by) in boss_xy():
        plate = plate.cut(cyl_z(PLATE_SCREW_D, T + 2, bx, by, -1))
        plate = plate.cut(cyl_z(6.2, 1.2, bx, by, -0.01))

    # 보드 하부 통풍 슬롯
    for i in range(5):
        sx = BOARD_X0 + 8 + i * 6.0
        plate = plate.cut(Part.makeBox(2.5, 26.0, T + 2, vec(sx, BOARD_Y0 + 8.6, -1)))

    # 고무발 자리 (Ø10 x 0.6 음각)
    for (fx, fy) in ((12, 12), (W - 12, 12), (12, D - 12), (W - 12, D - 12)):
        plate = plate.cut(cyl_z(10.0, 0.6, fx, fy, -0.01))

    return plate.removeSplitter()


def make_dummies():
    board = Part.makeBox(PCB, PCB, PCB_T, vec(BOARD_X0, BOARD_Y0, BOARD_Z0))
    eth = Part.makeBox(16.0, 21.0, 13.5,                      # [MEASURE]
                       vec(PORT_CX - 8.0 - 6.0, BOARD_Y1 + ETH_OVERHANG - 21.0, BOARD_Z0 + PCB_T))
    spk = cyl_x(SPK_D, 15.0, W - T - SPK_RING_H - 15.0, SPK_CY, SPK_CZ)
    return Part.makeCompound([board, eth, spk])


def check(name, shape):
    ok = shape.isValid()
    bb = shape.BoundBox
    print("[%s] valid=%s solids=%d volume=%.1f mm3 bbox=(%.1f x %.1f x %.1f)"
          % (name, ok, len(shape.Solids), shape.Volume, bb.XLength, bb.YLength, bb.ZLength))
    if not ok or len(shape.Solids) == 0:
        raise RuntimeError("invalid shape: " + name)


def interference(a, b, name):
    v = a.common(b).Volume
    print("[interference %s] %.3f mm3" % (name, v))
    return v


def export(shape, base):
    step = os.path.join(OUT_DIR, base + ".step")
    shape.exportStep(step)
    stl = os.path.join(OUT_DIR, base + ".stl")
    mesh = Mesh.Mesh(shape.tessellate(0.05))
    mesh.write(stl)
    print("exported:", step, stl)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    shell = make_shell()
    base = make_base()
    dummies = make_dummies()
    check("shell", shell)
    check("base", base)

    # 조립 간섭 검사: 쉘-바닥판, 쉘-더미(보드/잭/스피커)
    bad = 0.0
    bad += interference(shell, base, "shell-base")
    for i, s in enumerate(dummies.Solids):
        bad += interference(shell, s, "shell-dummy%d" % i)
        bad += interference(base, s, "base-dummy%d" % i)
    if bad > 0.5:
        print("WARNING: interference total %.2f mm3" % bad)

    export(shell, "beatling_shell")
    export(base, "beatling_base")
    Part.makeCompound([shell, base, dummies]).exportStep(
        os.path.join(OUT_DIR, "beatling_assembly.step"))
    print("done")


main()
