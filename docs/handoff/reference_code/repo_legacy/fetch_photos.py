"""참고 사본 (v2.0.0) — 원본: hyperframes/scripts/bundle_to_video.py (archive/hyperframes-briefing).

실행 대상이 아니다. Phase 6.5 미디어 수집(tools/media_fetch.py) 참고용 (docs/handoff/19 §5.3).
"""

def fetch_photos(b: dict, report_id: str) -> dict:
    """images[] 를 다운로드해 로컬 자산화 → {image_id: photo 씬 dict}. (IMAGE_BUNDLE_CONTRACT)

    권리 게이트(G4-8/C9): rights_status == "cleared" 만 다운로드·사용. 나머지와
    실패 건은 photos_manifest.json 에 사유와 함께 기록만 한다(추적성). 섹션이
    참조하지 않는 이미지는 받지 않는다. url 이 로컬 파일 경로면 복사(테스트/오프라인).
    """
    import shutil
    import urllib.request

    images = b.get("images") or []
    if not images:
        return {}
    referenced = {r for s in b.get("sections", []) for r in (s.get("image_refs") or [])}
    photo_dir = BRIEFING / "assets" / "photos" / report_id
    out: dict = {}
    manifest = []
    ext_by_mime = {"image/jpeg": ".jpg", "image/png": ".png",
                   "image/webp": ".webp", "image/gif": ".gif"}

    for im in images:
        iid = im.get("image_id") or ""
        url = im.get("url") or ""
        rights = im.get("rights_status") or "needs_review"
        entry = {"image_id": iid, "url": url, "caption": im.get("caption", ""),
                 "credit": im.get("credit", ""), "rights_status": rights,
                 "license": im.get("license", ""), "source_id": im.get("source_id", ""),
                 "used": False, "reason": ""}
        manifest.append(entry)
        if not iid or not url:
            entry["reason"] = "image_id/url 누락"
            continue
        if rights != "cleared":
            entry["reason"] = f"권리 게이트: rights_status={rights} (cleared 만 사용)"
            continue
        if not (im.get("credit") or "").strip():
            # §3.1-a: cleared 의 근거가 출처표기 갈음이므로 credit 없는 cleared 는
            # 전제 불성립 — 소비측 fail-closed 이중화 (producer 보증과 별개).
            entry["reason"] = "credit 누락 — §3.1-a 출처표기 갈음 전제 불성립"
            continue
        if iid not in referenced:
            entry["reason"] = "어느 섹션도 참조하지 않음"
            continue
        try:
            photo_dir.mkdir(parents=True, exist_ok=True)
            if url.startswith(("http://", "https://")):
                req = urllib.request.Request(url, headers={"User-Agent": "osint-generator/0.42"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    mime = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
                    ext = ext_by_mime.get(mime) or (Path(url.split("?")[0]).suffix or ".jpg")
                    data = resp.read(12 * 1024 * 1024 + 1)
                if len(data) > 12 * 1024 * 1024:
                    entry["reason"] = "12MB 초과"
                    continue
                if mime and not mime.startswith("image/"):
                    entry["reason"] = f"이미지 아님: {mime}"
                    continue
                fname = f"{iid}{ext}"
                (photo_dir / fname).write_bytes(data)
            else:
                src = Path(url)
                if not src.exists():
                    entry["reason"] = "로컬 파일 없음"
                    continue
                fname = f"{iid}{src.suffix or '.jpg'}"
                shutil.copyfile(src, photo_dir / fname)
        except Exception as e:  # 다운로드 실패는 스킵 — 파이프라인은 계속
            entry["reason"] = f"다운로드 실패: {type(e).__name__}"
            continue
        entry["used"] = True
        out[iid] = {"src": f"assets/photos/{report_id}/{fname}",
                    "caption": clip(im.get("caption", ""), 60),
                    "credit": clip(im.get("credit", ""), 30),
                    "focus": im.get("focus", "center")}

    if manifest:
        photo_dir.mkdir(parents=True, exist_ok=True)
        (photo_dir / "photos_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        skipped = [m for m in manifest if not m["used"]]
        print(f"[bundle_to_video] photos: {len(out)}장 사용 / {len(skipped)}건 스킵"
              + (f" ({'; '.join(m['image_id'] + ':' + m['reason'] for m in skipped[:3])})"
                 if skipped else ""))
    return out
