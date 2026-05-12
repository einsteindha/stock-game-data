"""
투자 게임용 주가 데이터 수집 스크립트 v4
- 종목별 난이도 태그 (easy/normal/hard)
- 게임 포인트에 난이도 태그 포함
실행: python fetch_stock_data.py
"""

import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

# ── 종목 목록 (difficulty: easy/normal/hard) ──────────────────
KOSPI_STOCKS = [
    # 쉬움 — 대형 우량주 (변동성 낮음)
    {"ticker":"005930.KS","name":"삼성전자","difficulty":"easy"},
    {"ticker":"005380.KS","name":"현대차","difficulty":"easy"},
    {"ticker":"000270.KS","name":"기아","difficulty":"easy"},
    {"ticker":"055550.KS","name":"신한지주","difficulty":"easy"},
    {"ticker":"105560.KS","name":"KB금융","difficulty":"easy"},
    {"ticker":"086790.KS","name":"하나금융지주","difficulty":"easy"},
    {"ticker":"316140.KS","name":"우리금융지주","difficulty":"easy"},
    {"ticker":"000810.KS","name":"삼성화재","difficulty":"easy"},
    {"ticker":"032830.KS","name":"삼성생명","difficulty":"easy"},
    {"ticker":"012330.KS","name":"현대모비스","difficulty":"easy"},
    {"ticker":"028260.KS","name":"삼성물산","difficulty":"easy"},
    {"ticker":"034730.KS","name":"SK","difficulty":"easy"},
    {"ticker":"017670.KS","name":"SK텔레콤","difficulty":"easy"},
    {"ticker":"030200.KS","name":"KT","difficulty":"easy"},
    {"ticker":"066570.KS","name":"LG전자","difficulty":"easy"},
    {"ticker":"003550.KS","name":"LG","difficulty":"easy"},
    {"ticker":"097950.KS","name":"CJ제일제당","difficulty":"easy"},
    {"ticker":"004370.KS","name":"농심","difficulty":"easy"},
    {"ticker":"271560.KS","name":"오리온","difficulty":"easy"},
    {"ticker":"139480.KS","name":"이마트","difficulty":"easy"},
    # 보통 — 중형주 + 성장주
    {"ticker":"000660.KS","name":"SK하이닉스","difficulty":"normal"},
    {"ticker":"035420.KS","name":"NAVER","difficulty":"normal"},
    {"ticker":"035720.KS","name":"카카오","difficulty":"normal"},
    {"ticker":"051910.KS","name":"LG화학","difficulty":"normal"},
    {"ticker":"006400.KS","name":"삼성SDI","difficulty":"normal"},
    {"ticker":"096770.KS","name":"SK이노베이션","difficulty":"normal"},
    {"ticker":"005490.KS","name":"POSCO홀딩스","difficulty":"normal"},
    {"ticker":"068270.KS","name":"셀트리온","difficulty":"normal"},
    {"ticker":"207940.KS","name":"삼성바이오로직스","difficulty":"normal"},
    {"ticker":"128940.KS","name":"한미약품","difficulty":"normal"},
    {"ticker":"018260.KS","name":"삼성에스디에스","difficulty":"normal"},
    {"ticker":"352820.KS","name":"하이브","difficulty":"normal"},
    {"ticker":"041510.KS","name":"에스엠","difficulty":"normal"},
    {"ticker":"003490.KS","name":"대한항공","difficulty":"normal"},
    {"ticker":"011200.KS","name":"HMM","difficulty":"normal"},
    {"ticker":"012450.KS","name":"한화에어로스페이스","difficulty":"normal"},
    {"ticker":"329180.KS","name":"현대중공업","difficulty":"normal"},
    {"ticker":"259960.KS","name":"크래프톤","difficulty":"normal"},
    {"ticker":"373220.KS","name":"LG에너지솔루션","difficulty":"normal"},
    {"ticker":"003670.KS","name":"포스코퓨처엠","difficulty":"normal"},
    # 어려움 — 고변동성
    {"ticker":"247540.KS","name":"에코프로비엠","difficulty":"hard"},
    {"ticker":"086520.KS","name":"에코프로","difficulty":"hard"},
    {"ticker":"326030.KS","name":"SK바이오팜","difficulty":"hard"},
    {"ticker":"145020.KS","name":"휴젤","difficulty":"hard"},
    {"ticker":"035900.KS","name":"JYP엔터테인먼트","difficulty":"hard"},
    {"ticker":"122870.KS","name":"와이지엔터테인먼트","difficulty":"hard"},
    {"ticker":"042660.KS","name":"한화오션","difficulty":"hard"},
    {"ticker":"010140.KS","name":"삼성중공업","difficulty":"hard"},
    {"ticker":"047040.KS","name":"대우건설","difficulty":"hard"},
    {"ticker":"011170.KS","name":"롯데케미칼","difficulty":"hard"},
]

US_STOCKS = [
    # 쉬움
    {"ticker":"SPY","name":"S&P500 ETF","difficulty":"easy"},
    {"ticker":"QQQ","name":"나스닥100 ETF","difficulty":"easy"},
    {"ticker":"IWM","name":"러셀2000 ETF","difficulty":"easy"},
    {"ticker":"JPM","name":"JPMorgan","difficulty":"easy"},
    {"ticker":"BAC","name":"Bank of America","difficulty":"easy"},
    {"ticker":"JNJ","name":"Johnson & Johnson","difficulty":"easy"},
    {"ticker":"WMT","name":"Walmart","difficulty":"easy"},
    {"ticker":"COST","name":"Costco","difficulty":"easy"},
    {"ticker":"V","name":"Visa","difficulty":"easy"},
    {"ticker":"MA","name":"Mastercard","difficulty":"easy"},
    {"ticker":"XOM","name":"ExxonMobil","difficulty":"easy"},
    {"ticker":"CVX","name":"Chevron","difficulty":"easy"},
    # 보통
    {"ticker":"AAPL","name":"Apple","difficulty":"normal"},
    {"ticker":"MSFT","name":"Microsoft","difficulty":"normal"},
    {"ticker":"GOOGL","name":"Alphabet","difficulty":"normal"},
    {"ticker":"AMZN","name":"Amazon","difficulty":"normal"},
    {"ticker":"META","name":"Meta","difficulty":"normal"},
    {"ticker":"NVDA","name":"NVIDIA","difficulty":"normal"},
    {"ticker":"INTC","name":"Intel","difficulty":"normal"},
    {"ticker":"QCOM","name":"Qualcomm","difficulty":"normal"},
    {"ticker":"MCD","name":"McDonald's","difficulty":"normal"},
    {"ticker":"SBUX","name":"Starbucks","difficulty":"normal"},
    {"ticker":"NKE","name":"Nike","difficulty":"normal"},
    {"ticker":"DIS","name":"Disney","difficulty":"normal"},
    {"ticker":"NFLX","name":"Netflix","difficulty":"normal"},
    {"ticker":"GS","name":"Goldman Sachs","difficulty":"normal"},
    {"ticker":"MS","name":"Morgan Stanley","difficulty":"normal"},
    {"ticker":"UNH","name":"UnitedHealth","difficulty":"normal"},
    {"ticker":"PFE","name":"Pfizer","difficulty":"normal"},
    {"ticker":"BA","name":"Boeing","difficulty":"normal"},
    {"ticker":"COP","name":"ConocoPhillips","difficulty":"normal"},
    # 어려움
    {"ticker":"TSLA","name":"Tesla","difficulty":"hard"},
    {"ticker":"AMD","name":"AMD","difficulty":"hard"},
    {"ticker":"RIVN","name":"Rivian","difficulty":"hard"},
    {"ticker":"LCID","name":"Lucid","difficulty":"hard"},
    {"ticker":"PLTR","name":"Palantir","difficulty":"hard"},
    {"ticker":"CRM","name":"Salesforce","difficulty":"hard"},
    {"ticker":"NOW","name":"ServiceNow","difficulty":"hard"},
    {"ticker":"MRK","name":"Merck","difficulty":"hard"},
    {"ticker":"ABBV","name":"AbbVie","difficulty":"hard"},
    {"ticker":"UAL","name":"United Airlines","difficulty":"hard"},
    {"ticker":"T","name":"AT&T","difficulty":"hard"},
]

ALL_STOCKS = KOSPI_STOCKS + US_STOCKS
PERIOD = "5y"
OUTPUT_DIR = "stock_data"
MIN_CANDLES = 60
MIN_GAME_POINTS = 5

# 난이도별 허용 포인트 유형
DIFFICULTY_POINTS = {
    "easy":   ["golden_cross","dead_cross"],
    "normal": ["golden_cross","dead_cross","rsi_overbought","rsi_oversold","momentum_up","momentum_down"],
    "hard":   ["fake_breakout","volume_surge_down","momentum_up","momentum_down","rsi_overbought","rsi_oversold"],
}

# ── 지표 계산 ──────────────────────────────────────────────────
def calc_ma(closes, period):
    return [None if i<period-1 else round(sum(closes[i-period+1:i+1])/period,2) for i in range(len(closes))]

def calc_rsi(closes, period=14):
    result = [None]*period
    for i in range(period, len(closes)):
        gains = losses = 0
        for j in range(i-period+1, i+1):
            d = closes[j]-closes[j-1]
            if d>0: gains+=d
            else: losses+=abs(d)
        ag,al = gains/period, losses/period
        result.append(100.0 if al==0 else round(100-(100/(1+ag/al)),2))
    return result

def calc_ema(values, period):
    k = 2/(period+1)
    result, prev = [], None
    for v in values:
        if v is None: result.append(None); continue
        prev = v if prev is None else v*k+prev*(1-k)
        result.append(round(prev,2))
    return result

def calc_macd(closes):
    e12,e26 = calc_ema(closes,12), calc_ema(closes,26)
    macd = [round(a-b,2) if a and b else None for a,b in zip(e12,e26)]
    sig  = calc_ema(macd,9)
    hist = [round(m-s,2) if m is not None and s is not None else None for m,s in zip(macd,sig)]
    return macd, sig, hist

# ── 게임 포인트 감지 ──────────────────────────────────────────
def detect_game_points(candles):
    points = []
    n = len(candles)
    closes = [c["c"] for c in candles]
    vols   = [c["v"] for c in candles]
    ma5    = [c.get("ma5")  for c in candles]
    ma20   = [c.get("ma20") for c in candles]
    rsi    = [c.get("rsi")  for c in candles]
    hist   = [c.get("hist") for c in candles]
    avg_vol = sum(v for v in vols if v) / len(vols)

    for i in range(MIN_CANDLES, n-20):
        if ma5[i-1] and ma20[i-1] and ma5[i] and ma20[i]:
            if ma5[i-1] < ma20[i-1] and ma5[i] >= ma20[i]:
                points.append({"index":i,"type":"golden_cross","label":"골든크로스"})
            if ma5[i-1] > ma20[i-1] and ma5[i] <= ma20[i]:
                points.append({"index":i,"type":"dead_cross","label":"데드크로스"})
        if i>=20:
            recent_high = max(c["h"] for c in candles[i-20:i])
            if candles[i]["h"] > recent_high and vols[i] < avg_vol*0.7:
                points.append({"index":i,"type":"fake_breakout","label":"가짜돌파"})
        if rsi[i-1] and rsi[i]:
            if rsi[i-1] < 70 <= rsi[i]:
                points.append({"index":i,"type":"rsi_overbought","label":"RSI과매수"})
            if rsi[i-1] > 30 >= rsi[i]:
                points.append({"index":i,"type":"rsi_oversold","label":"RSI과매도"})
        if hist[i-1] is not None and hist[i] is not None:
            if hist[i-1] < 0 and hist[i] >= 0:
                points.append({"index":i,"type":"momentum_up","label":"모멘텀상승"})
            if hist[i-1] > 0 and hist[i] <= 0:
                points.append({"index":i,"type":"momentum_down","label":"모멘텀하락"})
        if vols[i] > avg_vol*2.5 and closes[i] < closes[i-1]*0.98:
            points.append({"index":i,"type":"volume_surge_down","label":"거래량급증하락"})

    filtered, last_idx = [], -999
    for p in sorted(points, key=lambda x: x["index"]):
        if p["index"]-last_idx >= 30:
            filtered.append(p)
            last_idx = p["index"]
    return filtered

# ── 수집 & 처리 ───────────────────────────────────────────────
def fetch_and_process(stock_info):
    ticker = stock_info["ticker"]
    difficulty = stock_info.get("difficulty","normal")
    print(f"  [{difficulty}] {stock_info['name']} ({ticker})", end="", flush=True)
    try:
        df = yf.download(ticker, period=PERIOD, interval="1d", progress=False, auto_adjust=True)
        if df.empty: print(" → 데이터 없음"); return None
        df = df.dropna()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        dates  = df.index.strftime("%Y-%m-%d").tolist()
        opens  = [round(float(v),2) for v in df["Open"].values]
        highs  = [round(float(v),2) for v in df["High"].values]
        lows   = [round(float(v),2) for v in df["Low"].values]
        closes = [round(float(v),2) for v in df["Close"].values]
        vols   = [int(v) for v in df["Volume"].values]

        ma5   = calc_ma(closes,5)
        ma20  = calc_ma(closes,20)
        ma60  = calc_ma(closes,60)
        ma120 = calc_ma(closes,120)
        rsi   = calc_rsi(closes,14)
        macd, signal, histogram = calc_macd(closes)

        candles = [{"date":dates[i],"o":opens[i],"h":highs[i],"l":lows[i],"c":closes[i],"v":vols[i],
                    "ma5":ma5[i],"ma20":ma20[i],"ma60":ma60[i],"ma120":ma120[i],
                    "rsi":rsi[i],"macd":macd[i],"signal":signal[i],"hist":histogram[i]}
                   for i in range(len(dates))]

        all_points = detect_game_points(candles)

        # 난이도별 포인트 필터링
        allowed = DIFFICULTY_POINTS.get(difficulty, DIFFICULTY_POINTS["normal"])
        filtered_points = [p for p in all_points if p["type"] in allowed]

        print(f" → {len(candles)}일치 / 전체포인트 {len(all_points)}개 / {difficulty}포인트 {len(filtered_points)}개")

        if len(filtered_points) < MIN_GAME_POINTS:
            # 포인트 부족 시 전체 포인트로 보완
            filtered_points = all_points
            if len(filtered_points) < MIN_GAME_POINTS:
                print(f"    !! 포인트 부족 — 제외")
                return None

        return {
            "ticker":      ticker,
            "name":        stock_info["name"],
            "difficulty":  difficulty,
            "currency":    "KRW" if ticker.endswith(".KS") else "USD",
            "total":       len(candles),
            "updated":     datetime.now().strftime("%Y-%m-%d"),
            "game_points": filtered_points,
            "candles":     candles,
        }
    except Exception as e:
        print(f" → 오류: {e}")
        return None

# ── 실행 ─────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    index = []
    success = fail = 0

    for stock in ALL_STOCKS:
        data = fetch_and_process(stock)
        if data is None: fail+=1; continue

        filename = stock["ticker"].replace(".", "_") + ".json"
        with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",",":"))

        index.append({
            "ticker":      stock["ticker"],
            "name":        stock["name"],
            "difficulty":  data["difficulty"],
            "file":        filename,
            "total":       data["total"],
            "currency":    data["currency"],
            "game_points": len(data["game_points"]),
            "updated":     data["updated"],
        })
        success+=1

    with open(os.path.join(OUTPUT_DIR,"index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    easy   = sum(1 for s in index if s["difficulty"]=="easy")
    normal = sum(1 for s in index if s["difficulty"]=="normal")
    hard   = sum(1 for s in index if s["difficulty"]=="hard")
    print(f"\n완료! 총 {success}개 (쉬움:{easy} / 보통:{normal} / 어려움:{hard}) / 실패:{fail}개")

if __name__ == "__main__":
    main()
