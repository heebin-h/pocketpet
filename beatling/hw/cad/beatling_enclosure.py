# -*- coding: utf-8 -*-
"""
BEATLING Rev A 함체 — "가로 포켓 플레이어" (기획서 D11, §6.5) FreeCAD 파라메트릭 스크립트

실행:
  /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
    /Users/heebiny/diyProj/pocketpet/beatling/hw/cad/beatling_enclosure.py

출력:
  OUT_DIR/beatling_shell.step|.stl     전면 쉘 (전면 + 4측면, 뒤 개방)
  OUT_DIR/beatling_cover.step|.stl     뒤판 (보드·캐리어 스탠드오프)
  OUT_DIR/beatling_keycaps.step|.stl   윗면 건반 키캡 4개
  OUT_DIR/beatling_assembly.step       조립 확인용 (부품 더미 포함)
  OUT_DIR/check.txt                    검사 결과 (아래 main() 출력과 동일)
  LAYOUT_SVG                           3면 배치도 (부품 외곽 bbox 투영) — 리뷰용, git 추적

좌표계: X=폭(정면에서 왼→오), Y=깊이(전면 y=0 → 후면 y=D), Z=높이(바닥 z=0). 단위 mm.
표기: [MEASURE] 실물 실측 후 수정할 추정값 / [DWG] Radxa product brief Rev1.5 p.7 도면에서
      픽셀 계측한 값(±0.3mm) / [예시] 부품 미선정, 대표 치수.

조립 순서 (검사 대상):
  1) 쉘에 전면 부품 장착: OLED(리브 포켓), 스피커(리브 포켓), 엔코더·LED·3.5mm 잭(패널),
     전원 USB-C 브레이크아웃(우측 선반), 키캡 → 키 기판(윗면 레일에 뒤에서 슬라이드).
  2) 뒤판에 ROCK Pi S(부품면이 뒤판 쪽)와 캐리어를 스탠드오프로 고정.
  3) 뒤판을 -Y 방향으로 밀어 넣고 코너 보스 4개에 M3 체결.
  → 2)의 부품이 3)의 삽입 경로에서 1)의 부품·쉘과 부딪히지 않는지 sweep 검사.
"""
import os
import itertools
import FreeCAD as App
import Part
import Mesh

OUT_DIR = os.environ.get("BEATLING_CAD_OUT",
                         "/Users/heebiny/diyProj/pocketpet/beatling/hw/cad/out")
LAYOUT_SVG = os.environ.get("BEATLING_CAD_LAYOUT",
                            "/Users/heebiny/diyProj/pocketpet/beatling/hw/cad/layout.svg")

# ================================================================ 외형
W, H, D = 120.0, 62.0, 30.0      # 폭 x 높이 x 두께 (기획서 §6.5 목표 120x62x30)
T = 2.4                          # 벽 두께
R_OUT = 8.0                      # 정면에서 보이는 4 모서리 R (Y 방향 모서리)
CLR = 0.2                        # 뒤판-쉘 끼움 공차 (편측)
GAP = 0.5                        # 부품 간 설계 최소 여유
MIN_GAP_ASSERT = 0.0             # 간섭 판정: 공통 부피 > 1e-3 mm3 이면 실패

# ================================================================ 앞면 층 (y = T 부터 뒤로)
# OLED 0.96" SSD1306 모듈 [MEASURE] — 헤더 핀 미장착, 전선 직납 가정
OLED_MOD_W, OLED_MOD_H = 27.3, 27.8
OLED_GLASS_W, OLED_GLASS_H = 26.7, 19.3
OLED_GLASS_T, OLED_PCB_T, OLED_BACK_T = 1.5, 1.2, 1.5
OLED_CX, OLED_CZ = 32.0, 35.9            # 모듈 중심
OLED_GLASS_DZ = 3.5                      # 유리 중심이 모듈 중심보다 위 [MEASURE]
OLED_WIN_W, OLED_WIN_H = 23.0, 12.0      # 표시영역 21.74x10.86 + 여유
OLED_RIB_T, OLED_RIB_CLR = 1.2, 0.3

# 스피커 — 슬림 직사각형 마이크로 스피커 [예시: 30x20x5, 모델 선정 후 MEASURE]
SPK_W, SPK_H, SPK_T = 30.0, 20.0, 5.0
SPK_CX, SPK_CZ = 79.0, 14.0
SPK_GASKET = 0.4
SPK_RIB_T, SPK_RIB_H, SPK_RIB_CLR = 1.2, 3.0, 0.3
GRILLE_SLOT_W, GRILLE_PITCH = 1.6, 3.2
GRILLE_SPAN_X, GRILLE_SPAN_Z = 24.0, 12.0

# EC11 엔코더 (전면 우측, 다이얼) [MEASURE]
ENC_CX, ENC_CZ = 96.0, 40.0
ENC_BODY_W, ENC_BODY_H, ENC_BODY_T, ENC_PIN_T = 12.4, 13.2, 6.5, 3.5
ENC_D = 7.2                              # M7 부싱
ENC_TAB_D, ENC_TAB_OFF = 2.6, 7.8        # 회전방지 탭 (Z+ 방향) [MEASURE]

# LED Ø3
LED_D, LED_CX, LED_CZ, LED_LEN = 3.2, 68.0, 42.0, 5.3

# ================================================================ ROCK Pi S (부품면이 뒤(+Y)를 향함)
PCB, PCB_T = 43.2, 1.6
ETH_OVERHANG = 48.0 - 43.2               # brief 도면
HOLE_D = 2.5
HOLE_INSET_X, HOLE_INSET_Z = 2.4, 2.5    # [DWG] 장착홀 중심-모서리
HDR_TAIL = 3.0                           # 헤더 납땜 꼬리 (보드 뒷면=앞쪽) [MEASURE]
HDR_PIN = 8.5                            # 헤더 플라스틱+핀 높이 (부품면) [MEASURE]
HDR_ROW_W = 5.07                         # 2열 헤더 폭 (가장자리부터) [DWG]
ETH_H, ETH_LEN = 13.5, 21.0              # [MEASURE]
PORT_FACE_GAP = 0.5                      # 잭 면 ↔ 좌측 내벽
BOARD_Z0 = 5.0
BOARD_X0 = T + PORT_FACE_GAP + ETH_OVERHANG
BOARD_X1 = BOARD_X0 + PCB
BOARD_Z1 = BOARD_Z0 + PCB


def dwg_x(dx):
    """brief 도면 좌측 모서리부터 거리 dx → 함체 X (뒤에서 보면 도면과 같은 방향)."""
    return BOARD_X1 - dx


def dwg_z(dy):
    """brief 도면 상단 모서리부터 거리 dy → 함체 Z."""
    return BOARD_Z1 - dy


ETH_DY = (18.0, 34.2)                    # [DWG] 이더넷 폭 구간
USBA_DY = (9.1, 15.0)                    # [DWG] USB-A 폭 구간 (5.9mm → 세로형 추정) [MEASURE]
USBA_H, USBA_LEN = 13.5, 14.0            # [MEASURE]
BUSBC_DY = (19.0 - 4.5, 19.0 + 4.5)      # [DWG] 보드 USB-C (Maskrom 전용) 중심 dy≈18.9
HDR_DX = (4.9, 38.2)                     # [DWG] 헤더 X 구간
SOC_DXY = (19.3, 19.0)                   # [DWG] SoC 중심 → 뒤판 통풍구 위치

# Y 스택: 전면벽 → OLED → 여유 → 헤더 꼬리 → PCB → 이더넷 → 여유 → 뒤판
OLED_STACK = OLED_GLASS_T + OLED_PCB_T + OLED_BACK_T
PCB_Y0 = T + OLED_STACK + GAP + HDR_TAIL
PCB_Y1 = PCB_Y0 + PCB_T
COVER_Y0 = D - T                         # 뒤판 안쪽 면

# ================================================================ 캐리어 (뒤판 스탠드오프, 부품면이 앞)
CAR_X0, CAR_X1, CAR_Z0, CAR_Z1 = 62.0, 102.0, 4.0, 28.0
CAR_STANDOFF = 5.0
CAR_PART_H = 12.0                        # 최대 부품 높이 (470uF 전해 8x12) [MEASURE]

# ================================================================ 우측면 (x = W)
JACK_D, JACK_CY, JACK_CZ = 6.2, 15.0, 16.0   # 3.5mm 패널 잭 [MEASURE]
JACK_BODY_D, JACK_BODY_L = 8.0, 14.0
PWR_CY, PWR_CZ = 15.0, 42.0                  # 전원 USB-C 브레이크아웃 [MEASURE]
PWR_W, PWR_H = 9.6, 3.8                      # 개구
PWR_REC_L, PWR_PCB_L, PWR_PCB_W = 7.3, 14.0, 10.0

# ================================================================ 좌측면 (x = 0) 포트 포켓
PORT_POCKET_DEPTH = 1.4                  # 바깥에서 파서 벽을 2.4→1.0 (플러그 삽입 깊이 확보)
PORT_MARGIN = 0.5

# ================================================================ 윗면 키 + 마이크
KEY_CY = 14.5
KEY_XS = (27.0, 45.0, 75.0, 93.0)        # FEED / PLAY / SLEEP / TALK, 가운데는 마이크
KEY_W, KEY_DY = 14.0, 10.0               # 키캡 상단
KEY_HOLE_CLR = 0.2
KEY_FLANGE_W, KEY_FLANGE_DY, KEY_FLANGE_T = 16.0, 12.4, 1.0
KEY_PROUD = 2.0                          # 윗면 위로 돌출
SW_SIZE, SW_BODY_H, SW_STEM_D, SW_STEM_H = 12.0, 3.6, 3.5, 0.7   # 12x12 택트 [MEASURE]
KEY_PLUNGER_D, KEY_PLUNGER_GAP = 3.0, 0.1
KB_X0, KB_X1, KB_Y0, KB_Y1 = 12.0, 107.0, 4.0, 25.0   # 키 기판
KB_PCB_T, KB_TAIL = 1.6, 2.0
RAIL_T, RAIL_LIP = 1.2, 2.3
MIC_CX, MIC_D, MIC_CAP_D, MIC_CAP_H = 60.0, 2.0, 9.7, 4.5
MIC_BOOT_OD, MIC_BOOT_ID = 13.0, 10.1

# ================================================================ 체결
BOSS_D, BOSS_PILOT, BOSS_PILOT_DEPTH = 7.0, 2.5, 10.0   # M3 셀프탭
BOSS_IN = T + BOSS_D / 2.0 - 0.5         # 벽과 0.5 겹쳐 일체화
BOSSES = [(BOSS_IN, 54.0),               # 좌상 (보드 위)
          (55.5, BOSS_IN),               # 하단 중앙 (보드와 스피커 사이)
          (W - BOSS_IN, BOSS_IN),        # 우하
          (W - BOSS_IN, H - BOSS_IN)]    # 우상
COVER_SCREW_D, COVER_CSK_D, COVER_CSK_H = 3.4, 6.5, 1.5
BOARD_STANDOFF_D, BOARD_PILOT_D = 4.4, 2.1      # M2.5 셀프탭
BOARD_SCREW_HEAD_D, BOARD_SCREW_HEAD_H = 4.5, 1.8
VENT_W, VENT_H, VENT_N, VENT_PITCH = 2.5, 20.0, 5, 4.5
FOOT_D, FOOT_DEPTH = 8.0, 0.6

# ================================================================ 파생값: 키 높이 스택 (위→아래)
TOP_IN = H - T                                   # 윗벽 안쪽 면
FLANGE_Z0 = TOP_IN - KEY_FLANGE_T
SW_TOP = FLANGE_Z0 - KEY_PLUNGER_GAP - 0.3       # 0.3 = 플런저 길이
KB_PCB_Z1 = SW_TOP - SW_STEM_H - SW_BODY_H
KB_PCB_Z0 = KB_PCB_Z1 - KB_PCB_T
KB_TAIL_Z0 = KB_PCB_Z0 - KB_TAIL


def vec(x, y, z):
    return App.Vector(x, y, z)


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, vec(x0, y0, z0))


def rbox_y(x0, x1, y0, y1, z0, z1, r):
    b = box(x0, x1, y0, y1, z0, z1)
    if r > 0:
        edges = [e for e in b.Edges
                 if abs(e.Vertexes[0].Point.y - e.Vertexes[1].Point.y) > 1e-6]
        b = b.makeFillet(r, edges)
    return b


def cyl_x(d, x0, x1, cy, cz):
    return Part.makeCylinder(d / 2.0, x1 - x0, vec(x0, cy, cz), vec(1, 0, 0))


def cyl_y(d, y0, y1, cx, cz):
    return Part.makeCylinder(d / 2.0, y1 - y0, vec(cx, y0, cz), vec(0, 1, 0))


def cyl_z(d, z0, z1, cx, cy):
    return Part.makeCylinder(d / 2.0, z1 - z0, vec(cx, cy, z0), vec(0, 0, 1))


def board_holes():
    xs = (dwg_x(HOLE_INSET_X), dwg_x(PCB - HOLE_INSET_X))
    zs = (dwg_z(HOLE_INSET_Z), dwg_z(PCB - HOLE_INSET_Z))
    return [(x, z) for x in xs for z in zs]


def car_holes():
    return [(x, z) for x in (CAR_X0 + 2.5, CAR_X1 - 2.5) for z in (CAR_Z0 + 2.5, CAR_Z1 - 2.5)]


def oled_mod():
    return (OLED_CX - OLED_MOD_W / 2, OLED_CX + OLED_MOD_W / 2,
            OLED_CZ - OLED_MOD_H / 2, OLED_CZ + OLED_MOD_H / 2)


def spk_rect():
    return (SPK_CX - SPK_W / 2, SPK_CX + SPK_W / 2, SPK_CZ - SPK_H / 2, SPK_CZ + SPK_H / 2)


# ================================================================ 쉘
def rib_frame(x0, x1, z0, z1, clr, t, y0, y1, sides):
    """부품 외곽(x0..x1, z0..z1) 둘레 리브. sides ⊂ {'L','R','B','T'}."""
    parts = []
    if "L" in sides:
        parts.append(box(x0 - clr - t, x0 - clr, y0, y1, z0 - clr - t, z1 + clr))
    if "R" in sides:
        parts.append(box(x1 + clr, x1 + clr + t, y0, y1, z0 - clr - t, z1 + clr))
    if "B" in sides:
        parts.append(box(x0 - clr - t, x1 + clr + t, y0, y1, z0 - clr - t, z0 - clr))
    if "T" in sides:
        parts.append(box(x0 - clr - t, x1 + clr + t, y0, y1, z1 + clr, z1 + clr + t))
    return parts


def make_shell():
    shell = rbox_y(0, W, 0, D, 0, H, R_OUT).cut(
        rbox_y(T, W - T, T, D + 1.0, T, H - T, R_OUT - T))

    adds = []
    # 코너 보스: 전면벽 → 뒤판 안쪽 면
    for (bx, bz) in BOSSES:
        adds.append(cyl_y(BOSS_D, T - 0.5, COVER_Y0, bx, bz))
    # OLED 포켓 리브 (좌·우·하, 위는 배선 출구) — 높이 = 유리+PCB
    ox0, ox1, oz0, oz1 = oled_mod()
    adds += rib_frame(ox0, ox1, oz0, oz1, OLED_RIB_CLR, OLED_RIB_T,
                      T - 0.5, T + OLED_GLASS_T + OLED_PCB_T, "LRB")
    # 스피커 포켓 리브 (4면)
    sx0, sx1, sz0, sz1 = spk_rect()
    adds += rib_frame(sx0, sx1, sz0, sz1, SPK_RIB_CLR, SPK_RIB_T,
                      T - 0.5, T + SPK_RIB_H, "LRBT")
    # 전원 USB-C 브레이크아웃 선반 (우측 내벽)
    adds.append(box(W - T - 9.0, W - T + 0.5, PWR_CY - PWR_PCB_W / 2, PWR_CY + PWR_PCB_W / 2,
                    PWR_CZ - 1.6 - 1.6 - 2.0, PWR_CZ - 1.6 - 1.6))
    # 키 기판 레일 (좌·우): 윗벽에서 내려오는 벽 + 기판 아래 립. 기판은 뒤에서 슬라이드.
    rail_z0 = KB_PCB_Z0 - 1.5
    adds.append(box(KB_X0 - 0.8 - RAIL_T, KB_X0 - 0.8, KB_Y0, KB_Y1, rail_z0, TOP_IN + 0.5))
    adds.append(box(KB_X0 - 0.8 - RAIL_T, KB_X0 + RAIL_LIP - 0.8, KB_Y0, KB_Y1, rail_z0, KB_PCB_Z0))
    adds.append(box(KB_X1 + 0.8, KB_X1 + 0.8 + RAIL_T, KB_Y0, KB_Y1, rail_z0, TOP_IN + 0.5))
    adds.append(box(KB_X1 - RAIL_LIP + 0.8, KB_X1 + 0.8 + RAIL_T, KB_Y0, KB_Y1, rail_z0, KB_PCB_Z0))
    # 마이크 부트 링 (윗벽 안쪽)
    adds.append(cyl_z(MIC_BOOT_OD, FLANGE_Z0, TOP_IN + 0.5, MIC_CX, KEY_CY).cut(
        cyl_z(MIC_BOOT_ID, FLANGE_Z0 - 0.1, TOP_IN + 0.01, MIC_CX, KEY_CY)))
    for a in adds:
        shell = shell.fuse(a)

    cuts = []
    # --- 전면 (y=0)
    gz = OLED_CZ + OLED_GLASS_DZ
    cuts.append(box(OLED_CX - OLED_WIN_W / 2, OLED_CX + OLED_WIN_W / 2, -1, T + 0.1,
                    gz - OLED_WIN_H / 2, gz + OLED_WIN_H / 2))
    cuts.append(cyl_y(LED_D, -1, T + 0.1, LED_CX, LED_CZ))
    cuts.append(cyl_y(ENC_D, -1, T + 0.1, ENC_CX, ENC_CZ))
    cuts.append(cyl_y(ENC_TAB_D, T - 1.2, T + 0.1, ENC_CX, ENC_CZ + ENC_TAB_OFF))
    n = int(GRILLE_SPAN_X // GRILLE_PITCH)
    for i in range(n):
        x = SPK_CX - GRILLE_SPAN_X / 2 + GRILLE_PITCH * (i + 0.5)
        cuts.append(box(x - GRILLE_SLOT_W / 2, x + GRILLE_SLOT_W / 2, -1, T + 0.1,
                        SPK_CZ - GRILLE_SPAN_Z / 2, SPK_CZ + GRILLE_SPAN_Z / 2))
    # --- 윗면 (z=H): 키 구멍 + 마이크 포트
    for kx in KEY_XS:
        hw, hd = KEY_W / 2 + KEY_HOLE_CLR, KEY_DY / 2 + KEY_HOLE_CLR
        cuts.append(box(kx - hw, kx + hw, KEY_CY - hd, KEY_CY + hd, TOP_IN - 0.1, H + 1))
    cuts.append(cyl_z(MIC_D, TOP_IN - 0.1, H + 1, MIC_CX, KEY_CY))
    # --- 좌측면 (x=0): 포트 포켓 + 이더넷/USB-A 개구
    ez0, ez1 = sorted((dwg_z(ETH_DY[0]), dwg_z(ETH_DY[1])))
    uz0, uz1 = sorted((dwg_z(USBA_DY[0]), dwg_z(USBA_DY[1])))
    py0, py1 = PCB_Y1 - PORT_MARGIN, PCB_Y1 + max(ETH_H, USBA_H) + PORT_MARGIN
    cuts.append(box(-1, PORT_POCKET_DEPTH, py0 - 1.0, py1 + 1.0,
                    ez0 - PORT_MARGIN - 1.0, uz1 + PORT_MARGIN + 1.0))
    cuts.append(box(-1, T + 0.1, py0, py1, ez0 - PORT_MARGIN, ez1 + PORT_MARGIN))
    cuts.append(box(-1, T + 0.1, py0, py1, uz0 - PORT_MARGIN, uz1 + PORT_MARGIN))
    # --- 우측면 (x=W): 3.5mm 잭 + 전원 USB-C
    cuts.append(cyl_x(JACK_D, W - T - 0.1, W + 1, JACK_CY, JACK_CZ))
    cuts.append(box(W - T - 0.1, W + 1, PWR_CY - PWR_W / 2, PWR_CY + PWR_W / 2,
                    PWR_CZ - PWR_H / 2, PWR_CZ + PWR_H / 2))
    # --- 바닥면 (z=0): 고무발 자리
    for fx in (15.0, W - 15.0):
        for fy in (8.0, D - 8.0):
            cuts.append(cyl_z(FOOT_D, -0.01, FOOT_DEPTH, fx, fy))
    # --- 보스 파일럿 (뒤에서)
    for (bx, bz) in BOSSES:
        cuts.append(cyl_y(BOSS_PILOT, COVER_Y0 - BOSS_PILOT_DEPTH, COVER_Y0 + 0.01, bx, bz))

    shell = shell.cut(Part.makeCompound(cuts))
    return shell.removeSplitter()


# ================================================================ 뒤판
def make_cover():
    plate = rbox_y(T + CLR, W - T - CLR, COVER_Y0, D, T + CLR, H - T - CLR, R_OUT - T - CLR)
    for (hx, hz) in board_holes():
        plate = plate.fuse(cyl_y(BOARD_STANDOFF_D, PCB_Y1, COVER_Y0 + 0.5, hx, hz))
    for (cx, cz) in car_holes():
        plate = plate.fuse(cyl_y(5.0, COVER_Y0 - CAR_STANDOFF, COVER_Y0 + 0.5, cx, cz))
    cuts = []
    for (hx, hz) in board_holes():
        cuts.append(cyl_y(BOARD_PILOT_D, PCB_Y1 - 0.01, PCB_Y1 + 8.0, hx, hz))
    for (cx, cz) in car_holes():
        cuts.append(cyl_y(2.1, COVER_Y0 - CAR_STANDOFF - 0.01, COVER_Y0 - 0.5, cx, cz))
    for (bx, bz) in BOSSES:
        cuts.append(cyl_y(COVER_SCREW_D, COVER_Y0 - 1, D + 1, bx, bz))
        cuts.append(Part.makeCone(COVER_SCREW_D / 2, COVER_CSK_D / 2, COVER_CSK_H,
                                  vec(bx, D - COVER_CSK_H, bz), vec(0, 1, 0)))
        cuts.append(cyl_y(COVER_CSK_D, D - 0.001, D + 1, bx, bz))
    # SoC 뒤 통풍 슬롯
    sx, sz = dwg_x(SOC_DXY[0]), dwg_z(SOC_DXY[1])
    for i in range(VENT_N):
        x = sx + (i - (VENT_N - 1) / 2.0) * VENT_PITCH
        cuts.append(box(x - VENT_W / 2, x + VENT_W / 2, COVER_Y0 - 1, D + 1,
                        sz - VENT_H / 2, sz + VENT_H / 2))
    return plate.cut(Part.makeCompound(cuts)).removeSplitter()


# ================================================================ 키캡
def make_keycaps():
    caps = []
    for kx in KEY_XS:
        body = box(kx - KEY_W / 2, kx + KEY_W / 2, KEY_CY - KEY_DY / 2, KEY_CY + KEY_DY / 2,
                   FLANGE_Z0, H + KEY_PROUD)
        flange = box(kx - KEY_FLANGE_W / 2, kx + KEY_FLANGE_W / 2,
                     KEY_CY - KEY_FLANGE_DY / 2, KEY_CY + KEY_FLANGE_DY / 2, FLANGE_Z0, TOP_IN)
        plunger = cyl_z(KEY_PLUNGER_D, SW_TOP + KEY_PLUNGER_GAP, FLANGE_Z0 + 0.01, kx, KEY_CY)
        caps.append(body.fuse(flange).fuse(plunger).removeSplitter())
    return caps


# ================================================================ 부품 더미 (외곽 envelope)
def make_dummies():
    """반환: [(이름, shape, 장착처 'shell'|'cover')]"""
    d = []
    # --- 뒤판 장착: ROCK Pi S
    d.append(("board_pcb", box(BOARD_X0, BOARD_X1, PCB_Y0, PCB_Y1, BOARD_Z0, BOARD_Z1), "cover"))
    ez0, ez1 = sorted((dwg_z(ETH_DY[0]), dwg_z(ETH_DY[1])))
    jx0 = BOARD_X0 - ETH_OVERHANG
    d.append(("eth", box(jx0, jx0 + ETH_LEN, PCB_Y1, PCB_Y1 + ETH_H, ez0, ez1), "cover"))
    uz0, uz1 = sorted((dwg_z(USBA_DY[0]), dwg_z(USBA_DY[1])))
    d.append(("usb_a", box(jx0, jx0 + USBA_LEN, PCB_Y1, PCB_Y1 + USBA_H, uz0, uz1), "cover"))
    bz0, bz1 = sorted((dwg_z(BUSBC_DY[0]), dwg_z(BUSBC_DY[1])))
    d.append(("board_usbc", box(BOARD_X1 - 7.3, BOARD_X1 + 0.7, PCB_Y1, PCB_Y1 + 3.2, bz0, bz1),
              "cover"))
    hx0, hx1 = sorted((dwg_x(HDR_DX[0]), dwg_x(HDR_DX[1])))
    for nm, z0, z1 in (("hdr1", BOARD_Z1 - HDR_ROW_W, BOARD_Z1), ("hdr2", BOARD_Z0, BOARD_Z0 + HDR_ROW_W)):
        d.append((nm + "_pins", box(hx0, hx1, PCB_Y1, PCB_Y1 + HDR_PIN, z0, z1), "cover"))
        d.append((nm + "_tails", box(hx0, hx1, PCB_Y0 - HDR_TAIL, PCB_Y0, z0, z1), "cover"))
    for i, (hx, hz) in enumerate(board_holes()):
        d.append(("board_screw%d" % i,
                  cyl_y(BOARD_SCREW_HEAD_D, PCB_Y0 - BOARD_SCREW_HEAD_H, PCB_Y0, hx, hz), "cover"))
    # --- 뒤판 장착: 캐리어
    car_y1 = COVER_Y0 - CAR_STANDOFF
    d.append(("carrier_pcb", box(CAR_X0, CAR_X1, car_y1 - PCB_T, car_y1, CAR_Z0, CAR_Z1), "cover"))
    d.append(("carrier_parts", box(CAR_X0, CAR_X1, car_y1 - PCB_T - CAR_PART_H, car_y1 - PCB_T,
                                   CAR_Z0, CAR_Z1), "cover"))
    # --- 쉘 장착: 전면
    ox0, ox1, oz0, oz1 = oled_mod()
    gz = OLED_CZ + OLED_GLASS_DZ
    d.append(("oled_glass", box(OLED_CX - OLED_GLASS_W / 2, OLED_CX + OLED_GLASS_W / 2,
                                T, T + OLED_GLASS_T, gz - OLED_GLASS_H / 2, gz + OLED_GLASS_H / 2),
              "shell"))
    y = T + OLED_GLASS_T
    d.append(("oled_pcb", box(ox0, ox1, y, y + OLED_PCB_T, oz0, oz1), "shell"))
    d.append(("oled_back", box(ox0, ox1, y + OLED_PCB_T, y + OLED_PCB_T + OLED_BACK_T, oz0, oz1),
              "shell"))
    sx0, sx1, sz0, sz1 = spk_rect()
    d.append(("speaker", box(sx0, sx1, T + SPK_GASKET, T + SPK_GASKET + SPK_T, sz0, sz1), "shell"))
    ex0, ex1 = ENC_CX - ENC_BODY_W / 2, ENC_CX + ENC_BODY_W / 2
    ez0e, ez1e = ENC_CZ - ENC_BODY_H / 2, ENC_CZ + ENC_BODY_H / 2
    d.append(("enc_body", box(ex0, ex1, T, T + ENC_BODY_T, ez0e, ez1e), "shell"))
    d.append(("enc_pins", box(ex0, ex1, T + ENC_BODY_T, T + ENC_BODY_T + ENC_PIN_T, ez0e, ez1e),
              "shell"))
    d.append(("led", cyl_y(3.0, T, T + LED_LEN, LED_CX, LED_CZ), "shell"))
    d.append(("jack", cyl_x(JACK_BODY_D, W - T - JACK_BODY_L, W - T, JACK_CY, JACK_CZ), "shell"))
    rz0 = PWR_CZ - 1.6
    d.append(("pwr_usbc", box(W - T - 0.3 - PWR_REC_L, W - T - 0.3,
                              PWR_CY - 4.45, PWR_CY + 4.45, rz0, rz0 + 3.2), "shell"))
    d.append(("pwr_pcb", box(W - T - 0.3 - PWR_PCB_L, W - T - 0.3,
                             PWR_CY - PWR_PCB_W / 2, PWR_CY + PWR_PCB_W / 2, rz0 - 1.6, rz0), "shell"))
    # --- 쉘 장착: 키 기판
    d.append(("kb_pcb", box(KB_X0, KB_X1, KB_Y0, KB_Y1, KB_PCB_Z0, KB_PCB_Z1), "shell"))
    d.append(("kb_tails", box(KB_X0 + RAIL_LIP, KB_X1 - RAIL_LIP, KB_Y0, KB_Y1, KB_TAIL_Z0, KB_PCB_Z0),
              "shell"))
    for i, kx in enumerate(KEY_XS):
        s = SW_SIZE / 2
        d.append(("sw%d" % i, box(kx - s, kx + s, KEY_CY - s, KEY_CY + s,
                                  KB_PCB_Z1, KB_PCB_Z1 + SW_BODY_H), "shell"))
        d.append(("sw%d_stem" % i, cyl_z(SW_STEM_D, KB_PCB_Z1 + SW_BODY_H, SW_TOP, kx, KEY_CY),
                  "shell"))
    d.append(("mic", cyl_z(MIC_CAP_D, KB_PCB_Z1, KB_PCB_Z1 + MIC_CAP_H, MIC_CX, KEY_CY), "shell"))
    return d


# ================================================================ 검사
LOG = []


def log(msg):
    print(msg)
    LOG.append(msg)


def check_solid(name, shape, expect_solids):
    bb = shape.BoundBox
    ok = shape.isValid() and len(shape.Solids) == expect_solids
    log("[%s] valid=%s solids=%d volume=%.1f mm3 bbox=(%.1f x %.1f x %.1f)"
        % (name, shape.isValid(), len(shape.Solids), shape.Volume,
           bb.XLength, bb.YLength, bb.ZLength))
    return ok


def common_vol(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    return a.common(b).Volume


# 물리적으로 맞닿게 설계한 쌍 (면 접촉 → 공통 부피 0 이어야 정상이지만, 같은 부품 내부의
# 구성요소라 겹쳐도 무방한 쌍은 여기 등록). 현재는 없음 — 모두 면 접촉으로 모델링.
ALLOWED = set()


def run_checks(shell, cover, caps, dummies):
    fails = []
    ok = check_solid("shell", shell, 1)
    ok &= check_solid("cover", cover, 1)
    for i, c in enumerate(caps):
        ok &= check_solid("keycap%d" % i, c, 1)
    if not ok:
        fails.append("invalid solid")

    parts = [("shell", shell, "shell"), ("cover", cover, "cover")]
    parts += [("keycap%d" % i, c, "shell") for i, c in enumerate(caps)]
    parts += dummies
    for (na, a, _), (nb, b, _) in itertools.combinations(parts, 2):
        if (na, nb) in ALLOWED:
            continue
        v = common_vol(a, b)
        if v > 1e-3:
            fails.append("interference %s-%s %.3f mm3" % (na, nb, v))

    # 뒤판 삽입 경로 sweep: 뒤판 장착 부품의 bbox를 +Y로 D 밖까지 늘린 것과
    # 쉘 + 쉘 장착 부품의 간섭
    shell_side = [("shell", shell)] + [(n, s) for (n, s, m) in dummies if m == "shell"] \
        + [("keycap%d" % i, c) for i, c in enumerate(caps)]
    for (n, s, m) in dummies:
        if m != "cover":
            continue
        bb = s.BoundBox
        sweep = box(bb.XMin, bb.XMax, bb.YMin, D + 5.0, bb.ZMin, bb.ZMax)
        for (ns, ss) in shell_side:
            v = common_vol(sweep, ss)
            if v > 1e-3:
                fails.append("insertion %s->%s %.3f mm3" % (n, ns, v))
    # 키 기판도 뒤에서 슬라이드: 기판+꼬리+스위치+마이크 bbox sweep vs 쉘, 앞서 장착된 전면 부품
    kb_names = {"kb_pcb", "kb_tails", "mic"} | {"sw%d" % i for i in range(4)} \
        | {"sw%d_stem" % i for i in range(4)}
    for (n, s, m) in dummies:
        if n not in kb_names:
            continue
        bb = s.BoundBox
        sweep = box(bb.XMin, bb.XMax, bb.YMin, D + 5.0, bb.ZMin, bb.ZMax)
        for (ns, ss) in [("shell", shell)] + [(x, y) for (x, y, mm) in dummies
                                             if mm == "shell" and x not in kb_names]:
            v = common_vol(sweep, ss)
            if v > 1e-3:
                fails.append("kb-insertion %s->%s %.3f mm3" % (n, ns, v))

    # 최소 여유 보고 (설계 목표 GAP 미만인 쌍)
    tight = []
    for (na, a, _), (nb, b, _) in itertools.combinations(dummies, 2):
        if not a.BoundBox.intersect(b.BoundBox):
            bba, bbb = a.BoundBox, b.BoundBox
            gx = max(bbb.XMin - bba.XMax, bba.XMin - bbb.XMax, 0)
            gy = max(bbb.YMin - bba.YMax, bba.YMin - bbb.YMax, 0)
            gz = max(bbb.ZMin - bba.ZMax, bba.ZMin - bbb.ZMax, 0)
            g = max(gx, gy, gz)
            if 0 < g < GAP - 1e-6:
                tight.append("%s-%s %.2f" % (na, nb, g))

    log("[stack] PCB_Y0=%.2f PCB_Y1=%.2f eth_rear=%.2f cover_inner=%.2f spare=%.2f"
        % (PCB_Y0, PCB_Y1, PCB_Y1 + ETH_H, COVER_Y0, COVER_Y0 - (PCB_Y1 + ETH_H)))
    log("[stack] key: flange_z0=%.2f sw_top=%.2f kb_pcb=%.2f..%.2f tails_z0=%.2f board_top=%.2f oled_top=%.2f"
        % (FLANGE_Z0, SW_TOP, KB_PCB_Z0, KB_PCB_Z1, KB_TAIL_Z0, BOARD_Z1, oled_mod()[3]))
    log("[pairs] checked %d parts, %d pairs" % (len(parts), len(parts) * (len(parts) - 1) // 2))
    for t in tight:
        log("[tight<%.1f] %s" % (GAP, t))
    for f in fails:
        log("[FAIL] " + f)
    log("RESULT: %s" % ("PASS" if not fails else "FAIL (%d)" % len(fails)))
    return not fails


# ================================================================ 배치도 (SVG)
def write_layout(dummies, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle
    from matplotlib import font_manager

    font = os.environ.get("BEATLING_CAD_FONT", "/System/Library/Fonts/Supplemental/AppleGothic.ttf")
    if os.path.exists(font):   # 없으면 기본 폰트 (한글 깨짐만, 형상 결과와 무관)
        font_manager.fontManager.addfont(font)
        matplotlib.rcParams["font.family"] = font_manager.FontProperties(fname=font).get_name()
    matplotlib.rcParams["svg.fonttype"] = "none"
    matplotlib.rcParams["svg.hashsalt"] = "beatling"   # 재실행 시 id 고정 (git diff 최소화)

    colors = {"cover": "#d9822b", "shell": "#2b7bd9"}
    fig, axes = plt.subplots(1, 3, figsize=(18, 6.5),
                             gridspec_kw={"width_ratios": [W, W, D * 1.6]})
    views = [("Front (X-Z, 정면에서 투시)", 0, 2), ("Top (X-Y, 위에서 투시)", 0, 1),
             ("Side (Y-Z, 우측에서 투시)", 1, 2)]
    lim = {0: (-3, W + 3), 1: (-3, D + 3), 2: (-3, H + 3)}
    for ax, (title, a, b) in zip(axes, views):
        ext = {0: W, 1: D, 2: H}
        ax.add_patch(Rectangle((0, 0), ext[a], ext[b], fill=False, lw=1.5, ec="black"))
        ax.add_patch(Rectangle((T, T), ext[a] - 2 * T, ext[b] - 2 * T, fill=False, lw=0.6,
                               ec="gray", ls="--"))
        for (n, s, m) in dummies:
            bb = s.BoundBox
            mins = (bb.XMin, bb.YMin, bb.ZMin)
            maxs = (bb.XMax, bb.YMax, bb.ZMax)
            ax.add_patch(Rectangle((mins[a], mins[b]), maxs[a] - mins[a], maxs[b] - mins[b],
                                   fill=True, alpha=0.18, lw=0.6, ec=colors[m], fc=colors[m]))
            if not (n.startswith("board_screw") or n.endswith("_stem") or n.endswith("_tails")):
                ax.text((mins[a] + maxs[a]) / 2, (mins[b] + maxs[b]) / 2, n, fontsize=5,
                        ha="center", va="center")
        if (a, b) == (0, 2):
            for (bx, bz) in BOSSES:
                ax.add_patch(Circle((bx, bz), BOSS_D / 2, fill=False, ec="black", lw=0.8))
        ax.set_xlim(*lim[a])
        ax.set_ylim(*lim[b])
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=9)
        ax.tick_params(labelsize=6)
    fig.suptitle("BEATLING pocket enclosure %gx%gx%g mm — 파랑: 쉘 장착 / 주황: 뒤판 장착 / ○ 코너 보스"
                 % (W, H, D), fontsize=10)
    fig.tight_layout()
    fig.savefig(path, metadata={"Date": None})
    fig.savefig(os.path.join(OUT_DIR, "layout.png"), dpi=110)
    plt.close(fig)
    log("layout: " + path)


def write_preview(shapes, path):
    """간이 3D 미리보기 (matplotlib, 음영 근사). 정면-좌상 / 후면-우상 2컷."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(14, 6))
    for k, (elev, azim, title) in enumerate(((20, -60, "front"), (20, 120, "rear (cover)"))):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        for shape, color in shapes:
            pts, tris = shape.tessellate(0.3)
            polys = [[(pts[i].x, pts[i].y, pts[i].z) for i in t] for t in tris]
            pc = Poly3DCollection(polys, facecolors=color, edgecolor="none", shade=True)
            ax.add_collection3d(pc)
        ax.set_xlim(0, W)
        ax.set_ylim(-45, 75)
        ax.set_zlim(-29, 91)
        ax.view_init(elev=elev, azim=azim)
        ax.set_box_aspect((1, 1, 1))
        ax.set_axis_off()
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    log("preview: " + path)


# ================================================================ 출력
def export(shape, base):
    step = os.path.join(OUT_DIR, base + ".step")
    shape.exportStep(step)
    stl = os.path.join(OUT_DIR, base + ".stl")
    Mesh.Mesh(shape.tessellate(0.05)).write(stl)
    log("exported: %s %s" % (step, stl))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    shell = make_shell()
    cover = make_cover()
    caps = make_keycaps()
    dummies = make_dummies()
    passed = run_checks(shell, cover, caps, dummies)

    export(shell, "beatling_shell")
    export(cover, "beatling_cover")
    export(Part.makeCompound(caps), "beatling_keycaps")
    Part.makeCompound([shell, cover] + caps + [s for (_, s, _) in dummies]).exportStep(
        os.path.join(OUT_DIR, "beatling_assembly.step"))
    try:
        write_layout(dummies, LAYOUT_SVG)
    except Exception as e:  # 배치도 실패는 형상 검사 결과와 분리
        log("layout FAILED: %r" % (e,))
    try:
        write_preview([(shell, "#cfd8e3"), (cover, "#e3c9a8")] + [(c, "#7a8ca3") for c in caps],
                      os.path.join(OUT_DIR, "preview.png"))
    except Exception as e:
        log("preview FAILED: %r" % (e,))
    with open(os.path.join(OUT_DIR, "check.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    if not passed:
        raise SystemExit(1)


main()
