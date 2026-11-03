---
last_synced_with: v7.4.0
---
# 유튜브 업로드 (`tools/youtube_upload.py`, D-1200)

완성 영상(`out/final.mp4` 원본 화질)을 유튜브에 **항상 비공개(private)** 로 올린다. 공개 전환은 사용자가 유튜브 스튜디오에서 직접 한다.

## 입력
| 파일 | 쓰임 |
|---|---|
| `out/final.mp4` | 영상(전달용 압축본 아님). `--video` 로 바꿀 수 있음 |
| `out/description.txt` | 첫 줄 = 제목(100자 이하), 빈 줄 뒤 = 설명(UTF-8 5000바이트 이하, `<` `>` 금지) |
| `out/final.srt` | 자막(captions.insert). `--no-caption` 으로 생략 |

한도를 넘으면 **자르지 않고 오류**로 멈춘다(15 P6). 줄인 설명은 `--description-file` 로 넘긴다.
실측: china_tech_export_controls_2026 설명은 5,844바이트로 한도를 넘는다(출처 원문 목록이 대부분).

## 비밀값 (C9)
환경 변수 `YT_CLIENT_ID`·`YT_CLIENT_SECRET`·`YT_REFRESH_TOKEN`. 클라우드 환경 설정에 저장하고 **새 세션**에서 실행한다.
저장소·로그·커밋에 값을 남기지 않는다. 없으면 오류.

## 실행
```
python tools/youtube_upload.py projects/<pid> --synthetic-media yes --dry-run   # 메타데이터만 검증(비밀값 불필요)
python tools/youtube_upload.py projects/<pid> --synthetic-media yes             # 실제 업로드(비공개)
```
`--synthetic-media` 는 기본값 없이 매번 명시한다(`status.containsSyntheticMedia`, 사실적인 변형·합성 콘텐츠 공개 표시).
결과: `out/youtube_upload.json`(schema_version 1 — video_id·url·uploaded_at·privacy_status·caption_id).

## 할당량 (공식 문서, 2026-11-03 확인)
- videos.insert: Video Uploads 별도 버킷, 1회 1단위, 하루 100회.
- captions.insert: 400단위(공용 버킷 기본 하루 10,000단위).
- 과거 자료의 "업로드 1,600단위"는 옛 값이다.

## 토큰 만료
OAuth 앱이 "테스트 중"(외부 사용자 유형)이면 리프레시 토큰이 7일마다 만료된다. `invalid_grant` 면 도구가
"토큰 만료" 안내로 멈춘다 → OAuth Playground 에서 새 토큰 → 환경 변수 교체 → 새 세션.
영구 해결: 홈페이지·개인정보처리방침 공개 페이지 + 승인된 도메인 등록 → "앱 게시".

## 설정
`config.yaml youtube:`(엔드포인트·카테고리·언어·조각 크기·재시도·한도). `privacy_status` 는 `private` 만 허용(스키마).
