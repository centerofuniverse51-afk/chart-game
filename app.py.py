import json
import os
import random
import socket
import subprocess
import sys
import threading
import traceback
import webbrowser
from datetime import datetime

# 1. 필수 라이브러리 자동 설치
for pkg, import_name in [
    ("finance-datareader", "FinanceDataReader"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("flask", "flask"),
]:
    try:
        __import__(import_name)
    except ImportError:
        print(f"📦 필수 부품({pkg}) 자동 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])

import FinanceDataReader as fdr
import numpy as np
import pandas as pd
from flask import Flask, Response, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
HISTORY_JSON = os.path.join(BASE_DIR, "chart_game_history.json")
HISTORY_CSV = os.path.join(BASE_DIR, "chart_game_stats.csv")


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# 2. 초기 즉시 실행용 핵심 종목 풀 (시총 1천억 이상 & 거래대금 500억 이상 빈발 종목)
INITIAL_POOL = [
    {"Code": "005930", "Name": "삼성전자", "Market": "KOSPI", "Marcap": 400000000000000},
    {"Code": "000660", "Name": "SK하이닉스", "Market": "KOSPI", "Marcap": 140000000000000},
    {"Code": "373220", "Name": "LG에너지솔루션", "Market": "KOSPI", "Marcap": 90000000000000},
    {"Code": "207940", "Name": "삼성바이오로직스", "Market": "KOSPI", "Marcap": 65000000000000},
    {"Code": "005380", "Name": "현대차", "Market": "KOSPI", "Marcap": 50000000000000},
    {"Code": "000270", "Name": "기아", "Market": "KOSPI", "Marcap": 40000000000000},
    {"Code": "068270", "Name": "셀트리온", "Market": "KOSPI", "Marcap": 38000000000000},
    {"Code": "005490", "Name": "POSCO홀딩스", "Market": "KOSPI", "Marcap": 30000000000000},
    {"Code": "035420", "Name": "NAVER", "Market": "KOSPI", "Marcap": 28000000000000},
    {"Code": "035720", "Name": "카카오", "Market": "KOSPI", "Marcap": 18000000000000},
    {"Code": "051910", "Name": "LG화학", "Market": "KOSPI", "Marcap": 24000000000000},
    {"Code": "006400", "Name": "삼성SDI", "Market": "KOSPI", "Marcap": 25000000000000},
    {"Code": "105560", "Name": "KB금융", "Market": "KOSPI", "Marcap": 32000000000000},
    {"Code": "055550", "Name": "신한지주", "Market": "KOSPI", "Marcap": 26000000000000},
    {"Code": "012450", "Name": "한화에어로스페이스", "Market": "KOSPI", "Marcap": 16000000000000},
    {"Code": "042700", "Name": "한미반도체", "Market": "KOSPI", "Marcap": 12000000000000},
    {"Code": "003670", "Name": "포스코퓨처엠", "Market": "KOSPI", "Marcap": 18000000000000},
    {"Code": "034020", "Name": "두산에너빌리티", "Market": "KOSPI", "Marcap": 13000000000000},
    {"Code": "259960", "Name": "크래프톤", "Market": "KOSPI", "Marcap": 15000000000000},
    {"Code": "009540", "Name": "HD한국조선해양", "Market": "KOSPI", "Marcap": 13000000000000},
    {"Code": "267260", "Name": "HD현대일렉트릭", "Market": "KOSPI", "Marcap": 11000000000000},
    {"Code": "247540", "Name": "에코프로비엠", "Market": "KOSDAQ", "Marcap": 17000000000000},
    {"Code": "086520", "Name": "에코프로", "Market": "KOSDAQ", "Marcap": 12000000000000},
    {"Code": "196170", "Name": "알테오젠", "Market": "KOSDAQ", "Marcap": 16000000000000},
    {"Code": "028300", "Name": "HLB", "Market": "KOSDAQ", "Marcap": 10000000000000},
    {"Code": "066970", "Name": "엘앤에프", "Market": "KOSPI", "Marcap": 4000000000000},
    {"Code": "000100", "Name": "유한양행", "Market": "KOSPI", "Marcap": 9000000000000},
    {"Code": "278470", "Name": "에이피알", "Market": "KOSPI", "Marcap": 2200000000000},
    {"Code": "058470", "Name": "리노공업", "Market": "KOSDAQ", "Marcap": 3100000000000},
    {"Code": "214150", "Name": "클래시스", "Market": "KOSDAQ", "Marcap": 3300000000000},
    {"Code": "145020", "Name": "휴젤", "Market": "KOSDAQ", "Marcap": 3200000000000},
    {"Code": "039030", "Name": "이오테크닉스", "Market": "KOSDAQ", "Marcap": 2100000000000},
    {"Code": "403870", "Name": "HPSP", "Market": "KOSDAQ", "Marcap": 2500000000000},
    {"Code": "010120", "Name": "LS ELECTRIC", "Market": "KOSPI", "Marcap": 5500000000000},
    {"Code": "047810", "Name": "한국항공우주", "Market": "KOSPI", "Marcap": 5400000000000},
    {"Code": "064350", "Name": "현대로템", "Market": "KOSPI", "Marcap": 6200000000000},
    {"Code": "079550", "Name": "LIG넥스원", "Market": "KOSPI", "Marcap": 4800000000000},
    {"Code": "329180", "Name": "HD현대중공업", "Market": "KOSPI", "Marcap": 15000000000000},
    {"Code": "042660", "Name": "한화오션", "Market": "KOSPI", "Marcap": 9800000000000},
    {"Code": "010140", "Name": "삼성중공업", "Market": "KOSPI", "Marcap": 9200000000000},
    {"Code": "352820", "Name": "하이브", "Market": "KOSPI", "Marcap": 8200000000000},
    {"Code": "009150", "Name": "삼성전기", "Market": "KOSPI", "Marcap": 10500000000000},
    {"Code": "066570", "Name": "LG전자", "Market": "KOSPI", "Marcap": 16500000000000},
    {"Code": "011200", "Name": "HMM", "Market": "KOSPI", "Marcap": 13000000000000},
]

STOCK_POOL = list(INITIAL_POOL)
DF_CACHE = {}


def load_full_krx_in_background():
    global STOCK_POOL
    try:
        df_krx = fdr.StockListing("KRX")
        cond = (
            df_krx["Market"].isin(["KOSPI", "KOSDAQ"])
            & (df_krx["Marcap"] >= 100_000_000_000)
            & (~df_krx["Name"].str.contains("스팩|리츠|우$|우B$|우C$", regex=True))
        )
        sub = df_krx[cond].copy()
        if "Amount" in sub.columns:
            sub = sub.sort_values("Amount", ascending=False)
        records = sub[["Code", "Name", "Market", "Marcap"]].to_dict("records")
        if len(records) >= 50:
            STOCK_POOL = records
            print(f"✅ [백그라운드 완료] 시총 1,000억 이상 전 종목({len(STOCK_POOL):,}개) 연동 완료!")
    except Exception:
        pass


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50)


def safe_float(val, default=None):
    if val is None or pd.isna(val) or np.isnan(val) or np.isinf(val):
        return default
    return float(val)


def fetch_stock_df(code):
    if code in DF_CACHE:
        return DF_CACHE[code]
    df = fdr.DataReader(code, "2019-01-01")
    if df is None or len(df) < 420:
        return None
    df = df[df["Volume"] > 0].dropna(subset=["Open", "High", "Low", "Close", "Volume"]).copy()
    if len(df) < 420:
        return None
    df["Amount"] = df["Close"].astype(float) * df["Volume"].astype(float)
    df["MA5"] = df["Close"].rolling(5).mean().round(0)
    df["MA20"] = df["Close"].rolling(20).mean().round(0)
    df["MA60"] = df["Close"].rolling(60).mean().round(0)
    df["MA300"] = df["Close"].rolling(300).mean().round(0)
    df["RSI"] = calculate_rsi(df["Close"], 14).round(1)
    df["Recent20MaxAmt"] = df["Amount"].rolling(20).max()
    DF_CACHE[code] = df
    return df


def generate_game_data(trend_mode="bull"):
    initial_bars = 80
    default_turns = 50
    max_future_turns = 150

    top_pool = STOCK_POOL[: min(350, len(STOCK_POOL))]
    chosen_stock = None
    df = None
    start_pos = 220
    end_pos = 400
    recent_max_eok = 500
    is_bull = True

    for attempt in range(12):
        pool_to_use = top_pool if attempt < 8 else STOCK_POOL
        stock = random.choice(pool_to_use)
        code = stock["Code"]

        try:
            cand_df = fetch_stock_df(code)
            if cand_df is None:
                continue

            search_df = cand_df.iloc[300 : len(cand_df) - 65]
            if len(search_df) == 0:
                continue

            cond_amt = search_df["Recent20MaxAmt"] >= 50_000_000_000
            if trend_mode == "bull":
                cond_trend = search_df["Close"] >= search_df["MA300"]
            elif trend_mode == "bear":
                cond_trend = search_df["Close"] < search_df["MA300"]
            else:
                cond_trend = pd.Series(True, index=search_df.index)

            valid_positions = np.where(cond_amt & cond_trend)[0]
            if len(valid_positions) == 0:
                continue

            pos = int(random.choice(valid_positions)) + 300
            start_pos = pos - (initial_bars - 1)
            end_pos = min(len(cand_df), pos + 1 + max_future_turns)
            df = cand_df
            recent_max_eok = int(df["Recent20MaxAmt"].iloc[pos] // 100_000_000)
            is_bull = bool(df["Close"].iloc[pos] >= df["MA300"].iloc[pos])
            chosen_stock = stock
            break
        except Exception:
            continue

    if chosen_stock is None or df is None:
        chosen_stock = INITIAL_POOL[0]
        df = fetch_stock_df(chosen_stock["Code"])
        pos = random.randint(300, len(df) - 70)
        start_pos = pos - (initial_bars - 1)
        end_pos = min(len(df), pos + 1 + max_future_turns)
        recent_max_eok = int(df["Recent20MaxAmt"].iloc[pos] // 100_000_000)
        is_bull = bool(df["Close"].iloc[pos] >= safe_float(df["MA300"].iloc[pos], 0))

    # 볼린저밴드가 어떤 기간(예: 60일, 120일 등)에서도 1봉부터 완벽히 그려지도록 이전 150봉 종가를 함께 전달
    pre_start = max(0, start_pos - 150)
    pre_closes = [safe_float(x, 10000.0) for x in df["Close"].iloc[pre_start:start_pos].tolist()]

    game_df = df.iloc[start_pos:end_pos].copy()
    dates = game_df.index.strftime("%Y-%m-%d").tolist()
    candles = []
    for i, (_, row) in enumerate(game_df.iterrows()):
        t = (i + 1) * 86400
        candles.append({
            "time": t,
            "date": dates[i],
            "open": safe_float(row["Open"], 10000.0),
            "high": safe_float(row["High"], 10000.0),
            "low": safe_float(row["Low"], 10000.0),
            "close": safe_float(row["Close"], 10000.0),
            "volume": safe_float(row["Volume"], 1000.0),
            "amount_eok": round(safe_float(row["Amount"], 0.0) / 100_000_000, 1),
            "ma5": safe_float(row["MA5"], None),
            "ma20": safe_float(row["MA20"], None),
            "ma60": safe_float(row["MA60"], None),
            "ma300": safe_float(row["MA300"], None),
            "rsi": safe_float(row["RSI"], 50.0),
        })

    marcap_eok = int(chosen_stock.get("Marcap", 100000000000) // 100_000_000)
    avail_turns = max(10, len(candles) - initial_bars)
    return {
        "stock_name": chosen_stock["Name"],
        "stock_code": chosen_stock["Code"],
        "market": chosen_stock.get("Market", "KRX"),
        "marcap_str": (
            f"{marcap_eok // 10000}조 {marcap_eok % 10000:,}억"
            if marcap_eok >= 10000
            else f"{marcap_eok:,}억"
        ),
        "recent_max_eok": f"{recent_max_eok:,}억",
        "trend_label": "정배열(300일선 위)" if is_bull else "역배열(300일선 아래)",
        "start_date": dates[initial_bars - 1],
        "end_date": dates[-1],
        "initial_bars": initial_bars,
        "total_turns": min(default_turns, avail_turns),
        "pool_count": len(STOCK_POOL),
        "pre_closes": pre_closes,
        "candles": candles,
    }


def load_saved_history():
    if os.path.exists(HISTORY_JSON):
        try:
            with open(HISTORY_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def append_saved_history(record):
    history = load_saved_history()
    history.insert(0, record)
    with open(HISTORY_JSON, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    try:
        pd.DataFrame(history).to_csv(HISTORY_CSV, index=False, encoding="utf-8-sig")
    except Exception:
        pass


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>프로 종가매매 차트 훈련소</title>
    <script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"
            onerror="this.onerror=null;this.src='https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js';"></script>
    <style>
        * { box-sizing: border-box; font-family: 'Pretendard', -apple-system, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { 
            margin: 0; background: #101216; color: #e1e3e6; 
            display: flex; flex-direction: column; min-height: 100dvh; 
            overflow-x: hidden; overflow-y: auto; -webkit-overflow-scrolling: touch; font-size: 12px; 
        }

        /* 노트북 화면에서도 상단~하단이 한눈에 들어오도록 슬림화된 상단바 */
        .top-bar { display: flex; justify-content: space-between; align-items: center; padding: 4px 10px; background: #181b20; border-bottom: 1px solid #282c34; flex-wrap: wrap; gap: 4px; flex-shrink: 0; }
        .stock-badge { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
        .stock-title { font-size: 13px; font-weight: 800; color: #ffffff; background: #262b33; padding: 3px 8px; border-radius: 5px; border-left: 3px solid #00c471; }
        .stock-sub { font-size: 11px; color: #9ba3ae; background: #20242b; padding: 2px 6px; border-radius: 4px; }
        .top-actions { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
        select, input[type="number"] { background: #22262e; color: #fff; border: 1px solid #363c48; border-radius: 4px; padding: 2px 5px; font-size: 11px; }

        .status-bar { display: flex; justify-content: space-between; align-items: center; padding: 4px 10px; background: #14171c; border-bottom: 1px solid #242830; flex-wrap: wrap; gap: 4px; flex-shrink: 0; }
        .stats-group { display: flex; gap: 12px; align-items: center; overflow-x: auto; width: 100%; }
        .stat-item { white-space: nowrap; flex-shrink: 0; display: flex; align-items: baseline; gap: 4px; }
        .stat-item span { color: #8b949e; font-size: 11px; }
        .stat-item strong { font-size: 12px; }
        .plus { color: #f04452 !important; }
        .minus { color: #3182f6 !important; }

        .tools-bar { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; font-size: 11px; background: #181b20; padding: 3px 10px; border-bottom: 1px solid #282c34; flex-shrink: 0; }
        .tool-box { display: flex; align-items: center; gap: 3px; background: #22262e; padding: 2px 6px; border-radius: 4px; flex-wrap: wrap; }

        /* 차트 영역: 사용자가 직접 높이를 조절할 수 있는 구조 */
        .charts-wrapper { position: relative; width: 100%; display: flex; flex-direction: column; flex-shrink: 0; }
        #main-chart { width: 100%; height: 240px; }
        #rsi-chart { width: 100%; height: 80px; border-top: 1px solid #282c34; }
        
        .legend { position: absolute; top: 5px; left: 8px; z-index: 10; font-size: 10px; pointer-events: none; display: flex; flex-wrap: wrap; gap: 6px; background: rgba(16,18,22,0.82); padding: 2px 6px; border-radius: 4px; }
        .toast-msg { position: absolute; top: 28px; left: 50%; transform: translateX(-50%); background: rgba(240, 68, 82, 0.95); color: #fff; padding: 5px 14px; border-radius: 20px; font-weight: 700; font-size: 12px; z-index: 30; display: none; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }

        /* 하단 컨트롤 바 컴팩트화 */
        .controls { padding: 6px 10px; padding-bottom: calc(14px + env(safe-area-inset-bottom)); background: #181b20; border-top: 1px solid #282c34; display: flex; flex-direction: column; gap: 4px; flex-shrink: 0; }
        .btn-row { display: flex; gap: 4px; width: 100%; align-items: center; }
        button { border: none; border-radius: 5px; font-weight: 700; cursor: pointer; font-size: 12px; transition: 0.1s; padding: 7px 4px; flex: 1; text-align: center; color: #fff; background: #2b303b; }
        button:active { transform: scale(0.97); }
        button:disabled { opacity: 0.35; cursor: not-allowed; }
        .btn-sm { flex: unset; padding: 3px 7px; font-size: 11px; }

        .btn-buy { background: rgba(240, 68, 82, 0.18); color: #ff5c6a; border: 1px solid rgba(240, 68, 82, 0.55); }
        .btn-buy:hover:not(:disabled), .btn-buy:active { background: #f04452; color: #fff; }
        .btn-sell { background: rgba(49, 130, 246, 0.18); color: #5ca0ff; border: 1px solid rgba(49, 130, 246, 0.55); }
        .btn-sell:hover:not(:disabled), .btn-sell:active { background: #3182f6; color: #fff; }
        .btn-hold { background: #323846; color: #fff; font-size: 12px; font-weight: 800; flex: 1.5; border: 1px solid #485063; padding: 8px 6px; }
        .btn-green { background: #00c471; color: #fff; }
        .btn-blue { background: #3b82f6; color: #fff; }
        .btn-active { background: #f59e0b !important; color: #111 !important; border-color: #f59e0b !important; }

        .limit-bar { display: flex; gap: 4px; align-items: center; flex-wrap: wrap; background: #13161b; padding: 4px 8px; border-radius: 5px; border: 1px solid #262b35; font-size: 11px; }

        .modal { display: none; position: fixed; top: 12%; left: 50%; transform: translateX(-50%); background: #1e222a; border-radius: 10px; border: 1px solid #454d5e; z-index: 200; width: 92%; max-width: 380px; box-shadow: 0 14px 36px rgba(0,0,0,0.85); overflow: hidden; }
        .modal-wide { max-width: 660px; top: 8%; }
        .modal-header { background: #282e38; padding: 8px 12px; cursor: move; display: flex; justify-content: space-between; align-items: center; font-weight: 700; font-size: 12px; user-select: none; border-bottom: 1px solid #383f4d; }
        .modal-body { padding: 12px; max-height: 70vh; overflow-y: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 8px; }
        th, td { border-bottom: 1px solid #2d333f; padding: 5px 4px; text-align: center; }
        th { background: #232832; color: #9ba3ae; }
    </style>
</head>
<body>

<div class="top-bar" id="top-bar-el">
    <div class="stock-badge">
        <span class="stock-title" id="ui-stock-name">차트 불러오는 중...</span>
        <span class="stock-sub" id="ui-stock-info">시총 - | 20일최대거래대금 -</span>
        <span class="stock-sub" id="turn-badge" style="color:#facc15; font-weight:700;">턴: 0 / 50</span>
        <button class="btn-sm" onclick="extendTurns(10)">+10턴 연장</button>
    </div>
    <div class="top-actions">
        <select id="trend-select" onchange="startNewGame()">
            <option value="bull" selected>📈 정배열(300일선 위)</option>
            <option value="bear">📉 역배열(300일선 아래)</option>
            <option value="all">🎲 랜덤</option>
        </select>
        <button class="btn-sm btn-green" id="btn-next-stock" onclick="startNewGame()">🔄 새종목</button>
        <button class="btn-sm" onclick="openStatsModal()">📊 통계/저장</button>
        <button class="btn-sm" onclick="openMobileModal()">📱 URL</button>
    </div>
</div>

<div class="status-bar" id="status-bar-el">
    <div class="stats-group">
        <div class="stat-item"><span>현재종가</span><strong id="cur-price">-</strong></div>
        <div class="stat-item"><span>내평단(비중)</span><strong id="avg-price">- (0%)</strong></div>
        <div class="stat-item"><span>총자산(수익률)</span><strong id="total-equity">1,000만 (0.00%)</strong></div>
        <div class="stat-item"><span>가용현금</span><strong id="cash-val">1,000만원</strong></div>
        <div class="stat-item"><span>거래대금</span><strong id="cur-amt">-</strong></div>
        <div class="stat-item"><span>종목풀</span><strong id="pool-count-text" style="color:#00c471;">1천억+</strong></div>
    </div>
</div>

<div class="tools-bar" id="tools-bar-el">
    <!-- 2. 볼린저밴드 실시간 수정 (타이핑 즉시 반영) -->
    <div class="tool-box">
        <label style="cursor:pointer;"><input type="checkbox" id="bb-toggle" checked onchange="updateBollinger()"> <b>볼밴</b></label>
        <span>기간</span><input type="number" id="bb-period" value="20" min="2" max="150" style="width:42px;" oninput="updateBollinger()" onchange="updateBollinger()">
        <span>승수</span><input type="number" id="bb-mult" value="2.0" step="0.1" min="0.1" max="10.0" style="width:44px;" oninput="updateBollinger()" onchange="updateBollinger()">
    </div>
    <!-- 9. 자동손절 -->
    <div class="tool-box">
        <label style="color:#ff6b6b; font-weight:700; cursor:pointer;"><input type="checkbox" id="sl-toggle" checked onchange="updatePriceLines()"> 🛡️손절</label>
        <span>-</span><input type="number" id="sl-pct" value="12" min="1" max="50" style="width:38px;" oninput="updatePriceLines()" onchange="updatePriceLines()"><span>%</span>
    </div>
    <!-- 11. 가로선 긋기 -->
    <div class="tool-box">
        <button class="btn-sm" id="btn-draw-line" onclick="toggleDrawLineMode()">📏 가로선</button>
        <button class="btn-sm" onclick="clearUserLines()">🗑️ 지우기</button>
    </div>
    <!-- 차트 & 보조지표(RSI) 높이 직접 조절 도구 -->
    <div class="tool-box" style="border: 1px solid #3b82f6;">
        <span style="color:#60a5fa; font-weight:700;">📐 높이조절:</span>
        <span>차트</span>
        <button class="btn-sm" onclick="changeChartSize(-25, 0)">-</button>
        <span id="lbl-main-h" style="min-width:32px; text-align:center;">240</span>
        <button class="btn-sm" onclick="changeChartSize(25, 0)">+</button>
        <span style="margin-left:4px;">RSI</span>
        <button class="btn-sm" onclick="changeChartSize(0, -15)">-</button>
        <span id="lbl-rsi-h" style="min-width:26px; text-align:center;">75</span>
        <button class="btn-sm" onclick="changeChartSize(0, 15)">+</button>
        <label style="margin-left:3px; cursor:pointer;"><input type="checkbox" id="rsi-toggle" checked onchange="toggleRsiVisible()">표시</label>
        <button class="btn-sm btn-blue" onclick="autoFitLaptopScreen()" title="현재 창 높이에 딱 맞게 차트 크기를 자동 조절합니다">💻 화면딱맞춤</button>
    </div>
</div>

<div class="charts-wrapper" id="charts-wrapper-el">
    <div class="legend">
        <span style="color:#f59e0b">●5일</span>
        <span style="color:#ec4899">●20일</span>
        <span style="color:#10b981">●60일</span>
        <span style="color:#38bdf8; font-weight:700;">━300일선</span>
        <span id="bb-legend-text" style="color:#e2e8f0">---볼밴(20, 2)</span>
        <span style="color:#a855f7">●RSI(14)</span>
    </div>
    <div id="toast-box" class="toast-msg"></div>
    <div id="main-chart"></div>
    <div id="rsi-chart"></div>

    <!-- 결과창 -->
    <div id="result-modal" class="modal">
        <div class="modal-header" id="result-modal-header">
            <span>🏁 매매 종료 (잡고 드래그하여 이동)</span>
            <div style="display:flex; gap:4px;">
                <button class="btn-sm" onclick="toggleResultBody()">접기/펴기</button>
                <button class="btn-sm" onclick="document.getElementById('result-modal').style.display='none'">✖</button>
            </div>
        </div>
        <div class="modal-body" id="result-modal-body" style="text-align:center;">
            <h3 style="margin:0 0 4px 0;" id="reveal-title">종목명</h3>
            <div id="reveal-info" style="color:#00c471; font-size:12px; font-weight:600; margin-bottom:4px;"></div>
            <div id="reveal-period" style="color:#9ba3ae; font-size:12px;"></div>
            <hr style="border-color:#323846; margin:10px 0;">
            <p style="margin:5px 0; font-size:14px;">내 최종 수익률: <strong id="final-my-return" style="font-size:20px;"></strong></p>
            <p style="margin:5px 0; font-size:12px; color:#adb5bd;">단순 보유(존버) 수익률: <strong id="final-bh-return"></strong></p>
            <div style="display:flex; gap:6px; margin-top:12px;">
                <button class="btn-sm btn-blue" style="flex:1; padding:9px;" onclick="extendTurns(20)">⏳ +20턴 연장</button>
                <button class="btn-sm" style="flex:1; padding:9px;" onclick="downloadChartImage()">📸 차트저장</button>
            </div>
            <button class="btn-green" style="width:100%; margin-top:6px; padding:10px; font-size:13px;" onclick="startNewGame()">🔄 다음 종목 시작 (Enter)</button>
        </div>
    </div>

    <!-- 통계창 -->
    <div id="stats-modal" class="modal modal-wide">
        <div class="modal-header" id="stats-modal-header">
            <span>📊 누적 매매 통계 및 저장</span>
            <button class="btn-sm" onclick="document.getElementById('stats-modal').style.display='none'">✖</button>
        </div>
        <div class="modal-body">
            <div id="stats-summary" style="display:flex; justify-content:space-around; background:#14171d; padding:10px; border-radius:6px; margin-bottom:10px; text-align:center;"></div>
            <div style="display:flex; gap:6px; margin-bottom:8px;">
                <button class="btn-sm btn-green" onclick="downloadChartImage()">📸 현재 차트 이미지(PNG) 저장</button>
                <button class="btn-sm btn-blue" onclick="downloadCSV()">💾 전체 기록 엑셀(CSV) 저장</button>
            </div>
            <div style="max-height:220px; overflow-y:auto;">
                <table>
                    <thead>
                        <tr><th>일시</th><th>종목</th><th>배열</th><th>내수익</th><th>존버</th></tr>
                    </thead>
                    <tbody id="stats-tbody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- 모바일 접속 안내창 -->
    <div id="mobile-modal" class="modal">
        <div class="modal-header" id="mobile-modal-header">
            <span>📱 모바일 접속 주소</span>
            <button class="btn-sm" onclick="document.getElementById('mobile-modal').style.display='none'">✖</button>
        </div>
        <div class="modal-body" style="text-align:center;">
            <p style="font-size:12px; color:#adb5bd; margin-top:0;">컴퓨터의 검은 창을 켜둔 상태에서 접속하세요:</p>
            <div style="background:#12151a; padding:8px; border-radius:6px; border:1px solid #323846; margin:8px 0;">
                <strong id="mobile-url-text" style="color:#00c471; font-size:14px;">__MOBILE_URL__</strong>
            </div>
            <img id="mobile-qr" src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=__MOBILE_URL__" alt="QR코드" style="border-radius:8px; border:3px solid #fff; margin:6px 0;" />
        </div>
    </div>
</div>

<div class="controls" id="controls-el">
    <div class="limit-bar">
        <strong style="color:#facc15;">🎯 지정가:</strong>
        <input type="number" id="limit-price-input" placeholder="가격" style="width:76px;">
        <button class="btn-sm" id="btn-pick-price" onclick="togglePickPriceMode()">차트클릭</button>
        <button class="btn-sm" onclick="adjustLimitPrice(-0.03)">-3%</button>
        <button class="btn-sm" onclick="adjustLimitPrice(0.03)">+3%</button>
        <select id="limit-ratio-select">
            <option value="0.05">5%</option>
            <option value="0.10">10%</option>
            <option value="0.25" selected>25%</option>
            <option value="0.50">50%</option>
            <option value="1.00">100%</option>
        </select>
        <button class="btn-sm btn-buy" onclick="setLimitOrder('BUY')">매수예약</button>
        <button class="btn-sm btn-sell" onclick="setLimitOrder('SELL')">매도예약</button>
        <button class="btn-sm" onclick="clearLimitOrders()">취소</button>
        <span id="limit-status" style="color:#9ba3ae; font-size:10px; margin-left:auto;">대기없음</span>
    </div>

    <div class="btn-row">
        <button class="btn-buy" id="b5" onclick="trade('BUY', 0.05)">매수 5%</button>
        <button class="btn-buy" id="b10" onclick="trade('BUY', 0.10)">10%</button>
        <button class="btn-buy" id="b25" onclick="trade('BUY', 0.25)">25% [1]</button>
        <button class="btn-buy" id="b50" onclick="trade('BUY', 0.50)">50% [2]</button>
        <button class="btn-buy" id="b100" onclick="trade('BUY', 1.0)">풀매수 [3]</button>
    </div>

    <div class="btn-row">
        <button class="btn-hold" id="bHold" onclick="trade('HOLD', 0)">관망/다음봉 ➡️ [Space]</button>
        <button class="btn-sell" id="s5" onclick="trade('SELL', 0.05)">매도 5%</button>
        <button class="btn-sell" id="s10" onclick="trade('SELL', 0.10)">10%</button>
        <button class="btn-sell" id="s25" onclick="trade('SELL', 0.25)">25%</button>
        <button class="btn-sell" id="s50" onclick="trade('SELL', 0.50)">50% [A]</button>
        <button class="btn-sell" id="s100" onclick="trade('SELL', 1.0)">전량 [S]</button>
    </div>
</div>

<script>
let HISTORY_DATA = __HISTORY_DATA__;
let gameData = null;
let curIdx = 0;
let initialCash = 10000000;
let cash = initialCash;
let shares = 0;
let avgPrice = 0;
let markers = [];
let gameEnded = false;

let avgPriceLine = null;
let stopLossLine = null;
let limitBuyOrder = null;
let limitSellOrder = null;
let userDrawnLines = [];
let drawLineMode = false;
let pickPriceMode = false;

// 사용자 지정 차트 & RSI 높이 (로컬스토리지 기억)
let mainChartHeight = parseInt(localStorage.getItem('cg_main_h')) || 240;
let rsiChartHeight = parseInt(localStorage.getItem('cg_rsi_h')) || 75;
let rsiVisible = localStorage.getItem('cg_rsi_vis') !== 'false';

const mainContainer = document.getElementById('main-chart');
const rsiContainer = document.getElementById('rsi-chart');

const chartOptions = {
    width: mainContainer.clientWidth || 360,
    height: mainChartHeight,
    layout: { background: { color: '#101216' }, textColor: '#8b949e' },
    grid: { vertLines: { color: '#1c2026' }, horzLines: { color: '#1c2026' } },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    timeScale: { tickMarkFormatter: (t) => `${Math.round(t / 86400)}봉` },
    localization: { timeFormatter: (t) => `${Math.round(t / 86400)}번째 봉` }
};

const mainChart = LightweightCharts.createChart(mainContainer, chartOptions);
const candleSeries = mainChart.addCandlestickSeries({
    upColor: '#f04452', downColor: '#3182f6', borderVisible: false,
    wickUpColor: '#f04452', wickDownColor: '#3182f6'
});

const ma5Series = mainChart.addLineSeries({ color: '#f59e0b', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
const ma20Series = mainChart.addLineSeries({ color: '#ec4899', lineWidth: 2, priceLineVisible: false, lastValueVisible: false });
const ma60Series = mainChart.addLineSeries({ color: '#10b981', lineWidth: 1, priceLineVisible: false, lastValueVisible: false });
const ma300Series = mainChart.addLineSeries({ color: '#38bdf8', lineWidth: 2, priceLineVisible: false, lastValueVisible: false });

// 볼린저밴드 상단, 중심, 하단 시리즈 (선명한 색상과 점선 적용)
const bbUpperSeries = mainChart.addLineSeries({ color: 'rgba(226, 232, 240, 0.85)', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed, priceLineVisible: false, lastValueVisible: false });
const bbMidSeries = mainChart.addLineSeries({ color: 'rgba(250, 204, 21, 0.55)', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dotted, priceLineVisible: false, lastValueVisible: false });
const bbLowerSeries = mainChart.addLineSeries({ color: 'rgba(226, 232, 240, 0.85)', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed, priceLineVisible: false, lastValueVisible: false });

const volumeSeries = mainChart.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: '' });
volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });

const rsiChart = LightweightCharts.createChart(rsiContainer, {
    ...chartOptions,
    height: rsiChartHeight
});
const rsiSeries = rsiChart.addLineSeries({ color: '#a855f7', lineWidth: 2 });

mainChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
    if (range) rsiChart.timeScale().setVisibleLogicalRange(range);
});

// 차트 및 보조지표 크기 적용 함수
function applyChartSizes() {
    mainContainer.style.height = mainChartHeight + 'px';
    document.getElementById('lbl-main-h').innerText = mainChartHeight;
    document.getElementById('lbl-rsi-h').innerText = rsiVisible ? rsiChartHeight : 'OFF';
    document.getElementById('rsi-toggle').checked = rsiVisible;

    if (rsiVisible) {
        rsiContainer.style.display = 'block';
        rsiContainer.style.height = rsiChartHeight + 'px';
    } else {
        rsiContainer.style.display = 'none';
    }

    const w = mainContainer.clientWidth || window.innerWidth || 360;
    mainChart.resize(w, mainChartHeight);
    if (rsiVisible) {
        rsiChart.resize(w, rsiChartHeight);
    }
}

function changeChartSize(deltaMain, deltaRsi) {
    if (deltaMain !== 0) {
        mainChartHeight = Math.max(120, Math.min(700, mainChartHeight + deltaMain));
        localStorage.setItem('cg_main_h', mainChartHeight);
    }
    if (deltaRsi !== 0) {
        if (!rsiVisible) {
            rsiVisible = true;
            localStorage.setItem('cg_rsi_vis', 'true');
        }
        rsiChartHeight = Math.max(45, Math.min(300, rsiChartHeight + deltaRsi));
        localStorage.setItem('cg_rsi_h', rsiChartHeight);
    }
    applyChartSizes();
}

function toggleRsiVisible() {
    rsiVisible = document.getElementById('rsi-toggle').checked;
    localStorage.setItem('cg_rsi_vis', rsiVisible);
    applyChartSizes();
}

// 노트북/모니터 한 화면에 상단 종목명~하단 매도버튼이 딱 들어오도록 자동 계산
function autoFitLaptopScreen() {
    const vh = window.innerHeight;
    const topH = document.getElementById('top-bar-el').offsetHeight || 34;
    const statusH = document.getElementById('status-bar-el').offsetHeight || 28;
    const toolsH = document.getElementById('tools-bar-el').offsetHeight || 30;
    const ctrlH = document.getElementById('controls-el').offsetHeight || 115;
    const avail = Math.max(180, vh - topH - statusH - toolsH - ctrlH - 12);

    if (rsiVisible) {
        rsiChartHeight = Math.max(55, Math.round(avail * 0.24));
        mainChartHeight = Math.max(130, avail - rsiChartHeight);
    } else {
        mainChartHeight = avail;
    }
    localStorage.setItem('cg_main_h', mainChartHeight);
    localStorage.setItem('cg_rsi_h', rsiChartHeight);
    applyChartSizes();
    mainChart.timeScale().fitContent();
}

window.addEventListener('resize', () => {
    applyChartSizes();
});

mainChart.subscribeClick((param) => {
    if (!param.point || !gameData) return;
    const clickedPrice = Math.round(candleSeries.coordinateToPrice(param.point.y));
    if (!clickedPrice || clickedPrice <= 0) return;

    if (drawLineMode) {
        const line = candleSeries.createPriceLine({
            price: clickedPrice, color: '#00f5d4', lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Solid, axisLabelVisible: true, title: '가로선'
        });
        userDrawnLines.push(line);
        showToast(`📏 ${clickedPrice.toLocaleString()}원에 가로선을 그었습니다.`);
    } else if (pickPriceMode) {
        document.getElementById('limit-price-input').value = clickedPrice;
        togglePickPriceMode(false);
        showToast(`🎯 지정가 ${clickedPrice.toLocaleString()}원이 선택되었습니다.`);
    }
});

function toggleDrawLineMode() {
    drawLineMode = !drawLineMode;
    if (drawLineMode) pickPriceMode = false;
    document.getElementById('btn-draw-line').innerText = `📏 ${drawLineMode ? 'ON' : '가로선'}`;
    document.getElementById('btn-draw-line').classList.toggle('btn-active', drawLineMode);
    document.getElementById('btn-pick-price').classList.remove('btn-active');
}

function clearUserLines() {
    userDrawnLines.forEach(l => candleSeries.removePriceLine(l));
    userDrawnLines = [];
}

function togglePickPriceMode(forceState) {
    pickPriceMode = (forceState !== undefined) ? forceState : !pickPriceMode;
    if (pickPriceMode) {
        drawLineMode = false;
        document.getElementById('btn-draw-line').innerText = '📏 가로선';
        document.getElementById('btn-draw-line').classList.remove('btn-active');
    }
    document.getElementById('btn-pick-price').classList.toggle('btn-active', pickPriceMode);
}

function showToast(msg) {
    const el = document.getElementById('toast-box');
    el.innerText = msg;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 2400);
}

// 2. 볼린저밴드 완벽 수정: 과거 150봉(pre_closes)을 결합해 어떤 기간/승수를 넣어도 1봉부터 즉시 표시!
function updateBollinger() {
    if (!gameData || !gameData.candles) return;
    const enabled = document.getElementById('bb-toggle').checked;
    if (!enabled) {
        bbUpperSeries.setData([]);
        bbMidSeries.setData([]);
        bbLowerSeries.setData([]);
        document.getElementById('bb-legend-text').innerText = '---볼밴(OFF)';
        return;
    }

    let rawPeriod = parseInt(document.getElementById('bb-period').value, 10);
    let rawMult = parseFloat(document.getElementById('bb-mult').value);
    if (isNaN(rawPeriod) || rawPeriod < 2) rawPeriod = 20;
    if (rawPeriod > 150) rawPeriod = 150;
    if (isNaN(rawMult) || rawMult <= 0) rawMult = 2.0;

    document.getElementById('bb-legend-text').innerText = `---볼밴(${rawPeriod}, ${rawMult})`;

    const pre = Array.isArray(gameData.pre_closes) ? gameData.pre_closes : [];
    const slice = gameData.candles.slice(0, curIdx + 1);
    const allCloses = pre.concat(slice.map(c => Number(c.close)));
    const offset = pre.length;

    const upper = [];
    const mid = [];
    const lower = [];

    for (let i = 0; i < slice.length; i++) {
        const idxInAll = offset + i;
        if (idxInAll + 1 < rawPeriod) continue;

        let sum = 0.0;
        for (let j = idxInAll - rawPeriod + 1; j <= idxInAll; j++) {
            sum += allCloses[j];
        }
        const mean = sum / rawPeriod;

        let sqSum = 0.0;
        for (let j = idxInAll - rawPeriod + 1; j <= idxInAll; j++) {
            const diff = allCloses[j] - mean;
            sqSum += diff * diff;
        }
        const std = Math.sqrt(sqSum / rawPeriod);

        const uVal = Number((mean + rawMult * std).toFixed(2));
        const mVal = Number(mean.toFixed(2));
        const lVal = Number(Math.max(0, mean - rawMult * std).toFixed(2));

        upper.push({ time: slice[i].time, value: uVal });
        mid.push({ time: slice[i].time, value: mVal });
        lower.push({ time: slice[i].time, value: lVal });
    }

    bbUpperSeries.setData(upper);
    bbMidSeries.setData(mid);
    bbLowerSeries.setData(lower);
}

async function startNewGame() {
    document.getElementById('result-modal').style.display = 'none';
    const nextBtn = document.getElementById('btn-next-stock');
    const trendMode = document.getElementById('trend-select').value;
    nextBtn.innerText = '⏳ 추출중...';
    setButtonsDisabled(true);

    try {
        const res = await fetch(`/api/new_game?mode=${trendMode}&t=${Date.now()}`, {
            headers: { 'ngrok-skip-browser-warning': '69420' }
        });
        if (!res.ok) throw new Error("서버 응답 오류");
        gameData = await res.json();

        nextBtn.innerText = '🔄 새종목';
        setButtonsDisabled(false);
        gameEnded = false;

        cash = initialCash;
        shares = 0;
        avgPrice = 0;
        markers = [];
        clearUserLines();
        clearLimitOrders();
        updatePriceLines();

        curIdx = gameData.initial_bars - 1;
        document.getElementById('limit-price-input').value = gameData.candles[curIdx].close;

        document.getElementById('ui-stock-name').innerText = `${gameData.stock_name} (${gameData.stock_code})`;
        document.getElementById('ui-stock-info').innerText = `${gameData.market} · 시총 ${gameData.marcap_str} · 20일최대 ${gameData.recent_max_eok}`;
        if (gameData.pool_count) {
            document.getElementById('pool-count-text').innerText = `${gameData.pool_count.toLocaleString()}종목`;
        }

        renderUpTo(curIdx);
        applyChartSizes();
        mainChart.timeScale().fitContent();
        updateUI();
    } catch (e) {
        console.error(e);
        showToast("⚠️ 서버 연결을 확인 후 [새종목]을 다시 눌러주세요.");
        nextBtn.innerText = '🔄 새종목';
        setButtonsDisabled(false);
    }
}

function renderUpTo(idx) {
    const slice = gameData.candles.slice(0, idx + 1);
    candleSeries.setData(slice);
    ma5Series.setData(slice.filter(d => d.ma5 !== null).map(d => ({ time: d.time, value: d.ma5 })));
    ma20Series.setData(slice.filter(d => d.ma20 !== null).map(d => ({ time: d.time, value: d.ma20 })));
    ma60Series.setData(slice.filter(d => d.ma60 !== null).map(d => ({ time: d.time, value: d.ma60 })));
    ma300Series.setData(slice.filter(d => d.ma300 !== null).map(d => ({ time: d.time, value: d.ma300 })));
    volumeSeries.setData(slice.map(d => ({
        time: d.time, value: d.volume,
        color: d.close >= d.open ? 'rgba(240, 68, 82, 0.35)' : 'rgba(49, 130, 246, 0.35)'
    })));
    rsiSeries.setData(slice.map(d => ({ time: d.time, value: d.rsi })));
    updateBollinger();
    markers.sort((a, b) => a.time - b.time);
    candleSeries.setMarkers(markers);
}

function updatePriceLines() {
    if (avgPriceLine) { candleSeries.removePriceLine(avgPriceLine); avgPriceLine = null; }
    if (stopLossLine) { candleSeries.removePriceLine(stopLossLine); stopLossLine = null; }

    if (shares > 0 && avgPrice > 0) {
        avgPriceLine = candleSeries.createPriceLine({
            price: avgPrice, color: '#facc15', lineWidth: 2,
            lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: '내 평단가'
        });
        if (document.getElementById('sl-toggle').checked) {
            const slPct = parseFloat(document.getElementById('sl-pct').value) || 12;
            const slPrice = Math.round(avgPrice * (1 - slPct / 100));
            stopLossLine = candleSeries.createPriceLine({
                price: slPrice, color: '#ff4d4f', lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dotted, axisLabelVisible: true, title: `손절(-${slPct}%)`
            });
        }
    }
}

function adjustLimitPrice(pct) {
    const input = document.getElementById('limit-price-input');
    const base = parseFloat(input.value) || (gameData ? gameData.candles[curIdx].close : 10000);
    input.value = Math.round(base * (1 + pct));
}

function setLimitOrder(type) {
    if (!gameData) return;
    const price = Math.round(parseFloat(document.getElementById('limit-price-input').value));
    const ratio = parseFloat(document.getElementById('limit-ratio-select').value) || 0.25;
    if (!price || price <= 0) return;

    if (type === 'BUY') {
        if (limitBuyOrder && limitBuyOrder.line) candleSeries.removePriceLine(limitBuyOrder.line);
        const line = candleSeries.createPriceLine({
            price: price, color: '#ff5c6a', lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: `예약매수(${Math.round(ratio*100)}%)`
        });
        limitBuyOrder = { price, ratio, line };
    } else {
        if (limitSellOrder && limitSellOrder.line) candleSeries.removePriceLine(limitSellOrder.line);
        const line = candleSeries.createPriceLine({
            price: price, color: '#5ca0ff', lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: `예약매도(${Math.round(ratio*100)}%)`
        });
        limitSellOrder = { price, ratio, line };
    }
    updateLimitStatusText();
}

function clearLimitOrders() {
    if (limitBuyOrder && limitBuyOrder.line) candleSeries.removePriceLine(limitBuyOrder.line);
    if (limitSellOrder && limitSellOrder.line) candleSeries.removePriceLine(limitSellOrder.line);
    limitBuyOrder = null;
    limitSellOrder = null;
    updateLimitStatusText();
}

function updateLimitStatusText() {
    const parts = [];
    if (limitBuyOrder) parts.push(`매수 ${limitBuyOrder.price.toLocaleString()}`);
    if (limitSellOrder) parts.push(`매도 ${limitSellOrder.price.toLocaleString()}`);
    document.getElementById('limit-status').innerText = parts.length ? parts.join(' | ') : '대기없음';
}

function executeBuy(price, ratio, time, label) {
    const totalEquity = cash + (shares * price);
    const targetAmt = ratio >= 0.99 ? cash : Math.min(cash, totalEquity * ratio);
    const buyShares = Math.floor(targetAmt / price);
    if (buyShares > 0) {
        const totalCost = (shares * avgPrice) + (buyShares * price);
        shares += buyShares;
        cash -= buyShares * price;
        avgPrice = Math.round(totalCost / shares);
        markers.push({ time: time, position: 'belowBar', color: '#f04452', shape: 'arrowUp', text: label });
        return true;
    }
    return false;
}

function executeSell(price, ratio, time, label) {
    if (shares <= 0) return false;
    const sellShares = ratio >= 0.99 ? shares : Math.max(1, Math.floor(shares * ratio));
    cash += sellShares * price * 0.998;
    shares -= sellShares;
    if (shares === 0) avgPrice = 0;
    markers.push({ time: time, position: 'aboveBar', color: '#3182f6', shape: 'arrowDown', text: label });
    return true;
}

function trade(action, ratio) {
    if (!gameData || gameEnded) return;
    const curBar = gameData.candles[curIdx];
    const price = curBar.close;

    if (action === 'BUY') {
        executeBuy(price, ratio, curBar.time, `매수${Math.round(ratio*100)}%`);
    } else if (action === 'SELL') {
        executeSell(price, ratio, curBar.time, `매도${Math.round(ratio*100)}%`);
    }

    if (curIdx + 1 < gameData.candles.length) {
        curIdx++;
        const nextBar = gameData.candles[curIdx];

        if (shares > 0 && document.getElementById('sl-toggle').checked) {
            const slPct = parseFloat(document.getElementById('sl-pct').value) || 12;
            const slPrice = Math.round(avgPrice * (1 - slPct / 100));
            if (nextBar.low <= slPrice) {
                const execPrice = Math.min(nextBar.open, slPrice);
                executeSell(execPrice, 1.0, nextBar.time, `⚡손절(-${slPct}%)`);
                showToast(`⚡ 자동손절 발동! ${execPrice.toLocaleString()}원에 전량 매도되었습니다.`);
            }
        }

        if (limitBuyOrder && nextBar.low <= limitBuyOrder.price) {
            const execPrice = Math.min(nextBar.open, limitBuyOrder.price);
            if (executeBuy(execPrice, limitBuyOrder.ratio, nextBar.time, `🎯지정매수`)) {
                showToast(`🎯 지정가 매수 체결 (${execPrice.toLocaleString()}원)`);
            }
            candleSeries.removePriceLine(limitBuyOrder.line);
            limitBuyOrder = null;
            updateLimitStatusText();
        }
        if (limitSellOrder && shares > 0 && nextBar.high >= limitSellOrder.price) {
            const execPrice = Math.max(nextBar.open, limitSellOrder.price);
            if (executeSell(execPrice, limitSellOrder.ratio, nextBar.time, `🎯지정매도`)) {
                showToast(`🎯 지정가 매도 체결 (${execPrice.toLocaleString()}원)`);
            }
            candleSeries.removePriceLine(limitSellOrder.line);
            limitSellOrder = null;
            updateLimitStatusText();
        }
    }

    updatePriceLines();
    renderUpTo(curIdx);
    updateUI();

    const playedTurns = curIdx - (gameData.initial_bars - 1);
    if (playedTurns >= gameData.total_turns || curIdx >= gameData.candles.length - 1) {
        finishGame();
    }
}

function extendTurns(addCount) {
    if (!gameData) return;
    const maxPossible = gameData.candles.length - gameData.initial_bars;
    if (gameData.total_turns >= maxPossible) {
        showToast("⚠️ 더 이상 남은 과거 데이터가 없습니다.");
        return;
    }
    gameData.total_turns = Math.min(maxPossible, gameData.total_turns + addCount);
    gameEnded = false;
    setButtonsDisabled(false);
    document.getElementById('result-modal').style.display = 'none';
    updateUI();
    showToast(`⏳ 진행 턴이 ${gameData.total_turns}턴으로 연장되었습니다!`);
}

function updateUI() {
    const curBar = gameData.candles[curIdx];
    const prevBar = curIdx > 0 ? gameData.candles[curIdx - 1] : curBar;
    const price = curBar.close;
    const dayChg = ((price - prevBar.close) / prevBar.close * 100).toFixed(2);
    const stockEval = shares * price;
    const totalEquity = Math.round(cash + stockEval);
    const returnPct = ((totalEquity - initialCash) / initialCash * 100).toFixed(2);
    const weightPct = Math.round((stockEval / totalEquity) * 100);
    const playedTurns = curIdx - (gameData.initial_bars - 1);

    document.getElementById('turn-badge').innerText = `턴: ${playedTurns} / ${gameData.total_turns}`;
    
    const priceEl = document.getElementById('cur-price');
    priceEl.innerText = `${price.toLocaleString()}원 (${dayChg > 0 ? '+' : ''}${dayChg}%)`;
    priceEl.className = dayChg > 0 ? 'plus' : (dayChg < 0 ? 'minus' : '');

    document.getElementById('avg-price').innerText = shares > 0 ? `${avgPrice.toLocaleString()}원 (${weightPct}%)` : `- (0%)`;
    document.getElementById('cash-val').innerText = `${Math.round(cash/10000).toLocaleString()}만원`;
    document.getElementById('cur-amt').innerText = `${curBar.amount_eok.toLocaleString()}억`;

    const eqEl = document.getElementById('total-equity');
    eqEl.innerText = `${Math.round(totalEquity/10000).toLocaleString()}만원 (${returnPct > 0 ? '+' : ''}${returnPct}%)`;
    eqEl.className = returnPct > 0 ? 'plus' : (returnPct < 0 ? 'minus' : '');
}

async function finishGame() {
    gameEnded = true;
    setButtonsDisabled(true);
    const curBar = gameData.candles[curIdx];
    const firstPlayBar = gameData.candles[gameData.initial_bars - 1];
    const totalEquity = Math.round(cash + (shares * curBar.close));
    const myReturn = parseFloat(((totalEquity - initialCash) / initialCash * 100).toFixed(2));
    const bhReturn = parseFloat(((curBar.close - firstPlayBar.close) / firstPlayBar.close * 100).toFixed(2));

    document.getElementById('reveal-title').innerText = `🎉 ${gameData.stock_name} (${gameData.stock_code})`;
    document.getElementById('reveal-info').innerText = `${gameData.market} · ${gameData.marcap_str} · ${gameData.trend_label}`;
    document.getElementById('reveal-period').innerText = `실제 차트 기간: ${gameData.start_date} ~ ${curBar.date}`;

    const myRetEl = document.getElementById('final-my-return');
    myRetEl.innerText = `${myReturn > 0 ? '+' : ''}${myReturn}%`;
    myRetEl.className = myReturn >= 0 ? 'plus' : 'minus';

    document.getElementById('final-bh-return').innerText = `${bhReturn > 0 ? '+' : ''}${bhReturn}%`;
    document.getElementById('result-modal-body').style.display = 'block';
    document.getElementById('result-modal').style.display = 'block';

    const record = {
        date: new Date().toLocaleString('ko-KR'),
        stock_name: `${gameData.stock_name}(${gameData.stock_code})`,
        trend: gameData.trend_label,
        my_return: myReturn,
        bh_return: bhReturn,
        period: `${gameData.start_date}~${curBar.date}`
    };
    HISTORY_DATA.unshift(record);
    try {
        await fetch('/api/save_result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '69420' },
            body: JSON.stringify(record)
        });
    } catch (e) {}
}

function toggleResultBody() {
    const body = document.getElementById('result-modal-body');
    body.style.display = (body.style.display === 'none') ? 'block' : 'none';
}

function openStatsModal() {
    const total = HISTORY_DATA.length;
    const wins = HISTORY_DATA.filter(r => r.my_return > 0).length;
    const winRate = total > 0 ? ((wins / total) * 100).toFixed(1) : '0.0';
    const avgRet = total > 0 ? (HISTORY_DATA.reduce((a, b) => a + b.my_return, 0) / total).toFixed(2) : '0.00';

    document.getElementById('stats-summary').innerHTML = `
        <div><span style="color:#8b949e;font-size:11px;">총 횟수</span><br><strong style="font-size:15px;">${total}회</strong></div>
        <div><span style="color:#8b949e;font-size:11px;">승률</span><br><strong style="font-size:15px;color:#00c471;">${winRate}%</strong></div>
        <div><span style="color:#8b949e;font-size:11px;">평균수익률</span><br><strong style="font-size:15px;" class="${avgRet >= 0 ? 'plus' : 'minus'}">${avgRet}%</strong></div>
    `;

    const tbody = document.getElementById('stats-tbody');
    tbody.innerHTML = HISTORY_DATA.map(r => `
        <tr>
            <td>${r.date.split(' ')[0]}</td>
            <td><strong>${r.stock_name}</strong></td>
            <td>${r.trend.substring(0,3)}</td>
            <td class="${r.my_return >= 0 ? 'plus' : 'minus'}"><strong>${r.my_return > 0 ? '+' : ''}${r.my_return}%</strong></td>
            <td>${r.bh_return > 0 ? '+' : ''}${r.bh_return}%</td>
        </tr>
    `).join('');
    document.getElementById('stats-modal').style.display = 'block';
}

function openMobileModal() {
    document.getElementById('mobile-modal').style.display = 'block';
}

function downloadChartImage() {
    try {
        const c1 = mainChart.takeScreenshot();
        const c2 = rsiChart.takeScreenshot();
        const out = document.createElement('canvas');
        out.width = c1.width;
        out.height = c1.height + (rsiVisible ? c2.height : 0) + 50;
        const ctx = out.getContext('2d');
        ctx.fillStyle = '#101216';
        ctx.fillRect(0, 0, out.width, out.height);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 16px sans-serif';
        const eqText = document.getElementById('total-equity').innerText;
        ctx.fillText(`${gameData.stock_name}(${gameData.stock_code}) | 자산: ${eqText}`, 16, 30);
        ctx.drawImage(c1, 0, 50);
        if (rsiVisible) ctx.drawImage(c2, 0, 50 + c1.height);

        const link = document.createElement('a');
        link.download = `차트복기_${gameData.stock_name}_${gameData.candles[curIdx].date}.png`;
        link.href = out.toDataURL('image/png');
        link.click();
    } catch (e) {
        showToast("차트 이미지 저장 실패");
    }
}

function downloadCSV() {
    if (HISTORY_DATA.length === 0) { showToast("저장할 기록이 없습니다."); return; }
    const rows = ["\uFEFF일시,종목명,배열상태,내수익률(%),존버수익률(%),실제기간"];
    HISTORY_DATA.forEach(r => {
        rows.push(`"${r.date}","${r.stock_name}","${r.trend}",${r.my_return},${r.bh_return},"${r.period}"`);
    });
    const csvContent = rows.join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = '차트게임_누적통계.csv';
    link.click();
}

function setButtonsDisabled(disabled) {
    ['b5', 'b10', 'b25', 'b50', 'b100', 'bHold', 's5', 's10', 's25', 's50', 's100'].forEach(id => {
        document.getElementById(id).disabled = disabled;
    });
}

function makeDraggable(modalId, headerId) {
    const modal = document.getElementById(modalId);
    const header = document.getElementById(headerId);
    let isDragging = false, startX = 0, startY = 0, origX = 0, origY = 0;

    function dragStart(clientX, clientY) {
        isDragging = true;
        const rect = modal.getBoundingClientRect();
        modal.style.transform = 'none';
        modal.style.left = rect.left + 'px';
        modal.style.top = rect.top + 'px';
        startX = clientX; startY = clientY;
        origX = rect.left; origY = rect.top;
    }
    function dragMove(clientX, clientY) {
        if (!isDragging) return;
        modal.style.left = (origX + clientX - startX) + 'px';
        modal.style.top = Math.max(0, origY + clientY - startY) + 'px';
    }
    header.addEventListener('mousedown', e => dragStart(e.clientX, e.clientY));
    window.addEventListener('mousemove', e => dragMove(e.clientX, e.clientY));
    window.addEventListener('mouseup', () => { isDragging = false; });

    header.addEventListener('touchstart', e => {
        const t = e.touches[0];
        dragStart(t.clientX, t.clientY);
    }, { passive: true });
    window.addEventListener('touchmove', e => {
        if (!isDragging) return;
        const t = e.touches[0];
        dragMove(t.clientX, t.clientY);
    }, { passive: true });
    window.addEventListener('touchend', () => { isDragging = false; });
}

makeDraggable('result-modal', 'result-modal-header');
makeDraggable('stats-modal', 'stats-modal-header');
makeDraggable('mobile-modal', 'mobile-modal-header');

window.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
    const modalVisible = document.getElementById('result-modal').style.display === 'block';
    if (modalVisible && e.key === 'Enter') { startNewGame(); return; }
    if (document.getElementById('bHold').disabled) return;

    if (e.code === 'Space') { e.preventDefault(); trade('HOLD', 0); }
    else if (e.key === '1') trade('BUY', 0.25);
    else if (e.key === '2') trade('BUY', 0.50);
    else if (e.key === '3') trade('BUY', 1.0);
    else if (e.key.toLowerCase() === 'a') trade('SELL', 0.50);
    else if (e.key.toLowerCase() === 's') trade('SELL', 1.0);
});

// 초기 실행 시 저장된 높이가 없으면 화면에 딱 맞게 자동 조절 후 시작
if (!localStorage.getItem('cg_main_h')) {
    setTimeout(autoFitLaptopScreen, 100);
} else {
    applyChartSizes();
}
startNewGame();
</script>
</body>
</html>
"""

app = Flask(__name__)
LOCAL_IP = get_local_ip()
MOBILE_URL = f"http://{LOCAL_IP}:5000"


@app.route("/")
def index():
    history_data = json.dumps(load_saved_history(), ensure_ascii=False)
    html_out = HTML_TEMPLATE.replace("__HISTORY_DATA__", history_data).replace("__MOBILE_URL__", MOBILE_URL)
    return Response(html_out, mimetype="text/html; charset=utf-8")


@app.route("/api/new_game")
def api_new_game():
    mode = request.args.get("mode", "bull")
    return jsonify(generate_game_data(mode))


@app.route("/api/save_result", methods=["POST"])
def api_save_result():
    record = request.get_json(silent=True)
    if record:
        append_saved_history(record)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    try:
        threading.Thread(target=load_full_krx_in_background, daemon=True).start()
        print("=" * 65)
        print("🚀 [실시간 고속 모드] 서버가 시작되었습니다!")
        print(f"🖥️ PC 접속 주소     : http://127.0.0.1:5000")
        print(f"📱 스마트폰 접속 주소: {MOBILE_URL}")
        print("=" * 65)
        threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
        app.run(host="0.0.0.0", debug=False, port=5000, threaded=True)
    except Exception:
        traceback.print_exc()
        input("\n창을 닫으려면 엔터(Enter) 키를 누르세요...")