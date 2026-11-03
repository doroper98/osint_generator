---
id: R-0323
from: opus
to: fable
kind: progress
responds_to: []
phase: "E0"
version: v7.4.0
commit: 2499f012
status: done
---

# RENDER-AP-032 cherry-pick(fddc5526 → 1402503d, 4562b172 → 2499f012) — 골든·anti_inertia·조각 캐시 키

- 두 커밋을 SKIP_VERSION_CHECK=1 로 가져왔다. 충돌은 없었다.
- 아래 시험은 모두 `env -u FONTCONFIG_FILE` 로 돌렸다. 내 셸 설정 없이 장치가 저장소 설정으로 정하게 한 것이다.

## ① 골든 25컷
- 대상: test_provenance_e2e(골든 25컷)·test_q3_light_e2e·test_g12_version_stamp·test_fed_timeline_demo.
- 결과: **12 passed**(68.6초). 재고정은 하지 않았다.
- 옛 내 사본(conf.d 에서 12-unhinted-grayscale·70-fonts-noto-cjk 빠짐)과 저장소 `config/fontconfig/fonts.conf` 를 fc-match -v 로 대조했다. 대상은 IBM Plex Sans KR·GmarketSansBold·Noto Serif CJK KR 이다.
  - file·antialias·hinting·hintstyle 1·autohint·rgba 1·lcdfilter 1·embeddedbitmap 이 모두 같다.
  - 다른 것은 값의 강도 표시 (s)/(w) 뿐이다.
- 70-fonts-noto-cjk 가 빠졌어도 Noto Serif CJK KR 은 같은 파일로 맞는다.

## ② anti_inertia
- `-m "not slow" tests/anti_inertia`: **93 passed**.
- test_fontconfig_guard 따로: **6 passed**.

## ③ 조각 캐시 out/chunks 키에 글꼴 설정이 들어가는가
- 전역 키는 `engine/chunk_cache.py:97 global_key` 다. code_hash 는 :70 이다.
- 들어가는 것: engine·schemas·rules·geo·script·genres 의 .py, rules/*.yaml, config.yaml, 프로젝트·저장소 assets 목록(경로·크기·mtime).
- **들어가지 않는 것**:
  - `config/fontconfig/fonts.conf` 내용. config.yaml 에는 경로만 있다.
  - FONTCONFIG_FILE 환경값, 시스템 /etc/fonts/conf.d.
  - 설치 글꼴 파일(~/.local/share/fonts). 저장소 assets 밖에 있다.
- 간접으로 잡는 것:
  - 탐침 서명(:211·:219)은 출력 해상도 프레임 바이트의 sha1 이다.
  - 그래서 탐침 프레임에 글자가 있으면 글꼴 화소 변화가 키에 들어간다.
  - 다만 탐침 프레임은 1초 간격 + 이벤트 경계다. 글자가 없는 탐침만 있는 조각은 놓칠 수 있다.
- 이번 조치:
  - 이번에는 engine/fontenv.py 가 새로 생겨 code_hash 가 바뀌었다. 그래서 옛 조각은 이미 무효다.
  - 지시대로 캐시를 비웠다(projects/showcase_geo/out/chunks 24M 하나뿐이었다).
- 키 문제 제안(결정 아님): global_key 에 다음을 넣는다.
  - `fontenv.config_file()` 내용
  - `fc-match -v <probe_family>` 의 렌더 속성
  - 엔진 글꼴 파일 md5 9종(R-0322 §2)
  - 그러면 글꼴 설정·파일이 바뀔 때 전부 무효가 된다. 속도 트랙 소관이다.

## 그 밖
- geo 콘티 판(v4)은 R-0321(density B) 사용자 답을 기다린다.
- 장치가 들어왔으니 다음 렌더부터 /tmp/claude-0/work/env.sh 는 쓰지 않는다. 장치가 FONTCONFIG_FILE 을 덮어쓴다.
