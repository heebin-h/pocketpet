#!/usr/bin/env python3
"""
BEATLING Rev A — ROCK Pi S 핀 배치도 생성기 (pinmap.csv + pinout.svg)

실행: python3 /Users/heebiny/diyProj/pocketpet/beatling/hw/pinout/gen_pinout.py

근거: Radxa ROCK Pi S Product Brief Rev 1.5 (RAD-DOC-0118) §3.3 GPIO Interface 표.
gpiochip/line 은 Rockchip 명명 규칙으로 계산: GPIOx_Yz → gpiochip x, line = Y*8 + z
(A=0,B=1,C=2,D=3). 실기에서 `gpioinfo` 로 반드시 대조할 것.
"""
import csv
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# (pin, 보드 기본 이름, 대체기능 요약, BEATLING 할당, 분류)
# 분류: pwr, gnd, i2c, in, out, audio, reserve, spare
H1 = [
    (1, "+3.3V", "", "3V3 → OLED/RTC VCC, 풀업", "pwr"),
    (2, "+5.0V", "", "5V_IN (캐리어 → 보드 전원)", "pwr"),
    (3, "GPIO0_B3", "I2C1_SDA", "I2C1_SDA (OLED 0x3C, RTC 0x68)", "i2c"),
    (4, "+5.0V", "", "5V_IN (캐리어 → 보드 전원)", "pwr"),
    (5, "GPIO0_B4", "I2C1_SCL", "I2C1_SCL", "i2c"),
    (6, "GND", "", "GND (전원 리턴)", "gnd"),
    (7, "GPIO2_A4", "I2S0_8CH_MCLK / PDM_CLK_M_M2", "HP_DET (헤드폰 삽입 감지)", "in"),
    (8, "GPIO2_A1", "UART0_TX / SPI0_MOSI", "예약: 디버그 콘솔 TX (확인 필요)", "reserve"),
    (9, "GND", "", "GND", "gnd"),
    (10, "GPIO2_A0", "UART0_RX / SPI0_MISO", "예약: 디버그 콘솔 RX (확인 필요)", "reserve"),
    (11, "GPIO0_B7", "PWM2 / I2C3_SDA_M0", "ENC_A (로터리 엔코더 A)", "in"),
    (12, "GPIO2_A5", "I2S0_8CH_SCLK_TX", "BTN_TALK (말걸기)", "in"),
    (13, "GPIO0_C0", "PWM3 / I2C3_SCL_M0", "ENC_B (로터리 엔코더 B)", "in"),
    (14, "GND", "", "GND", "gnd"),
    (15, "GPIO0_C1", "SPDIF_TX", "ENC_SW (엔코더 푸시)", "in"),
    (16, "GPIO2_B2", "I2S0_8CH_SDO1", "BTN_FEED (밥)", "in"),
    (17, "+3.3V", "", "3V3 → 버튼/엔코더 풀업", "pwr"),
    (18, "GPIO2_B1", "I2S0_8CH_SDO0", "BTN_PLAY (놀자)", "in"),
    (19, "GPIO1_C7", "UART1_RTSN / UART2_TX_M0 / SPI2_MOSI", "AMP_MUTE (2N7002→PAM8302 SD, High=뮤트, 기본 뮤트)", "out"),
    (20, "GND", "", "GND", "gnd"),
    (21, "GPIO1_C6", "UART1_CTSN / UART2_RX_M0 / SPI2_MISO", "LED_NOTI (알림 LED, 1kΩ 직결 ≈1.5mA)", "out"),
    (22, "GPIO2_A7", "I2S0_8CH_LRCK_TX", "BTN_SLEEP (재워)", "in"),
    (23, "GPIO1_D0", "UART1_RX / I2C0_SDA / SPI2_CLK", "예비", "spare"),
    (24, "GPIO1_D1", "UART1_TX / I2C0_SCL / SPI2_CSN0", "예비", "spare"),
    (25, "GND", "", "GND", "gnd"),
    (26, "ADC_IN0", "SARADC", "예비 (볼륨 포트 옵션)", "spare"),
]
H2 = [
    (27, "GND", "", "AGND (마이크 리턴 전용)", "gnd"),
    (28, "GPIO2_B5", "I2S0_8CH_SDI0 / PDM_SDI0_M2", "예비", "spare"),
    (29, "ADC_KEY_IN1", "", "미사용 (용도 미확인)", "reserve"),
    (30, "GPIO2_B6", "I2S0_8CH_SDI1 / PDM_SDI1_M2", "예비", "spare"),
    (31, "MICBIAS2", "", "미사용", "spare"),
    (32, "GPIO2_B7", "I2S0_8CH_SDI2 / PDM_SDI2_M2", "예비", "spare"),
    (33, "MICBIAS1", "", "MIC_BIAS → 2.2kΩ → 일렉트렛", "audio"),
    (34, "GPIO2_C0", "I2S0_8CH_SDI3 / PDM_SDI3_M2", "예비", "spare"),
    (35, "MICN8", "", "미사용", "spare"),
    (36, "MICP8", "", "미사용", "spare"),
    (37, "MICN7", "", "미사용", "spare"),
    (38, "MICP7", "", "미사용", "spare"),
    (39, "GPIO3_B5", "UART3_TX / I2C3_SCL_M1 / SPI1_CSN0", "예비 (확장 UART)", "spare"),
    (40, "GPIO3_B4", "UART3_RX / I2C3_SDA_M1 / SPI1_MOSI", "예비 (확장 UART)", "spare"),
    (41, "GPIO3_B3", "SPI1_CLK", "예비", "spare"),
    (42, "GPIO3_B2", "SPI1_MISO", "예비", "spare"),
    (43, "GPIO2_B4", "I2S0_8CH_SDO3", "예비", "spare"),
    (44, "GPIO2_B3", "I2S0_8CH_SDO2", "예비", "spare"),
    (45, "GPIO2_B0", "I2S0_8CH_LRCK_RX", "예비", "spare"),
    (46, "GPIO2_A6", "I2S0_8CH_SCLK_RX / PDM_CLK_S_M2", "예비", "spare"),
    (47, "MICN2", "", "미사용", "spare"),
    (48, "MICP2", "", "미사용", "spare"),
    (49, "MICN1", "", "MIC_N (1µF → 마이크 GND)", "audio"),
    (50, "MICP1", "", "MIC_P (1µF ← 일렉트렛 +)", "audio"),
    (51, "LINEOUT_R", "", "LINE_R → 믹스/헤드폰 R", "audio"),
    (52, "LINEOUT_L", "", "LINE_L → 믹스/헤드폰 L", "audio"),
]

COLORS = {
    "pwr": "#d94841", "gnd": "#3b3b3b", "i2c": "#2f7ed8", "in": "#2e9e5b",
    "out": "#e08a1e", "audio": "#8a4fd1", "reserve": "#9e9e9e", "spare": "#d8d8d8",
}
LABELS = {
    "pwr": "전원", "gnd": "GND", "i2c": "I2C", "in": "입력(GPIO)", "out": "출력(GPIO)",
    "audio": "오디오(코덱)", "reserve": "예약/미사용", "spare": "예비",
}


def chip_line(name):
    """GPIOx_Yz → (chip, line). 비-GPIO 핀은 ('', '')."""
    if not name.startswith("GPIO") or "_" not in name:
        return "", ""
    bank = int(name[4])
    port = "ABCD".index(name.split("_")[1][0])
    idx = int(name.split("_")[1][1])
    return "gpiochip%d" % bank, str(port * 8 + idx)


def write_csv():
    path = os.path.join(OUT, "pinmap.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["header", "pin", "board_name", "alt_functions", "gpiochip", "line",
                    "beatling_signal", "class"])
        for hdr, rows in (("H1", H1), ("H2", H2)):
            for pin, name, alt, sig, cls in rows:
                chip, line = chip_line(name)
                w.writerow([hdr, pin, name, alt, chip, line, sig, cls])
    print("wrote", path)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def header_svg(rows, x0, y0, title):
    """2열 헤더: 홀수핀 왼쪽, 짝수핀 오른쪽 (보드 실크 기준 순서)."""
    out = []
    pitch = 26
    out.append('<text x="%d" y="%d" class="t">%s</text>' % (x0 + 210, y0 - 14, esc(title)))
    by_pin = {r[0]: r for r in rows}
    pins = sorted(by_pin)
    first = pins[0]
    for i in range(len(pins) // 2):
        lp, rp = first + 2 * i, first + 2 * i + 1
        y = y0 + i * pitch
        for pin, side in ((lp, "L"), (rp, "R")):
            _, name, alt, sig, cls = by_pin[pin]
            c = COLORS[cls]
            cx = x0 + 190 if side == "L" else x0 + 230
            out.append('<circle cx="%d" cy="%d" r="9" fill="%s" stroke="#222"/>' % (cx, y, c))
            pn_fill = "#222" if cls == "spare" else "#fff"
            out.append('<text x="%d" y="%d" class="pn" style="fill:%s">%d</text>' % (cx, y + 4, pn_fill, pin))
            chip, line = chip_line(name)
            cl = " (%s:%s)" % (chip.replace("gpiochip", "c"), line) if chip else ""
            if side == "L":
                out.append('<text x="%d" y="%d" class="nm" text-anchor="end">%s%s</text>'
                           % (cx - 14, y - 1, esc(name), esc(cl)))
                out.append('<text x="%d" y="%d" class="sg" text-anchor="end" fill="%s">%s</text>'
                           % (cx - 14, y + 10, "#555" if cls in ("spare", "reserve") else c, esc(sig)))
            else:
                out.append('<text x="%d" y="%d" class="nm">%s%s</text>'
                           % (cx + 14, y - 1, esc(name), esc(cl)))
                out.append('<text x="%d" y="%d" class="sg" fill="%s">%s</text>'
                           % (cx + 14, y + 10, "#555" if cls in ("spare", "reserve") else c, esc(sig)))
    return out


def write_svg():
    w, h = 900, 1120
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (w, h, w, h),
             '<style>.t{font:bold 15px sans-serif}.pn{font:bold 8px sans-serif;fill:#fff;text-anchor:middle}'
             '.nm{font:10px monospace;fill:#222}.sg{font:bold 10px sans-serif}'
             '.h{font:bold 18px sans-serif}.s{font:11px sans-serif;fill:#444}</style>',
             '<rect width="100%%" height="100%%" fill="#ffffff"/>',
             '<text x="20" y="30" class="h">BEATLING Rev A — ROCK Pi S (RS308-D4) 핀 배치도</text>',
             '<text x="20" y="48" class="s">근거: Radxa ROCK Pi S Product Brief Rev1.5 §3.3 · 모든 GPIO 3.3V (허용 3.63V) · '
             '(cN:L) = gpiochipN line L (Rockchip 규칙 계산값, gpioinfo로 대조 필요)</text>']
    parts += header_svg(H1, 150, 100, "26-pin Header 1 (Pin 1–26)")
    parts += header_svg(H2, 150, 500, "26-pin Header 2 (Pin 27–52)")
    # 범례
    ly = 880
    parts.append('<text x="20" y="%d" class="t">범례</text>' % ly)
    for i, (k, c) in enumerate(COLORS.items()):
        x = 20 + (i % 4) * 200
        y = ly + 24 + (i // 4) * 22
        parts.append('<rect x="%d" y="%d" width="14" height="14" fill="%s" stroke="#222"/>' % (x, y - 11, c))
        parts.append('<text x="%d" y="%d" class="s">%s</text>' % (x + 20, y, LABELS[k]))
    # 주의
    notes = [
        "• Pin 8/10(UART0)은 디버그 콘솔로 가정해 예약 — 실기 /proc/cmdline 의 console= 으로 확인 후 해제 여부 결정",
        "• Pin 12/16/18/22(I2S0 TX)를 GPIO로 사용 — 내장 코덱만 쓰므로 외부 I2S 불필요. pinmux 충돌은 /sys/kernel/debug/pinctrl 로 확인",
        "• OLED·RTC 모듈은 반드시 3.3V(Pin 1/17)로 공급 — 5V 공급 시 모듈 풀업이 SDA/SCL을 5V로 끌어 3.63V 허용치 초과",
        "• 보드 전원은 캐리어 USB-C → Pin 2/4 (5V). 보드 자체 USB-C와 동시 연결 금지 (전원 역류) — 계획서 §3 참조",
        "• Pin 27 GND는 마이크 아날로그 리턴 전용으로 분리 배선 (앰프 전류 리턴과 섞지 않음)",
        "• 보드 방향: brief 사진 기준 Pin1은 Header1 하단(이더넷 쪽), Pin27은 Header2 상단(USB-C 쪽) — 실물 실크로 확인",
    ]
    for i, n in enumerate(notes):
        parts.append('<text x="20" y="%d" class="s">%s</text>' % (ly + 90 + i * 20, esc(n)))
    parts.append("</svg>")
    path = os.path.join(OUT, "pinout.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print("wrote", path)


def self_check():
    pins = [r[0] for r in H1 + H2]
    assert pins == list(range(1, 53)), "핀 번호 누락/중복"
    sigs = [r[3] for r in H1 + H2 if r[4] in ("in", "out", "i2c")]
    assert len(sigs) == len(set(sigs)), "신호 중복 할당"
    print("self-check OK: 52 pins, %d assigned GPIO/I2C signals, no duplicates" % len(sigs))


if __name__ == "__main__":
    self_check()
    write_csv()
    write_svg()
