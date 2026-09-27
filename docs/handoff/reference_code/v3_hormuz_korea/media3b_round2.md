# media 2차 수집·가공 (라운드 7) — 실행 기록

`media3.py`(1차: 호르무즈 통과 사진, P-8A 컷아웃, 7.7 타격 영상) 이후 채팅에서 인라인으로 실행한 2차 처리 절차.

1. 후보 검색: `media3.py`와 같은 Commons API 검색에 쿼리 추가
   - zaytun: 'Zaytun Division Korean soldiers Iraq' → `Southkoreansoldiersiraq.jpg` (Public domain, 2003) 채택
   - tanker_photo: 'oil tanker at sea filetype:bitmap' → CC BY 4.0 후보(풍력단지 위주) **탈락**(관련성 부족)
   - hormuz_video(1차 결과 재사용): `Oil tanker Niovi seized by Iran's Islamic Revolutionary Guard Corps…webm` (Public domain, 2023-05-03) 채택
2. 다운로드: 429가 지속되어 60~90초 대기 후 **원본 URL**로 받음(요청 사이 15초). extmetadata Artist가 템플릿 문자열로 오염 → 저작자 'U.S. Government (PD-USGov)'로 정제.
3. 사진 가공: 원본 → thumbnail(1600) → 커버 크롭 720×450 → 채도 0.82, 대비 1.06 → `rok_iraq_720.jpg`
4. 영상 구간 선택: 전체에서 12장 썸네일 시트 → 고속정이 유조선을 에워싸는 28.0~33.0초 선택(사람 식별 없음)
5. 영상 추출:
```bash
ffmpeg -ss 28.0 -t 5.0 -i media/niovi.webm -vf "scale=480:270,fps=24" -f rawvideo -pix_fmt rgb24 media/niovi_480.rgb
python -c "import numpy as np; a=np.fromfile('media/niovi_480.rgb',np.uint8).reshape(-1,270,480,3); np.save('media/niovi_480.npy',a)"
# 1차 타격 영상도 같은 방식: -ss 1.5 -t 5.0 -i media/strikes.webm → strikes_480.npy
```
6. 기사 클리핑 카드(Reuters 9.4, The Korea Herald 9.7)는 자산 없이 `render3.py`의 `ev('article', …)`로 조판.
