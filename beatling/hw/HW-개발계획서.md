# BEATLING HW 개발계획서 — Rev A (탁상형 프로토타입)

- 작성일: 2026-11-10
- 상위 컨셉: `/Users/heebiny/diyProj/pocketpet/concepts/03-beatling-음악먹는-펫-mp3.md`
- 대상 보드: Radxa ROCK Pi S **RS308-D4** (RK3308B, 512MB DDR3, 무선 없음, eMMC 없음 → microSD 부팅)
- 범위: **HW만** (전원·회로·핀 할당·기구·HW 시험). 펫 엔진 등 SW는 범위 밖 — bring-up·시험용 명령만 포함.
- 표기: **[근거]** 공식 문서로 확인 / **[추정]** 일반 지식·계산 기반 / **[확인 필요]** 실기 측정 전 미확정

### 산출물

| 파일 | 내용 |
|---|---|
| `/Users/heebiny/diyProj/pocketpet/beatling/hw/HW-개발계획서.md` | 이 문서 (회로 구성도 포함) |
| `/Users/heebiny/diyProj/pocketpet/beatling/hw/pinout/pinout.svg` | 핀 배치도 (그림) |
| `/Users/heebiny/diyProj/pocketpet/beatling/hw/pinout/pinmap.csv` | 핀 할당표 (gpiochip/line 포함) |
| `/Users/heebiny/diyProj/pocketpet/beatling/hw/pinout/gen_pinout.py` | 위 두 파일 생성기 (핀 할당의 단일 원본) |
| `/Users/heebiny/diyProj/pocketpet/beatling/hw/cad/beatling_enclosure.py` | 함체 FreeCAD 파라메트릭 스크립트 (치수의 단일 원본) |
| `/Users/heebiny/diyProj/pocketpet/beatling/hw/cad/out/beatling_shell.step` `.stl` | 상부 쉘 |
| `/Users/heebiny/diyProj/pocketpet/beatling/hw/cad/out/beatling_base.step` `.stl` | 바닥판 |
| `/Users/heebiny/diyProj/pocketpet/beatling/hw/cad/out/beatling_assembly.step` | 조립 확인용 (보드·잭·스피커 더미 포함) |
| `/Users/heebiny/diyProj/pocketpet/beatling/hw/cad/out/preview.png` | 간이 미리보기 (matplotlib, 음영 부정확) |

---

## 1. 보드 확정 사양 (설계 입력)

출처: Radxa *ROCK Pi S Product Brief* Rev 1.5 (RAD-DOC-0118, 2026-06-26) — https://dl2.radxa.com/rockpis/docs/hw/radxa_rock_pi_s_product_brief.pdf, GPIO 표는 https://docs.radxa.com/en/rockpi/rockpis/hardware/pin-gpio 와 일치 확인.

| 항목 | 값 | 설계 영향 |
|---|---|---|
| SoC | RK3308B, Cortex-A35 x4 **최대 1.0GHz** [근거] | 오디오 특징 추출은 임포트 시 1회로 제한 (컨셉 문서 원칙 유지) |
| 전원 | **+5V 전용**: USB-C 5V@1A 또는 **GPIO Pin 2·4** [근거] | 캐리어에서 Pin 2·4로 급전 (§3) |
| GPIO 레벨 | **3.3V, 허용 3.63V** [근거] | 5V 신호 직결 금지 — OLED/RTC 3.3V 급전, 앰프 SD는 MOSFET 경유 |
| 헤더 | 26핀 x2 (Pin 1–26, 27–52), 2.54mm [근거] | IDC 26P 리본 2개로 캐리어 연결 |
| 오디오 | Header2에 **LINEOUT_L/R(52/51)**, **MICP/N 1·2·7·8**, **MICBIAS1/2** [근거] | 내장 코덱 사용 → 외부 DAC/코덱 불필요 |
| 크기 | 43.2 x 43.2mm, 장착홀 4x Ø2.5, 이더넷 돌출 포함 48.0 [근거] | CAD 반영. 장착홀 위치는 brief 미기재 → [확인 필요] |
| 동작 온도 | 0~50°C, SoC 85°C에서 스로틀 [근거] | 밀폐 함체 → 통풍 슬롯, 열 시험 (§9) |
| 공급 보장 | **2028년 9월까지** [근거] | Rev A/B 프로토타입엔 충분. 양산 판단 시 재확인 |
| 디버그 UART | brief 미기재 | UART0(Pin 8/10)로 가정해 **예약** [확인 필요] |

---

## 2. 시스템 블록도

```
                         5V/3A USB-C 어댑터
                                │
                    ┌───────────▼────────────┐
                    │  캐리어 보드 (Rev A: 만능기판 40x24)                 │
                    │  USB-C 입력(CC 5.1kΩ x2) → PTC 2A → TVS → 벌크 캡     │
                    │      ├──────────── 5V_SYS ─────────┐                │
                    │      │                             ▼                │
                    │      │                  PAM8302A 앰프 ── 스피커 40mm 4Ω │
                    │      │                      ▲ A+/A-   ▲ SD           │
                    │      │       믹스망(10k x2+1µF)┘        └ 2N7002 (뮤트) │
                    └──────┼──────────────▲──────────────────▲────────────┘
                           │ 5V(Pin2/4)    │ LINEOUT_L/R      │ AMP_MUTE
                 IDC 26P x2│              │ (Pin 52/51)      │ (Pin 19)
                    ┌──────▼──────────────┴──────────────────┴────┐
                    │              ROCK Pi S (RK3308B)                │
                    │  내장 코덱: LINEOUT_L/R, MIC1(P/N), MICBIAS1       │
                    │  I2C1(Pin3/5) · GPIO 8입력 · 2출력 · USB-A · eth  │
                    └──┬──────────┬──────────┬───────────┬──────┬────┘
                       │I2C1(3V3) │GPIO       │MIC1       │LINEOUT│USB-A
             ┌─────────▼───┐ ┌────▼──────┐ ┌──▼────────┐ ┌▼──────┐ ┌▼─────────┐
             │OLED 128x64   │ │프런트 패널  │ │일렉트렛 마이크│ │3.5mm 잭 │ │USB 메모리   │
             │SSD1306 0x3C  │ │버튼4·LED·   │ │(좌측면 부트) │ │+HP_DET │ │(음악 라이브러리)│
             │RTC DS3231 0x68│ │EC11 엔코더  │ └────────────┘ └────────┘ └────────────┘
             └──────────────┘ └───────────┘
```

**분할 원칙**
- **보드**: 그대로 사용(무개조). 보드 자체 USB-C는 **Maskrom 플래싱 전용** — 운용 중 미사용.
- **캐리어**: 전원 입력 + 앰프 + 뮤트 + 커넥터 집선. 소음원(앰프 스위칭)을 한곳에 모음.
- **프런트 패널**: 사람 손이 닿는 것(버튼·LED·OLED·엔코더) — 캐리어와 JST-PH 케이블.
- **마이크**: 앰프·스피커와 반대편(좌측면)에 배치 → 스피커 음향 결합·전원 노이즈 최소화.

---

## 3. 전원 설계

### 3.1 전력 예산

| 부하 | 정상 | 피크 | 근거 |
|---|---|---|---|
| ROCK Pi S (USB 메모리 제외) | — | 1.0A | brief의 공급 요구 5V@1A를 상한으로 사용 [근거] |
| USB 메모리 | 0.05A | 0.2A | 일반 USB 2.0 메모리 [추정] |
| PAM8302A @ 2.5W/4Ω | 0.1A | 0.6A | 2.5W ÷ 효율 ~85% ÷ 5V ≈ 0.59A [추정] |
| OLED + RTC + LED | 0.03A | 0.03A | 3.3V 레일 경유 [추정] |
| **합계** | ~0.4A | **~1.85A** | → **5V/3A 어댑터** 지정 |

- 3.3V 주변장치는 보드 3V3 핀(Pin 1·17)에서 공급. 보드 3.3V 레일 여유 전류는 brief 미기재 [확인 필요] — 부하 ~30mA라 문제없을 것으로 추정.

### 3.2 입력단 회로

```
USB-C 리셉터클(브레이크아웃)
  VBUS ──┬── F1 PTC (hold 2.0A) ──┬──────────┬──────────┬──────► 5V_SYS
         │                        │          │          │
  CC1 ── R1 5.1kΩ ── GND     D1 TVS     C1 470µF   C2 10µF(X5R)
  CC2 ── R2 5.1kΩ ── GND     SMBJ5.0A   (저ESR 전해)  (세라믹)
  GND ───────────────────────────┴──────────┴──────────┴──────► GND (스타 포인트)

5V_SYS ──► 캐리어 IDC Pin 2, Pin 4 (보드 5V)
       ──► PAM8302A VIN (별도 굵은 배선, C3 220µF 근접 배치)
```

- **CC 5.1kΩ 풀다운 필수**: 없으면 USB-C to C 충전기가 VBUS를 내보내지 않음. 브레이크아웃에 내장된 제품이 많으나 모델별 상이 → [확인 필요].
- **전원 역류 금지**: Pin 2·4 급전 중에 보드 USB-C를 PC에 꽂으면 두 5V 소스가 직결될 가능성 (보드 내부 VBUS–5V 경로 구조는 미확인).
  - Rev A 운용 규칙: **Maskrom 플래싱 시 캐리어 전원 분리 후 보드 USB-C만 사용.**
  - Rev B 대책: 캐리어 5V 출력에 ideal diode(예: TI LM66100, 5.5V/1.5A급)로 역류 차단 — 부품 선정 시 데이터시트 확인.
- **브라운아웃 대책**: 앰프 피크 전류로 5V 강하 → SD 카드 쓰기 중 리셋 시 파일시스템 손상. C1 470µF + 앰프 근처 C3 220µF, 앰프와 보드 5V 배선 분리(공통 임피던스 최소화), SW 볼륨 상한 설정. 판정은 §9 T1.

### 3.3 접지

- 스타 포인트 = USB-C 입력 GND.
- **앰프 GND**(대전류 스위칭)는 스타 포인트로 단독 귀환.
- **마이크 GND**는 보드 Pin 27에 단독 연결 (핀맵상 MIC 핀들과 같은 Header2) — 앰프 리턴과 섞지 않음.
- 디지털 GND(버튼·OLED·RTC)는 보드 Header1 GND 핀(6/9/14/20/25).

---

## 4. 회로 구성도 (서브회로별)

### 4.1 스피커 출력 — LINEOUT → 모노 믹스 → PAM8302A

```
Pin52 LINEOUT_L ── R3 10kΩ ──┐
                             ├── C4 1µF ── A+  ┌──────────┐ VO+ ──┐
Pin51 LINEOUT_R ── R4 10kΩ ──┘                 │ PAM8302A │       SPK 40mm 4Ω 3W
                     GND(Pin25) ── C5 1µF ── A- │ (브레이크  │ VO- ──┘
                                               │  아웃)    │
                             5V_SYS ── C3 220µF ┤VIN       │
                                               │       SD ├──┐
                                               └──────────┘  │ (브레이크아웃 내부 풀업, 레벨 확인 필요)
                                                             │
                                                     Q1 2N7002 Drain
Pin19 AMP_MUTE ── R5 100Ω ── Q1 Gate                 Q1 Source ── GND
                  R6 10kΩ: Gate ── 3V3   (기본 = 뮤트)
```

- **왜 MOSFET 경유인가**: 브레이크아웃이 SD를 VIN(5V)으로 풀업하고 있으면 GPIO 직결 시 3.63V 허용치 초과. Q1은 open-drain이라 SD 측 전압과 무관 [추정 — 브레이크아웃 회로도로 확인 필요].
- **로직**: AMP_MUTE High → Q1 ON → SD Low → **앰프 정지(뮤트)**. R6 풀업으로 부팅 중 GPIO가 떠 있어도 뮤트 유지 → **부팅 팝 노이즈 방지**. SW가 재생 직전 Low로 해제.
- **모노 믹스**: 10kΩ 합산. LINEOUT 출력 임피던스와 상호 간섭은 무시 가능 수준 [추정].
- C4/C5: 브레이크아웃에 입력 커플링 캡이 이미 있으면 생략 가능 [확인 필요].
- 헤드폰 삽입 시 HP_DET로 SW가 AMP_MUTE High → 스피커 자동 차단.

### 4.2 헤드폰 출력

```
Pin52 LINEOUT_L ── C6 220µF(+) ── R7 33Ω ── TIP   ┐
Pin51 LINEOUT_R ── C7 220µF(+) ── R8 33Ω ── RING  ├ 3.5mm 잭 (스위치 내장형, PJ-313/SJ-3523 계열)
GND(Pin25) ──────────────────────────────── SLEEVE┘
잭 검출 스위치 ── Pin7 HP_DET (R9 10kΩ → 3V3 풀업, C8 100nF)
```

- 220µF: 32Ω 헤드폰 기준 저역 차단 fc = 1/(2π·(32+33)·220µF) ≈ 11Hz [계산].
- **LINEOUT의 헤드폰 직접 구동 능력(출력 전류·DC 오프셋)은 미확인** → H1에서 측정. 음량 부족 시 Rev B에 헤드폰 앰프 추가(부품 1개).
- 검출 스위치 극성(삽입 시 열림/닫힘)은 잭 모델마다 다름 → SW 설정값으로 흡수.

### 4.3 마이크 입력 — 일렉트렛 의사차동

```
Pin33 MICBIAS1 ── R10 2.2kΩ ──┬── MIC+ (일렉트렛 Ø9.7, 좌측면 부트)
                              │
                              └── C9 1µF ── Pin50 MICP1
Pin49 MICN1 ── C10 1µF ──┬── MIC- 
                         └── Pin27 GND (마이크 전용 리턴)
배선: 차폐 2심 케이블, 실드는 Pin27 쪽 한 점 접지
```

- RK3308B 내장 코덱 레퍼런스의 바이어스 저항/캡 값은 미확인 → 위 값은 일반 일렉트렛 회로 [추정]. Rockchip RK3308 하드웨어 설계 가이드 입수 시 대조.
- MIC1이 ALSA의 몇 번째 캡처 채널인지 미확인 → H0에서 다채널 녹음으로 확인 (§8).

### 4.4 I2C — OLED + RTC

```
3V3(Pin1) ──┬── OLED VCC ── SSD1306 128x64 (0x3C)
            └── RTC  VCC ── DS3231 모듈(ZS-042 계열, 0x68 + EEPROM 0x57)
Pin3 I2C1_SDA ─┬─ OLED SDA ─ RTC SDA
Pin5 I2C1_SCL ─┴─ OLED SCL ─ RTC SCL
풀업: 모듈 내장 풀업 병렬 사용 (외부 추가 안 함)
```

- **반드시 3.3V 급전**: 5V로 급전하면 모듈 풀업이 SDA/SCL을 5V로 끌어올림 → GPIO 허용치(3.63V) 초과 [근거: brief §5.2 + 모듈 일반 구조].
- 풀업 병렬값: 모듈별 4.7k~10k 병렬 → 약 2.4k~5k로 100kHz 운용에 적합 [추정]. 실측 후 3개 이상 겹치면 일부 제거.
- **ZS-042 충전 회로 주의**: VCC→다이오드/저항→코인셀 충전 경로가 있어 **CR2032(비충전)** 사용 시 해당 저항 제거 필요 (널리 알려진 이슈, 모듈 실물로 확인) [추정].
- RTC는 펫 시간의 기준 → 컨셉 문서의 시간 역행 감지 로직과 짝.

### 4.5 버튼 x4 · 엔코더 · LED

```
버튼 (FEED Pin16 / PLAY Pin18 / SLEEP Pin22 / TALK Pin12), 각각 동일:
  3V3 ── R 10kΩ ──┬── R 100Ω ── GPIO        (Active Low)
                  ├── C 100nF ── GND         (RC ≈ 1ms 하드웨어 디바운스 + SW 20ms)
                  └── SW(12x12 택트) ── GND

EC11 엔코더 (A Pin11 / B Pin13 / SW Pin15):
  A,B : 3V3 ── 10kΩ ──┬── 10kΩ ── GPIO,  노드 ── 10nF ── GND   (EC11 데이터시트 권장형)
  C   : GND
  SW  : 버튼과 동일 회로

LED (Pin21 LED_NOTI):
  GPIO ── 1kΩ ── LED(Ø3, 고효율) ── GND     → (3.3-1.8)/1k ≈ 1.5mA
```

- 입력 8개 모두 **이벤트(edge) 기반**(libgpiod) — 폴링 금지 (CPU·지연).
- 내부 풀업 대신 외부 10kΩ: 커널/DT 바이어스 설정 의존 제거, 부팅 직후 상태 결정적.
- GPIO 구동 전류 한계는 brief 미기재 → LED 1.5mA로 보수적 설정.

### 4.6 결선표 (보드 ↔ 외부)

핀 할당 원본: `/Users/heebiny/diyProj/pocketpet/beatling/hw/pinout/pinmap.csv` (그림: `pinout.svg`)

| 신호 | 보드 핀 | GPIO | gpiochip:line [계산] | 방향 | 연결처 |
|---|---|---|---|---|---|
| 5V_IN | 2, 4 | — | — | 전원 | 캐리어 5V_SYS |
| 3V3 | 1, 17 | — | — | 전원 | OLED·RTC / 풀업 |
| I2C1_SDA | 3 | GPIO0_B3 | 0:11 | 양방향 | OLED, RTC |
| I2C1_SCL | 5 | GPIO0_B4 | 0:12 | 출력 | OLED, RTC |
| HP_DET | 7 | GPIO2_A4 | 2:4 | 입력 | 3.5mm 잭 검출 |
| ENC_A | 11 | GPIO0_B7 | 0:15 | 입력 | EC11 A |
| BTN_TALK | 12 | GPIO2_A5 | 2:5 | 입력 | 말걸기 |
| ENC_B | 13 | GPIO0_C0 | 0:16 | 입력 | EC11 B |
| ENC_SW | 15 | GPIO0_C1 | 0:17 | 입력 | EC11 푸시 |
| BTN_FEED | 16 | GPIO2_B2 | 2:10 | 입력 | 밥 |
| BTN_PLAY | 18 | GPIO2_B1 | 2:9 | 입력 | 놀자 |
| AMP_MUTE | 19 | GPIO1_C7 | 1:23 | 출력 | Q1 게이트 |
| LED_NOTI | 21 | GPIO1_C6 | 1:22 | 출력 | LED |
| BTN_SLEEP | 22 | GPIO2_A7 | 2:7 | 입력 | 재워 |
| MIC_BIAS | 33 | MICBIAS1 | — | 아날로그 | R10 |
| MIC_N / MIC_P | 49 / 50 | MICN1 / MICP1 | — | 아날로그 | 일렉트렛 |
| LINE_R / LINE_L | 51 / 52 | LINEOUT_R/L | — | 아날로그 | 믹스망·헤드폰 |
| AGND | 27 | — | — | GND | 마이크 리턴 |
| (예약) | 8 / 10 | UART0 | 2:1 / 2:0 | — | 디버그 콘솔 |

- gpiochip:line은 Rockchip 규칙(`GPIOx_Yz → chip x, line = Y*8+z`, A=0…D=3) 계산값. **H0에서 `gpioinfo`로 반드시 대조.**
- Pin 12/16/18/22는 I2S0 TX 대체기능 핀 — 내장 코덱만 쓰므로 GPIO 사용. 다른 기능으로 pinmux 점유 여부는 H0에서 확인.
- 예비: Pin 23/24(UART1·I2C0), 39/40(UART3), 26(ADC_IN0, 볼륨 포트 옵션) — Rev B 확장 여지.

---

## 5. BOM (Rev A)

단가는 국내 소매 기준 대략치 [추정] — 발주 시 갱신.

| # | 품목 | 사양/예시 | 수량 | 비고 |
|---|---|---|---|---|
| 1 | ROCK Pi S | RS308-D4 (보유) | 1 | |
| 2 | microSD | 32GB High Endurance | 1 | 쓰기 수명 |
| 3 | USB 메모리 | 32GB USB 2.0 | 1 | 음악 라이브러리 |
| 4 | USB-C 리셉터클 브레이크아웃 | CC 5.1kΩ 내장형 | 1 | 내장 여부 확인 |
| 5 | PTC 퓨즈 | hold 2.0A | 1 | |
| 6 | TVS | SMBJ5.0A | 1 | |
| 7 | 전해 캐패시터 | 470µF 10V 저ESR / 220µF 10V x3 | 4 | C1, C3, C6, C7 |
| 8 | 세라믹 캐패시터 | 10µF, 1µF x4, 100nF x6, 10nF x2 | — | |
| 9 | 앰프 | PAM8302A 모노 2.5W 브레이크아웃 | 1 | SD 풀업 레벨 확인 |
| 10 | 스피커 | 40mm 4Ω 3W | 1 | 깊이 15mm 이하 |
| 11 | MOSFET | 2N7002 (SOT-23 → 변환기판) | 1 | Q1 |
| 12 | OLED | 0.96" SSD1306 I2C 128x64, 3.3V 동작 | 1 | 모듈 치수 실측 |
| 13 | RTC | DS3231 모듈(ZS-042) + CR2032 | 1 | 충전 저항 제거 |
| 14 | 로터리 엔코더 | EC11 스위치 포함, 20 디텐트 + 노브 | 1 | |
| 15 | 택트 스위치 | 12x12mm + 캡 Ø10 | 4 | |
| 16 | LED | Ø3 고효율 | 1 | |
| 17 | 일렉트렛 마이크 | Ø9.7 캡슐 | 1 | |
| 18 | 3.5mm 잭 | 스위치 내장형 패널 마운트 | 1 | |
| 19 | 저항 | 10kΩ x14, 2.2kΩ, 1kΩ, 100Ω x6, 33Ω x2 | — | |
| 20 | 커넥터 | 2x13 IDC 리본(F-F) x2, JST-PH 세트 | — | |
| 21 | 만능기판 | 40x24(캐리어), 80x25(프런트) | 2 | |
| 22 | 체결 | M2.5x6 셀프탭 x4(보드), M2x5 x4(캐리어), M3x8 x4(바닥판) | — | |
| 23 | 어댑터 | 5V/3A USB-C | 1 | |
| 24 | 함체 | PETG 3D 프린팅 (쉘 + 바닥판) | 1 | PLA는 여름 차내 변형 위험 |

---

## 6. 기구 설계 (CAD)

> ⚠️ **2026-11-10 기획서 D11로 외관이 "가로 포켓 플레이어"(약 120×62×30mm)로 변경됨.** 아래 박스형(100×90×62) CAD는 구버전 — 기획 승인 후 M2에서 재설계해 대체한다. 스피커도 40mm 원형 → 슬림 직사각형으로 변경 예정 (기획서 §6.5).

원본: `/Users/heebiny/diyProj/pocketpet/beatling/hw/cad/beatling_enclosure.py` (FreeCAD 1.x `freecadcmd`로 실행)

### 6.1 구성

| 면 | 배치 | 치수 (스크립트 변수) |
|---|---|---|
| 외형 | 100(W) x 90(D) x 62(H), 벽 2.4, 수직 모서리 R6 | `W D H T R_OUT` |
| 전면 | OLED 창 24x13 (중앙 상단), LED Ø3.2, 버튼 4개 Ø10.5 피치 20 (하단) | `OLED_* LED_* BTN_*` |
| 상면 | EC11 Ø7.2 + 회전방지 탭 홀 | `ENC_*` |
| 우측면 | 스피커 40mm 그릴(Ø2.5 격자, R16) + 내부 고정 링 | `SPK_* GRILLE_*` |
| 좌측면 | 3.5mm 잭 Ø6.2, 마이크 음향포트 Ø2 + 내부 부트(Ø9.9) | `JACK_* MIC_*` |
| 후면 | 이더넷+USB-A 통합 개구 40x17, 전원 USB-C 슬롯 9.6x3.8 | `PORT_* USBC_*` |
| 바닥판 | 보드 스탠드오프 4(높이 6), 캐리어 스탠드오프 4, 통풍 슬롯 5, M3 카운터보어 4, 고무발 자리 4 | `make_base()` |

- 보드는 **이더넷/USB-A 면이 후면 벽에 닿도록** 배치 (`BOARD_Y1 = D - T - 4.8`). 보드 USB-C는 내부(전면 방향)를 향함 → Maskrom 플래싱은 바닥판 분리 후.
- 마이크(좌측)–스피커(우측) 최대 이격.

### 6.2 검증 결과 (2026-11-10 실행)

```
[shell] valid=True solids=1 volume=78881.4 mm3 bbox=(100.0 x 90.0 x 62.0)
[base]  valid=True solids=1 volume=18845.5 mm3 bbox=(94.8 x 84.8 x 8.4)
[interference shell-base]   0.000 mm3
[interference shell-dummy*] 0.000 mm3   (보드 / 이더넷 잭 / 스피커 더미)
[interference base-dummy*]  0.000 mm3
```
- 1차 실행에서 좌후측 코너 보스와 보드·스탠드오프 간섭(4.45mm³) 발견 → `BOARD_X0` 8→12mm로 수정 후 0.
- **검사 범위 한계**: 더미는 보드·이더넷 잭·스피커만. OLED·버튼 기판·엔코더·캐리어 부품 높이는 미모델링 → 실측 후 더미 추가 필요.

### 6.3 실측 후 수정할 값 ([MEASURE] 표시)

| 변수 | 현재 가정 | 측정 방법 |
|---|---|---|
| `HOLE_INSET` | 3.0 | 보드 장착홀 중심–모서리 (brief 미기재) |
| `PORT_CX`, `PORT_W/H` | 보드 중심, 40x17 | 이더넷·USB-A 실제 위치/높이 → 개별 개구로 분리 |
| 이더넷 잭 높이 | 13.5 | 캘리퍼스 |
| `OLED_WIN_*` | 24x13 | 모듈 표시영역·모듈 장착홀 |
| `ENC_TAB_OFF` | 7.8 | EC11 탭 위치 |
| `SPK_D` | 40 | 스피커 외경·깊이 |
| `USBC_*` | 9.6x3.8 @ (82,14) | 브레이크아웃 모델 |

### 6.4 출력·인쇄

- 재질 PETG, 0.2mm 레이어, 벽 3 perimeter. 쉘은 **상면을 바닥으로** 뒤집어 인쇄 (전면 개구 브리지 최소화) [추정].
- 1차 인쇄 후 개구 위치 확인 → 스크립트 수정 → 재출력. 스크립트가 원본이므로 STL을 직접 고치지 않음.

---

## 7. 개발 단계 및 일정

기간은 주말 작업 기준 [추정].

| 단계 | 기간 | 작업 | 통과 게이트 |
|---|---|---|---|
| **H0** 보드 bring-up | 1주 | OS(Radxa Debian) 설치, 디버그 콘솔 확인, I2C1 활성화, ALSA 코덱 확인, `gpioinfo` 대조 | §8 체크리스트 전부 통과 |
| **H1** 브레드보드 검증 | 1주 | §4 서브회로를 하나씩 결선해 단독 시험 | T2~T6 단독 통과 |
| **H2** Rev A 조립 | 1주 | 캐리어·프런트 만능기판 납땜, 함체 1차 인쇄, [MEASURE] 반영 재인쇄 | 함체 조립 완료, 결선 도통 검사 |
| **H3** 통합 시험 | 1주 | §9 전 항목 | T1~T8 통과 |
| **H4** Rev B 설계 | 2~3주 | KiCad로 캐리어+프런트 PCB, 역류 방지 ideal diode, 실측 반영 함체 v2 | DRC 통과, PCB 발주 |

**단계 간 규칙**: 앞 단계 게이트 실패 시 다음 단계 진입 금지. 특히 **H0에서 LINEOUT·MIC 동작이 확인 안 되면** 오디오 경로를 USB 오디오 동글로 바꾸는 설계 변경을 H1 전에 결정.

---

## 8. H0 bring-up 체크리스트

| # | 확인 | 명령/방법 | 기대 결과 |
|---|---|---|---|
| 1 | 디버그 콘솔 | USB-UART(3.3V) → Pin 8(TX)/10(RX)/GND, 1500000 8N1 [확인 필요] | 부트 로그 출력. 안 나오면 115200 시도, `cat /proc/cmdline`의 `console=` 확인 |
| 2 | GPIO 번호 대조 | `gpioinfo` | §4.6 계산값과 라인 이름/번호 일치 |
| 3 | pinmux 점유 | `cat /sys/kernel/debug/pinctrl/*/pinmux-pins \| grep -E "gpio2-(4\|5\|7\|9\|10)"` | 할당 핀이 다른 기능에 점유되지 않음 |
| 4 | I2C1 활성화 | Radxa `rsetup` 오버레이 또는 DT 수정 [확인 필요] → `i2cdetect -l` | i2c-1(번호는 실기 확인) 존재 |
| 5 | 코덱 장치 | `aplay -l`, `arecord -l` | 내장 코덱 카드 표시 |
| 6 | LINEOUT | `speaker-test -c2 -t sine -f 1000` + 오실로스코프/이어폰 | Pin 51/52에 신호 |
| 7 | MIC 채널 | `arecord -D hw:<card>,0 -c 8 -r 16000 -f S16_LE -d 5 t.wav` 후 채널별 레벨 비교 | MIC1이 몇 번 채널인지 확정 |
| 8 | 온도 센서 | `cat /sys/class/thermal/thermal_zone*/temp` | 값 읽힘 (T7 기준) |

---

## 9. 통합 시험 계획 (H3)

| # | 항목 | 방법 | 합격 기준 |
|---|---|---|---|
| T1 | 5V 강하 | 최대 볼륨 1kHz 사인 + USB 메모리 읽기 동시, Pin 2에서 오실로스코프 | 최저 ≥ 4.75V [목표, 미검증] |
| T2 | 스피커 노이즈 | 무음 재생 시 청감 + 마이크로 노이즈 플로어 녹음 | 30cm에서 험/히스 청감상 없음 |
| T3 | 팝 노이즈 | 전원 투입·재부팅·재생 시작/정지 각 10회 | 뮤트 로직으로 팝 없음 |
| T4 | 헤드폰 전환 | 잭 삽입/제거 20회 | 스피커 자동 뮤트/복귀 20/20 |
| T5 | 입력 | 버튼별 100회, 엔코더 CW/CCW 각 20디텐트 x10, 빠른 회전 포함 | 누락·중복 0 (`gpiomon`) |
| T6 | I2C/RTC | `i2cdetect`, `hwclock -r`, 전원 차단 24시간 후 시각 | 0x3C/0x68 응답, 드리프트 ±2초/일 이내 [목표] |
| T7 | 열 | 함체 조립 상태로 1시간 연속 재생 + OLED 갱신, 실온 25°C | SoC < 70°C [목표 — 85°C 스로틀 대비 여유] |
| T8 | 정전 내성 | 재생+로그 쓰기 중 전원 강제 차단 100회 (릴레이 자동화) | 부팅 실패 0, `fsck` 오류 0 |

- T8 자동화: 다른 보드/릴레이로 30초 간격 전원 토글, 매 부팅 후 SSH로 `journalctl -b -1 -p err`와 fs 상태 수집.

---

## 10. 리스크·미확인 목록

| # | 항목 | 영향 | 확인 시점 | 대안 |
|---|---|---|---|---|
| R1 | 내장 코덱 LINEOUT/MIC가 기본 이미지에서 동작하는지 | 오디오 경로 전체 | H0 #5~7 | USB 오디오 동글 (USB-A 점유 → 음악은 microSD로) |
| R2 | 디버그 UART 위치·속도 | bring-up 난이도 | H0 #1 | 네트워크(SSH)만으로 진행 |
| R3 | PAM8302 브레이크아웃 SD 풀업 전압·입력 캡 유무 | GPIO 손상 / 부품 중복 | 부품 수령 시 회로도 확인 | MOSFET 경유 설계로 이미 대비 |
| R4 | 보드 USB-C ↔ Pin 2·4 역류 | 전원 충돌 | 운용 규칙(Rev A) | Rev B ideal diode |
| R5 | 앰프 피크 시 5V 강하 → SD 손상 | 데이터 손실 | T1, T8 | 캡 증설, 볼륨 상한, 앰프 전원 분리 |
| R6 | LINEOUT 헤드폰 구동력 | 헤드폰 음량 부족 | H1 | 헤드폰 앰프 추가 |
| R7 | 밀폐 함체 발열 | 스로틀 → 오디오 끊김 | T7 | 통풍 슬롯 확대, 방열판 |
| R8 | 보드 장착홀·포트 실제 위치 | 함체 재출력 | H2 | 파라메트릭 수정 |
| R9 | 장기 공급 (2028-09 보장) | 양산 | 양산 판단 시 | Core SoM 또는 RK3308 직접 설계 |
| R10 | Linux 부팅 시간 | "켜면 바로" 경험 | H0 측정 | 상시 전원 운용(탁상형 전제), 휴대형은 재설계(컨셉 문서 §3) |
