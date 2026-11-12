# -*- coding: utf-8 -*-
FPS = 30
W, H = 1920, 1080
DUR = 30.0

# msg: side L(봇)/R(사용자), kind n(일반)/kw(키워드 강조), t = 장면 시작 기준 초
SC = [
 dict(id='intro',  t0=0.00,  t1=4.95,  tag='FOOD TREND 2027', voice=0, msgs=[
    dict(side='R', kind='n',  t=0.25, text='내년 외식업, 뭐가 뜰까?'),
    dict(side='L', kind='n',  t=1.75, text='2027 트렌드 4가지,\n바로 정리해 줄게요!')]),
 dict(id='value',  t0=4.95,  t1=10.00, tag='TREND 01 / 04', voice=1, msgs=[
    dict(side='L', kind='kw', t=0.10, text='첫째, 가치소비'),
    dict(side='L', kind='n',  t=1.45, text='납득되는 가격이\n선택받아요')]),
 dict(id='ai',     t0=10.00, t1=14.80, tag='TREND 02 / 04', voice=2, msgs=[
    dict(side='L', kind='kw', t=0.10, text='둘째, AI 운영'),
    dict(side='L', kind='n',  t=1.45, text='비용은 줄고\n효율은 오릅니다')]),
 dict(id='exp',    t0=14.80, t1=19.60, tag='TREND 03 / 04', voice=3, msgs=[
    dict(side='L', kind='kw', t=0.10, text='셋째, 경험 소비'),
    dict(side='L', kind='n',  t=1.45, text='기억에 남는 한 끼가\n이깁니다')]),
 dict(id='health', t0=19.60, t1=24.30, tag='TREND 04 / 04', voice=4, msgs=[
    dict(side='L', kind='kw', t=0.10, text='넷째, 건강한 한 끼'),
    dict(side='L', kind='n',  t=1.45, text='맛과 건강,\n둘 다 잡으세요')]),
 dict(id='outro',  t0=24.30, t1=30.00, tag='SO, WHAT NOW?', voice=5, msgs=[
    dict(side='R', kind='n',  t=0.15, text='그래서 우린 뭘 해야 해?'),
    dict(side='L', kind='n',  t=0.95, text='트렌드는\n매출로 증명됩니다'),
    dict(side='L', kind='kw', t=2.85, text='우리 매장 데이터부터\n점검하세요')]),
]
VOICE_OFFSET = 0.08
DOTS = 0.5   # L 메시지 타이핑 점 표시 시간

def show_time(sc, m):
    return sc['t0'] + m['t'] + (DOTS if m['side'] == 'L' else 0.0)
