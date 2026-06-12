// build_basemap — 권역 베이스맵 사전 계산 생성기 (v0.39.0, 다권역판)
//
// world-atlas(Natural Earth 50m, 퍼블릭 도메인) → 메르카토르 투영 →
//   assets/maps/<region>_map.js        (window.SK_MAPS["<region>"] — 브라우저용)
//   assets/maps/<region>_map.meta.json (투영 파라미터 + bbox — 변환기(Python)용)
//
// 변환기는 meta 의 mercator 파라미터로 임의 lon/lat 를 px 로 투영하고,
// 권역 선택은 마커 bbox ⊂ 권역 bbox 검사로 한다.
//
// 실행: node hyperframes/scripts/build_basemap.mjs   (d3-geo 등은 작업 dir 의
//       node_modules 를 심볼릭 링크 — build_mideast_map.mjs 와 동일 절차)

import { geoMercator, geoPath } from "d3-geo";
import * as topojson from "topojson-client";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const topo = JSON.parse(readFileSync(require.resolve("world-atlas/countries-50m.json"), "utf8"));
const countries = topojson.feature(topo, topo.objects.countries);

// 권역 정의 — 새 권역은 여기 추가 후 재실행
const REGIONS = {
  mideast: {
    bbox: [[25.5, 26.5], [56.5, 40.5]],
    show: {
      364: ["이란", true], 422: ["레바논", true], 376: ["이스라엘", true],
      368: ["이라크", false], 760: ["시리아", false], 400: ["요르단", false],
      792: ["튀르키예", false], 682: ["사우디", false], 818: ["이집트", false],
      196: ["키프로스", false], 414: ["쿠웨이트", false], 275: ["팔레스타인", false],
      51: ["아르메니아", false], 31: ["아제르바이잔", false], 268: ["조지아", false],
      795: ["투르크메니스탄", false], 784: ["UAE", false], 634: ["카타르", false],
      48: ["바레인", false],
    },
    labeled: [364, 422, 376],
  },
  neasia: {
    bbox: [[112, 22], [148, 48]],
    show: {
      410: ["한국", true], 408: ["북한", true], 392: ["일본", true],
      156: ["중국", true], 643: ["러시아", false], 496: ["몽골", false],
      158: ["대만", false],
    },
    labeled: [410, 408, 392, 156],
  },
};

// 스테이지 밴드 (SceneKit.LAYOUT) fitExtent
const EXTENT = [[140, 268], [1780, 862]];

mkdirSync(new URL("../briefing/assets/maps/", import.meta.url), { recursive: true });

for (const [region, cfg] of Object.entries(REGIONS)) {
  const projection = geoMercator().fitExtent(EXTENT, {
    type: "MultiPoint",
    coordinates: cfg.bbox,
  });
  const path = geoPath(projection);

  const out = { countries: [], labels: [] };
  for (const f of countries.features) {
    const id = Number(f.id);
    if (!(id in cfg.show)) continue;
    const d = path(f);
    if (!d) continue;
    const [name, hi] = cfg.show[id];
    out.countries.push({ id, name, hi, d: d.replace(/(\d+\.\d{1})\d+/g, "$1") });
    if (cfg.labeled.includes(id)) {
      const [cx, cy] = path.centroid(f);
      out.labels.push({ name, x: +cx.toFixed(1), y: +cy.toFixed(1) });
    }
  }

  const banner = `/* ${region} basemap — 생성: hyperframes/scripts/build_basemap.mjs
 * 원천: world-atlas countries-50m (Natural Earth, public domain). 수정 금지. */
`;
  writeFileSync(
    new URL(`../briefing/assets/maps/${region}_map.js`, import.meta.url),
    banner + `window.SK_MAPS = window.SK_MAPS || {};\nwindow.SK_MAPS[${JSON.stringify(region)}] = ` +
      JSON.stringify(out) + ";\n",
  );

  // 변환기용 메타: d3 mercator 의 scale/translate → x = t[0] + k·λ,
  // y = t[1] − k·ln(tan(π/4 + φ/2))  (λ, φ 라디안)
  const meta = {
    region,
    bbox: cfg.bbox,
    k: projection.scale(),
    t: projection.translate(),
    extent: EXTENT,
  };
  writeFileSync(
    new URL(`../briefing/assets/maps/${region}_map.meta.json`, import.meta.url),
    JSON.stringify(meta, null, 1) + "\n",
  );
  console.log(`${region}: countries=${out.countries.length} labels=${out.labels.length} ` +
    `k=${meta.k.toFixed(1)} t=[${meta.t.map((v) => v.toFixed(1)).join(",")}]`);
}
