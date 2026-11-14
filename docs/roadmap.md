# BEATLING 로드맵 체크리스트

- 기준 문서: `/Users/heebiny/diyProj/pocketpet/beatling/기획서.md` §9(마일스톤), `/Users/heebiny/diyProj/pocketpet/beatling/hw/HW-개발계획서.md` §7(H0~H4)
- 이력·근거는 `/Users/heebiny/diyProj/pocketpet/docs/history.md`에 있다.
- 항목을 끝낼 때마다 같은 커밋에서 체크하고 이력을 남긴다. 미검증 항목은 하위 `[ ]`로 남긴다.

## M0 기획 승인

- [x] 기획서 v0.2 작성, PR 오픈 (develop ← feature/product-plan)
- [x] 기획서 리뷰 — `/Users/heebiny/diyProj/pocketpet/docs/review/기획서-v0.2-리뷰_2026-11-14.md`
- [ ] v0.3: 리뷰 R1(전원 OFF↔시간 점프), R2(기력 규칙) 수정 — **머지 전 권장**
- [ ] v0.3: R7(§0 D1~D11 표기), R6의 §6.5 반영(키 2+2 + 가운데 마이크, 두께 30 확정 근거, 엔코더 전면 우측)
- [ ] R3·R4·R5·R8 결정 (M3 전까지)
- [ ] D1~D9 승인 → PR 머지

## M2 (선행) 가로 포켓 함체 CAD 재설계 — `feature/cad-pocket-enclosure`

- [x] 1차 형상: 전면 쉘 + 뒤판 + 키캡 4 (120x62x30)
- [x] 자동 검사: 41개 파트 전 쌍 간섭 0, 뒤판·키 기판 삽입 경로 간섭 0
- [x] 검사기 음성 대조 3건 FAIL 검출 확인
- [x] HW 계획서 §1·§2·§4·§5 BOM·§6을 새 외관에 맞춰 갱신
- [ ] C1 USB-A 방향·치수 실물 확인
- [ ] [MEASURE] 값 실측 반영 (HW 계획서 §6.5 표)
- [ ] C2 OLED 배선 출구, C3 헤더 직납 배선 공간 — 실물 배선으로 확인
- [ ] 1차 인쇄 → 맞춤 확인 → 수정 → 재출력
- [ ] M2 게이트 "함체 간섭 0" — 실물 기준 통과

## M1 이후

- [ ] M1 기반 / H0 bring-up (HW 계획서 §8 체크리스트)
- [ ] M2 재생+스캔 / H1 브레드보드
- [ ] M3 펫 코어 / H2 Rev A 조립
- [ ] M4 진화+다이얼 / H3 통합 시험
- [ ] M5 공유+사서함
- [ ] M6 실운용 → `rev-a` 태그
