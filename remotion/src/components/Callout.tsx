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

// Callout v2 (v0.33.0) — light 톤. Subject + Connector + Note.
// 글로우/halo 제거. 1px hairline + 채워진 점. 검정 텍스트.

export type CalloutProps = {
  subject: { x: number; y: number };
  note: { x: number; y: number };
  title: string;
  body?: string | null;
  color?: string;
  startFrame?: number;
  subjectRadius?: number;
  noteWidth?: number;
  curve?: number;
};

export const Callout: React.FC<CalloutProps> = ({
  subject,
  note,
  title,
  body,
  color = accent.primary,
  startFrame = 0,
  subjectRadius = 5,
  noteWidth = 260,
  curve = 0.3,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const f = Math.max(0, frame - startFrame);

  const subjectEnd = msToFrames(duration.short, fps);
  const connectorStart = subjectEnd;
  const connectorEnd = connectorStart + msToFrames(duration.short, fps);
  const noteStart = connectorEnd - msToFrames(duration.micro, fps);
  const noteEnd = noteStart + msToFrames(duration.short, fps);

  const subjectScale = interpolate(f, [0, subjectEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: (t) => 1 - Math.pow(1 - t, 3),
  });
  const connectorProgress = interpolate(f, [connectorStart, connectorEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: (t) => 1 - Math.pow(1 - t, 3),
  });
  const noteOpacity = interpolate(f, [noteStart, noteEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const midX = (subject.x + note.x) / 2;
  const midY = (subject.y + note.y) / 2;
  const dx = note.x - subject.x;
  const dy = note.y - subject.y;
  const cx = midX + dy * curve * 0.4;
  const cy = midY - dx * curve * 0.4;
  const approxLen = Math.hypot(dx, dy) * 1.1;
  const dashOffset = approxLen * (1 - connectorProgress);

  return (
    <g>
      <path
        d={`M ${subject.x} ${subject.y} Q ${cx} ${cy} ${note.x} ${note.y}`}
        stroke={color}
        strokeWidth={strokeToken.thin}
        fill="none"
        strokeDasharray={approxLen}
        strokeDashoffset={dashOffset}
        strokeLinecap="round"
        opacity={0.7}
      />
      <circle
        cx={subject.x}
        cy={subject.y}
        r={subjectRadius * subjectScale}
        fill={color}
      />
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
              fontSize: size.caption,
              fontWeight: weight.extrabold,
              lineHeight: lineHeight.tight,
              color,
              marginBottom: 4,
              textTransform: "uppercase",
              letterSpacing: 1.5,
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
