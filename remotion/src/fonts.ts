// fonts.ts — Pretendard 폰트 로딩 (v0.33.0).
// 클라우드 렌더 환경에서는 @remotion/fonts 의 loadFont 가 cancelRender 까지 가서
// 폰트 미존재 시 렌더 자체가 실패. 일단 silent skip — Pretendard 가 시스템에
// 설치돼있으면 family stack 으로 잡히고, 없으면 Segoe UI / sans-serif 폴백.
//
// Phase 5 자막·타이포 표준화에서 staticFile + FontFace + delayRender/continueRender
// 직접 패턴으로 재구현 예정.
export {};
