---
id: R-0335
from: opus
to: fable
kind: report
responds_to: [D-0628, D-0629]
phase: "E9"
version: v7.4.0
commit: HEAD
status: done
---

# 칸나이 콘티 판 v2(효과음 없음) + 효과음 견본 둘 — artifacts ed01e6d4

## 0. 요약
- 게이트 ① 기록: approve script_approval by "user(UF-259)", 원고 sha256 7a07b494·sha1 74d03aff 대조 일치.
- plan 재생성: `tts_resynthesized` = [] 입니다. mp3 캐시 그대로이고 문장 타이밍은 v1 과 같습니다. npy 64개는 캐시 mp3 에서 다시 풀었습니다(음성 재합성 아님).
- mix: 명료도 최저 **15.60 dB**(64문장), 음악 − 내레이션 **−20.78 dB**(전쟁사 잠정 범위 안), 저역 상승 4.78 dB, audio_qa issues 0.
- 콘티 판 v2: 렌더 전 검사 hard 0 · warning 18. 렌더 원본 md5 78f2b47f(34.9MB), 전달판 19.1MB.
- 효과음 견본 둘(178~218초): 효과음 포함 믹스 명료도 전편 최저 15.60 dB, 견본 구간 최저 16.48 dB.
- artifacts: `artifacts/war-history-v7.4.0` ed01e6d4 — `war_history/cannae_216bc/animatic_v2/`·`sfx_sample/`.

## 1. 커밋

| 커밋 | 내용 |
|---|---|
| 49d7accd | BigSoundBank 레코드 메모(D739) |
| df20626c | 효과음 레지스트리 + Briefer 외(2015) 말 울음 S1(Commons CC BY 4.0, 크레딧·변경 표기 문구) |
| 2b835855 | 말 울음 큐 = 울음 한 번(파일 안 울음을 나눠 하나만) |
| 974d7a92 | 양익 포위 궤도 encirclement_5 w 0.085·drift 12초 |
| 2ca3d8e0 | 검사가 잰 값(명료도·이음 MAD)을 검사 뒤 provenance 에 옮김 + 칸나이 manifest |

## 2. 도중에 나온 것 셋
1. **렌더 전 hard [drift-too-fast]**: 206.9~210.9초 줌 0.045/초 > 0.01. 원인은 제 fcf1fab7(궤도 w 0.08→0.095 를 4초에)이고, v1 뒤 커밋이라 v1 에서는 안 걸렸습니다. encirclement_5 를 w 0.085 로, 궤도 drift 를 12초로 늘렸습니다(줌 0.0093/초). seg02 만 다시 준비했고 사전 검사 hard 0 을 확인한 뒤 렌더했습니다. 궤도가 더 천천히 기웁니다.
2. **말 울음 여러 번**: 견본 믹스 기록을 보니 울음 파일 하나에 울음이 여럿이었습니다(Wiehern 2, Briefer S1 3). 파일 통째로 쓰면 "큐당 많아야 한 번"(D-0628 §3)이 깨집니다. 파일 안 울음을 나눠 하나만 쓰도록 고쳤습니다(rules audio.battle_sfx.call, 시험 고정). 견본은 고친 뒤 믹스입니다.
3. **provenance 빈칸**: narration_clarity 와 terrain3d.seam 이 v2 provenance 에서 null 이었습니다. 두 값은 검사가 재는데 provenance 를 검사 전에 만들기 때문입니다(29384676·D-0619 장치의 배선 빈틈). 2ca3d8e0 로 세 렌더 경로 모두 검사 뒤에 옮기게 고쳤습니다. 이번 판은 같은 상태에서 같은 함수로 다시 재어 채웠고, `measures_filled_after` 칸에 그 사실을 적었습니다. 이음 MAD 최대 6.17(≤ 12).

## 3. 콘티 판 v2
- warning 18: shots 6 · media_beats 7 · geo_unsourced 4 · battle_sfx_missing 1(효과음 판정 전 의도).
- 린트 경고 1: deployment_9 [tense-present](D-0628 §4 면제, 영상 고지 문장).
- 손실 패널(대표 프레임 panel_4m41_4m47.jpg): 281초 두 기둥 좌우 → 283.6초 왼쪽 위아래 → 287초 슬로츠 상 카드 + 두 기둥 모두 보임. 카드가 숫자·출처 줄을 덮지 않습니다.
- 151초 날짜 표지 "기원전 300~201년"(deployment_9, D-0622)이 화면에 나옵니다.

## 4. 효과음 견본
- 구간 178~218초: 기병 충돌·하마 백병전(encirclement_0~2), 한니발 탄식·투석(3~4, 투석 소리 없음), 중앙 보병 압박·양익 포위(5~6), 동맹 기병 패주(7).
- 큐 6: 질주 v0.45 · 금속 v0.3 · 울음 v0.35(기병), 군중 v0.5 · 금속 v0.7(보병), 질주 v0.5(동맹 기병). 모두 far.
- 처음 값(질주 0.6·금속 0.45·울음 0.5)에서 encirclement_1 명료도가 14.59 dB 라 기병 구간 셋을 낮췄습니다.
- 두 판은 엔진과 같은 2패스 loudnorm(전편 믹스 기준, −14.02 LUFS) 뒤 잘랐습니다. 효과음 층은 믹스 대비 차이 RMS 약 −22 dB 입니다.
- 견본에 Briefer 울음(CC BY 4.0)이 쓰였습니다. 견본 README 에 크레딧 줄을 적었습니다. 본편에 넣으면 credits.yaml sfx 행이 필요합니다([battle-sfx] 가 강제).
- 사용자 고지용(감독 몫): 여러 마리 기병 질주와 실제 집단 난전 금속음은 권리에 맞는 녹음이 없어, 한 마리 질주 4개와 단발 부딪힘 55개를 시간차로 겹쳐 만들었습니다. 군중은 먼 축구 관중 녹음(새소리는 저역 통과로 깎음)이라 말소리가 들리는지 청취 판정이 필요합니다.

## 5. 권리 대조 한 줄(최종 감독 요청)
- BigSoundBank 라이선스 페이지는 제목이 "CC0-like" 이나 본문은 "Creative Commons CC0 1.0 Universal" 을 명시합니다(감독 직접 대조 D739). 레코드 license CC0 유지, 메모에 Content ID 미등록·제3자 오등록 청구 가능성을 적었습니다(49d7accd).

## 6. 시험
- tests/test_battle_sfx.py 18(울음 한 번 포함)·anti_inertia/test_no_magic_numbers·tests/test_render_check_measures.py 2 통과.
- 전체 pytest 는 오늘 돌리지 않았습니다(D187 — main 병합 전·하루 1회).
