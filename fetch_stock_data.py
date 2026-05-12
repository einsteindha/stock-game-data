"""
투자 게임용 주가 데이터 수집 스크립트 v3
- 코스피 주요 100개 + 미국 주요 50개
- 의미 있는 게임 포인트 자동 감지
- GitHub Actions 자동화 대응
실행: python fetch_stock_data.py
"""

import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

# ── 종목 목록 ──────────────────────────────────────────────────
KOSPI_STOCKS = [
    # 반도체/IT
    {"ticker":"005930.KS","name":"삼성전자"},
    {"ticker":"000660.KS","name":"SK하이닉스"},
    {"ticker":"066570.KS","name":"LG전자"},
    {"ticker":"018260.KS","name":"삼성에스디에스"},
    {"ticker":"034730.KS","name":"SK"},
    {"ticker":"017670.KS","name":"SK텔레콤"},
    {"ticker":"030200.KS","name":"KT"},
    {"ticker":"035420.KS","name":"NAVER"},
    {"ticker":"035720.KS","name":"카카오"},
    {"ticker":"259960.KS","name":"크래프톤"},
    # 자동차
    {"ticker":"005380.KS","name":"현대차"},
    {"ticker":"000270.KS","name":"기아"},
    {"ticker":"012330.KS","name":"현대모비스"},
    {"ticker":"011210.KS","name":"현대위아"},
    {"ticker":"204320.KS","name":"현대글로비스"},
    # 화학/소재
    {"ticker":"051910.KS","name":"LG화학"},
    {"ticker":"096770.KS","name":"SK이노베이션"},
    {"ticker":"011170.KS","name":"롯데케미칼"},
    {"ticker":"010950.KS","name":"S-Oil"},
    {"ticker":"004020.KS","name":"현대제철"},
    {"ticker":"005490.KS","name":"POSCO홀딩스"},
    {"ticker":"003670.KS","name":"포스코퓨처엠"},
    # 2차전지
    {"ticker":"006400.KS","name":"삼성SDI"},
    {"ticker":"373220.KS","name":"LG에너지솔루션"},
    {"ticker":"247540.KS","name":"에코프로비엠"},
    {"ticker":"086520.KS","name":"에코프로"},
    # 바이오/헬스
    {"ticker":"068270.KS","name":"셀트리온"},
    {"ticker":"207940.KS","name":"삼성바이오로직스"},
    {"ticker":"128940.KS","name":"한미약품"},
    {"ticker":"326030.KS","name":"SK바이오팜"},
    {"ticker":"145020.KS","name":"휴젤"},
    # 금융
    {"ticker":"055550.KS","name":"신한지주"},
    {"ticker":"105560.KS","name":"KB금융"},
    {"ticker":"086790.KS","name":"하나금융지주"},
    {"ticker":"139130.KS","name":"DGB금융지주"},
    {"ticker":"000810.KS","name":"삼성화재"},
    {"ticker":"032830.KS","name":"삼성생명"},
    {"ticker":"316140.KS","name":"우리금융지주"},
    # 건설/부동산
    {"ticker":"028260.KS","name":"삼성물산"},
    {"ticker":"000720.KS","name":"현대건설"},
    {"ticker":"047040.KS","name":"대우건설"},
    # 유통/소비
    {"ticker":"139480.KS","name":"이마트"},
    {"ticker":"023530.KS","name":"롯데쇼핑"},
    {"ticker":"004370.KS","name":"농심"},
    {"ticker":"097950.KS","name":"CJ제일제당"},
    {"ticker":"271560.KS","name":"오리온"},
    # 엔터/미디어
    {"ticker":"352820.KS","name":"하이브"},
    {"ticker":"041510.KS","name":"에스엠"},
    {"ticker":"035900.KS","name":"JYP엔터테인먼트"},
    {"ticker":"122870.KS","name":"와이지엔터테인먼트"},
    # 운송/물류
    {"ticker":"003490.KS","name":"대한항공"},
    {"ticker":"011200.KS","name":"HMM"},
    {"ticker":"000120.KS","name":"CJ대한통운"},
    # 방산/중공업
    {"ticker":"012450.KS","name":"한화에어로스페이스"},
    {"ticker":"329180.KS","name":"현대중공업"},
    {"ticker":"010140.KS","name":"삼성중공업"},
    {"ticker":"042660.KS","name":"한화오션"},
]

US_STOCKS = [
    # 빅테크
    {"ticker":"AAPL","name":"Apple"},
    {"ticker":"MSFT","name":"Microsoft"},
    {"ticker":"GOOGL","name":"Alphabet"},
    {"ticker":"AMZN","name":"Amazon"},
    {"ticker":"META","name":"Meta"},
    {"ticker":"NVDA","name":"NVIDIA"},
    {"ticker":"TSLA","name":"Tesla"},
    {"ticker":"AMD","name":"AMD"},
    {"ticker":"INTC","name":"Intel"},
    {"ticker":"QCOM","name":"Qualcomm"},
    # 금융
    {"ticker":"JPM","name":"JPMorgan"},
    {"ticker":"BAC","name":"Bank of America"},
    {"ticker":"GS","name":"Goldman Sachs"},
    {"ticker":"MS","name":"Morgan Stanley"},
    {"ticker":"V","name":"Visa"},
    {"ticker":"MA","name":"Mastercard"},
    # 헬스케어
    {"ticker":"JNJ","name":"Johnson & Johnson"},
    {"ticker":"PFE","name":"Pfizer"},
    {"ticker":"MRK","name":"Merck"},
    {"ticker":"ABBV","name":"AbbVie"},
    {"ticker":"UNH","name":"UnitedHealth"},
    # 에너지
    {"ticker":"XOM","name":"ExxonMobil"},
    {"ticker":"CVX","name":"Chevron"},
    {"ticker":"COP","name":"ConocoPhillips"},
    # 소비재
    {"ticker":"WMT","name":"Walmart"},
    {"ticker":"COST","name":"Costco"},
    {"ticker":"MCD","name":"McDonald's"},
    {"ticker":"SBUX","name":"Starbucks"},
    {"ticker":"NKE","name":"Nike"},
    # 통신/미디어
    {"ticker":"NFLX","name":"Netflix"},
    {"ticker":"DIS","name":"Disney"},
    {"ticker":"T","name":"AT&T"},
    # 항공/운송
    {"ticker":"BA","name":"Boeing"},
    {"ticker":"UAL","name":"United Airlines"},
    # 전기차/배터리
    {"ticker":"RIVN","name":"Rivian"},
    {"ticker":"LCID","name":"Lucid"},
    # AI/클라우드
    {"ticker":"CRM","name":"Salesforce"},
    {"ticker":"NOW","name":"ServiceNow"},
    {"ticker":"PLTR","name":"Palantir"},
    # ETF (지수 흐름 파악용)
    {"ticker":"SPY","name":"S&P500 ETF"},
    {"ticker":"QQQ","name":"나스닥100 ETF"},
    {"ticker":"IWM","name":"러셀2000 ETF"},
]

ALL_STOCKS = KOSPI_STOCKS + US_STOCKS
PERIOD = "5y"
OUTPUT_DIR = "stock_data"
MIN_CANDLES = 60
MIN_GAME_POINTS = 5  # 게임 포인트 최소 개수

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
    ma5    = [c.get("ma5")   for c in candles]
    ma20   = [c.get("ma20")  for c in candles]
    rsi    = [c.get("rsi")   for c in candles]
    hist   = [c.get("hist")  for c in candles]
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

    # 최소 30일 간격 필터링
    filtered, last_idx = [], -999
    for p in sorted(points, key=lambda x: x["index"]):
        if p["index"]-last_idx >= 30:
            filtered.append(p)
            last_idx = p["index"]
    return filtered

# ── 수집 & 처리 ───────────────────────────────────────────────
def fetch_and_process(stock_info):
    ticker = stock_info["ticker"]
    print(f"  수집 중: {stock_info['name']} ({ticker})", end="", flush=True)
    try:
        df = yf.download(ticker, period=PERIOD, interval="1d", progress=False, auto_adjust=True)
        if df.empty:
            print(" → 데이터 없음")
            return None
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

        game_points = detect_game_points(candles)
        print(f" → {len(candles)}일치 / 포인트 {len(game_points)}개")

        if len(game_points) < MIN_GAME_POINTS:
            print(f"    !! 포인트 부족 ({len(game_points)}개) — 제외")
            return None

        return {
            "ticker":      ticker,
            "name":        stock_info["name"],
            "currency":    "KRW" if ticker.endswith(".KS") else "USD",
            "total":       len(candles),
            "updated":     datetime.now().strftime("%Y-%m-%d"),
            "game_points": game_points,
            "candles":     candles,
        }
    except Exception as e:
        print(f" → 오류: {e}")
        return None

# ── 실행 ─────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    index = []
    success = fail = skipped = 0

    for stock in ALL_STOCKS:
        data = fetch_and_process(stock)
        if data is None:
            fail += 1
            continue

        filename = stock["ticker"].replace(".", "_") + ".json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",",":"))

        index.append({
            "ticker":      stock["ticker"],
            "name":        stock["name"],
            "file":        filename,
            "total":       data["total"],
            "currency":    data["currency"],
            "game_points": len(data["game_points"]),
            "updated":     data["updated"],
        })
        success += 1

    index_path = os.path.join(OUTPUT_DIR, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n완료! 성공 {success}개 / 실패·제외 {fail}개")
    print(f"총 종목: {success}개 → {OUTPUT_DIR}/index.json")

if __name__ == "__main__":
    main()
