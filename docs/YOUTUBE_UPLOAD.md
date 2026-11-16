---
last_synced_with: v7.4.0
---
# 유튜브 업로드 (`publish/youtube.py`, D-1200)

완성 영상을 유튜브에 **항상 비공개(private)** 로 올린다. 공개 전환은 사용자가 유튜브 스튜디오에서 직접 한다.

## 파이프라인 위치
DELIVER 상태 = `engine.mux`(deliver) → `publish.youtube`(upload). 둘 다 ok 여야 DONE 으로 간다(`orchestrator/engine_service.py STATE_STAGES`).
업로드가 실패하면 DELIVER 에 머문다(15 P6). 같은 영상(md5)을 이미 올렸으면 다시 올리지 않는다 — advance 재실행이 안전하다.
단독 실행:
```
python -m publish.youtube projects/<pid> --dry-run   # 메타데이터만 검증(비밀값 불필요)
python -m publish.youtube projects/<pid>             # 실제 업로드(비공개)
```

## 입력
| 파일 | 쓰임 |
|---|---|
| `out/final.mp4` | 영상(원본 화질, 전달용 압축본 아님). `--video` 로 바꿀 수 있음 |
| `out/description.txt` | 첫 줄 = 제목(100자 이하), 빈 줄 뒤 = 설명(UTF-8 5000바이트 이하, `<` `>` 금지) |
| `out/final.srt` | 자막(captions.insert). `--no-caption` 으로 생략 |

## 설명 한도 맞추기 (자르지 않고, 정해진 순서로, 기록과 함께)
1. 출처 줄의 제목 인용(“…”)을 뺀다 — 기관·매체 이름과 링크는 남는다.
2. 그래도 넘으면 뒤쪽 출처부터 링크를 빼고, 뺀 건수를 설명 끝에 한 줄로 밝힌다(출처 이름은 모두 남음).
3. 그래도 넘으면 오류 — `--description-file` 로 줄인 설명을 넘긴다.
줄인 내용은 StageResult warnings 와 `out/youtube_upload.json description_trims` 에 남는다.
실측: china_tech_export_controls_2026 은 5,844B → 1단계(6건) + 2단계(3건) → 4,917B.

## 합성 미디어 표시
`status.containsSyntheticMedia` 기본값은 `config.yaml youtube.contains_synthetic_media: true`(AI 합성 내레이션). 영상별로 `--synthetic-media no` 로 바꿀 수 있다.

## 비밀값 (C9)
환경 변수 `YT_CLIENT_ID`·`YT_CLIENT_SECRET`·`YT_REFRESH_TOKEN`. 클라우드 환경 설정(로컬은 `.env`)에 저장하고 **새 세션**에서 실행한다.
저장소·로그·커밋에 값을 남기지 않는다. 없으면 오류.

## 할당량 (공식 문서, 2026-11-03 확인)
- videos.insert: Video Uploads 별도 버킷, 1회 1단위, 하루 100회.
- captions.insert: 400단위(공용 버킷 기본 하루 10,000단위).
- 과거 자료의 "업로드 1,600단위"는 옛 값이다.

## 영구 해결 — OAuth 앱 게시 (7일 토큰 만료 없애기)
"테스트 중" + 외부 사용자 유형이면 리프레시 토큰이 7일마다 만료된다. "프로덕션"으로 게시하면 철회·비밀번호 변경 전까지 유지된다.
게시에는 브랜딩 정보가 필요하다. 저장소 `docs/` 는 Vercel 로 공개 배포되므로(`vercel.json`) 그 안에 페이지를 둔다.
| 항목 | 값 |
|---|---|
| 앱 홈페이지 | `https://osint-generator.vercel.app/youtube-app` (`docs/youtube-app/index.html`) |
| 개인정보처리방침 | `https://osint-generator.vercel.app/youtube-app/privacy` (`docs/youtube-app/privacy.html`) |
| 승인된 도메인 | `osint-generator.vercel.app` |
페이지는 Vercel 의 운영 배포 브랜치(main)에 들어가야 열린다. 게시 뒤 첫 동의 화면에는 "확인되지 않은 앱" 경고가 뜬다(개인용, 사용자 100명 미만 — 심사 없이 사용). 고급 → 이동 → 허용.
게시 후에는 리프레시 토큰을 **한 번 새로 받아야** 한다(테스트 중에 받은 토큰은 7일 만료가 그대로).

## 토큰 오류
`invalid_grant` 면 "리프레시 토큰 만료·철회" 안내로 멈춘다 → OAuth Playground 에서 새 토큰 → 환경 변수 교체 → 새 세션.

## 설정
`config.yaml youtube:`(엔드포인트·카테고리·언어·합성 표시·조각 크기·재시도·한도). `privacy_status` 는 `private` 만 허용(스키마).
