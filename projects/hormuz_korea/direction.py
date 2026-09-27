"""『호르무즈와 한국』 연출층 (v2.1.0) — v3 render3.py 상단 연출층(:173-266)을 그대로 옮겼다.

바뀐 것은 세 가지뿐이다.
1. `dip(t)` + `CUT_TARGET` 큐 → `dip(t, lon, lat, w)` 인자형(19 §3.10). 컷 목적지 값은 v3 큐 순서 그대로.
2. 패널 문구·인물·국가·표시 시각을 패널 이벤트 필드로 옮겼다(D25). 좌표·크기·색은 engine/panels/*.py.
3. 이미지 이름: 사진·컷아웃은 media/ 파일명, 휘장은 emblems/ id. 선박 점 영역·시드·봉쇄 라벨은 이벤트 필드.
연출 시각은 문장 앵커(S/E/SC/SC_END/at_word)로만 쓴다(02 §1).
"""

from __future__ import annotations

from engine.camera import Director
from engine.timebase import Timebase

PL = {"hormuz": (56.35, 26.55), "seoul": (126.98, 37.57), "ulsan": (129.31, 35.54), "busan": (129.04, 35.10),
      "kharg": (50.32, 29.24), "aden": (46.8, 12.4), "embassy": (126.9775, 37.5725), "erbil": (44.01, 36.19)}
ROUTE = [(56.2, 26.45), (57.8, 24.9), (60.5, 22.6), (65.0, 18.2), (72.0, 11.0), (79.5, 5.4), (88.0, 5.6), (95.2, 5.9),
         (98.8, 4.6), (101.5, 2.6), (104.1, 1.25), (106.5, 3.8), (110.0, 9.5), (115.0, 15.5), (120.2, 20.2), (122.4, 23.8),
         (123.8, 28.2), (126.2, 32.2), (128.6, 34.5), (129.35, 35.45)]
CHEONG = [(129.04, 35.05), (126.4, 32.3), (123.9, 28.3), (122.5, 23.9), (120.3, 20.3), (115.0, 15.5), (110.0, 9.5),
          (106.5, 3.8), (104.1, 1.25), (101.5, 2.6), (98.8, 4.6), (95.2, 5.9), (88.0, 5.6), (79.5, 5.4), (70.0, 9.0),
          (60.0, 12.0), (52.5, 12.6), (47.2, 12.3)]


def direct(tb: Timebase) -> Director:  # noqa: PLR0915 — 연출 한 편은 긴 목록이다
    S, E, SC, SC_END, at_word = tb.S, tb.E, tb.SC, tb.SC_END, tb.at_word  # noqa: N806
    TOTAL = tb.total  # noqa: N806
    title = tb.card("title")
    d = Director()
    cam, ev, dip = d.cam, d.ev, d.dip

    cam(0, 127.35, 36.35, 6.4, 0, "cut")
    # open
    ev("marker", S("open_0", 0.2), SC_END("open"), lon=PL["seoul"][0], lat=PL["seoul"][1], label="서울", sub="대통령실 기자회견", side="right", hl=True)
    ev("badge", S("open_0", 0.6), SC_END("open"), lon=125.05, lat=37.25, kind="person", pid="lee_jae_myung", flag="kr", R=34, label="이재명", role="대한민국 대통령", accent="gold")
    ev("card", S("open_1", 0.1), E("open_2", 0.6), tag="기자회견 · 9월 18일", lines=["전쟁에 개입하는 파병은 없다", "한국 선박·국민 보호는 최소한으로 계속"], accent="gold")
    # title (camera cut hidden under title card)
    dip(title.t0 + 2.9, 57.6, 25.3, 24, under=True)
    # route
    ev("marker", S("route_0", 0.1), SC_END("route"), lon=PL["hormuz"][0], lat=PL["hormuz"][1], label="호르무즈 해협", sub="가장 좁은 곳 약 39km", side="right", hl=True)
    cam(S("route_1", -0.6), 88.5, 19.5, 90, 3.4)
    ev("route", S("route_1", 0.6), SC_END("route"), pts=ROUTE, grow=E("route_3", -0.4) - S("route_1", 0.6), col="gold", ship=True)
    ev("card", S("route_1", 0.5), E("route_2", 0.7), tag="2025년 수입 중 호르무즈 경유 비중", bigs=[("61%", "원유"), ("54%", "나프타")], accent="gold", src="로이터 · 대통령실 인용 수치")
    ev("badge", E("route_3", -0.5), SC_END("route"), lon=127.0, lat=31.3, kind="flag", flag="kr", R=18, label="울산", accent="gold")
    # war
    cam(S("war_0", -1.2), 54.8, 27.0, 14.0, 3.4)
    ev("country", S("war_0", 0.1), SC_END("war"), codes=["IR"], col="ru", a=0.07)
    ev("boom", S("war_0", 1.2), S("war_0", 3.4), lon=PL["kharg"][0], lat=PL["kharg"][1])
    ev("marker", S("war_0", 1.2), E("war_0", 0.5), lon=PL["kharg"][0], lat=PL["kharg"][1], label="하르그섬", sub="이란 원유 수출 거점", side="left", icon="boom")
    ev("badge", S("war_1", 0.2), E("war_1", 0.8), lon=57.6, lat=29.35, kind="person", pid="khamenei", flag="ir", R=32, label="알리 하메네이", role="이란 최고지도자 (1939–2026)", accent="ru")
    ev("marker", S("war_2", 0.0), SC_END("war"), lon=PL["hormuz"][0], lat=PL["hormuz"][1], label="호르무즈 해협", sub="3월 2일 IRGC 봉쇄 선언", side="right", hl=True)
    ev("barrier", S("war_2", 0.3), SC_END("war"), p0=(56.28, 27.05), p1=(56.42, 26.28), label="봉쇄")
    ev("route", S("war_3", 0.2), SC_END("war"), pts=[(56.9, 25.9), (58.2, 25.0), (60.4, 24.3)], grow=1.8, col="teal", ship=False, dashed=True, label="허가받은 배만 통과")
    ev("badge", S("war_3", 1.6), SC_END("war"), lon=59.4, lat=23.35, kind="flag", flag="cn", R=17, label="중국", accent="teal")
    ev("badge", S("war_3", 2.0), SC_END("war"), lon=60.9, lat=23.35, kind="flag", flag="in", R=17, label="인도", accent="teal")
    # ask panels
    ev("panel", SC("ask") - 0.2, E("ask_3", 0.5), kind="refusal", title="3월 15일의 요구, 다음 날의 거절",
       actor=dict(pid="trump", flag="us", label="도널드 트럼프", role="미국 대통령", accent="us"),
       rows=[dict(flag=c, label=nm, t_refuse=at_word("ask_1", nm), hl=(c == "kr"))
             for c, nm in (("de", "독일"), ("gb", "영국"), ("jp", "일본"), ("au", "호주"), ("kr", "한국"))],
       demand_label="해협 방어 참여 요구", refuse_label="거절",
       quote_bottom=dict(text="“우리가 시작한 전쟁이 아니다” — 보리스 피스토리우스 독일 국방장관", t0=S("ask_2", 0.3), t1=E("ask_2", 0.9)),
       quote_actor=dict(text="“매우 어리석은 실수” — 트럼프 대통령", t0=S("ask_3", 0.2), t1=E("ask_3", 1.2)))
    ev("panel", S("ask_4", -0.3), SC_END("ask"), kind="statement", title="3월 21일 공동성명", subtitle="이란의 공격 규탄 · 항행의 자유 보장 촉구",
       signers=[dict(flag=c, label=nm) for c, nm in (("gb", "영국"), ("fr", "프랑스"), ("de", "독일"), ("it", "이탈리아"),
                                                     ("jp", "일본"), ("nl", "네덜란드"), ("ca", "캐나다"))],
       joiner=dict(flag="kr", label="대한민국", role="성명에 동참", t_join=at_word("ask_4", "한국")))
    # timeline panel
    t_tl0, t_tl1 = SC("timeline") - 0.2, SC_END("timeline")
    ev("panel", t_tl0, t_tl1, kind="timeline", title="해협의 일곱 달", subtitle="2026년 2월 – 9월", start="2026-02-01", end="2026-09-30",
       band=dict(start="2026-04-08", end="2026-07-08", label="휴전 4.8 – 7.8", col="green", t_show=S("timeline_3", 0.0)),
       events=[dict(date="2026-02-28", label="개전 · 해협 봉쇄", col="ru", side=-1, t=t_tl0 + 0.8),
               dict(date="2026-03-15", label="트럼프, 동맹에 요구", col="us", side=1, t=t_tl0 + 0.8),
               dict(date="2026-04-07", label="안보리 거부권", col="ru", side=-2, t=S("timeline_1", 0.1)),
               dict(date="2026-04-13", label="미국 해상 봉쇄", col="us", side=2, t=S("timeline_2", 0.1)),
               dict(date="2026-06-17", label="양해각서 서명", col="green", side=-1, t=S("timeline_3", 0.1)),
               dict(date="2026-07-08", label="휴전 붕괴", col="ru", side=1, t=S("timeline_4", 0.1)),
               dict(date="2026-08-25", label="기뢰 제거 발표", col="us", side=-2, t=S("timeline_5", 0.1)),
               dict(date="2026-09-18", label="한국, 파병 않기로", col="gold", side=2, t=t_tl1 - 3.0, dim=True)])
    # cost
    cam(SC("cost") - 1.0, 52.4, 27.2, 13.5, 3.0)
    ev("ships", S("cost_0", 0.2), SC_END("cost"), box=(48.3, 56.2, 24.2, 29.9), n=150, seed=4)
    ev("card", S("cost_0", 0.4), SC_END("cost") - 0.2, tag="국제해사기구 · 6월 11일 기준", lines=["선박 공격 46건", "선원 사망 14명", "발 묶인 배 약 1,000척 · 선원 2만 명"], accent="ru")
    # review
    dip(SC("review") - 0.55, 88.5, 21.5, 92)
    ev("route", S("review_0", 0.3), SC_END("review"), pts=CHEONG, grow=4.5, col="teal", ship=True, label="")
    ev("marker", S("review_0", 4.6), SC_END("review"), lon=PL["aden"][0], lat=PL["aden"][1], label="아덴만", sub="청해부대 2009년~", side="bottom", hl=True)
    ev("badge", S("review_0", 0.3), SC_END("review"), lon=125.6, lat=22.3, kind="flag", flag="kr", R=18, label="부산에서 출항", accent="gold")
    ev("card", S("review_1", 0.0), E("review_2", 0.6), tag="거론된 선택지", lines=["해상초계기", "군수지원함"], accent="teal", src="JTBC·MBC 보도 · 대통령실 “결정된 것 없다”")
    # past panel
    ev("panel", SC("past") - 0.2, SC_END("past"), kind="precedent", title="한국의 해외 파견 결정", subtitle="전례와 이번 결정",
       cards=[dict(year="2004", title="이라크 자이툰 부대", lines=["아르빌 파견", "6자회담 속 대미 관계", "국내 반대 여론"], t0=S("past_1", 0.0),
                   person=dict(pid="roh_moo_hyun", flag="kr", caption="노무현 대통령")),
              dict(year="2009", title="청해부대", lines=["소말리아 아덴만", "해적 대응 · 상선 보호"], t0=S("past_3", 0.2)),
              dict(year="2020", title="작전 구역 확대", lines=["호르무즈까지 확대", "지휘권은 한국군"], t0=at_word("past_3", "호르무즈")),
              dict(year="2026", title="이번 결정", lines=["전쟁 개입 파병 없음", "최소한의 활동만"], t0=E("past_3", -0.6), hl=True)])
    # debate
    dip(SC("debate") - 0.55, 127.0, 37.45, 3.4)
    ev("marker", S("debate_1", 0.2), SC_END("debate"), lon=PL["embassy"][0], lat=PL["embassy"][1], label="주한 미국대사관", sub="9월 8일 파병 반대 집회", side="right", hl=True)
    ev("article", S("debate_0", 0.3), E("debate_0", 1.0), pub="The Korea Herald", date="2026. 09. 07", headline="정부, 전투 격화·반대 여론 확산에 호르무즈 파병 계획 재조정", hl="재조정", sub="국방부 “항행의 자유 회복에 실질적으로 기여할 방안을 국제사회와 협의 중”", note="헤드라인 번역 · 원문 영어")
    ev("panel", S("debate_2", -0.3), SC_END("debate"), kind="versus", title="파병을 둘러싼 두 입장",
       sides=[dict(title="지지하는 쪽", src="UPI 기고 · 9월 8일",
                   items=[dict(text="호르무즈는 곧 한국의 경제 안보", t=S("debate_2", 0.3)),
                          dict(text="원유 61% · 나프타 54%가 이 해협 경유", t=S("debate_2", 1.6))]),
              dict(title="반대하는 쪽", src="Foreign Policy · 9월 10일",
                   items=[dict(text="비전투 부대도 표적이 될 수 있다", t=S("debate_3", 0.3)),
                          dict(text="미국 방공 미사일 재고 감소", t=S("debate_4", 0.3)),
                          dict(text="2004년 파병 당시의 국내 갈등", t=S("debate_4", 1.8))])])
    # decision
    cam(SC("decision") - 0.8, 127.35, 36.6, 6.4, 3.2)
    ev("marker", SC("decision"), SC_END("decision"), lon=PL["seoul"][0], lat=PL["seoul"][1], label="서울", sub="9월 18일 발표", side="right", hl=True)
    ev("badge", S("decision_0", 0.4), SC_END("decision"), lon=125.05, lat=37.25, kind="person", pid="lee_jae_myung", flag="kr", R=34, label="이재명", role="대한민국 대통령", accent="gold")
    ev("card", S("decision_0", 0.8), SC_END("decision") - 0.1, tag="이재명 대통령 · 발언 요지", lines=["“전쟁에 관여하거나 들어가는", "파병은 없다”"], accent="gold", quote=True)
    # now
    dip(SC("now") - 0.55, 88.5, 19.5, 90)
    ev("route", SC("now") - 0.2, TOTAL, pts=ROUTE, grow=0.01, col="gold", ship=False, glow_only=True)
    ev("tanker_loop", SC("now"), TOTAL, pts=ROUTE)
    ev("badge", S("now_0", 0.2), TOTAL, lon=61.8, lat=20.2, kind="emblem", img="navcent", R=28, label="미 해군 중부사령부", role="호위 작전", accent="us")
    ev("card", S("now_0", 0.5), E("now_1", 0.4), tag="미 중부사령부 발표", bigs=[("10억 배럴", "호위 작전으로 반출된 원유")], accent="us")
    ev("card", S("now_2", 0.1), E("now_2", 0.8), tag="2025년 기준", bigs=[("61%", "원유 수입의 호르무즈 경유 비중")], accent="gold")
    ev("marker", SC("now"), TOTAL, lon=PL["hormuz"][0], lat=PL["hormuz"][1], label="호르무즈 해협", sub="", side="right", hl=True)
    cam(S("now_3", -0.5), 90, 20, 96, 9.0)

    # media events (photo / video / cutout / article clipping)
    ev("clip", S("war_2", 0.2), S("war_2", 0.2) + 5.0, clip="niovi", x=40, y=150, w=300, mid="niovi",
       caption="이란 혁명수비대 고속정의 유조선 나포", credit="자료 영상 · 2023. 05. 03 · U.S. Navy · Public domain")
    ev("photo", S("past_1", 0.6), E("past_2", 0.2), img="rok_iraq_720.jpg", x=292, y=138, w=280, mid="rok_iraq",
       caption="이라크에 파병된 한국군 장병", credit="자료사진 · 2003 · U.S. Government · Public domain")
    ev("article", S("review_0", 0.3), E("review_0", 0.9), pub="Reuters", date="2026. 09. 04", headline="한국, 호르무즈 군사 선택지 검토… 대통령실 “결정된 것은 없다”", hl="결정된 것은 없다", sub="JTBC·MBC의 ‘연내 파병 준비’ 보도 이후 나온 대통령실 설명", note="헤드라인 번역 · 원문 영어")
    ev("photo", S("now_0", 1.0), E("now_1", 0.4), img="hormuz_transit_720.jpg", x=560, y=196, w=262, mid="hormuz_transit",
       caption="호르무즈 해협 통과 중 경계 근무를 서는 미 해군", credit="자료사진 · 2023. 05 · U.S. Navy · Public domain")
    ev("clip", S("timeline_4", 0.3), S("timeline_4", 0.3) + 5.0, clip="strikes", x=207, y=112, w=440, mid="strikes",
       caption="미 중부사령부 공개 영상 · 이란 군사 목표 타격", credit="2026. 07. 07 · U.S. Central Command · Public domain")
    ev("cutout", S("review_1", 0.1), E("review_2", 0.4), img="p8_cut.png", lon=112.0, lat=12.5, w=150, mid="p8",
       label="해상초계기 P-8A", sub="자료사진 · U.S. Navy")
    return d
