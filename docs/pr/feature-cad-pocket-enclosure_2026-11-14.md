# PR: 가로 포켓 플레이어 함체 CAD 1차

- base: `develop` ← head: `feature/cad-pocket-enclosure`
- 머지 방식: Create a merge commit
- 선행 PR #1(기획 승인) 머지 후 develop(`f53483c`) 위로 rebase 완료.

## 요약

기획서 D11(가로 포켓 플레이어)에 맞춰 함체를 재설계했다. 구버전은 100x90x62 박스형이었다.

- 외형 120x62x30. 전면 쉘 + 뒤판 + 키캡 4개로 구성
- ROCK Pi S는 부품면이 뒤판 쪽을 향함. 이더넷·USB-A는 좌측면, 전원 USB-C·3.5mm는 우측면
- 전면: OLED(좌)·LED·EC11 다이얼(우)·스피커 그릴(하단 우). 윗면: 키 2+2 + 가운데 마이크
- 스크립트 자동 검사: 41개 파트 820쌍 간섭 0, 뒤판·키 기판 삽입 경로 간섭 0. 검사기 음성 대조 3건이 FAIL로 검출됨
- 3면 배치도 `beatling/hw/cad/layout.svg` 추가 (재실행해도 동일 출력)
- HW 개발계획서 §1·§2·§4·§5(BOM)·§6을 새 외관에 맞춰 갱신 (40mm 스피커·IDC 리본·프런트 패널·바닥판 제거)
- `docs/roadmap.md`(체크리스트), `docs/history.md`(이력) 신설

## 검증

```
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd \
  /Users/heebiny/diyProj/pocketpet/beatling/hw/cad/beatling_enclosure.py
→ beatling/hw/cad/out/check.txt : RESULT: PASS
```

## 미검증 / 다음

- 더미는 envelope 기준이라 배선 공간은 검사하지 않았다.
- USB-A 방향(세로형 추정), OLED 배선 출구 2.1mm — HW 계획서 §6.4 C1~C9
- [MEASURE] 실측 반영과 1차 인쇄 맞춤 확인

## 변경 파일

- `beatling/hw/cad/beatling_enclosure.py` — 전면 재작성
- `beatling/hw/cad/layout.svg` — 신규 (스크립트 생성)
- `beatling/hw/HW-개발계획서.md`
- `docs/roadmap.md`, `docs/history.md`, `docs/pr/feature-cad-pocket-enclosure_2026-11-14.md` — 신규

🤖 Generated with [Claude Code](https://claude.com/claude-code)
