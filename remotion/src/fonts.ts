// fonts.ts — Pretendard 로딩 (v0.33.0).
// 클라우드 렌더에서 @remotion/fonts 의 loadFont 가 cancelRender 까지 가서 폰트
// fetch 실패 시 렌더 자체 실패. 일단 silent skip — Pretendard 가 사용자 머신에
// 설치돼 있으면 family stack 으로 잡힘, 없으면 시스템 sans-serif 폴백.
//
// Phase 5 자막·타이포 표준화에서 staticFile + FontFace + delayRender/continueRender
// 직접 패턴으로 안전 재구현 예정.
export {};
