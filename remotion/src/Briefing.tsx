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
      {/* 좌상단 브랜드 */}
      <div
        style={{
          position: "absolute",
          top: 56,
          left: 64,
          fontSize: 34,
          fontWeight: 700,
          letterSpacing: 3,
          color: "rgba(245,247,250,0.42)",
        }}
      >
        {BRAND}
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

      {/* 우상단 검증 라벨 배지 */}
      {scene.label ? (
        <div
          style={{
            position: "absolute",
            top: 52,
            right: 64,
            backgroundColor: LABEL_COLOR[scene.label] ?? "#888888",
            color: "#10131a",
            padding: "12px 28px",
            borderRadius: 10,
            fontSize: 40,
            fontWeight: 800,
          }}
        >
          {scene.label}
        </div>
      ) : null}

      {/* 중앙: key takeaway (화면엔 핵심만) */}
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

      {/* 하단 자막 바: 전체 나레이션 (인용이면 강조색 + 「」) */}
      {subtitle ? (
        <div
          style={{
            position: "absolute",
            bottom: 70,
            left: 0,
            right: 0,
            display: "flex",
            justifyContent: "center",
            padding: "0 140px",
          }}
        >
          <div
            style={{
              backgroundColor: "rgba(8,11,16,0.82)",
              borderRadius: 14,
              padding: "22px 44px",
              maxWidth: 1480,
              borderLeft: isQuote ? `8px solid ${ACCENT}` : "none",
              opacity: cueOpacity,
            }}
          >
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
          </div>
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
