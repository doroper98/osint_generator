import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

// render_props.json 의 scene 1개와 동일 구조 (orchestrator/render_io.py:RenderSceneProps).
export type Scene = {
  sceneId: string;
  startSec: number;
  durationSec: number;
  caption: string;
  narration: string;
  label: string | null;
  sourceLinkRequired: boolean;
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

export const DEFAULT_PROPS: BriefingProps = {
  title: "OSINT 브리핑 (샘플)",
  scenes: [
    {
      sceneId: "scene_01",
      startSec: 0,
      durationSec: 5,
      caption: "샘플 캡션",
      narration: "render_props.json 이 전달되지 않으면 보이는 기본 슬라이드입니다.",
      label: null,
      sourceLinkRequired: false,
    },
  ],
};

const Slide: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG,
        color: "#f5f7fa",
        fontFamily: "sans-serif",
        padding: 120,
        justifyContent: "center",
        opacity,
      }}
    >
      {scene.label ? (
        <div
          style={{
            position: "absolute",
            top: 80,
            right: 80,
            backgroundColor: LABEL_COLOR[scene.label] ?? "#888888",
            color: "#10131a",
            padding: "12px 28px",
            borderRadius: 10,
            fontSize: 44,
            fontWeight: 800,
          }}
        >
          {scene.label}
        </div>
      ) : null}
      <div style={{ fontSize: 66, fontWeight: 800, marginBottom: 48, lineHeight: 1.2 }}>
        {scene.caption}
      </div>
      <div style={{ fontSize: 40, lineHeight: 1.6, color: "#c7ccd4" }}>
        {scene.narration}
      </div>
      {scene.sourceLinkRequired ? (
        <div
          style={{
            position: "absolute",
            bottom: 80,
            left: 120,
            fontSize: 28,
            color: "#7a8290",
          }}
        >
          출처: source_registry 참조
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
            <Slide scene={scene} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
