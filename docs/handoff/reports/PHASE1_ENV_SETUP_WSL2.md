<!--
tier: 2
last_synced_with: v2.0.0
ssot_for: [phase1-env-setup-wsl2]
depends_on: [tools/check_env.py, docs/handoff/DECISIONS.md, docs/handoff/19a_V3_CODE_INVENTORY.md]
last_review: 2026-09-27
-->

# Phase 1 실행 환경 — WSL2 설치 절차 (D9)

> **검증 범위**: 아래 절차는 Ubuntu 24.04 클라우드 컨테이너에서 그대로 실행했습니다(2026-09-27).
> `tools/check_env.py`가 **20 ok / 0 missing, exit 0**으로 끝났습니다. WSL2 기본 배포판도 Ubuntu 24.04라
> 같은 결과가 기대됩니다. 다만 **사용자 WSL2에서 직접 돌린 결과는 아직 없습니다.** 8단계 출력을 보내 주세요.

## 0. 설치 전 상태 (클라우드 컨테이너 실측)

`check_env` 첫 실행 결과 누락 11건이었습니다. WSL2 신규 설치도 비슷할 것입니다.

| 분류 | 누락 |
|---|---|
| 모듈 | pycairo, shapely, scipy, edge-tts, cairosvg, fonttools, rembg |
| 폰트 | IBM Plex Sans KR, Noto Serif CJK KR, GmarketSans, IBM Plex Mono |
| 바이너리 | ffmpeg (컨테이너는 imageio-ffmpeg로 대체돼 있었음) |

## 1. WSL2 준비 (Windows PowerShell, 관리자)

```powershell
wsl --install -d Ubuntu-24.04
```

- 저장소는 **Linux 파일시스템**(`~/`)에 clone합니다. `/mnt/c/...`는 렌더 I/O가 크게 느립니다.

## 2. 시스템 패키지 (WSL2 Ubuntu 셸)

```bash
sudo apt-get update
sudo apt-get install -y git python3-venv python3-dev pkg-config libcairo2-dev ffmpeg fontconfig fonts-noto-cjk
```

- `libcairo2-dev`·`pkg-config`가 없으면 pycairo 빌드가 실패합니다.
- `fonts-noto-cjk`가 `Noto Serif CJK KR`을 제공합니다(v3는 이 폰트를 내려받지 않고 설치돼 있다고 가정).

## 3. 저장소와 가상환경

```bash
cd ~ && git clone https://github.com/doroper98/osint_generator.git && cd osint_generator
git checkout overhaul/v2-map-engine
git config core.hooksPath .githooks
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 4. 엔진 파이썬 모듈

```bash
pip install pycairo numpy pillow shapely scipy pyyaml pydantic edge-tts requests cairosvg fonttools rembg onnxruntime
```

- `rembg`는 첫 사용 때 모델(약 170MB)을 받습니다. 인물 1순위는 저장소 라이브러리이고 rembg는 폴백입니다(19 §8 R4).
- 이 목록은 Phase 1에서 `requirements-engine.txt`로 고정할 예정입니다.

## 5. 폰트 4종 (D3 — 저장소에 커밋하지 않음)

URL은 v3 `prep3.py fonts()`와 같습니다(19a §B). 설치 위치는 사용자 폰트 폴더입니다.

```bash
F=~/.local/share/fonts/osint; mkdir -p "$F"; cd "$F"
B=https://raw.githubusercontent.com/google/fonts/main/ofl
for w in Regular Medium SemiBold Bold; do curl -fsSL -o IBMPlexSansKR-$w.ttf $B/ibmplexsanskr/IBMPlexSansKR-$w.ttf; done
for w in Medium SemiBold; do curl -fsSL -o IBMPlexMono-$w.ttf $B/ibmplexmono/IBMPlexMono-$w.ttf; done
for w in Bold Medium; do curl -fsSL -o GmarketSans$w.woff https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.1/GmarketSans$w.woff; done
python3 -c "
from fontTools.ttLib import TTFont
for w in ('Bold','Medium'):
    f=TTFont(f'GmarketSans{w}.woff'); f.flavor=None; f.save(f'GmarketSans{w}.otf')"
rm -f GmarketSans*.woff && fc-cache -f && cd ~/osint_generator
```

- GmarketSans woff→otf 변환본은 공백 글리프가 깨집니다. v3 `text()`의 공백 특례로 보정하며, 알려진 현상입니다(19 §3.13).
- Phase 1의 `tools/fetch_data.py fonts`가 이 단계를 대체합니다(D3).

## 6. 폰트 이름 해석 확인 (위험 R1)

v3 렌더러가 부르는 이름 8개가 의도한 굵기로 잡히는지 봅니다.

```bash
for n in "IBM Plex Sans KR" "IBM Plex Sans KR Medium" "IBM Plex Sans KR SemiBold" "GmarketSansBold" \
         "GmarketSansMedium" "IBM Plex Mono SemiBold" "IBM Plex Mono Medium" "Noto Serif CJK KR"; do
  printf "%-28s -> " "$n"; fc-match "$n" family style; done
```

컨테이너 실측 결과 8개 모두 해당 굵기로 해석됐습니다(예: `IBM Plex Sans KR Medium -> …:style=Medium`).
WSL2는 fontconfig를 쓰므로 Windows 네이티브 cairo의 이름 해석 위험(R1)은 피합니다.

## 7. 비밀 값

```bash
cp .env.example .env 2>/dev/null || touch .env   # ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID — 커밋 금지(C9)
```

Phase 1 골든 재현은 edge-tts 음성을 쓰므로 ElevenLabs 키가 없어도 됩니다. 키는 Phase 4부터 필요합니다.

## 8. 점검 — 이 출력을 보내 주세요

```bash
python tools/check_env.py; echo "exit=$?"
python -m pytest -q
```

기대값은 `summary: 20 ok / 0 missing`, `exit=0`, `388 passed, 8 xfailed`입니다.
