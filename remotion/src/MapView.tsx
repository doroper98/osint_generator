import React from "react";
import { geoMercator, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import worldData from "world-atlas/countries-110m.json";

export type MapMarker = {
  id: string;
  name: string;
  lng: number;
  lat: number;
  highlight?: boolean;
};
export type MapArc = {
  fromId: string;
  toId: string;
  label?: string;
  highlight?: boolean;
};
export type MapData = {
  center: number[];
  zoom: number;
  markers: MapMarker[];
  arcs: MapArc[];
};

const ACCENT = "#e0a458";
const LAND = "#1b2230";
const LAND_BORDER = "#2c3647";
const SEA = "#0b0f16";

// world-atlas TopoJSON → 육지 FeatureCollection (런타임 fetch 없음 — npm 패키지 번들).
const land = feature(worldData as any, (worldData as any).objects.countries) as any;

export const MapView: React.FC<{ data: MapData; width: number; height: number }> = ({
  data,
  width,
  height,
}) => {
  const markers = data.markers ?? [];
  const pad = 90;
  const projection = geoMercator();
  if (markers.length >= 2) {
    // 마커 전체가 보이도록 투영을 맞춘다(패딩 포함).
    projection.fitExtent(
      [
        [pad, pad],
        [width - pad, height - pad],
      ],
      { type: "MultiPoint", coordinates: markers.map((m) => [m.lng, m.lat]) } as any
    );
  } else {
    const c = data.center && data.center.length === 2 ? data.center : [0, 20];
    projection
      .center([c[0], c[1]])
      .scale(220 * (data.zoom || 3))
      .translate([width / 2, height / 2]);
  }
  const path = geoPath(projection);
  const xy = (lng: number, lat: number): [number, number] =>
    (projection([lng, lat]) as [number, number]) ?? [0, 0];
  const byId: Record<string, MapMarker> = {};
  markers.forEach((m) => {
    byId[m.id] = m;
  });

  return (
    <svg width={width} height={height} style={{ display: "block", borderRadius: 16, background: SEA }}>
      <path d={path(land) ?? ""} fill={LAND} stroke={LAND_BORDER} strokeWidth={1} />

      {(data.arcs ?? []).map((a, i) => {
        const f = byId[a.fromId];
        const t = byId[a.toId];
        if (!f || !t) return null;
        const p1 = xy(f.lng, f.lat);
        const p2 = xy(t.lng, t.lat);
        const mx = (p1[0] + p2[0]) / 2;
        const my = (p1[1] + p2[1]) / 2;
        const dx = p2[0] - p1[0];
        const dy = p2[1] - p1[1];
        const cx = mx - dy * 0.22;
        const cy = my + dx * 0.22;
        const col = a.highlight ? ACCENT : "#7f8aa0";
        return (
          <path
            key={`arc-${i}`}
            d={`M${p1[0]},${p1[1]} Q${cx},${cy} ${p2[0]},${p2[1]}`}
            fill="none"
            stroke={col}
            strokeWidth={a.highlight ? 4 : 2.5}
            strokeDasharray="2 9"
            strokeLinecap="round"
            opacity={0.92}
          />
        );
      })}

      {markers.map((m, i) => {
        const [x, y] = xy(m.lng, m.lat);
        const col = m.highlight ? ACCENT : "#cdd4df";
        const r = m.highlight ? 11 : 7;
        return (
          <g key={`mk-${i}`}>
            <circle cx={x} cy={y} r={r} fill={col} stroke="#0e1116" strokeWidth={2} />
            <text
              x={x}
              y={y - r - 9}
              fontSize={26}
              fontWeight={700}
              textAnchor="middle"
              fill="#f5f7fa"
              stroke="#0b0f16"
              strokeWidth={5}
              paintOrder="stroke"
              style={{ fontFamily: "sans-serif" }}
            >
              {m.name}
            </text>
          </g>
        );
      })}
    </svg>
  );
};
