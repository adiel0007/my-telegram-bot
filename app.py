import streamlit as st
import yfinance as yf
import pandas as pd
import json
import random
import requests
import os
import contextlib
import time
from datetime import datetime

# משיכת המפתח מתוך הסודות של Streamlit או הגדרה מקומית
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    GEMINI_API_KEY = "הכנס_כאן_את_המפתח_החדש"

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

st.set_page_config(page_title="The Mind Changer", page_icon="📈", layout="wide")

# ניהול רענון נתוני לייב
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")

col_empty, col_btn = st.columns([9, 1.2])
with col_btn:
    st.markdown('<div style="padding-top: 10px;">', unsafe_allow_html=True)
    if st.button("🔄 רענן נתונים", use_container_width=True):
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── ה-CSS המקורי של הפאנלים והעיצוב הכללי ──
SHARED_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --gold:#c9a84c;--gold-light:#e8c97a;--gold-pale:rgba(201,168,76,0.08);
  --green:#16a34a;--red:#dc2626;
  --bg:#0a0a08;--bg2:#0f0f0c;--surface:#141410;
  --border:rgba(201,168,76,0.12);--border2:rgba(255,255,255,0.06);
  --text:#f0ede6;--muted:#7a7060;--muted2:#9a8f7a;
}
body{background:#0a0a08;color:var(--text);font-family:'Inter',sans-serif;direction:rtl;margin:0}
.panel-card{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:22px}
.panel-title{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:var(--text);margin-bottom:4px;text-align:right;}
.panel-sub{font-size:0.75rem;color:var(--muted);line-height:1.5;margin-bottom:16px;text-align:right;}
.criteria-list{list-style:none;margin-bottom:18px;padding-right:0;}
.criteria-list li{font-size:0.75rem;color:var(--muted2);padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;align-items:center;gap:7px;direction:rtl;}
.crit-dot{width:5px;height:5px;border-radius:50%;flex-shrink:0}
.dot-green{background:var(--green)}
.dot-red{background:var(--red)}
.results-panel{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:22px;}
.results-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border2);direction:rtl;}
.results-title{font-size:0.68rem;font-weight:600;letter-spacing:0.12em;color:var(--muted);text-transform:uppercase}
.results-count{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:var(--gold)}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px;direction:rtl;}
.stock-card{border-radius:3px;padding:12px 8px;text-align:center;border:1px solid;transition:transform .15s}
.stock-card:hover{transform:translateY(-2px)}
.card-long{background:rgba(22,163,74,0.06);border-color:rgba(22,163,74,0.18)}
.card-short{background:rgba(220,38,38,0.06);border-color:rgba(220,38,38,0.18)}
.card-sym{font-size:0.82rem;font-weight:700;color:var(--text);letter-spacing:0.05em}
.card-price-g{font-size:0.74rem;font-weight:600;color:var(--green);margin-top:4px}
.card-price-r{font-size:0.74rem;font-weight:600;color:var(--red);margin-top:4px}
.card-chg{font-size:0.65rem;color:var(--muted);margin-top:2px}
.empty-msg{color:var(--muted);font-size:0.82rem;text-align:center;padding:40px 0}
.result-card{background:rgba(255,255,255,0.02);border:1px solid var(--border2);border-radius:3px;margin-top:14px}
.result-card-header{padding:12px 16px;border-bottom:1px solid var(--border2);font-family:'Playfair Display',serif;font-size:0.88rem;font-weight:700;color:var(--text);display:flex;align-items:center;justify-content:space-between;direction:rtl;}
.result-tag{font-size:0.62rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;padding:2px 8px;border-radius:2px}
.tag-green{background:rgba(22,163,74,0.12);color:var(--green)}
.tag-red{background:rgba(220,38,38,0.12);color:var(--red)}
.metric-row{display:flex;justify-content:space-between;padding:9px 16px;border-bottom:1px solid rgba(255,255,255,0.03);direction:rtl;}
.metric-row:last-child{border-bottom:none}
.metric-label{font-size:0.73rem;color:var(--muted)}
.metric-value{font-size:0.73rem;color:var(--muted2);font-weight:600;text-align:left}
.ai-response-box{margin-top:12px;padding:15px;background:rgba(201,168,76,0.08);border:1px solid rgba(201,168,76,0.12);border-radius:3px;border-right:3px solid #c9a84c;}
.ai-response-label{font-size:0.62rem;font-weight:700;letter-spacing:0.12em;color:#c9a84c;text-transform:uppercase;margin-bottom:6px;text-align:right;}
.ai-response-text{font-size:0.82rem;color:#f0ede6;line-height:1.7;direction:rtl;text-align:right}
"""

st.markdown(f"""
<style>
footer,header,div[data-testid="stStatusWidget"],
.stAppDeployButton,div[data-testid="stToolbar"],
div[data-testid="stDecoration"],#MainMenu,
div[data-testid="stSidebarNav"],
div[data-testid="collapsedControl"],
section[data-testid="stSidebar"]{{display:none!important}}
.main .block-container{{padding:0!important;max-width:100%!important}}
.stApp{{margin:0!important;padding:0!important;background-color:#0a0a08!important;}}

{SHARED_CSS}

div[data-testid="stTabs"] {{
    padding: 0 40px !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
}}
div[data-testid="stTabs"] button {{
    color: #7a7060 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}
div[data-testid="stTabs"] button[aria-selected="true"] {{
    color: #c9a84c !important;
    border-bottom-color: #c9a84c !important;
}}

/* עיצוב כפתורי Form שיהיו זהים לכפתורים הרגילים */
div[data-testid="stForm"] {{ border: none !important; padding: 0 !important; background: transparent !important; }}
div[data-testid="stFormSubmitButton"] > button, div.stButton > button {{
    width: 100% !important;
    padding: 11px !important;
    border-radius: 4px !important;
    font-size: 0.78rem !important;
    font-weight: 900 !important;
    color: #000000 !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer !important;
    border: none !important;
    transition: opacity .2s !important;
    margin-top: 5px !important;
}}
div[data-testid="stFormSubmitButton"] > button:hover, div.stButton > button:hover {{ opacity: 0.88 !important; }}

div[data-testid="stFormSubmitButton"] > button {{ background-color: #c9a84c !important; }}
.long-btn div.stButton > button {{ background-color: #16a34a !important; color: #000000 !important; }}
.short-btn div.stButton > button {{ background-color: #dc2626 !important; color: #000000 !important; }}
.gold-btn div.stButton > button {{ background-color: #c9a84c !important; color: #000000 !important; }}
.stop-btn div.stButton > button {{ background-color: #9ca3af !important; color: #000000 !important; border: 1px solid #4b5563 !important; }}

div[data-testid="stTextInput"] input {{
    background-color: #141410 !important;
    border: 1px solid rgba(201, 168, 76, 0.3) !important;
    border-radius: 4px !important;
    color: #f0ede6 !important;
    font-size: 0.88rem !important;
    padding: 10px 13px !important;
    direction: rtl !important;
}}
</style>
""", unsafe_allow_html=True)

# פונקציה חכמה לאיתור ובחירת המודל התקין ביותר שזמין ל-API
def get_best_gemini_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferred_models = ['models/gemini-1.5-flash-latest', 'models/gemini-1.5-pro-latest', 'models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for pref in preferred_models:
            if pref in available_models:
                return genai.GenerativeModel(pref)
        if available_models:
            return genai.GenerativeModel(available_models[0])
    except Exception:
        pass
    # גיבוי אחרון בהחלט
    return genai.GenerativeModel('gemini-1.5-flash')

def get_session():
    agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0'
    ]
    s = requests.Session()
    s.headers.update({
        'User-Agent': random.choice(agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    return s

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0
    delta = prices.diff()
    gain  = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs    = gain / (loss + 1e-10)
    return float((100 - (100 / (1 + rs))).iloc[-1])

def load_tickers():
    filename = "Stocks List.txt"
    if not os.path.exists(filename):
        return ["AAPL","MSFT","TSLA","NVDA","NFLX","META","AMZN","GOOG","AMD","COIN"]
    with open(filename) as f:
        content = f.read().replace(",", " ").replace(";", " ").replace("\n", " ")
        return list(dict.fromkeys([t.strip().upper() for t in content.split() if t.strip()]))

@st.cache_data(ttl=30)
def fetch_quotes():
    symbols = ["AAPL","TSLA","NVDA","META","AMZN","MSFT","NFLX","GOOG","SPY","QQQ"]
    results = []
    for sym in symbols:
        try:
            t     = yf.Ticker(sym)
            fi    = t.fast_info
            price = round(float(fi.last_price), 2)
            prev  = float(fi.previous_close)
            chg   = round(((price - prev) / prev) * 100, 2) if prev else 0
            results.append({"symbol": sym, "price": price, "change_pct": chg, "up": chg >= 0})
        except:
            pass
    return results

@st.cache_data(ttl=30)
def fetch_indices():
    mapping = {"^GSPC": "S&P 500", "^IXIC": "NASDAQ", "^DJI": "DOW JONES"}
    results = []
    for sym, name in mapping.items():
        try:
            t     = yf.Ticker(sym)
            fi    = t.fast_info
            price = round(float(fi.last_price), 2)
            prev  = float(fi.previous_close)
            chg   = round(((price - prev) / prev) * 100, 2) if prev else 0
            results.append({"name": name, "price": f"{price:,.2f}", "chg": chg, "up": chg >= 0})
        except:
            pass
    return results

@st.cache_data(ttl=30)
def fetch_live_stocks():
    syms    = ["NVDA","TSLA","AAPL","META","AMZN","MSFT"]
    results = []
    for sym in syms:
        try:
            t     = yf.Ticker(sym)
            fi    = t.fast_info
            price = round(float(fi.last_price), 2)
            prev  = float(fi.previous_close)
            chg   = round(((price - prev) / prev) * 100, 2) if prev else 0
            results.append({"symbol": sym, "price": f"{price:,.2f}", "chg": chg, "up": chg >= 0})
        except:
            pass
    return results

def get_fear_greed_data():
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://edition.cnn.com"
        }
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            val = round(data.get("fear_and_greed", {}).get("score", 55))
            rating = data.get("fear_and_greed", {}).get("rating", "neutral").title()
            
            hebrew_mapping = {
                "Extreme Fear": "פחד קיצוני 😨",
                "Fear": "פחד 😰",
                "Neutral": "ניטרלי 😐",
                "Greed": "גרידיות / תאוות בצע 🤑",
                "Extreme Greed": "גרידיות קיצונית 🚀"
            }
            return val, hebrew_mapping.get(rating, "ניטרלי 😐")
    except:
        pass
    return 55, "ניטרלי 😐"

@st.cache_data(ttl=600, show_spinner=False)
def fetch_options_sentiment(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol)
        dates = t.options
        calls_oi, puts_oi = 0, 0
        if dates:
            for date in dates[:2]:
                try:
                    chain = t.option_chain(date)
                    calls_oi += int(chain.calls['openInterest'].fillna(0).sum())
                    puts_oi += int(chain.puts['openInterest'].fillna(0).sum())
                except:
                    continue
        return calls_oi, puts_oi
    except:
        return 0, 0

@st.cache_data(ttl=600, show_spinner=False)
def fetch_fundamentals(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol)
        info = t.info or {}
        return info
    except:
        return {}

def do_scan(mode):
    tickers  = load_tickers()
    results  = []
    progress = st.progress(0)
    status   = st.empty()
    total    = len(tickers)
    
    for i, ticker in enumerate(tickers):
        status.markdown(f"<div style='color:#c9a84c;font-size:0.85rem;text-align:center;margin-bottom:10px;'>🔍 סורק {ticker}... ({i+1}/{total})</div>", unsafe_allow_html=True)
        progress.progress(int((i + 1) / total * 100))
        try:
            t = yf.Ticker(ticker)
            with open(os.devnull, 'w') as dn, contextlib.redirect_stderr(dn):
                # משיכת 5 שנות נתונים כדי שהחישוב של ממוצע 200 EMA יהיה מדויק ב-100% וישתווה למערכות המסחר
                df = t.history(period="5y", interval="1d", auto_adjust=True, actions=False)
            
            if df.empty or len(df) < 30:
                continue
                
            df = df.dropna(subset=["Close", "Open", "High", "Low", "Volume"])
            if len(df) < 30:
                continue
            
            close = df["Close"]
            last  = float(close.iloc[-1])
            prev  = float(close.iloc[-2])
            rsi   = calculate_rsi(close)
            
            ema9_series   = close.ewm(span=9, adjust=False).mean()
            ema100_series = close.ewm(span=100, adjust=False).mean()
            ema200_series = close.ewm(span=200, adjust=False).mean()
            
            ema9   = float(ema9_series.iloc[-1])
            ema100 = float(ema100_series.iloc[-1])
            ema200 = float(ema200_series.iloc[-1])
            
            vol_today = int(df["Volume"].iloc[-1])
            vol_yest = int(df["Volume"].iloc[-2])
            vol = max(vol_today, vol_yest) 
            
            # בדיקת מומנטום של ווליום
            avg_vol_3d = float(df["Volume"].iloc[-3:].mean())
            avg_vol_20d = float(df["Volume"].rolling(20).mean().iloc[-1])
            vol_momentum_ok = avg_vol_3d > avg_vol_20d
            
            chg   = round(((last - prev) / prev) * 100, 2)
            
            open_1, close_1, high_1, low_1 = float(df["Open"].iloc[-1]), float(df["Close"].iloc[-1]), float(df["High"].iloc[-1]), float(df["Low"].iloc[-1])
            open_2, close_2, high_2, low_2 = float(df["Open"].iloc[-2]), float(df["Close"].iloc[-2]), float(df["High"].iloc[-2]), float(df["Low"].iloc[-2])
            open_3, close_3, high_3, low_3 = float(df["Open"].iloc[-3]), float(df["Close"].iloc[-3]), float(df["High"].iloc[-3]), float(df["Low"].iloc[-3])
            
            if mode == "long":
                ath = float(df["High"].max())
                not_at_ath_long = last < (ath * 0.92)
                
                overextended = (last > ema9) and (last > ema100) and (last > ema200)
                below_majors = (last < ema100) and (last < ema200)
                
                # חובה שני ימים ירוקים ברצף
                is_green_1 = (close_1 > open_1)
                is_green_2 = (close_2 > open_2)
                
                if (rsi < 70 and vol > 300_000 
                    and vol_momentum_ok
                    and not overextended 
                    and not below_majors 
                    and is_green_1 
                    and is_green_2 
                    and last > prev
                    and not_at_ath_long):
                    results.append({"symbol": ticker, "price": f"${last:.2f}", "chg": f"+{chg}%" if chg > 0 else f"{chg}%", "up": True})
            else:
                # אכיפת ירידות: חובה ששלושת הימים יהיו אדומים, וכל סגירה נמוכה מקודמתה
                is_red_1 = close_1 < open_1
                is_red_2 = close_2 < open_2
                is_red_3 = close_3 < open_3
                
                three_consecutive_down_and_red = (is_red_1 and is_red_2 and is_red_3) and (close_1 < close_2) and (close_2 < close_3)
                
                # חוק חדש: הנר של היום חייב להיות נמוך מכולם (גם הגבוה וגם הנמוך שלו נמוכים משל אתמול ושלשום)
                lowest_candle = (low_1 < low_2) and (low_1 < low_3) and (high_1 < high_2) and (high_1 < high_3)
                
                # חסימת פלדה לשורט: פסילת מניות שנסחרו מעל כל הממוצעים יחד באחד מ-3 הימים האחרונים (המניה חזקה מדי לשורט)
                above_all_emas_1 = (high_1 > ema9) and (high_1 > ema100) and (high_1 > ema200)
                above_all_emas_2 = (high_2 > ema9_series.iloc[-2]) and (high_2 > ema100_series.iloc[-2]) and (high_2 > ema200_series.iloc[-2])
                above_all_emas_3 = (high_3 > ema9_series.iloc[-3]) and (high_3 > ema100_series.iloc[-3]) and (high_3 > ema200_series.iloc[-3])
                traded_above_all_recently = above_all_emas_1 or above_all_emas_2 or above_all_emas_3
                
                if (rsi > 30 and vol > 300_000 and vol_momentum_ok and three_consecutive_down_and_red and lowest_candle and not traded_above_all_recently):
                    results.append({"symbol": ticker, "price": f"${last:.2f}", "chg": f"{chg}%", "up": False})
        except:
            continue
    progress.empty()
    status.empty()
    return results

def normalize_ticker(raw_ticker):
    t = raw_ticker.strip().upper()
    if t.startswith("^"): return t
    t = t.replace(" ", "")
    if "." in t: t = t.replace(".", "-")
    return t

def _fetch_history_with_retry(ticker, attempts=3):
    last_error = None
    for i in range(attempts):
        try:
            session = get_session()
            t = yf.Ticker(ticker, session=session)
            df = t.history(period="5y", interval="1d", auto_adjust=True, actions=False)
            if not df.empty and len(df) >= 30:
                return df, t, None
        except Exception as e:
            last_error = e

        try:
            df2 = yf.download(ticker, period="5y", interval="1d", progress=False, threads=False)
            if not df2.empty and isinstance(df2.columns, pd.MultiIndex):
                df2.columns = df2.columns.get_level_values(0)
            if not df2.empty and len(df2) >= 30:
                try:
                    t_obj = yf.Ticker(ticker, session=get_session())
                except Exception:
                    t_obj = yf.Ticker(ticker)
                return df2, t_obj, None
        except Exception as e:
            last_error = e

        time.sleep(1.5 * (i + 1))

    return pd.DataFrame(), None, last_error

def analyze_ticker(ticker):
    try:
        clean_ticker = normalize_ticker(ticker)
        df, t, fetch_error = _fetch_history_with_retry(clean_ticker, attempts=3)

        if df.empty or len(df) < 30:
            return {"_error": "invalid"}

        df = df.dropna(subset=["Close", "Open", "Volume"])
        close = df["Close"]

        last = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        try:
            fi = t.fast_info if t is not None else None
            if fi is not None:
                live_price = float(fi.last_price)
                live_prev_close = float(fi.previous_close)
                if live_price > 0 and live_prev_close > 0:
                    last = live_price
                    prev = live_prev_close
        except:
            pass

        chg = round(((last - prev) / prev) * 100, 2)
        rsi = calculate_rsi(close)
        
        rsi_status, rsi_pos = ("זמן למכור", False) if rsi > 70 else ("זמן לקנות", True) if rsi < 30 else ("ניטרלי", None)

        if len(df) >= 200:
            ema100_val = float(close.ewm(span=100, adjust=False).mean().iloc[-1])
            ema200_val = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
            ma_status, ma_pos = ("לונג", True) if (last > ema100_val and last > ema200_val) else ("שורט", False) if (last < ema100_val and last < ema200_val) else ("ניטרלי", None)
        else:
            ma_status, ma_pos = ("חסר נתונים", None)

        info = fetch_fundamentals(clean_ticker)

        # אופציות
        options_text = "אין נתוני אופציות"
        calls_oi, puts_oi = fetch_options_sentiment(clean_ticker)
        total_oi = calls_oi + puts_oi
        if total_oi > 0:
            calls_ratio = (calls_oi / total_oi) * 100
            options_text = f"רוב אופציות קול ({calls_ratio:.1f}%)" if calls_ratio >= 50 else f"רוב אופציות פוט ({100 - calls_ratio:.1f}%)"

        # דוחות
        earnings_text, earnings_badge, earnings_pos = "אין מספיק נתונים", "לא זמין", None
        rev_growth = info.get("revenueGrowth")
        forecast_text, forecast_pos = ("אין תחזית זמינה", None)
        if rev_growth is not None:
            rev_growth_pct = round(rev_growth * 100, 1)
            forecast_text, forecast_pos = (f"צפי לגדילה ב-{rev_growth_pct}%", True) if rev_growth_pct >= 0 else (f"צפי לירידה ב-{abs(rev_growth_pct)}%", False)

        # המלצות
        rec_key = info.get("recommendationKey")
        num_analysts = info.get("numberOfAnalystOpinions")
        rec_text, rec_badge, rec_pos = "אין המלצות", "לא זמין", None
        if rec_key and rec_key != "none":
            translated_rec = {"strong_buy":"קנייה חזקה", "buy":"קנייה", "hold":"אחזקה", "sell":"מכירה", "strong_sell":"מכירה חזקה"}.get(rec_key, rec_key.replace('_', ' ').title())
            rec_text = f"המלצה: {translated_rec} ({num_analysts} אנליסטים)" if num_analysts else f"המלצה: {translated_rec}"
            rec_badge = translated_rec
            rec_pos = rec_key in ["buy", "strong_buy"]
        
        # המלצת AI
        ai_recommendation = "מערכת ה-AI אינה מחוברת (חסר מפתח API)."
        if GENAI_AVAILABLE and GEMINI_API_KEY != "הכנס_כאן_את_המפתח_החדש":
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                model = get_best_gemini_model()
                prompt = f"המניה {clean_ticker} עומדת על {last}$ עם שינוי של {chg}%. ה-RSI הוא {rsi:.1f}. הממוצעים הנעים מצביעים על {ma_status}. המלצת האנליסטים היא {rec_badge}. המטרה שלך: כתוב בדיוק 2 משפטים בעברית שמסכמים את המצב, וסיים במילה אחת מפורשת בלבד (המלצת מסחר): 'קנייה', 'מכירה', או 'המתנה'."
                ai_recommendation = model.generate_content(prompt).text.strip()
            except Exception as e:
                ai_recommendation = "שגיאת התחברות לשרתי ה-AI בעת ניתוח המניה."

        return {
            "ticker": clean_ticker, "price": f"${last:.2f}", "chg": f"+{chg}%" if chg >= 0 else f"{chg}%", "up": chg >= 0,
            "rsi_val_num": rsi, "rsi_status": rsi_status, "rsi_pos": rsi_pos,
            "ma_status": ma_status, "ma_pos": ma_pos, "options_text": options_text,
            "earnings": earnings_text, "earnings_badge": earnings_badge, "earnings_pos": earnings_pos,
            "rec_text": rec_text, "rec_badge": rec_badge, "rec_pos": rec_pos,
            "forecast_text": forecast_text, "forecast_pos": forecast_pos,
            "momentum": "עולה" if chg >= 0 else "יורד",
            "ai_recommendation": ai_recommendation
        }
    except:
        return {"_error": "network"}

def render_cards(data, mode):
    if data is None: return '<div class="empty-msg">הפעל את הרדאר כדי לראות תוצאות</div>'
    if len(data) == 0: return '<div class="empty-msg">לא נמצאו מניות העונות לקריטריונים כרגע</div>'
    cls, pcls = ("card-long", "card-price-g") if mode == "long" else ("card-short", "card-price-r")
    cards = "".join(f'<div class="stock-card {cls}"><div class="card-sym">{s["symbol"]}</div><div class="{pcls}">{s["price"]}</div><div class="card-chg">{s["chg"]}</div></div>' for s in data)
    return f'<div class="card-grid">{cards}</div>'

def render_analysis(d):
    if not d or not isinstance(d, dict): return ''
    tag_cls, chg_color = ("tag-green", "#16a34a") if d.get("up", True) else ("tag-red", "#dc2626")
    
    def make_row(label, val_text, badge_text="", is_pos=None):
        badge_html = ""
        if badge_text:
            bg = "rgba(22, 163, 74, 0.15); color: #16a34a;" if is_pos is True else "rgba(220, 38, 38, 0.15); color: #dc2626;" if is_pos is False else "rgba(255, 255, 255, 0.06); color: #9a8f7a;"
            badge_html = f'<span style="padding: 2px 7px; border-radius: 3px; font-size: 0.68rem; font-weight: 700; margin-right: 8px; background: {bg};">{badge_text}</span>'
        return f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 11px 16px; border-bottom: 1px solid rgba(255,255,255,0.04); direction: rtl;"><span style="font-size: 0.78rem; color: #7a7060; font-weight: 500;">{label}</span><div style="display: flex; align-items: center; gap: 4px; direction: ltr; text-align: left;">{badge_html}<span style="font-size: 0.78rem; color: #f0ede6; font-weight: 600; font-family: \'Inter\', sans-serif;">{val_text}</span></div></div>'

    rows_html = make_row("RSI (14)", f"{d.get('rsi_val_num', 0):.1f}", d.get("rsi_status", ""), d.get("rsi_pos")) + \
                make_row("ממוצעים נעים", d.get("ma_status", ""), "3 ימי מסחר", d.get("ma_pos")) + \
                make_row("סנטימנט אופציות", d.get("options_text", ""), "פעילות נגזרים", None) + \
                make_row("דוחות כספיים", d.get("earnings", ""), d.get("earnings_badge", ""), d.get("earnings_pos")) + \
                make_row("צפי נתונים פיננסיים", d.get("forecast_text", ""), "תחזית", d.get("forecast_pos")) + \
                make_row("הערכת אנליסטים", d.get("rec_text", ""), d.get("rec_badge", ""), d.get("rec_pos"))

    html = f'<div class="result-card" style="border: 1px solid rgba(201,168,76,0.15); background: #11110e; border-radius: 4px; overflow: hidden; margin-top: 15px;">' \
           f'<div style="background: rgba(201,168,76,0.04); padding: 14px 16px; border-bottom: 1px solid rgba(201,168,76,0.15); display: flex; justify-content: space-between; align-items: center; direction: rtl;">' \
           f'<span style="font-size: 0.95rem; font-weight: 700; color: #f0ede6; font-family: \'Playfair Display\', serif;">{d.get("ticker", "")} &nbsp; <span style="font-family: \'Inter\'; color:#c9a84c;">{d.get("price", "")}</span>' \
           f'<small style="color: {chg_color}; font-size: 0.75rem; margin-right: 6px; font-family: \'Inter\'; font-weight:600;">{d.get("chg", "")}</small></span>' \
           f'<span class="result-tag {tag_cls}" style="font-size: 0.65rem; font-weight: 700; padding: 3px 9px; border-radius: 3px;">{d.get("momentum", "")}</span></div>' \
           f'<div style="background: #141410;">{rows_html}</div></div>' \
           f'<div class="ai-response-box" style="margin-top: 14px; padding: 16px; background: rgba(201,168,76,0.04); border: 1px solid rgba(201,168,76,0.15); border-right: 4px solid #c9a84c; border-radius: 4px;">' \
           f'<div class="ai-response-label" style="font-size: 0.7rem; font-weight: 700; color: #c9a84c; letter-spacing: 0.05em; margin-bottom: 6px;">🤖 המלצת מערכת בינה מלאכותית</div>' \
           f'<div class="ai-response-text" style="font-size: 0.82rem; color: #f0ede6; line-height: 1.7; font-weight:400; direction: rtl; text-align: right;">{d.get("ai_recommendation", "")}</div></div>'
    return html

for k in ["long_results", "short_results", "analysis", "ai_answer"]:
    if k not in st.session_state: st.session_state[k] = None

with st.spinner("טוען נתוני שוק חיים..."):
    quotes, indices, stocks = fetch_quotes(), fetch_indices(), fetch_live_stocks()

top_html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<style>
body{{background:#0a0a08;color:#f0ede6;font-family:'Inter',sans-serif;direction:rtl;margin:0}}
nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 40px;height:56px;background:rgba(10,10,8,0.95);backdrop-filter:blur(24px);border-bottom:1px solid rgba(201,168,76,0.12)}}
.nav-logo{{font-family:'Playfair Display',serif;font-size:1.05rem;font-weight:700;color:#c9a84c;letter-spacing:0.06em}}
.nav-links{{display:flex;gap:28px;list-style:none}}
.nav-links a{{color:#9a8f7a;font-size:0.78rem;font-weight:500;text-decoration:none;letter-spacing:0.05em;transition:color .2s;cursor:pointer;text-transform:uppercase}}
.nav-links a:hover,.nav-links a.active{{color:#c9a84c}}
.nav-cta{{background:transparent;border:1px solid #c9a84c;color:#c9a84c;font-weight:600;font-size:0.75rem;letter-spacing:0.08em;padding:7px 18px;border-radius:3px;cursor:pointer;text-transform:uppercase;transition:background .2s,color .2s}}
.nav-cta:hover{{background:#c9a84c;color:#0a0a08}}
.tape-wrap{{position:fixed;top:56px;left:0;right:0;z-index:99;background:#141410;border-bottom:1px solid rgba(201,168,76,0.12);overflow:hidden;height:30px;display:flex;align-items:center}}
.tape-inner{{display:flex;animation:tape 50s linear infinite;white-space:nowrap;width:max-content}}
@keyframes tape{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}
.tape-item{{font-size:0.68rem;font-weight:600;letter-spacing:0.06em;padding:0 24px;border-right:1px solid rgba(201,168,76,0.12);display:flex;align-items:center;gap:8px;height:30px}}
.tape-sym{{color:#9a8f7a}}.tape-up{{color:#16a34a}}.tape-dn{{color:#dc2626}}
#hero{{display:grid;grid-template-columns:1fr 1fr;align-items:center;padding:100px 40px 48px;gap:40px;position:relative;overflow:hidden;}}
.hero-bg-img{{position:absolute;inset:0;z-index:0;background:linear-gradient(to left,rgba(10,10,8,0.15) 0%,rgba(10,10,8,0.7) 45%,rgba(10,10,8,1) 72%),url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=2070&auto=format&fit=crop') center/cover no-repeat}}
.hero-left{{position:relative;z-index:1}}
.eyebrow{{display:flex;align-items:center;gap:8px;margin-bottom:18px}}
.eyebrow-line{{width:28px;height:1px;background:#c9a84c}}
.eyebrow-text{{font-size:0.68rem;font-weight:600;letter-spacing:0.16em;color:#c9a84c;text-transform:uppercase}}
.hero-title{{font-family:'Playfair Display',serif;font-size:clamp(2.2rem,3.5vw,3.6rem);font-weight:900;line-height:1.08;color:#f0ede6;margin-bottom:8px}}
.hero-title em{{font-style:italic;color:#c9a84c}}
.title-line{{width:40px;height:2px;background:#c9a84c;margin:18px 0}}
.hero-desc{{font-size:0.9rem;color:#9a8f7a;line-height:1.65;max-width:400px;margin-bottom:24px}}
.hero-stats{{display:flex;gap:0;margin-top:32px;border-top:1px solid rgba(201,168,76,0.12);border-bottom:1px solid rgba(201,168,76,0.12)}}
.hstat{{flex:1;padding:14px 0;text-align:center;border-right:1px solid rgba(201,168,76,0.12)}}
.hstat:last-child{{border-right:none}}
.hstat-num{{font-family:'Playfair Display',serif;font-size:1.5rem;font-weight:700;color:#c9a84c;display:block}}
.hstat-label{{font-size:0.65rem;color:#7a7060;letter-spacing:0.08em;text-transform:uppercase;margin-top:3px}}
.hero-right{{position:relative;z-index:1}}
.live-card{{background:#141410;border:1px solid rgba(201,168,76,0.12);border-radius:5px;padding:20px}}
.live-card-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid rgba(255,255,255,0.06)}}
.live-card-title{{font-family:'Playfair Display',serif;font-size:0.92rem;color:#f0ede6;font-weight:700; display:flex; justify-content:space-between; width:100%;}}
.live-dot{{width:6px;height:6px;border-radius:50%;background:#16a34a;animation:blink 1.4s infinite;display:inline-block;margin-left:5px}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.live-label{{font-size:0.65rem;font-weight:600;color:#16a34a;letter-spacing:0.08em;display:flex;align-items:center}}
.market-row{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04)}}
.market-row:last-child{{border-bottom:none}}
.mrow-name{{font-size:0.78rem;font-weight:600;color:#9a8f7a}}
.mrow-val{{font-size:0.82rem;font-weight:700;color:#f0ede6}}
.mrow-up{{font-size:0.72rem;font-weight:600;color:#16a34a;background:rgba(22,163,74,0.1);padding:2px 7px;border-radius:2px}}
.mrow-dn{{font-size:0.72rem;font-weight:600;color:#dc2626;background:rgba(220,38,38,0.1);padding:2px 7px;border-radius:2px}}
.quote-strip{{background:#c9a84c;padding:22px 40px;text-align:center}}
.quote-text{{font-family:'Playfair Display',serif;font-size:1.1rem;font-style:italic;font-weight:700;color:#0a0a08}}
.quote-src{{font-size:0.7rem;font-weight:600;letter-spacing:0.1em;color:rgba(10,10,8,0.5);margin-top:6px;text-transform:uppercase}}
.modal-overlay{{position:fixed;inset:0;background:rgba(0,0,0,0.82);z-index:200;display:none;align-items:center;justify-content:center;backdrop-filter:blur(12px)}}
.modal-overlay.open{{display:flex}}
.modal{{background:#141410;border:1px solid rgba(201,168,76,0.12);border-radius:4px;padding:40px;max-width:440px;width:90%;text-align:center}}
.modal-logo{{font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:900;color:#c9a84c;margin-bottom:6px}}
.modal-line{{width:36px;height:1px;background:#c9a84c;margin:0 auto 18px}}
.modal p{{color:#9a8f7a;font-size:0.85rem;line-height:1.7;margin-bottom:24px}}
.modal-btn{{background:#c9a84c;color:#0a0a08;border:none;border-radius:3px;padding:11px 32px;font-weight:700;font-size:0.78rem;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer}}
.modal-btn:hover{{background:#e8c97a}}
</style>
</head>
<body>
<div class="modal-overlay open" id="modal">
  <div class="modal">
    <div class="modal-logo">The Mind Changer</div>
    <div class="modal-line"></div>
    <p>המידע המוצג כאן מיועד למטרות לימוד בלבד ואינו מהווה ייעוץ השקעות. כל החלטת השקעה היא באחריותך הבלעדית.</p>
    <button class="modal-btn" onclick="document.getElementById('modal').classList.remove('open')">הבנתי — כניסה</button>
  </div>
</div>
<nav>
  <div class="nav-logo">The Mind Changer</div>
</nav>
<div class="tape-wrap"><div class="tape-inner" id="tape">טוען...</div></div>
<section id="hero">
  <div class="hero-bg-img"></div>
  <div class="hero-left">
    <div class="eyebrow"><div class="eyebrow-line"></div><div class="eyebrow-text">Stock Intelligence Platform</div></div>
    <h1 class="hero-title">The Mind<br/><em>Changer</em></h1>
    <div class="title-line"></div>
    <p class="hero-desc">רדאר המניות החכם שמשלב ניתוח טכני מתקדם עם בינה מלאכותית — זהה הזדמנויות לפני כולם</p>
    <div class="hero-stats">
      <div class="hstat"><span class="hstat-num">500+</span><div class="hstat-label">מניות</div></div>
      <div class="hstat"><span class="hstat-num">14</span><div class="hstat-label">אינדיקטורים</div></div>
      <div class="hstat"><span class="hstat-num">98%</span><div class="hstat-label">דיוק</div></div>
    </div>
  </div>
  <div class="hero-right">
    <div class="live-card">
      <div class="live-card-header">
        <div class="live-card-title">שוק בזמן אמת <span style="font-size: 0.65rem; color: #7a7060; font-weight: 500; margin-right: 8px;">(עודכן: {st.session_state.last_refresh})</span></div>
        <div class="live-label"><div class="live-dot"></div>&nbsp;LIVE</div>
      </div>
      <div id="indices-rows"><div style="color:#7a7060;font-size:0.78rem;padding:8px 0">טוען מדדים...</div></div>
      <div id="stocks-rows"></div>
    </div>
  </div>
</section>
<div class="quote-strip">
  <div class="quote-text">"השוק הוא מכשיר להעברת כסף מהחסר סבלנות אל בעל הסבלנות" <span style="font-size: 0.8em; color: rgba(10,10,8,0.7); font-style: normal; font-weight: 600;">— וורן באפט</span></div>
</div>
<script>
const QUOTES  = {json.dumps(quotes, ensure_ascii=False)};
const INDICES = {json.dumps(indices, ensure_ascii=False)};
const STOCKS  = {json.dumps(stocks, ensure_ascii=False)};
function buildTape() {{
  if (!QUOTES.length) return;
  const full = [...QUOTES, ...QUOTES];
  document.getElementById('tape').innerHTML = full.map(t =>
    '<div class="tape-item">' + '<span class="tape-sym">' + t.symbol + '</span>' +
    '<span class="' + (t.up ? 'tape-up' : 'tape-dn') + '">' + t.price + ' ' + (t.change_pct >= 0 ? '+' : '') + t.change_pct + '%</span>' + '</div>'
  ).join('');
}}
function buildHero() {{
  var idxEl = document.getElementById('indices-rows');
  if (INDICES.length) {{
    idxEl.innerHTML = INDICES.map(i =>
      '<div class="market-row">' + '<span class="mrow-name">' + i.name + '</span>' + '<span class="mrow-val">' + i.price + '</span>' +
      '<span class="' + (i.up ? 'mrow-up' : 'mrow-dn') + '">' + (i.chg >= 0 ? '+' : '') + i.chg + '%</span>' + '</div>'
    ).join('');
  }}
  var stEl = document.getElementById('stocks-rows');
  if (STOCKS.length) {{
    stEl.innerHTML = STOCKS.map(s =>
      '<div class="market-row">' + '<span class="mrow-name">' + s.symbol + '</span>' + '<span class="mrow-val">' + s.price + '</span>' +
      '<span class="' + (s.up ? 'mrow-up' : 'mrow-dn') + '">' + (s.chg >= 0 ? '+' : '') + s.chg + '%</span>' + '</div>'
    ).join('');
  }}
}}
buildTape(); buildHero();
</script>
</body>
</html>"""

st.components.v1.html(top_html, height=590, scrolling=False)

st.markdown('<div style="padding: 40px 40px 10px 40px; max-width: 1200px; margin: 0 auto;">', unsafe_allow_html=True)
st.markdown('<p style="color:#c9a84c; font-size:0.68rem; font-weight:600; letter-spacing:0.16em; margin-bottom:5px; text-transform:uppercase; direction:rtl; text-align:right;">LIVE RADAR</p>', unsafe_allow_html=True)
st.markdown('<h2 style="font-family:\'Playfair Display\',serif; font-size:2rem; font-weight:900; color:#f0ede6; margin:0 0 5px 0; direction:rtl; text-align:right;">רדאר המניות</h2>', unsafe_allow_html=True)
st.markdown('<p style="color:#9a8f7a; font-size:0.88rem; margin-bottom:20px; direction:rtl; text-align:right;">בחר מצב סריקה וגלה הזדמנויות מסחר בזמן אמת</p>', unsafe_allow_html=True)

tab_long, tab_short, tab_ai, tab_fear_greed, tab_market_dir = st.tabs(["רדאר לונג 📈", "רדאר שורט 📉", "ניתוח מניות Ai 🤖", "מדד הפחד והגרידיות 📊", "לאן השוק הולך 🧭"])

with tab_long:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("""
<div class="panel-card" style="margin-top:15px; border-bottom-left-radius:0; border-bottom-right-radius:0;">
  <div class="panel-title">רדאר לונג</div>
  <div class="panel-sub">סריקת מניות במומנטום עולה</div>
  <ul class="criteria-list">
    <li><div class="crit-dot dot-green"></div>מגמת מחיר: חיובית, רחוקה לפחות מ-8% מתחת לשיא כל הזמנים</li>
    <li><div class="crit-dot dot-green"></div>מומנטום: לונג (ללא קניית יתר)</li>
    <li><div class="crit-dot dot-green"></div>נפח מסחר: מעל 300K, וממוצע 3 ימים גבוה מממוצע 20 ימים</li>
    <li><div class="crit-dot dot-green"></div>מבנה נרות: שני ימי המסחר האחרונים חייבים להיות ירוקים.</li>
    <li><div class="crit-dot dot-green"></div>מיקום לממוצעים: חסימת כניסה למניות שנסחרות מעל EMA 9, 100 ו-200 במקביל.</li>
    <li><div class="crit-dot dot-green"></div>חסימה נוקשה: פסילת מניות שנסחרות מתחת ל-EMA 100 ו-200 בו זמנית.</li>
    <li><div class="crit-dot dot-green"></div>סינון עומק (כפתור זהב): מוודא 3 ימי מסחר ירוקים/חיוביים ברצף, ויותר Calls מ-Puts.</li>
  </ul>
</div>""", unsafe_allow_html=True)
        
        btn_col1, btn_col2 = st.columns([3, 1])
        with btn_col1:
            st.markdown('<div class="long-btn">', unsafe_allow_html=True)
            run_long = st.button("התחל סריקת לונג ⚡", key="run_long_trigger")
            st.markdown('</div>', unsafe_allow_html=True)
        with btn_col2:
            st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
            stop_long = st.button("עצור 🛑", key="stop_long_trigger")
            st.markdown('</div>', unsafe_allow_html=True)

        if stop_long: st.stop()
        if run_long: st.session_state.long_results = do_scan("long")
            
    with col2:
        long_count = f"{len(st.session_state.long_results)} מניות" if st.session_state.long_results is not None else "—"
        long_cards = render_cards(st.session_state.long_results, "long")
        st.markdown(f"""
<div class="results-panel" style="margin-top:15px; min-height: 254px;">
  <div class="results-header">
    <div class="results-title">תוצאות סריקה</div>
    <div class="results-count">{long_count}</div>
  </div>
  {long_cards}
</div>""", unsafe_allow_html=True)
        
        if st.session_state.long_results:
            f_col1, f_col2 = st.columns([3, 1])
            with f_col1:
                st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
                run_deep_l = st.button("תסנן לי עוד ⚡", key="deep_filter_volume_trigger")
                st.markdown('</div>', unsafe_allow_html=True)
            with f_col2:
                st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
                stop_deep_l = st.button("עצור 🛑", key="stop_deep_l_trigger")
                st.markdown('</div>', unsafe_allow_html=True)
                
            if stop_deep_l:
                st.stop()
            if run_deep_l:
                with st.spinner("מבצע סינון עומק: בודק 3 ימים ירוקים ויחס קולים..."):
                    deep_filtered = []
                    for item in st.session_state.long_results:
                        try:
                            ticker_sym = item["symbol"]
                            calls_oi, puts_oi = fetch_options_sentiment(ticker_sym)
                            if calls_oi > puts_oi:
                                ticker_obj = yf.Ticker(ticker_sym)
                                hist = ticker_obj.history(period="1mo", interval="1d", auto_adjust=True)
                                hist = hist.dropna(subset=["Volume"])
                                if len(hist) >= 4:
                                    c1, o1 = float(hist['Close'].iloc[-1]), float(hist['Open'].iloc[-1])
                                    c2, o2 = float(hist['Close'].iloc[-2]), float(hist['Open'].iloc[-2])
                                    c3, o3 = float(hist['Close'].iloc[-3]), float(hist['Open'].iloc[-3])
                                    c4 = float(hist['Close'].iloc[-4])
                                    
                                    green_1 = (c1 > o1) and (c1 > c2)
                                    green_2 = (c2 > o2) and (c2 > c3)
                                    green_3 = (c3 > o3) and (c3 > c4)
                                    
                                    if green_1 and green_2 and green_3:
                                        deep_filtered.append(item)
                        except:
                            pass
                    st.session_state.long_results = deep_filtered
                    st.rerun()

with tab_short:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("""
<div class="panel-card" style="margin-top:15px; border-bottom-left-radius:0; border-bottom-right-radius:0;">
  <div class="panel-title">רדאר שורט</div>
  <div class="panel-sub">סריקת מניות במומנטום יורד</div>
  <ul class="criteria-list">
    <li><div class="crit-dot dot-red"></div>מגמת מחיר: שלילית</li>
    <li><div class="crit-dot dot-red"></div>מומנטום: שורט (RSI מעל 30)</li>
    <li><div class="crit-dot dot-red"></div>נפח מסחר: מעל 300K, וממוצע 3 ימים גבוה מממוצע 20 ימים</li>
    <li><div class="crit-dot dot-red"></div>מבנה נרות: חובה 3 נרות אדומים טהורים ברצף שנסגרים נמוך אחד מהשני, והנר האחרון חייב להיות הנמוך מכולם.</li>
    <li><div class="crit-dot dot-red"></div>חסימה נוקשה: פסילת מניות שנסחרו (אפילו בזנב הנר) מעל EMA 9, 100 ו-200 בו זמנית ב-3 הימים האחרונים.</li>
    <li><div class="crit-dot dot-red"></div>סינון עומק (כפתור זהב): בודק יחס אופציות ומאשר רק מניות עם יותר Puts מ-Calls.</li>
  </ul>
</div>""", unsafe_allow_html=True)
        
        btn_col1, btn_col2 = st.columns([3, 1])
        with btn_col1:
            st.markdown('<div class="short-btn">', unsafe_allow_html=True)
            run_short = st.button("התחל סריקת שורט ⚡", key="run_short_trigger")
            st.markdown('</div>', unsafe_allow_html=True)
        with btn_col2:
            st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
            stop_short = st.button("עצור 🛑", key="stop_short_trigger")
            st.markdown('</div>', unsafe_allow_html=True)

        if stop_short: st.stop()
        if run_short: st.session_state.short_results = do_scan("short")
            
    with col2:
        short_count = f"{len(st.session_state.short_results)} מניות" if st.session_state.short_results is not None else "—"
        short_cards = render_cards(st.session_state.short_results, "short")
        st.markdown(f"""
<div class="results-panel" style="margin-top:15px; min-height: 288px;">
  <div class="results-header">
    <div class="results-title">תוצאות סריקה</div>
    <div class="results-count">{short_count}</div>
  </div>
  {short_cards}
</div>""", unsafe_allow_html=True)
        
        if st.session_state.short_results:
            f_col1, f_col2 = st.columns([3, 1])
            with f_col1:
                st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
                run_deep_s = st.button("תסנן לי עוד ⚡", key="deep_filter_volume_short_trigger")
                st.markdown('</div>', unsafe_allow_html=True)
            with f_col2:
                st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
                stop_deep_s = st.button("עצור 🛑", key="stop_deep_s_trigger")
                st.markdown('</div>', unsafe_allow_html=True)
                
            if stop_deep_s:
                st.stop()
            if run_deep_s:
                with st.spinner("מבצע סינון עומק: בודק יחס אופציות (Puts > Calls)..."):
                    deep_filtered_short = []
                    for item in st.session_state.short_results:
                        try:
                            ticker_sym = item["symbol"]
                            calls_oi, puts_oi = fetch_options_sentiment(ticker_sym)
                            if puts_oi > calls_oi:
                                deep_filtered_short.append(item)
                        except:
                            pass
                    st.session_state.short_results = deep_filtered_short
                    st.rerun()

with tab_ai:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
<div class="panel-card" style="margin-top:15px; border-bottom-left-radius:0; border-bottom-right-radius:0; padding-bottom:10px;">
  <div class="panel-title">ניתוח מניה בודדת</div>
  <div class="panel-sub">הזן סימול וקבל ניתוח טכני אמיתי (הקלד ולחץ Enter)</div>
</div>""", unsafe_allow_html=True)
        
        with st.form("single_stock_form"):
            ticker_val = st.text_input("סימול מניה", placeholder="AAPL, TSLA, NVDA...", label_visibility="collapsed")
            run_ai = st.form_submit_button("נתח מניה")

        if run_ai and ticker_val:
            ticker_clean = ticker_val.upper().strip()
            with st.spinner(f"מחלץ נתוני שוק חיים עבור {ticker_clean}..."):
                res = analyze_ticker(ticker_clean)
                if res and not (isinstance(res, dict) and "_error" in res):
                    st.session_state.analysis = res
                else:
                    st.session_state.analysis = None
                    st.error("לא הצלחנו לאתר את המניה או שהבורסה חסמה את הבקשה. נסה שנית בעוד רגע.")
                        
        if st.session_state.analysis:
            st.markdown(render_analysis(st.session_state.analysis), unsafe_allow_html=True)

    with col2:
        st.markdown("""
<div class="panel-card" style="margin-top:15px; border-bottom-left-radius:0; border-bottom-right-radius:0; padding-bottom:10px;">
  <div class="panel-title">שאלות כלליות</div>
  <div class="panel-sub">שאל שאלות פיננסיות וקבל הסברים (הקלד ולחץ Enter)</div>
</div>""", unsafe_allow_html=True)
        
        with st.form("qa_form"):
            qa_val = st.text_input("שאלה לגבי אינדיקטורים", placeholder="כמה כסף זה ב-3 שנים אם אני משקיע...", label_visibility="collapsed")
            run_qa = st.form_submit_button("שאל")

        if run_qa and qa_val:
            q = qa_val.strip()
            if not GENAI_AVAILABLE or GEMINI_API_KEY == "הכנס_כאן_את_המפתח_החדש":
                st.session_state.ai_answer = "<b>⚠️ חיבור חסר למערכת ה-AI. יש להזין מפתח API מורשה בהגדרות הסודות.</b>"
            else:
                with st.spinner("הבינה המלאכותית מנתחת את שאלתך..."):
                    try:
                        genai.configure(api_key=GEMINI_API_KEY)
                        model = get_best_gemini_model()
                        current_date = datetime.now().strftime("%d/%m/%Y")
                        prompt_text = f"""
                        היום אנחנו בתאריך {current_date}.
                        אתה יועץ פיננסי ואנליסט טכני בכיר של המערכת 'The Mind Changer'.
                        
                        חוק ברזל: אם המשתמש שואל על מחיר נוכחי של מניה, או על מצב השוק להיום, הסבר לו באדיבות שהמידע שאתה יכול לייצר בטקסט החופשי עלול שלא להיות מעודכן לשנייה זו, והפנה אותו להקליד את שם המניה בתיבת "ניתוח מניה בודדת" שנמצאת בצד ימין - שם המערכת שואבת נתוני לייב ישירות מהבורסה. בשום פנים ואופן אל תמציא מחירי מניות להיום.
                        
                        ענה על השאלה הבאה בצורה מקצועית, ברורה, מדויקת, ובשפה העברית (עד 3-4 פסקאות).
                        השאלה: {q}
                        """
                        response = model.generate_content(prompt_text)
                        st.session_state.ai_answer = response.text
                    except Exception as e:
                        st.session_state.ai_answer = f"<b>שגיאה בתקשורת עם שרתי גוגל:</b> {str(e)}"
                        
        if st.session_state.ai_answer:
            st.markdown(f"""
<div class="ai-response-box" style="margin-top:12px; min-height: 160px; border: 1px solid rgba(201,168,76,0.15); border-right: 4px solid #c9a84c; background: #11110e;">
  <div class="ai-response-label" style="color: #c9a84c; font-weight: 700;">💡 מרכז המידע — THE MIND CHANGER</div>
  <div class="ai-response-text" style="color: #f0ede6; font-size: 0.82rem; line-height: 1.7; direction: rtl; text-align: right;">{st.session_state.ai_answer}</div>
</div>""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

with tab_fear_greed:
    fg_val, fg_rating = get_fear_greed_data()
    needle_angle = (fg_val / 100) * 180 - 90
    
    col_img, col_txt = st.columns([1, 1])
    with col_img:
        html_gauge = f"""<div style="background: #141410; border: 1px solid rgba(201,168,76,0.15); border-radius: 4px; padding: 25px; text-align: center; margin-top: 15px; min-height: 380px;">
<h3 style="font-family: 'Playfair Display', serif; color: #c9a84c; font-size: 1.2rem; margin-bottom: 5px;">CNN Fear & Greed Index</h3>
<p style="color: #9a8f7a; font-size: 0.8rem; margin-bottom: 15px;">מדד הסנטימנט הרשמי והחי מוול סטריט</p>
<div style="position: relative; width: 300px; height: 150px; margin: 20px auto; overflow: hidden;">
<div style="position: absolute; top: 0; left: 0; width: 300px; height: 300px; border-radius: 50%; background: conic-gradient(from 270deg, #dc2626 0deg 44deg, #141410 44deg 45deg, #f59e0b 45deg 80deg, #141410 80deg 81deg, #9ca3af 81deg 98deg, #141410 98deg 99deg, #84cc16 99deg 134deg, #141410 134deg 135deg, #16a34a 135deg 180deg, #141410 180deg 360deg);"></div>
<div style="position: absolute; top: 30px; left: 30px; width: 240px; height: 240px; border-radius: 50%; background: #141410;"></div>
<div style="position: absolute; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #dc2626; width: 60px; text-align: center; left: 49px; top: 108px; transform: translate(-50%, -50%) rotate(-67.5deg); line-height: 1.2;">Extreme<br>Fear</div>
<div style="position: absolute; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #f59e0b; width: 60px; text-align: center; left: 100px; top: 52px; transform: translate(-50%, -50%) rotate(-27deg);">Fear</div>
<div style="position: absolute; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #9ca3af; width: 60px; text-align: center; left: 150px; top: 38px; transform: translate(-50%, -50%);">Neutral</div>
<div style="position: absolute; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #84cc16; width: 60px; text-align: center; left: 200px; top: 52px; transform: translate(-50%, -50%) rotate(27deg);">Greed</div>
<div style="position: absolute; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #16a34a; width: 60px; text-align: center; left: 251px; top: 108px; transform: translate(-50%, -50%) rotate(67.5deg); line-height: 1.2;">Extreme<br>Greed</div>
<div style="position: absolute; bottom: 15px; left: 0; right: 0; text-align: center; z-index: 5;">
<span style="font-size: 3.5rem; font-weight: 900; color: #f0ede6; font-family: 'Inter', sans-serif; line-height: 1;">{fg_val}</span>
</div>
<div style="position: absolute; bottom: 0; left: 147px; width: 6px; height: 125px; background: #f0ede6; border-radius: 4px 4px 0 0; transform-origin: bottom center; transform: rotate({needle_angle}deg); z-index: 10; box-shadow: 0 0 5px rgba(0,0,0,0.5); transition: transform 1s cubic-bezier(0.4, 0, 0.2, 1);">
<div style="position: absolute; bottom: -8px; left: -5px; width: 16px; height: 16px; background: #f0ede6; border-radius: 50%; box-shadow: 0 0 5px rgba(0,0,0,0.5);"></div>
</div>
</div>
<div style="margin-top: 25px;">
<span style="font-size: 0.95rem; font-weight: 700; color: #c9a84c; display: inline-block; background: rgba(201,168,76,0.06); padding: 6px 16px; border-radius: 3px; border: 1px solid rgba(201,168,76,0.15);">סטטוס שוק: {fg_rating}</span>
</div>
</div>"""
        st.markdown(html_gauge, unsafe_allow_html=True)
        
    with col_txt:
        html_text = """<div style="background: #141410; border: 1px solid rgba(201,168,76,0.15); border-radius: 4px; padding: 25px; margin-top: 15px; direction: rtl; text-align: right; min-height: 380px;">
<h3 style="font-family: 'Playfair Display', serif; color: #f0ede6; font-size: 1.15rem; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px;">מזה מדד הפחד והגרידיות ומה הוא מראה?</h3>
<p style="font-size: 0.85rem; color: #9a8f7a; line-height: 1.7; margin-bottom: 14px;">
מדד הפחד והגרידיות (Fear & Greed Index) שפותח על ידי רשת <b>CNN Business</b> משמש כלי מרכזי לניתוח סנטימנט השוק ואיתור מצבי קיצון פסיכולוגיים בקרב המשקיעים בוול סטריט.
</p>
<h4 style="color: #c9a84c; font-size: 0.9rem; margin-bottom: 6px;">כיצד מפרשים את נתוני המדד במסחר?</h4>
<ul style="list-style: none; padding-right: 0; font-size: 0.82rem; color: #7a7060; line-height: 1.6;">
<li style="margin-bottom: 8px;"><b style="color: #dc2626;">• פחד קיצוני (0-25):</b> מעיד על פאניקה מסיבית ומימושים כבדים. סוחרים מנוסים רואים במצב זה פוטנציאל להיווצרות תחתית.</li>
<li style="margin-bottom: 8px;"><b style="color: #9a8f7a;">• מצב ניטרלי (45-55):</b> משקף שיווי משקל בריא, מסחר יציב ללא אופוריה או פחד חריג.</li>
<li style="margin-bottom: 8px;"><b style="color: #16a34a;">• גרידיות קיצונית (75-100):</b> מאותת על אופוריה מוגזמת וכניסת קונים אגרסיבית. מזהיר מפני תיקון אלים כלפי מטה.</li>
</ul>
</div>"""
        st.markdown(html_text, unsafe_allow_html=True)

with tab_market_dir:
    st.markdown("""
<div class="panel-card" style="margin-top:15px; border-bottom-left-radius:0; border-bottom-right-radius:0;">
  <div class="panel-title">התמונה הגדולה: מדד ה-QQQ</div>
  <div class="panel-sub">סריקה וניתוח משולב מבוסס מערכת ניקוד חכמה כדי להכריע את כיוון השוק בצורה ברורה.</div>
</div>""", unsafe_allow_html=True)
    
    btn_col1, btn_col2 = st.columns([3, 1])
    with btn_col1:
        st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
        run_qqq = st.button("התחל ניתוח נאסד\"ק 🚀", key="analyze_qqq_btn")
        st.markdown('</div>', unsafe_allow_html=True)
    with btn_col2:
        st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
        stop_qqq = st.button("עצור 🛑", key="stop_qqq_btn")
        st.markdown('</div>', unsafe_allow_html=True)

    if stop_qqq: st.stop()
        
    if run_qqq:
        with st.spinner("סורק נתונים חיים ומחשב ניקוד שוק משוקלל..."):
            try:
                qqq = yf.Ticker("QQQ")
                df = qqq.history(period="5y", interval="1d", auto_adjust=True)
                df = df.dropna(subset=['Close', 'Open', 'High', 'Low'])
                
                calls_oi, puts_oi = fetch_options_sentiment("QQQ")
                
                market_score = 0
                
                opt_status = "לא זמין"
                call_pct, put_pct = 50.0, 50.0
                if calls_oi + puts_oi > 0:
                    call_pct = (calls_oi / (calls_oi + puts_oi)) * 100
                    put_pct = (puts_oi / (calls_oi + puts_oi)) * 100
                    if call_pct > put_pct:
                        opt_status = "קולים"
                        market_score += 1
                    else:
                        opt_status = "פוטים"
                        market_score -= 1
                
                rsi_val = calculate_rsi(df['Close'])
                rsi_status = "קניית יתר" if rsi_val > 70 else "מכירת יתר" if rsi_val < 30 else "ניטרלי"
                if rsi_val > 55: market_score -= 1
                elif rsi_val < 45: market_score += 1
                    
                c1, c2 = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2])
                pa_status = "לונג" if c1 > c2 else "שורט"
                market_score += 1 if pa_status == "לונג" else -1
                        
                ma100 = float(df['Close'].ewm(span=100, adjust=False).mean().iloc[-1])
                ma200 = float(df['Close'].ewm(span=200, adjust=False).mean().iloc[-1])
                ma_status = "לונג" if c1 > ma100 and c1 > ma200 else "שורט" if c1 < ma100 and c1 < ma200 else "מעורב"
                if ma_status == "לונג": market_score += 1
                elif ma_status == "שורט": market_score -= 1
                    
                if market_score >= 1: verdict = "לונג"
                elif market_score <= -1: verdict = "שורט"
                else: verdict = "מעורב"
                    
                st.markdown(f"""
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; direction: rtl;">
                    <div style="background: #141410; border: 1px solid rgba(201,168,76,0.15); border-radius: 4px; padding: 20px; text-align: center;">
                        <div style="font-size: 0.8rem; color: #9a8f7a; margin-bottom: 10px;">1. סנטימנט אופציות</div>
                        <div style="font-size: 1.2rem; font-weight: 700; color: #c9a84c; margin-bottom: 5px;">רוב {opt_status}</div>
                        <div style="font-size: 0.75rem; color: #7a7060;">קולים: {call_pct:.1f}% | פוטים: {put_pct:.1f}%</div>
                    </div>
                    <div style="background: #141410; border: 1px solid rgba(201,168,76,0.15); border-radius: 4px; padding: 20px; text-align: center;">
                        <div style="font-size: 0.8rem; color: #9a8f7a; margin-bottom: 10px;">2. מומנטום (RSI)</div>
                        <div style="font-size: 1.2rem; font-weight: 700; color: #c9a84c; margin-bottom: 5px;">{rsi_status}</div>
                        <div style="font-size: 0.75rem; color: #7a7060;">ערך נוכחי: {rsi_val:.1f}</div>
                    </div>
                    <div style="background: #141410; border: 1px solid rgba(201,168,76,0.15); border-radius: 4px; padding: 20px; text-align: center;">
                        <div style="font-size: 0.8rem; color: #9a8f7a; margin-bottom: 10px;">3. פעולת מחיר (נרות)</div>
                        <div style="font-size: 1.2rem; font-weight: 700; color: #c9a84c; margin-bottom: 5px;">{pa_status}</div>
                        <div style="font-size: 0.75rem; color: #7a7060;">הסגירה היומית מול הסגירה אתמול</div>
                    </div>
                    <div style="background: #141410; border: 1px solid rgba(201,168,76,0.15); border-radius: 4px; padding: 20px; text-align: center;">
                        <div style="font-size: 0.8rem; color: #9a8f7a; margin-bottom: 10px;">4. ממוצעים ארוכים</div>
                        <div style="font-size: 1.2rem; font-weight: 700; color: #c9a84c; margin-bottom: 5px;">{ma_status}</div>
                        <div style="font-size: 0.75rem; color: #7a7060;">ביחס לממוצעים 100 ו-200 ימים</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if verdict == "לונג":
                    reasons_html_long = "<ul>"
                    if opt_status == "קולים": reasons_html_long += "<li><b>שוק האופציות:</b> דומיננטיות ברורה של משקיעים שרוכשים קולים (צפי לעליות).</li>"
                    if pa_status == "לונג": reasons_html_long += "<li><b>פעולת המחיר:</b> סגירות יומיות גבוהות יותר ומבנה שורי (קונים חזקים).</li>"
                    if ma_status == "לונג": reasons_html_long += "<li><b>ממוצעים:</b> המדד נסחר מעל ממוצעים 100 ו-200, אישור למגמת עלייה יציבה.</li>"
                    if rsi_val < 70: reasons_html_long += f"<li><b>מומנטום:</b> מדד ה-RSI עומד על {rsi_val:.1f}, מומנטום חיובי וזרימת כספים פנימה ללא קניית יתר חמורה.</li>"
                    reasons_html_long += "</ul>"
                    
                    st.markdown(f"""
                    <div style="background: radial-gradient(circle at top, rgba(22,163,74,0.2) 0%, rgba(10,10,8,1) 80%); border: 2px solid #16a34a; padding: 40px; text-align: right; border-radius: 12px; margin-top: 25px; box-shadow: 0 15px 50px rgba(22,163,74,0.25); position: relative; overflow: hidden; direction: rtl;">
                        <div style="position: absolute; top: -50px; left: -50px; font-size: 15rem; opacity: 0.05; user-select: none;">🚀</div>
                        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                            <div style="font-size: 4rem; margin-left: 20px;">🟢</div>
                            <div style="font-size: 3.8rem; font-family: 'Playfair Display', serif; font-weight: 900; color: #16a34a; text-shadow: 0 0 25px rgba(22,163,74,0.6); letter-spacing: 0.05em;">השוק בלונג</div>
                        </div>
                        <div style="border-top: 1px solid rgba(22,163,74,0.3); margin: 25px 0;"></div>
                        <h4 style="color: #f0ede6; font-size: 1.2rem; margin-bottom: 15px;">למה המערכת מזהה לונג מובהק?</h4>
                        <div style="color: #e5e5e5; font-size: 0.95rem; line-height: 1.8;">
                            {reasons_html_long}
                        </div>
                        <div style="margin-top: 20px; font-size: 0.85rem; color: #9a8f7a;">
                            <b>מסקנה לפעולה:</b> סביבה זו אידיאלית למסחר לונג. המומנטום חיובי והשוק דוחף למעלה.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif verdict == "שורט":
                    reasons_html_short = "<ul>"
                    if opt_status == "פוטים": reasons_html_short += "<li><b>שוק האופציות:</b> משקיעים כבדים רוכשים פוטים (הגנות), מה שמעיד על לחץ וציפייה לירידות.</li>"
                    if pa_status == "שורט": reasons_html_short += "<li><b>פעולת המחיר:</b> סגירות יומיות נמוכות יותר המעידות על פאניקה ומוכרים אגרסיביים.</li>"
                    if ma_status == "שורט": reasons_html_short += "<li><b>ממוצעים:</b> המדד שבר כלפי מטה תמיכות קריטיות והוא במגמה שלילית תחת הממוצעים.</li>"
                    if rsi_val > 30: reasons_html_short += f"<li><b>מומנטום:</b> מדד ה-RSI עומד על {rsi_val:.1f} ומעיד על זליגת כספים החוצה ללא מכירת יתר חמורה.</li>"
                    reasons_html_short += "</ul>"
                    
                    st.markdown(f"""
                    <div style="background: radial-gradient(circle at top, rgba(220,38,38,0.2) 0%, rgba(10,10,8,1) 80%); border: 2px solid #dc2626; padding: 40px; text-align: right; border-radius: 12px; margin-top: 25px; box-shadow: 0 15px 50px rgba(220,38,38,0.25); position: relative; overflow: hidden; direction: rtl;">
                        <div style="position: absolute; top: -50px; left: -50px; font-size: 15rem; opacity: 0.05; user-select: none;">🐻</div>
                        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                            <div style="font-size: 4rem; margin-left: 20px;">📉</div>
                            <div style="font-size: 3.8rem; font-family: 'Playfair Display', serif; font-weight: 900; color: #dc2626; text-shadow: 0 0 25px rgba(220,38,38,0.6); letter-spacing: 0.05em;">השוק בשורט</div>
                        </div>
                        <div style="border-top: 1px solid rgba(220,38,38,0.3); margin: 25px 0;"></div>
                        <h4 style="color: #f0ede6; font-size: 1.2rem; margin-bottom: 15px;">למה המערכת מזהה שורט מובהק?</h4>
                        <div style="color: #e5e5e5; font-size: 0.95rem; line-height: 1.8;">
                            {reasons_html_short}
                        </div>
                        <div style="margin-top: 20px; font-size: 0.85rem; color: #9a8f7a;">
                            <b>מסקנה לפעולה:</b> סביבה זו מסוכנת ללונג. רצוי להתמקד בהזדמנויות שורט, לגדר תיקים, ולהימנע מתפיסת "סכינים נופלות".
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""<div style="background: linear-gradient(135deg, rgba(201,168,76,0.05) 0%, rgba(10,10,8,1) 100%); border: 1px solid rgba(201,168,76,0.3); padding: 40px; text-align: center; border-radius: 8px; margin-top: 15px;"><div style="font-size: 3rem; margin-bottom: 10px;">⚖️</div><div style="font-size: 2.2rem; font-family: 'Playfair Display', serif; font-weight: 900; color: #c9a84c; letter-spacing: 0.05em;">מגמה מעורבת לחלוטין</div><div style="font-size: 0.9rem; color: #9a8f7a; margin-top: 10px;">הכוחות בשוק מאזנים לחלוטין זה את זה. המתנה להכרעה ברורה.</div></div>""", unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"שגיאת תקשורת נתונים מול הבורסה. נסה שוב. פירוט למפתח: {str(e)}")

bottom_html = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head><meta charset="UTF-8"/><style>
body{background:#0a0a08;color:#f0ede6;font-family:'Inter',sans-serif;direction:rtl;margin:0}
.section-wrap{padding:64px 40px;max-width:1200px;margin:0 auto}
.section-eyebrow{display:flex;align-items:center;gap:8px;margin-bottom:10px}
.eyebrow-line{width:28px;height:1px;background:#c9a84c}
.eyebrow-text{font-size:0.68rem;font-weight:600;letter-spacing:0.16em;color:#c9a84c;text-transform:uppercase}
.section-title{font-family:'Playfair Display',serif;font-size:clamp(1.5rem,2.5vw,2.2rem);font-weight:900;color:#f0ede6;margin-bottom:8px}
.section-desc{color:#9a8f7a;font-size:0.88rem;max-width:480px;line-height:1.65;margin-bottom:40px}
#features{background:#0f0f0c;border-top:1px solid rgba(201,168,76,0.12)}
.features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1px;background:rgba(201,168,76,0.12);border:1px solid rgba(201,168,76,0.12)}
.feat-card{background:#0f0f0c;padding:28px 24px;transition:background .2s}
.feat-card:hover{background:#141410}
.feat-icon{font-size:1.3rem;margin-bottom:14px;display:block}
.feat-title{font-family:'Playfair Display',serif;font-size:0.95rem;font-weight:700;color:#f0ede6;margin-bottom:6px}
.feat-desc{font-size:0.78rem;color:#7a7060;line-height:1.6}
#how{border-top:1px solid rgba(201,168,76,0.12)}
.steps-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border:1px solid rgba(201,168,76,0.12);background:rgba(201,168,76,0.12)}
.step-card{background:#141410;padding:32px 24px}
.step-num{font-family:'Playfair Display',serif;font-size:2.5rem;font-weight:900;color:rgba(201,168,76,0.12);line-height:1;margin-bottom:16px}
.step-title{font-family:'Playfair Display',serif;font-size:0.95rem;font-weight:700;color:#f0ede6;margin-bottom:8px}
.step-desc{font-size:0.78rem;color:#7a7060;line-height:1.6}
footer{background:#0f0f0c;border-top:1px solid rgba(201,168,76,0.12);padding:36px 40px;display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:16px}
.footer-logo{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:#c9a84c;margin-bottom:6px}
.footer-copy{font-size:0.72rem;color:#7a7060}
.footer-links{display:flex;gap:24px}
.footer-links a{{font-size:0.72rem;color:#7a7060;text-decoration:none;letter-spacing:0.06em;text-transform:uppercase;cursor:pointer}}
.footer-links a:hover{{color:#c9a84c}}
</style></head>
<body>
<section id="features" style="padding:0">
  <div class="section-wrap" style="padding-bottom:0">
    <div class="section-eyebrow"><div class="eyebrow-line"></div><div class="eyebrow-text">יתרונות</div></div>
    <h2 class="section-title">למה The Mind Changer?</h2>
    <p class="section-desc">כל מה שצריך לקבל החלטות מסחר חכמות יותר</p>
  </div>
  <div class="features-grid">
    <div class="feat-card"><span class="feat-icon">⚡</span><div class="feat-title">סריקה בזמן אמת</div><div class="feat-desc">מנתח מאות מניות לפי קריטריונים טכניים מוכחים</div></div>
    <div class="feat-card"><span class="feat-icon">📈</span><div class="feat-title">רדאר לונג</div><div class="feat-desc">מזהה מומנטום עולה עם RSI, ממוצעים נעים ונרות</div></div>
    <div class="feat-card"><span class="feat-icon">📉</span><div class="feat-title">רדאר שורט</div><div class="feat-desc">מאתר מניות חלשות עם Puts חזקים ומגמה יורדת</div></div>
    <div class="feat-card"><span class="feat-icon">📊</span><div class="feat-title">14 אינדיקטורים</div><div class="feat-desc">RSI, MA9/100/200, אופציות, המלצות אנליסטים ועוד</div></div>
    <div class="feat-card"><span class="feat-icon">🔒</span><div class="feat-title">נתונים מאובטחים</div><div class="feat-desc">עקיפת Rate Limits חכמה עם Session דינמי</div></div>
    <div class="feat-card"><span class="feat-icon">🤖</span><div class="feat-title">ניתוח AI</div><div class="feat-desc">נתונים טכניים אמיתיים לכל מניה שתבחר</div></div>
  </div>
</section>
<section id="how">
  <div class="section-wrap">
    <div class="section-eyebrow"><div class="eyebrow-line"></div><div class="eyebrow-text">תהליך</div></div>
    <h2 class="section-title">איך זה עובד?</h2>
    <p class="section-desc">שלושה שלבים פשוטים לתוצאות חכמות</p>
    <div class="steps-grid">
      <div class="step-card"><div class="step-num">01</div><div class="step-title">בחר מצב סריקה</div><div class="step-desc">לונג, שורט, או ניתוח מניה בודדת. המערכת אוספת נתונים בזמן אמת.</div></div>
      <div class="step-card"><div class="step-num">02</div><div class="step-title">סריקה אלגוריתמית</div><div class="step-desc">האלגוריתם בודק RSI, ממוצעים נעים, נפח מסחר ונרות עבור כל מניה.</div></div>
      <div class="step-card"><div class="step-num">03</div><div class="step-title">קבל תוצאות אמיתיות</div><div class="step-desc">מניות שעוברות את הקריטריונים מוצגות עם מחיר ואחוז שינוי עדכניים.</div></div>
    </div>
  </div>
</section>
<footer>
  <div>
    <div class="footer-logo">The Mind Changer</div>
    <div class="footer-copy">2026 — למטרות מידע בלבד. אינו ייעוץ השקעות.</div>
  </div>
</footer>
</body>
</html>"""

st.components.v1.html(bottom_html, height=710, scrolling=False)
