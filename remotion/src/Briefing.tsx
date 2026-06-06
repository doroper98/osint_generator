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
import { SurfaceCard } from "./components/SurfaceCard";
import {
  accent,
  fontFamily,
  koreanTextStyle,
  labelColor,
  letterSpacing,
  lineHeight,
  radius,
  shadow,
  size,
  space,
  surface,
  text,
  weight,
} from "./design";

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

const BRAND = "OSINT 브리핑"; // 채널 브랜드(좌상단). 추후 config 화.

// 작은 라벨 배지 — 흰 카드 + 컬러 도트 + 컬러 텍스트 (light 톤).
const LabelBadge: React.FC<{ label: string }> = ({ label }) => {
  const c = labelColor(label);
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 10,
        padding: "8px 18px",
        background: surface.card,
        borderRadius: radius.pill,
        boxShadow: shadow.card,
      }}
    >
      <span style={{ width: 12, height: 12, borderRadius: 6, background: c }} />
      <span
        style={{
          fontSize: size.caption,
          fontWeight: weight.black,
          color: c,
          letterSpacing: letterSpacing.wide,
        }}
      >
        {label}
      </span>
    </div>
  );
};

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
  const opacity = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const isQuote = Boolean(scene.isQuote);
  const hasMap = Boolean(scene.mapData && (scene.mapData.markers?.length ?? 0) > 0);
  const hasChart = Boolean(scene.chartData && scene.chartData.type);
  const hasVisual = hasMap || hasChart;
  const takeaway = scene.caption
    ? isQuote
      ? `"${scene.caption}"`
      : scene.caption
    : "";

  const cues = scene.subtitleCues ?? [];
  const tSec = frame / fps;
  let subtitle = scene.narration;
  let cueOpacity = 1;
  if (cues.length > 0) {
    const active =
      cues.find((c) => tSec >= c.startSec && tSec < c.startSec + c.durationSec) ??
      cues[cues.length - 1];
    subtitle = active.text;
    const cueFrame = (tSec - active.startSec) * fps;
    cueOpacity = interpolate(cueFrame, [0, 8], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  }

  // Ken Burns 미세 스케일 — 모든 씬 1.0 → 1.03 (날리지식 풍 천천히 확대).
  const kenScale = interpolate(frame, [0, scene.durationSec * fps], [1.0, 1.03], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: surface.page,
        color: text.primary,
        fontFamily,
        ...koreanTextStyle,
      }}
    >
      {/* 좌상단 브랜드 */}
      <div
        style={{
          position: "absolute",
          top: space.xxl,
          left: space.xxxl,
          display: "flex",
          alignItems: "center",
          gap: 12,
          zIndex: 10,
        }}
      >
        <span style={{ width: 14, height: 14, borderRadius: 3, background: accent.primary }} />
        <span
          style={{
            fontSize: size.caption,
            fontWeight: weight.black,
            letterSpacing: letterSpacing.wider,
            color: text.primary,
            textTransform: "uppercase",
          }}
        >
          {BRAND}
        </span>
      </div>

      {/* 상단 출처 */}
      {scene.source ? (
        <div
          style={{
            position: "absolute",
            top: space.xxl + 4,
            left: 460,
            right: 460,
            textAlign: "center",
            fontSize: size.meta,
            color: text.tertiary,
            fontWeight: weight.medium,
          }}
        >
          출처 · {scene.source}
        </div>
      ) : null}

      {/* 우상단 검증 라벨 배지 */}
      {scene.label ? (
        <div style={{ position: "absolute", top: space.xxl, right: space.xxxl, zIndex: 10 }}>
          <LabelBadge label={scene.label} />
        </div>
      ) : null}

      {/* 중앙 컨텐츠 — Ken Burns */}
      <AbsoluteFill
        style={{
          transform: `scale(${kenScale})`,
          transformOrigin: "center",
          opacity,
        }}
      >
        {hasVisual ? (
          <div
            style={{
              position: "absolute",
              top: 160,
              left: 0,
              right: 0,
              bottom: 280,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <SurfaceCard padding={space.xxl} style={{ width: 1520 }}>
              <div
                style={{
                  fontSize: size.title,
                  fontWeight: weight.black,
                  lineHeight: lineHeight.display,
                  letterSpacing: letterSpacing.tight,
                  color: isQuote ? accent.primary : text.primary,
                  marginBottom: space.lg,
                  ...koreanTextStyle,
                }}
              >
                {takeaway}
              </div>
              {hasMap ? (
                <MapView data={scene.mapData as MapData} width={1456} height={560} />
              ) : (
                <ChartView chart={scene.chartData as ChartData} width={1456} height={560} />
              )}
            </SurfaceCard>
          </div>
        ) : (
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              padding: "200px 200px 280px",
            }}
          >
            <div
              style={{
                fontSize: 124,
                fontWeight: weight.black,
                lineHeight: lineHeight.tight,
                letterSpacing: letterSpacing.tighter,
                textAlign: "center",
                color: isQuote ? accent.primary : text.primary,
                maxWidth: 1600,
                ...koreanTextStyle,
              }}
            >
              {takeaway}
            </div>
          </div>
        )}
      </AbsoluteFill>

      {/* 하단 자막 — 날리지식 풍 다크 translucent + 흰 굵은 자막 */}
      {subtitle ? (
        <div
          style={{
            position: "absolute",
            bottom: space.xxl,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            padding: "0 140px",
            opacity: cueOpacity,
            zIndex: 20,
          }}
        >
          <div
            style={{
              background: "rgba(26,26,26,0.82)",
              padding: "20px 40px",
              borderRadius: 10,
              maxWidth: 1520,
              borderLeft: isQuote ? `4px solid ${accent.primary}` : undefined,
            }}
          >
            <span
              style={{
                fontSize: 36,
                lineHeight: lineHeight.normal,
                fontWeight: weight.bold,
                color: isQuote ? accent.primary : "#ffffff",
                letterSpacing: letterSpacing.tight,
                ...koreanTextStyle,
              }}
            >
              {subtitle}
            </span>
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

export const Briefing: React.FC<BriefingProps> = ({ scenes }) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: surface.page }}>
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
