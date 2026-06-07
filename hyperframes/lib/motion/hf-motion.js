/*
  hf-motion.js — HyperFrames 모션 헬퍼 (v0.34.18).
  gsap-skills(MIT, greensock) + taste-skill(MIT, Leonxlnx) 의 기술을 우리 결정론적 영상
  렌더에 맞게 내재화한 것. 플러그인 의존 없이(core gsap 만) 자체 구현 — 라이선스/번들 안전.

  영상 렌더 제약과의 정합:
  - 모든 효과는 paused 타임라인(tl)에 add 되어 seek 로 재생됨(스크롤/상호작용 없음).
  - ScrollTrigger/Smoother/Draggable 류는 영상에 부적합 → 미포함. 대신 "진행도 reveal" 서사는
    타임라인 위치(position) 기반으로 표현.
  - 결정론(랜덤/시계 금지): 난수는 seeded PRNG(mulberry32)만.

  사용: <script src="assets/gsap.min.js"></script><script src="lib/motion/hf-motion.js"></script>
        그 뒤 window.__hf.<fn>.
*/
window.__hf = window.__hf || {};
(function (H) {
  "use strict";

  // ── SplitText 기법: 텍스트를 단어 span 으로 분리(스태거 등장용). 플러그인 없이 자체.
  //    반환: 분리된 단어 span 배열(공백은 텍스트노드로 보존). 한글 keep-all 유지.
  H.splitWords = function (el) {
    if (!el) return [];
    var text = el.textContent;
    el.textContent = "";
    var parts = text.split(/(\s+)/);
    var spans = [];
    parts.forEach(function (w) {
      if (w === "") return;
      if (/^\s+$/.test(w)) { el.appendChild(document.createTextNode(w)); return; }
      var s = document.createElement("span");
      s.textContent = w;
      s.style.display = "inline-block";
      s.style.willChange = "transform, opacity";
      el.appendChild(s);
      spans.push(s);
    });
    return spans;
  };

  // ── SplitText(글자 단위): 짧은 디스플레이 타이틀용. 단어 안을 글자 span 으로.
  H.splitChars = function (el) {
    if (!el) return [];
    var text = el.textContent;
    el.textContent = "";
    var spans = [];
    Array.prototype.forEach.call(text, function (ch) {
      if (ch === " ") { el.appendChild(document.createTextNode(" ")); return; }
      var s = document.createElement("span");
      s.textContent = ch;
      s.style.display = "inline-block";
      s.style.willChange = "transform, opacity";
      el.appendChild(s);
      spans.push(s);
    });
    return spans;
  };

  // ── 단어 reveal 프리셋: rise + 미세 회전 + opacity, expo 로 묵직하게(taste: premium).
  H.revealWords = function (tl, el, at, opt) {
    opt = opt || {};
    var spans = H.splitWords(el);
    tl.fromTo(spans,
      { opacity: 0, yPercent: 120, rotationX: -40, transformOrigin: "50% 100%" },
      { opacity: 1, yPercent: 0, rotationX: 0,
        duration: opt.duration || 0.7, ease: opt.ease || "expo.out",
        stagger: opt.stagger || 0.06 },
      at || 0);
    return spans;
  };

  // ── ScrambleText/number 기법: 수치 카운트업(타임라인 add, seek 안전).
  //    el.textContent 를 from→to 로. format(n)->string 커스텀(소수/통화/한글 단위).
  H.countUp = function (tl, el, from, to, opt) {
    opt = opt || {};
    var o = { v: from };
    var fmt = opt.format || function (n) { return String(Math.round(n)); };
    tl.to(o, {
      v: to, duration: opt.duration || 1.4, ease: opt.ease || "power2.out",
      onUpdate: function () { el.textContent = (opt.prefix || "") + fmt(o.v) + (opt.suffix || ""); },
    }, opt.at != null ? opt.at : 0);
  };

  // ── 크로스페이드 전환(ScrollTrigger 의 "reveal 서사"를 타임라인 위치로 번역).
  //    opacity 만으로(visibility 애니 금지 규칙 정합). toEl 은 초기 opacity:0 가정.
  H.crossfade = function (tl, fromEl, toEl, at, opt) {
    opt = opt || {};
    var d = opt.duration || 0.6;
    if (fromEl) tl.to(fromEl, { opacity: 0, duration: d, ease: "power2.inOut" }, at);
    if (toEl) tl.fromTo(toEl, { opacity: 0 }, { opacity: 1, duration: d, ease: "power2.inOut" }, at + d * 0.35);
  };

  // ── gsap-utils 내재화: 결정론 seeded PRNG / clamp / lerp / mapRange.
  H.prng = function (seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
      var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  H.clamp = function (v, a, b) { return Math.max(a, Math.min(b, v)); };
  H.lerp = function (a, b, t) { return a + (b - a) * t; };
  H.mapRange = function (v, a, b, c, d) { return c + (d - c) * ((v - a) / ((b - a) || 1)); };
})(window.__hf);
