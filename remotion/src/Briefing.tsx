import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { MapView, MapData } from "./MapView";
import { ChartView, ChartData } from "./ChartView";
import { AuroraGlassCard } from "./AuroraGlassCard";

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

// render_props.json 의 scene 1개와 동일 구조 (orchestrator/render_io.py:RenderSceneProps).
export type SubtitleCue = {
  text: string;
  startSec: number;
  durationSec: number;
};

export type Scene = {
  sceneId: string;
  startSec: number;
  durationSec: number;
  caption: string;
  narration: string;
  subtitleCues?: SubtitleCue[];
  mapData?: MapData | null;
  chartData?: ChartData | null;
  label: string | null;
  sourceLinkRequired: boolean;
  // 화면 상단 출처 표기(있을 때만). 소스 본문 배선 전엔 빈 문자열.
  source?: string;
  // on-screen 텍스트가 인용이면 강조색 + 인용부호로 표기 (영상 문법 ③).
  isQuote?: boolean;
  // 나레이션 wav 의 public-dir(=project_dir) 기준 상대경로. 무음이면 null.
  audioPath?: string | null;
};

export type BriefingProps = {
  title: string;
  scenes: Scene[];
};

// 라벨별 배지 색 (docs/06 §6 라벨 시스템).
const LABEL_COLOR: Record<string, string> = {
  "<확인>": "#5cb85c",
  "<추론>": "#5bc0de",
  "<주장>": "#f0ad4e",
  "<미검증>": "#d9534f",
  "<반박됨>": "#d9534f",
};

const BG = "#0e1116";
const ACCENT = "#e0a458"; // 인용 강조색
const BRAND = "OSINT 브리핑"; // 채널 브랜드(좌상단). 추후 config 화.

export const DEFAULT_PROPS: BriefingProps = {
  title: "OSINT 브리핑 (샘플)",
  scenes: [
    {
      sceneId: "scene_01",
      startSec: 0,
      durationSec: 5,
      caption: "핵심 한 줄",
      narration: "render_props.json 이 전달되지 않으면 보이는 기본 슬라이드입니다.",
      label: null,
      sourceLinkRequired: false,
    },
  ],
};

const Slide: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const isQuote = Boolean(scene.isQuote);
  const hasMap = Boolean(scene.mapData && (scene.mapData.markers?.length ?? 0) > 0);
  const hasChart = Boolean(scene.chartData && scene.chartData.type);
  const hasVisual = hasMap || hasChart;
  const takeaway = scene.caption
    ? isQuote
      ? `“${scene.caption}”` // “ ”
      : scene.caption
    : "";

  // 자막은 통문단이 아니라 큐(줄) 단위로 순차 표시 — 현재 프레임 시각에 해당하는 큐만.
  const cues = scene.subtitleCues ?? [];
  const tSec = frame / fps;
  let subtitle = scene.narration;
  let cueOpacity = 1;
  if (cues.length > 0) {
    const active =
      cues.find((c) => tSec >= c.startSec && tSec < c.startSec + c.durationSec) ??
      cues[cues.length - 1];
    subtitle = active.text;
    // 큐 시작 시 짧은 페이드인.
    const cueFrame = (tSec - active.startSec) * fps;
    cueOpacity = interpolate(cueFrame, [0, 6], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  }

  return (
    <AbsoluteFill style={{ backgroundColor: BG, color: "#f5f7fa", fontFamily: "sans-serif" }}>
      {/* 좌상단 브랜드 — 절제된 글래스 태그(글로우 약하게) */}
      <div style={{ position: "absolute", top: 48, left: 56 }}>
        <AuroraGlassCard radius={10} padding="8px 20px" glow={false} sweepSec={14}>
          <span style={{ fontSize: 30, fontWeight: 700, letterSpacing: 3, color: "rgba(245,247,250,0.78)" }}>
            {BRAND}
          </span>
        </AuroraGlassCard>
      </div>

      {/* 상단 출처 표기 (있을 때만) */}
      {scene.source ? (
        <div
          style={{
            position: "absolute",
            top: 60,
            left: 420,
            right: 420,
            textAlign: "center",
            fontSize: 24,
            lineHeight: 1.45,
            color: "rgba(245,247,250,0.4)",
          }}
        >
          출처 : {scene.source}
        </div>
      ) : null}

      {/* 우상단 검증 라벨 배지 — 글래스 카드 + 라벨 색 점/텍스트 */}
      {scene.label ? (
        <div style={{ position: "absolute", top: 48, right: 60 }}>
          <AuroraGlassCard radius={12} padding="10px 22px" sweepSec={11}>
            <span style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ width: 16, height: 16, borderRadius: 8, background: LABEL_COLOR[scene.label] ?? "#888888" }} />
              <span style={{ fontSize: 38, fontWeight: 800, color: LABEL_COLOR[scene.label] ?? "#cdd4df" }}>
                {scene.label}
              </span>
            </span>
          </AuroraGlassCard>
        </div>
      ) : null}

      {/* 중앙: 비주얼(지도/차트, 있으면) + key takeaway 는 제목으로 축소. 없으면 큰 takeaway. */}
      {hasVisual ? (
        <AbsoluteFill
          style={{
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            paddingTop: 150,
            paddingBottom: 280,
            opacity,
          }}
        >
          <div
            style={{
              fontSize: 52,
              fontWeight: 800,
              lineHeight: 1.25,
              textAlign: "center",
              maxWidth: 1500,
              marginBottom: 20,
              color: isQuote ? ACCENT : "#f5f7fa",
            }}
          >
            {takeaway}
          </div>
          {hasMap ? (
            <MapView data={scene.mapData as MapData} width={1360} height={600} />
          ) : (
            <ChartView chart={scene.chartData as ChartData} width={1360} height={560} />
          )}
        </AbsoluteFill>
      ) : (
        <AbsoluteFill
          style={{
            justifyContent: "center",
            alignItems: "center",
            padding: "180px 220px 320px",
            opacity,
          }}
        >
          <div
            style={{
              fontSize: 96,
              fontWeight: 800,
              lineHeight: 1.22,
              textAlign: "center",
              color: isQuote ? ACCENT : "#f5f7fa",
            }}
          >
            {takeaway}
          </div>
        </AbsoluteFill>
      )}

      {/* 하단 자막 바: 전체 나레이션 (인용이면 강조색 + 「」) */}
      {subtitle ? (
        <div
          style={{
            position: "absolute",
            bottom: 64,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            padding: "0 130px",
            opacity: cueOpacity,
          }}
        >
          <AuroraGlassCard radius={16} padding="22px 46px" maxWidth={1520} accentBar={isQuote ? ACCENT : undefined}>
            <span
              style={{
                fontSize: 42,
                lineHeight: 1.5,
                fontWeight: 600,
                color: isQuote ? ACCENT : "#ffffff",
              }}
            >
              {subtitle}
            </span>
          </AuroraGlassCard>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

export const Briefing: React.FC<BriefingProps> = ({ scenes }) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      {scenes.map((scene) => {
        const from = Math.round(scene.startSec * fps);
        const dur = Math.max(1, Math.round(scene.durationSec * fps));
        return (
          <Sequence key={scene.sceneId} from={from} durationInFrames={dur} name={scene.sceneId}>
            {scene.audioPath ? <Audio src={staticFile(scene.audioPath)} /> : null}
            <Slide scene={scene} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
