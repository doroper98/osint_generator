/* 공용 미니 캔들 SVG 생성 (mockup 비교용). NVDA-ish 상승 10봉. color/up/down 토큰 주입. */
window.__mockCandle = function (sel, opt) {
  opt = opt || {};
  var up = opt.up || "#1a1a1a", down = opt.down || "#ffffff", stroke = opt.stroke || up;
  var W = opt.w || 760, H = opt.h || 420, pad = 8;
  var data = [
    { o: 183, h: 186, l: 178, c: 180 }, { o: 180, h: 184, l: 167, c: 175 },
    { o: 175, h: 178, l: 165, c: 168 }, { o: 168, h: 176, l: 166, c: 174 },
    { o: 174, h: 190, l: 174, c: 188 }, { o: 188, h: 202, l: 187, c: 201 },
    { o: 201, h: 217, l: 200, c: 216 }, { o: 216, h: 236, l: 214, c: 225 },
    { o: 225, h: 230, l: 205, c: 210 }, { o: 210, h: 224, l: 204, c: 205 }
  ];
  var lo = 160, hi = 240, N = data.length;
  var x0 = 70, x1 = W - 24, base = H - 60, top = 20;
  function y(p) { return base - (p - lo) / (hi - lo) * (base - top); }
  function cx(i) { return x0 + i * (x1 - x0) / (N - 1); }
  var bw = Math.min(38, (x1 - x0) / N * 0.5);
  var p = [];
  // y grid
  [160, 180, 200, 220, 240].forEach(function (v) {
    p.push('<line x1="' + x0 + '" y1="' + y(v) + '" x2="' + x1 + '" y2="' + y(v) + '" class="mc-grid"/>');
    p.push('<text x="' + (x0 - 12) + '" y="' + (y(v) + 5) + '" class="mc-axis" text-anchor="end">' + v + '</text>');
  });
  data.forEach(function (d, i) {
    var c = cx(i), isUp = d.c >= d.o, yt = y(Math.max(d.o, d.c)), yb = y(Math.min(d.o, d.c));
    p.push('<line x1="' + c + '" y1="' + y(d.h) + '" x2="' + c + '" y2="' + y(d.l) + '" stroke="' + stroke + '" stroke-width="2"/>');
    p.push('<rect x="' + (c - bw / 2) + '" y="' + yt + '" width="' + bw + '" height="' + Math.max(2, yb - yt) +
      '" fill="' + (isUp ? up : down) + '" stroke="' + stroke + '" stroke-width="' + (isUp ? 0 : 2) + '"/>');
  });
  document.querySelector(sel).innerHTML =
    '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="100%">' + p.join("") + '</svg>';
};
