// build_mideast_map — 중동 베이스맵 사전 계산 생성기 (v0.35.3)
//
// world-atlas(Natural Earth 50m, 퍼블릭 도메인) TopoJSON → 메르카토르 투영 →
// hyperframes/briefing/assets/mideast_map.js (window.MIDEAST_MAP) 출력.
//
// 런타임(브라우저)은 d3 없이 사전 계산된 SVG path d 문자열과 px 좌표만 사용
// → HyperFrames 결정론 계약 유지 (fetch/라이브러리 없음).
//
// 실행 (저장소 root 기준):
//   cd /tmp/geowork   # d3-geo, topojson-client, world-atlas 설치된 작업 dir
//   node /path/to/hyperframes/scripts/build_mideast_map.mjs
//
// 좌표를 추가하려면 PLACES 에 [lon, lat] 을 추가하고 재실행.

import { geoMercator, geoPath } from "d3-geo";
import * as topojson from "topojson-client";
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const topo = JSON.parse(readFileSync(require.resolve("world-atlas/countries-50m.json"), "utf8"));
const countries = topojson.feature(topo, topo.objects.countries);

// 표시 대상 (numeric ISO id → 표기). hi = 사건 당사국 (밝게).
const SHOW = {
  364: { name: "이란", hi: true },
  422: { name: "레바논", hi: true },
  376: { name: "이스라엘", hi: true },
  368: { name: "이라크", hi: false },
  760: { name: "시리아", hi: false },
  400: { name: "요르단", hi: false },
  792: { name: "튀르키예", hi: false },
  682: { name: "사우디", hi: false },
  818: { name: "이집트", hi: false },
  196: { name: "키프로스", hi: false },
  414: { name: "쿠웨이트", hi: false },
  275: { name: "팔레스타인", hi: false },
  51: { name: "아르메니아", hi: false },
  31: { name: "아제르바이잔", hi: false },
  268: { name: "조지아", hi: false },
  795: { name: "투르크메니스탄", hi: false },
  784: { name: "UAE", hi: false },
  634: { name: "카타르", hi: false },
  48: { name: "바레인", hi: false },
};
// 권역 라벨을 직접 박을 나라 (centroid 사용)
const LABELED = new Set([364, 422, 376]);

// 스테이지 밴드 (SceneKit.LAYOUT)에 맞춘 fitExtent
const projection = geoMercator().fitExtent(
  [
    [140, 268],
    [1780, 862],
  ],
  {
    type: "MultiPoint",
    // 동지중해~이란 동부 bbox (lon, lat)
    coordinates: [
      [25.5, 26.5],
      [56.5, 40.5],
    ],
  },
);
const path = geoPath(projection);

const out = { countries: [], labels: [], places: {} };

for (const f of countries.features) {
  const id = Number(f.id);
  if (!(id in SHOW)) continue;
  const d = path(f);
  if (!d) continue;
  out.countries.push({
    id,
    name: SHOW[id].name,
    hi: SHOW[id].hi,
    d: d.replace(/(\d+\.\d{1})\d+/g, "$1"), // 소수 1자리 컷 (용량)
  });
  if (LABELED.has(id)) {
    const [cx, cy] = path.centroid(f);
    out.labels.push({ name: SHOW[id].name, x: +cx.toFixed(1), y: +cy.toFixed(1) });
  }
}

const PLACES = {
  tehran: [51.389, 35.689],
  dahieh: [35.5, 33.84], // 베이루트 다히예
  nisrael: [35.3, 33.05], // 북부 이스라엘 (키르야트 시모나 인근)
  beirut: [35.5, 33.89],
  slebanon: [35.4, 33.35], // 남부 레바논 (헤즈볼라 거점)
  jerusalem: [35.21, 31.77],
  washington_anchor: [27.5, 37.5], // 지도 밖 미국 노드 자리 (동지중해 상공)
};
for (const [k, lonlat] of Object.entries(PLACES)) {
  const [x, y] = projection(lonlat);
  out.places[k] = [+x.toFixed(1), +y.toFixed(1)];
}

const banner = `/* mideast_map — 사전 계산 베이스맵 (생성: hyperframes/scripts/build_mideast_map.mjs)
 * 원천: world-atlas countries-50m (Natural Earth, public domain)
 * 투영: Mercator fitExtent [[140,268],[1780,862]] bbox lon 25.5~56.5 / lat 26.5~40.5
 * 수정 금지 — 생성기를 고치고 재실행할 것. */
`;
writeFileSync(
  new URL("../briefing/assets/mideast_map.js", import.meta.url),
  banner + "window.MIDEAST_MAP = " + JSON.stringify(out) + ";\n",
);
console.log(
  `countries=${out.countries.length} labels=${out.labels.length} places=${Object.keys(out.places).length}`,
);
console.log("places px:", JSON.stringify(out.places));
