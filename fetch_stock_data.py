"""
투자 게임용 주가 데이터 수집 스크립트 v2
- 종목 확대 (코스피 주요 30개 + 미국 10개)
- 의미 있는 게임 구간 자동 감지 (모멘텀 전환, 가짜 신호, 골든/데드크로스 등)
- 섹터 힌트 제거 (완전 블라인드)
실행: python fetch_stock_data.py
"""

import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

# ── 종목 목록 ──────────────────────────────────────────────────
STOCKS = [
    # 코스피 대형주
    {"ticker": "005930.KS", "name": "삼성전자"},
    {"ticker": "000660.KS", "name": "SK하이닉스"},
    {"ticker": "005380.KS", "name": "현대차"},
    {"ticker": "000270.KS", "name": "기아"},
    {"ticker": "068270.KS", "name": "셀트리온"},
    {"ticker": "035420.KS", "name": "NAVER"},
    {"ticker": "035720.KS", "name": "카카오"},
    {"ticker": "051910.KS", "name": "LG화학"},
    {"ticker": "006400.KS", "name": "삼성SDI"},
    {"ticker": "003550.KS", "name": "LG"},
    {"ticker": "055550.KS", "name": "신한지주"},
    {"ticker": "105560.KS", "name": "KB금융"},
    {"ticker": "012330.KS", "name": "현대모비스"},
    {"ticker": "028260.KS", "name": "삼성물산"},
    {"ticker": "066570.KS", "name": "LG전자"},
    {"ticker": "034730.KS", "name": "SK"},
    {"ticker": "017670.KS", "name": "SK텔레콤"},
    {"ticker": "030200.KS", "name": "KT"},
    {"ticker": "096770.KS", "name": "SK이노베이션"},
    {"ticker": "003490.KS", "name": "대한항공"},
    {"ticker": "011200.KS", "name": "HMM"},
    {"ticker": "086790.KS", "name": "하나금융지주"},
    {"ticker": "000810.KS", "name": "삼성화재"},
    {"ticker": "032830.KS", "name": "삼성생명"},
    {"ticker": "018260.KS", "name": "삼성에스디에스"},
    # 미국 주요주
    {"ticker": "AAPL",  "name": "Apple"},
    {"ticker": "NVDA",  "name": "NVIDIA"},
    {"ticker": "MSFT",  "name": "Microsoft"},
    {"ticker": "TSLA",  "name": "Tesla"},
    {"ticker": "AMZN",  "name": "Amazon"},
    {"ticker": "META",  "name": "Meta"},
    {"ticker": "GOOGL", "name": "Alphabet"},
    {"ticker": "JPM",   "name": "JPMorgan"},
    {"ticker": "XOM",   "name": "ExxonMobil"},
    {"ticker": "AMD",   "name": "AMD"},
]

PERIOD     = "5y"
OUTPUT_DIR = "stock_data"
MIN_CANDLES_FOR_SIGNAL = 60  # 구간 감지에 필요한 최소 캔들 수

# ── 지표 계산 ──────────────────────────────────────────────────

def calc_ma(closes, period):
    result = []
    for i in range(len(closes)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(round(sum(closes[i-period+1:i+1]) / period, 2))
    return result

def calc_rsi(closes, period=14):
    result = [None] * period
    for i in range(period, len(closes)):
        gains = losses = 0
        for j in range(i - period + 1, i + 1):
            diff = closes[j] - closes[j-1]
            if diff > 0: gains += diff
            else: losses += abs(diff)
        avg_g = gains / period
        avg_l = losses / period
        if avg_l == 0:
            result.append(100.0)
        else:
            result.append(round(100 - (100 / (1 + avg_g/avg_l)), 2))
    return result

def calc_ema(values, period):
    k = 2 / (period + 1)
    result = []
    prev = None
    for v in values:
        if v is None:
            result.append(None)
            continue
        prev = v if prev is None else v * k + prev * (1 - k)
        result.append(round(prev, 2))
    return result

def calc_macd(closes):
    e12   = calc_ema(closes, 12)
    e26   = calc_ema(closes, 26)
    macd  = [round(a-b, 2) if a and b else None for a, b in zip(e12, e26)]
    sig   = calc_ema(macd, 9)
    hist  = [round(m-s, 2) if m is not None and s is not None else None for m, s in zip(macd, sig)]
    return macd, sig, hist

# ── 의미 있는 게임 구간 감지 ──────────────────────────────────

def detect_game_points(candles):
    """
    게임에서 플레이어가 판단해야 할 '의미 있는 순간' 인덱스를 반환.
    각 포인트는 그 직전 구간(context_before일)을 보여주고 선택하게 함.

    감지 유형:
    - golden_cross  : MA5가 MA20을 상향 돌파 직전
    - dead_cross    : MA5가 MA20을 하향 돌파 직전
    - fake_breakout : 거래량 없는 신고가 돌파 (가짜 신호)
    - rsi_overbought: RSI 70 이상 진입 직후
    - rsi_oversold  : RSI 30 이하 진입 직후
    - momentum_shift: MACD 히스토그램이 방향 전환
    - volume_surge  : 거래량 급증 + 가격 하락 (기관 매도)
    """
    points = []
    n = len(candles)

    closes = [c["c"] for c in candles]
    vols   = [c["v"] for c in candles]
    ma5    = [c.get("ma5")  for c in candles]
    ma20   = [c.get("ma20") for c in candles]
    rsi    = [c.get("rsi")  for c in candles]
    hist   = [c.get("hist") for c in candles]

    avg_vol = sum(v for v in vols if v) / len(vols)

    for i in range(MIN_CANDLES_FOR_SIGNAL, n - 20):
        # 1. 골든크로스 직전
        if (ma5[i-1] and ma20[i-1] and ma5[i] and ma20[i]):
            if ma5[i-1] < ma20[i-1] and ma5[i] >= ma20[i]:
                points.append({"index": i, "type": "golden_cross", "label": "골든크로스"})

        # 2. 데드크로스 직전
            if ma5[i-1] > ma20[i-1] and ma5[i] <= ma20[i]:
                points.append({"index": i, "type": "dead_cross", "label": "데드크로스"})

        # 3. 가짜 돌파 — 신고가인데 거래량이 평균 이하
        if i >= 20:
            recent_high = max(c["h"] for c in candles[i-20:i])
            if candles[i]["h"] > recent_high and vols[i] < avg_vol * 0.7:
                points.append({"index": i, "type": "fake_breakout", "label": "가짜돌파"})

        # 4. RSI 과매수 진입
        if rsi[i-1] and rsi[i]:
            if rsi[i-1] < 70 <= rsi[i]:
                points.append({"index": i, "type": "rsi_overbought", "label": "RSI과매수"})
            # 5. RSI 과매도 진입
            if rsi[i-1] > 30 >= rsi[i]:
                points.append({"index": i, "type": "rsi_oversold", "label": "RSI과매도"})

        # 6. MACD 모멘텀 전환
        if hist[i-1] is not None and hist[i] is not None:
            if hist[i-1] < 0 and hist[i] >= 0:
                points.append({"index": i, "type": "momentum_shift_up", "label": "모멘텀상승전환"})
            if hist[i-1] > 0 and hist[i] <= 0:
                points.append({"index": i, "type": "momentum_shift_down", "label": "모멘텀하락전환"})

        # 7. 거래량 급증 + 가격 하락 (기관 매도 신호)
        if vols[i] > avg_vol * 2.5 and closes[i] < closes[i-1] * 0.98:
            points.append({"index": i, "type": "volume_surge_down", "label": "거래량급증하락"})

    # 너무 가까운 포인트 제거 (최소 30일 간격)
    filtered = []
    last_idx = -999
    for p in sorted(points, key=lambda x: x["index"]):
        if p["index"] - last_idx >= 30:
            filtered.append(p)
            last_idx = p["index"]

    return filtered


# ── 데이터 수집 & 처리 ────────────────────────────────────────

def fetch_and_process(stock_info):
    ticker = stock_info["ticker"]
    print(f"  수집 중: {stock_info['name']} ({ticker})")

    df = yf.download(ticker, period=PERIOD, interval="1d", progress=False, auto_adjust=True)
    if df.empty:
        print(f"  !! 데이터 없음: {ticker}")
        return None

    df = df.dropna()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    dates  = df.index.strftime("%Y-%m-%d").tolist()
    opens  = [round(float(v), 2) for v in df["Open"].values]
    highs  = [round(float(v), 2) for v in df["High"].values]
    lows   = [round(float(v), 2) for v in df["Low"].values]
    closes = [round(float(v), 2) for v in df["Close"].values]
    vols   = [int(v) for v in df["Volume"].values]

    ma5   = calc_ma(closes, 5)
    ma20  = calc_ma(closes, 20)
    ma60  = calc_ma(closes, 60)
    ma120 = calc_ma(closes, 120)
    rsi   = calc_rsi(closes, 14)
    macd, signal, histogram = calc_macd(closes)

    candles = []
    for i in range(len(dates)):
        candles.append({
            "date":   dates[i],
            "o":      opens[i],
            "h":      highs[i],
            "l":      lows[i],
            "c":      closes[i],
            "v":      vols[i],
            "ma5":    ma5[i],
            "ma20":   ma20[i],
            "ma60":   ma60[i],
            "ma120":  ma120[i],
            "rsi":    rsi[i],
            "macd":   macd[i],
            "signal": signal[i],
            "hist":   histogram[i],
        })

    # 게임 포인트 감지
    game_points = detect_game_points(candles)
    print(f"    → {len(candles)}일치 / 게임포인트 {len(game_points)}개 감지")

    return {
        "ticker":      ticker,
        "name":        stock_info["name"],
        "currency":    "KRW" if ticker.endswith(".KS") else "USD",
        "total":       len(candles),
        "updated":     datetime.now().strftime("%Y-%m-%d"),
        "game_points": game_points,
        "candles":     candles,
    }


# ── 실행 ─────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    index = []
    success = 0
    fail = 0

    for stock in STOCKS:
        data = fetch_and_process(stock)
        if data is None:
            fail += 1
            continue

        filename = stock["ticker"].replace(".", "_") + ".json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

        index.append({
            "ticker":       stock["ticker"],
            "name":         stock["name"],
            "file":         filename,
            "total":        data["total"],
            "currency":     data["currency"],
            "game_points":  len(data["game_points"]),
        })
        success += 1

    index_path = os.path.join(OUTPUT_DIR, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n완료! 성공 {success}개 / 실패 {fail}개 → {OUTPUT_DIR}/")
    print(f"인덱스: {index_path}")

if __name__ == "__main__":
    main()
