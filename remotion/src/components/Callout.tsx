import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import {
  accent,
  duration,
  fontFamily,
  koreanTextStyle,
  lineHeight,
  msToFrames,
  size,
  stroke as strokeToken,
  text,
  weight,
} from "../design";

// Callout — D3-annotation Subject + Note + Connector 패턴.
// Subject: 데이터 포인트 (점/원).
// Connector: leader line (curved 또는 straight).
// Note: 라벨 텍스트 (제목 + 본문).
//
// SVG group 으로 반환. 호출자가 차트 좌표계에 위치시킨다.
// 진입 모션: Subject (300ms) → Connector draw (300ms) → Note fade (200ms).

export type CalloutProps = {
  // Subject 위치 (데이터 포인트, px).
  subject: { x: number; y: number };
  // Note 위치 (라벨 박스 좌상단, px). Connector 가 subject → note 로 그려진다.
  note: { x: number; y: number };
  title: string;
  body?: string | null;
  // 강조 컬러 (기본 spotlight).
  color?: string;
  // 진입 시작 프레임 (호출자가 차트 진입 + 지연을 제어).
  startFrame?: number;
  // Subject 점 반경.
  subjectRadius?: number;
  // Note 라벨 박스 폭.
  noteWidth?: number;
  // Connector 곡률 (0 = 직선, 1 = 강한 곡선).
  curve?: number;
};

export const Callout: React.FC<CalloutProps> = ({
  subject,
  note,
  title,
  body,
  color = accent.spotlight,
  startFrame = 0,
  subjectRadius = 6,
  noteWidth = 280,
  curve = 0.35,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const f = Math.max(0, frame - startFrame);

  // 진입 트랙: subject grow → connector draw → note fade.
  const subjectEnd = msToFrames(duration.short, fps);
  const connectorStart = subjectEnd;
  const connectorEnd = connectorStart + msToFrames(duration.short, fps);
  const noteStart = connectorEnd - msToFrames(duration.micro, fps);
  const noteEnd = noteStart + msToFrames(duration.micro * 1.5, fps);

  const subjectScale = interpolate(f, [0, subjectEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: (t) => 1 - Math.pow(1 - t, 3), // decelerate 근사
  });

  const connectorProgress = interpolate(
    f,
    [connectorStart, connectorEnd],
    [0, 1],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: (t) => 1 - Math.pow(1 - t, 3),
    }
  );

  const noteOpacity = interpolate(f, [noteStart, noteEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Bezier 컨트롤 포인트 — subject 와 note 의 중간점에 곡률 적용.
  const midX = (subject.x + note.x) / 2;
  const midY = (subject.y + note.y) / 2;
  const dx = note.x - subject.x;
  const dy = note.y - subject.y;
  // 수직 방향으로 곡률 — 부호는 note 위치에 따라.
  const cx = midX + dy * curve * 0.5;
  const cy = midY - dx * curve * 0.5;

  // path 길이 근사로 stroke-dasharray 진입.
  const approxLen = Math.hypot(dx, dy) * 1.15;
  const dashOffset = approxLen * (1 - connectorProgress);

  return (
    <g>
      {/* Connector (curved) */}
      <path
        d={`M ${subject.x} ${subject.y} Q ${cx} ${cy} ${note.x} ${note.y}`}
        stroke={color}
        strokeWidth={strokeToken.thin}
        fill="none"
        strokeDasharray={approxLen}
        strokeDashoffset={dashOffset}
        strokeLinecap="round"
        opacity={0.85}
      />

      {/* Subject — outer halo + inner dot */}
      <circle
        cx={subject.x}
        cy={subject.y}
        r={subjectRadius * 2.4 * subjectScale}
        fill={color}
        opacity={0.18 * subjectScale}
      />
      <circle
        cx={subject.x}
        cy={subject.y}
        r={subjectRadius * subjectScale}
        fill={color}
      />

      {/* Note — foreignObject 로 한글 줄바꿈 적용. */}
      <foreignObject
        x={note.x}
        y={note.y - 12}
        width={noteWidth}
        height={200}
        style={{ opacity: noteOpacity }}
      >
        <div
          style={{
            fontFamily,
            color: text.primary,
            ...koreanTextStyle,
          }}
        >
          <div
            style={{
              fontSize: size.body,
              fontWeight: weight.bold,
              lineHeight: lineHeight.tight,
              color,
              marginBottom: 4,
            }}
          >
            {title}
          </div>
          {body ? (
            <div
              style={{
                fontSize: size.caption,
                fontWeight: weight.medium,
                lineHeight: lineHeight.normal,
                color: text.secondary,
              }}
            >
              {body}
            </div>
          ) : null}
        </div>
      </foreignObject>
    </g>
  );
};
