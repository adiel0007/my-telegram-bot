import streamlit as st
import yfinance as yf
import pandas as pd
import json
import random
import requests
import os
import contextlib
import time

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

div.stButton > button {{
    width: 100% !important;
    padding: 11px !important;
    border-radius: 0 0 4px 4px !important;
    font-size: 0.78rem !important;
    font-weight: 900 !important;
    color: #000000 !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer !important;
    border: none !important;
    transition: opacity .2s !important;
    margin-top: -2px !important;
}}
div.stButton > button:hover {{ opacity: 0.88 !important; }}

.long-btn div[data-testid="stButton"] button {{ background-color: #16a34a !important; color: #000000 !important; }}
.short-btn div[data-testid="stButton"] button {{ background-color: #dc2626 !important; color: #000000 !important; }}
.gold-btn div[data-testid="stButton"] button {{ background-color: #c9a84c !important; color: #000000 !important; }}
.stop-btn div[data-testid="stButton"] button {{ background-color: #9ca3af !important; color: #000000 !important; border: 1px solid #4b5563 !important; }}

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

def _fetch_options_sentiment_raw(ticker_symbol):
    calls_oi, puts_oi = 0, 0
    got_valid_response = False
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    for attempt in range(3):
        try:
            session = requests.Session()
            session.headers.update(headers)
            session.get(f'https://finance.yahoo.com/quote/{ticker_symbol}', timeout=10)

            crumb = ""
            try:
                crumb_res = session.get('https://query2.finance.yahoo.com/v1/test/getcrumb', timeout=10)
                if crumb_res.status_code == 200 and crumb_res.text and "Too Many Requests" not in crumb_res.text:
                    crumb = crumb_res.text.strip()
            except Exception:
                pass

            url = f"https://query2.finance.yahoo.com/v7/finance/options/{ticker_symbol}"
            params = {"crumb": crumb} if crumb else {}
            res = session.get(url, params=params, timeout=10)

            if res.status_code == 200:
                data = res.json()
                result = data.get('optionChain', {}).get('result', [])
                if result:
                    got_valid_response = True 
                    all_dates = result[0].get('expirationDates', [])
                    dates_to_scan = all_dates[:4] if all_dates else [None]

                    for exp_date in dates_to_scan:
                        try:
                            if exp_date:
                                scan_url = f"{url}?date={exp_date}"
                                if crumb:
                                    scan_url += f"&crumb={crumb}"
                                scan_res = session.get(scan_url, timeout=10)
                                scan_data = scan_res.json()
                                opts_list = scan_data.get('optionChain', {}).get('result', [])
                            else:
                                opts_list = result

                            if not opts_list:
                                continue
                            opts = opts_list[0].get('options', [])
                            if not opts:
                                continue
                            opts = opts[0]

                            for c in opts.get('calls', []):
                                oi = c.get('openInterest')
                                if oi is not None:
                                    calls_oi += oi
                            for p in opts.get('puts', []):
                                oi = p.get('openInterest')
                                if oi is not None:
                                    puts_oi += oi
                        except Exception:
                            continue

                    if calls_oi > 0 or puts_oi > 0:
                        return calls_oi, puts_oi
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))

    for attempt in range(2):
        try:
            s2 = requests.Session()
            s2.headers.update(headers)
            t = yf.Ticker(ticker_symbol, session=s2)
            dates = t.options
            if dates:
                got_valid_response = True
                for date in dates[:4]:
                    try:
                        chain = t.option_chain(date)
                        if 'openInterest' in chain.calls.columns:
                            calls_oi += int(chain.calls['openInterest'].fillna(0).sum())
                        if 'openInterest' in chain.puts.columns:
                            puts_oi += int(chain.puts['openInterest'].fillna(0).sum())
                    except Exception:
                        continue
                if calls_oi > 0 or puts_oi > 0:
                    return calls_oi, puts_oi
        except Exception:
            pass
        time.sleep(1.5 * (attempt + 1))

    try:
        t2 = yf.Ticker(ticker_symbol)
        dates2 = t2.options
        if dates2:
            got_valid_response = True
            for date in dates2[:2]:
                try:
                    chain2 = t2.option_chain(date)
                    if 'openInterest' in chain2.calls.columns:
                        calls_oi += int(chain2.calls['openInterest'].fillna(0).sum())
                    if 'openInterest' in chain2.puts.columns:
                        puts_oi += int(chain2.puts['openInterest'].fillna(0).sum())
                except Exception:
                    continue
    except Exception:
        pass

    if got_valid_response:
        return calls_oi, puts_oi

    raise RuntimeError(f"לא ניתן היה לקבל תשובה מיאהו עבור אופציות {ticker_symbol}")

@st.cache_data(ttl=900, show_spinner=False)
def _fetch_options_sentiment_cached(ticker_symbol):
    return _fetch_options_sentiment_raw(ticker_symbol)

def fetch_options_sentiment(ticker_symbol):
    try:
        return _fetch_options_sentiment_cached(ticker_symbol)
    except Exception:
        try:
            return _fetch_options_sentiment_raw(ticker_symbol)
        except Exception:
            return 0, 0

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

@st.cache_data(ttl=300)
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

@st.cache_data(ttl=300)
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

@st.cache_data(ttl=600)
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://edition.cnn.com/",
            "Origin": "https://edition.cnn.com"
        }
        r = requests.get(url, headers=headers, timeout=10)
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

def do_scan(mode):
    tickers  = load_tickers()
    results  = []
    session  = get_session()
    progress = st.progress(0)
    status   = st.empty()
    total    = len(tickers)
    
    for i, ticker in enumerate(tickers):
        status.markdown(f"<div style='color:#c9a84c;font-size:0.85rem;text-align:center;margin-bottom:10px;'>🔍 סורק {ticker}... ({i+1}/{total})</div>", unsafe_allow_html=True)
        progress.progress(int((i + 1) / total * 100))
        try:
            t = yf.Ticker(ticker, session=session)
            with open(os.devnull, 'w') as dn, contextlib.redirect_stderr(dn):
                # שינוי משמעותי: לא מבקשים "max" שגורם לחסימות מהירות ביאהו, מספיק 5 שנים בשביל ATH
                df = t.history(period="5y", interval="1d", auto_adjust=True, actions=False)
            
            if df.empty or len(df) < 30:
                continue
                
            ath = float(df["High"].max())
            
            df = df.dropna(subset=["Close", "Open", "High", "Low", "Volume"])
            if len(df) < 3:
                continue
                
            close = df["Close"]
            last  = float(close.iloc[-1])
            prev  = float(close.iloc[-2])
            rsi   = calculate_rsi(close)
            
            ma9_series = close.rolling(9).mean()
            ma9   = float(ma9_series.iloc[-1])
            
            ma100 = float(close.rolling(100).mean().bfill().fillna(last).iloc[-1])
            ma200 = float(close.rolling(200).mean().bfill().fillna(last).iloc[-1])
            
            # בדיקת מחזור חכמה - מונעת נפילות בתחילת יום כשהמחזור עוד קטן
            vol_today = int(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0
            vol_yest = int(df["Volume"].iloc[-2]) if "Volume" in df.columns and len(df) > 1 else 0
            vol = max(vol_today, vol_yest) 
            
            chg   = round(((last - prev) / prev) * 100, 2)
            
            open_1, close_1, high_1, low_1 = float(df["Open"].iloc[-1]), float(df["Close"].iloc[-1]), float(df["High"].iloc[-1]), float(df["Low"].iloc[-1])
            open_2, close_2, high_2, low_2 = float(df["Open"].iloc[-2]), float(df["Close"].iloc[-2]), float(df["High"].iloc[-2]), float(df["Low"].iloc[-2])
            open_3, close_3_val, high_3, low_3 = float(df["Open"].iloc[-3]), float(df["Close"].iloc[-3]), float(df["High"].iloc[-3]), float(df["Low"].iloc[-3])
            
            body_1 = abs(close_1 - open_1)
            lower_shadow_1 = min(open_1, close_1) - low_1
            upper_shadow_1 = high_1 - max(open_1, close_1)
            is_hammer_today_relaxed = (body_1 >= 0) and (lower_shadow_1 >= 1.5 * body_1) and (upper_shadow_1 <= 1.5 * body_1)
            is_hammer_today_strict = (body_1 > 0) and (lower_shadow_1 >= 2 * body_1) and (upper_shadow_1 <= body_1)
            
            body_2 = abs(close_2 - open_2)
            lower_shadow_2 = min(open_2, close_2) - low_2
            upper_shadow_2 = high_2 - max(open_2, close_2)
            is_hammer_yesterday_relaxed = (body_2 >= 0) and (lower_shadow_2 >= 1.5 * body_2) and (upper_shadow_2 <= 1.5 * body_2)
            is_hammer_yesterday_strict = (body_2 > 0) and (lower_shadow_2 >= 2 * body_2) and (upper_shadow_2 <= body_2)
            
            body_3 = abs(close_3_val - open_3)
            lower_shadow_3 = min(open_3, close_3_val) - low_3
            upper_shadow_3 = high_3 - max(open_3, close_3_val)
            is_hammer_day_3_relaxed = (body_3 >= 0) and (lower_shadow_3 >= 1.5 * body_3) and (upper_shadow_3 <= 1.5 * body_3)
            is_hammer_day_3_strict = (body_3 > 0) and (lower_shadow_3 >= 2 * body_3) and (upper_shadow_3 <= body_3)
            
            recent_hammer_relaxed = is_hammer_today_relaxed or is_hammer_yesterday_relaxed or is_hammer_day_3_relaxed
            recent_hammer_strict = is_hammer_today_strict or is_hammer_yesterday_strict or is_hammer_day_3_strict
            
            is_shooting_star_yesterday = (body_2 > 0) and (upper_shadow_2 >= 2 * body_2) and (lower_shadow_2 <= body_2)
            
            if mode == "long":
                yesterday_green = (close_2 > open_2)
                not_at_ath_long = last < (ath * 0.92)

                if (last > ma9 and rsi < 70 and vol > 300_000
                        and not (last > ma100 and last > ma200 and last > ma9)
                        and not (last < ma100 and last < ma200 and last < ma9)
                        and close_1 > open_1
                        and last > prev
                        and yesterday_green
                        and recent_hammer_relaxed
                        and not_at_ath_long): 
                    results.append({"symbol": ticker, "price": f"${last:.2f}", "chg": f"+{chg}%" if chg > 0 else f"{chg}%", "up": True, "strict_hammer": recent_hammer_strict})
            else:
                three_consecutive_down = (close_1 < close_2) and (close_2 < close_3_val)
                yesterday_red_star = is_shooting_star_yesterday and (close_2 < open_2)
                today_red_lower = (close_1 < open_1) and (close_1 < close_2)
                star_condition = yesterday_red_star and today_red_lower
                short_pattern = three_consecutive_down or star_condition

                if (rsi > 30 and vol > 300_000 and short_pattern):
                    results.append({"symbol": ticker, "price": f"${last:.2f}", "chg": f"{chg}%", "up": False})
        except:
            continue
    progress.empty()
    status.empty()
    return results

def normalize_ticker(raw_ticker):
    t = raw_ticker.strip().upper()
    if t.startswith("^"):
        return t
    t = t.replace(" ", "")
    if "." in t:
        t = t.replace(".", "-")
    return t

def _fetch_history_with_retry(ticker, attempts=3):
    last_error = None
    for i in range(attempts):
        try:
            session = get_session()
            t = yf.Ticker(ticker, session=session)
            df = t.history(period="1y", interval="1d", auto_adjust=True, actions=False)
            if not df.empty and len(df) >= 30:
                return df, t, None
        except Exception as e:
            last_error = e

        try:
            df2 = yf.download(ticker, period="1y", interval="1d", progress=False, threads=False)
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

def _get_yahoo_crumb_session():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    session = requests.Session()
    session.headers.update(headers)
    crumb = ""
    try:
        session.get('https://fc.yahoo.com', timeout=8)
    except Exception:
        pass
    try:
        session.get('https://finance.yahoo.com/quote/AAPL', timeout=8)
    except Exception:
        pass
    try:
        crumb_res = session.get('https://query2.finance.yahoo.com/v1/test/getcrumb', timeout=8)
        if crumb_res.status_code == 200 and crumb_res.text and "Too Many Requests" not in crumb_res.text:
            crumb = crumb_res.text.strip()
    except Exception:
        pass
    return session, crumb

_CRUMB_CACHE = {"session": None, "crumb": None, "ts": 0.0}
_CRUMB_TTL_SECONDS = 25 * 60

def get_shared_yahoo_session(force_refresh=False):
    now = time.time()
    cached_ok = (
        not force_refresh
        and _CRUMB_CACHE["session"] is not None
        and _CRUMB_CACHE["crumb"]
        and (now - _CRUMB_CACHE["ts"]) < _CRUMB_TTL_SECONDS
    )
    if cached_ok:
        return _CRUMB_CACHE["session"], _CRUMB_CACHE["crumb"]

    session, crumb = _get_yahoo_crumb_session()
    if crumb:
        _CRUMB_CACHE["session"] = session
        _CRUMB_CACHE["crumb"] = crumb
        _CRUMB_CACHE["ts"] = now
        return session, crumb

    if _CRUMB_CACHE["crumb"]:
        return _CRUMB_CACHE["session"], _CRUMB_CACHE["crumb"]

    return session, crumb

def _fetch_fundamentals_raw(ticker_symbol):
    merged = {}

    def _raw(d, key):
        v = d.get(key)
        if isinstance(v, dict):
            return v.get("raw")
        return v

    def _parse_beat_list(quarters):
        beat = []
        for q in quarters:
            actual = _raw(q, "epsActual")
            estimate = _raw(q, "epsEstimate")
            if actual is not None and estimate is not None:
                beat.append(actual >= estimate)
        return beat[-4:]

    def _has_data(d):
        return any(v is not None for v in d.values() if not isinstance(v, list)) or bool(d.get("earnings_beat_list"))

    for attempt in range(3):
        try:
            t = yf.Ticker(ticker_symbol)
            try:
                info = t.info or {}
                if info and len(info) > 5:
                    merged["revenueGrowth"]           = info.get("revenueGrowth")
                    merged["recommendationKey"]        = info.get("recommendationKey")
                    merged["numberOfAnalystOpinions"]  = info.get("numberOfAnalystOpinions")
                    merged["earningsQuarterlyGrowth"]  = info.get("earningsQuarterlyGrowth")
                    merged["trailingEps"]              = info.get("trailingEps")
                    merged["forwardEps"]               = info.get("forwardEps")
            except Exception:
                pass

            if not merged.get("earnings_beat_list"):
                for attr in ["earnings_history", "quarterly_earnings"]:
                    try:
                        eh = getattr(t, attr, None)
                        if eh is not None and not getattr(eh, "empty", True):
                            cols = list(eh.columns) if hasattr(eh, "columns") else []
                            if "epsActual" in cols and "epsEstimate" in cols:
                                sub = eh.dropna(subset=["epsActual", "epsEstimate"]).tail(4)
                                if not sub.empty:
                                    merged["earnings_beat_list"] = [
                                        bool(a >= e) for a, e in
                                        zip(sub["epsActual"], sub["epsEstimate"])
                                    ]
                                    break
                    except Exception:
                        continue

            if _has_data(merged):
                return merged
        except Exception:
            pass
        if attempt < 2:
            time.sleep(1.5 * (attempt + 1))

    modules = "financialData,defaultKeyStatistics,earningsHistory"
    for attempt in range(3):
        try:
            force = (attempt > 0)
            session, crumb = get_shared_yahoo_session(force_refresh=force)

            for base in ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]:
                try:
                    url = f"{base}/v10/finance/quoteSummary/{ticker_symbol}"
                    params = {"modules": modules}
                    if crumb:
                        params["crumb"] = crumb
                    res = session.get(url, params=params, timeout=10)
                    if res.status_code != 200:
                        continue
                    data = res.json()
                    results = data.get("quoteSummary", {}).get("result", [])
                    if not results:
                        continue
                    r = results[0]
                    fin       = r.get("financialData", {}) or {}
                    stats     = r.get("defaultKeyStatistics", {}) or {}
                    earn_hist = r.get("earningsHistory", {}) or {}

                    if merged.get("revenueGrowth") is None:
                        merged["revenueGrowth"] = _raw(fin, "revenueGrowth")
                    if merged.get("recommendationKey") is None:
                        merged["recommendationKey"] = fin.get("recommendationKey")
                    if merged.get("numberOfAnalystOpinions") is None:
                        merged["numberOfAnalystOpinions"] = _raw(fin, "numberOfAnalystOpinions")
                    if merged.get("earningsQuarterlyGrowth") is None:
                        merged["earningsQuarterlyGrowth"] = _raw(stats, "earningsQuarterlyGrowth")
                    if merged.get("trailingEps") is None:
                        merged["trailingEps"] = _raw(stats, "trailingEps")
                    if merged.get("forwardEps") is None:
                        merged["forwardEps"] = _raw(stats, "forwardEps")
                    if not merged.get("earnings_beat_list"):
                        quarters = earn_hist.get("history", []) or []
                        bl = _parse_beat_list(quarters)
                        if bl:
                            merged["earnings_beat_list"] = bl

                    if _has_data(merged):
                        return merged
                except Exception:
                    continue
        except Exception:
            pass
        if attempt < 2:
            time.sleep(2 * (attempt + 1))

    if _has_data(merged):
        return merged

    raise RuntimeError(f"לא ניתן היה למשוך נתוני יסוד עבור {ticker_symbol} אחרי כל הניסיונות")

@st.cache_data(ttl=600, show_spinner=False)
def _fetch_fundamentals_cached(ticker_symbol):
    return _fetch_fundamentals_raw(ticker_symbol)

def fetch_fundamentals(ticker_symbol):
    try:
        return _fetch_fundamentals_cached(ticker_symbol)
    except Exception:
        try:
            return _fetch_fundamentals_raw(ticker_symbol)
        except Exception:
            return {}

def analyze_ticker(ticker):
    try:
        clean_ticker = normalize_ticker(ticker)
        df, t, fetch_error = _fetch_history_with_retry(clean_ticker, attempts=3)

        if df.empty or len(df) < 30:
            try:
                test_info = yf.Ticker(clean_ticker).fast_info
                _ = test_info.last_price
                return {"_error": "network"}
            except Exception:
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
        except Exception:
            pass

        chg = round(((last - prev) / prev) * 100, 2)
        rsi = calculate_rsi(close)
        
        if rsi > 70:
            rsi_status, rsi_pos = "זמן למכור", False
        elif rsi < 30:
            rsi_status, rsi_pos = "זמן לקנות", True
        else:
            rsi_status, rsi_pos = "ניטרלי", None

        ma100_series = close.rolling(100).mean().bfill().fillna(last)
        ma200_series = close.rolling(200).mean().bfill().fillna(last)
        
        above_all = True
        below_all = True
        for j in range(1, min(4, len(close))):
            c_val = float(close.iloc[-j])
            if not (c_val > float(ma100_series.iloc[-j]) and c_val > float(ma200_series.iloc[-j])):
                above_all = False
            if not (c_val < float(ma100_series.iloc[-j]) and c_val < float(ma200_series.iloc[-j])):
                below_all = False
                
        if above_all:
            ma_status, ma_pos = "לונג", True
        elif below_all:
            ma_status, ma_pos = "שורט", False
        else:
            ma_status, ma_pos = "ניטרלי", None

        info = fetch_fundamentals(clean_ticker)

        earnings_text = "אין נתונים מספיקים להערכה"
        earnings_badge = "לא זמין"
        earnings_pos = None

        beat_list = info.get("earnings_beat_list") or []
        if beat_list:
            total_q = len(beat_list)
            beats = sum(1 for b in beat_list if b)
            earnings_badge = f"{beats}/{total_q}"
            if beats == total_q:
                earnings_text = f"המניה עמדה בתחזית האנליסטים או עברה אותה ב-{beats} מתוך {total_q} הרבעונים האחרונים — רצף מושלם"
                earnings_pos = True
            elif beats == 0:
                earnings_text = f"המניה לא עמדה בתחזית האנליסטים באף אחד מ-{total_q} הרבעונים האחרונים"
                earnings_pos = False
            elif beats >= total_q / 2:
                earnings_text = f"המניה עמדה בתחזית האנליסטים או עברה אותה ב-{beats} מתוך {total_q} הרבעונים האחרונים"
                earnings_pos = True
            else:
                earnings_text = f"המניה עמדה בתחזית האנליסטים רק ב-{beats} מתוך {total_q} הרבעונים האחרונים"
                earnings_pos = False

        options_text = "אין נתוני אופציות"
        calls_oi, puts_oi = fetch_options_sentiment(clean_ticker)
        total_oi = calls_oi + puts_oi
        if total_oi > 0:
            calls_ratio = (calls_oi / total_oi) * 100
            if calls_ratio >= 50:
                options_text = f"רוב אופציות קול ({calls_ratio:.1f}%)"
            else:
                options_text = f"רוב אופציות פוט ({100 - calls_ratio:.1f}%)"

        rev_growth = info.get("revenueGrowth")
        if rev_growth is not None:
            rev_growth_pct = round(rev_growth * 100, 1)
            if rev_growth_pct >= 0:
                forecast_text = f"צפי לגדילה בהכנסות ב-{rev_growth_pct}%"
                forecast_pos = True
            else:
                forecast_text = f"צפי לירידה בהכנסות ב-{abs(rev_growth_pct)}%"
                forecast_pos = False
        else:
            forecast_text = "אין תחזית הכנסות זמינה"
            forecast_pos = None

        rec_key = info.get("recommendationKey")
        num_analysts = info.get("numberOfAnalystOpinions")
        
        if rec_key and rec_key != "none":
            hebrew_rec = {
                "strong_buy": "קנייה חזקה",
                "buy": "קנייה",
                "hold": "אחזקה",
                "sell": "מכירה",
                "strong_sell": "מכירה חזקה",
                "underperform": "תשואת חסר",
                "outperform": "תשואת יתר"
            }
            translated_rec = hebrew_rec.get(rec_key, rec_key.replace('_', ' ').title())
            analyst_text = f"מבוסס על {num_analysts} אנליסטים" if num_analysts else "קונצנזוס"
            rec_text = f"המלצה: {translated_rec} ({analyst_text})"
            rec_badge = translated_rec
            rec_pos = rec_key in ["buy", "strong_buy", "outperform"]
        else:
            rec_text = "אין המלצות אנליסטים"
            rec_badge = "לא זמין"
            rec_pos = None

        ma9_val = float(close.rolling(9).mean().iloc[-1]) if len(close) >= 9 else last
        trend_up = last > ma9_val 
        up = chg >= 0
        trend_status = "שורי (דומיננטיות קונים ברורה)" if trend_up else "דובי (לחץ מוכרים מוגבר)"
        
        formatted_opinion = (
            f"🎯 <b>מסקנה אנליטית:</b> מניית {clean_ticker} נמצאת כעת במבנה מחירים <b>{trend_status}</b> בטווח הקצר המיידי.<br/>"
            f"📊 <b style='color:#c9a84c;'>מצב המתנדים:</b> מדד ה-RSI עומד על {rsi:.1f} המייצג סביבה תנודתית, כאשר נפח המסחר משקף מעורבות מוסדית.<br/>"
            f"🌐 <b style='color:#c9a84c;'>טווח ארוך (מאקרו):</b> נכס הבסיס נסחר במגמה של <b>{ma_status}</b> ביחס לממוצעים 100 ו-200 ימים."
        )
        
        return {
            "ticker":   clean_ticker,
            "price":    f"${last:.2f}",
            "chg":      f"+{chg}%" if chg >= 0 else f"{chg}%",
            "up":       up,
            "rsi_val_num": rsi,
            "rsi_status": rsi_status,
            "rsi_pos":    rsi_pos,
            "ma_status":  ma_status,
            "ma_pos":     ma_pos,
            "options_text": options_text,
            "earnings":   earnings_text,
            "earnings_badge": earnings_badge,
            "earnings_pos":   earnings_pos,
            "rec_text":   rec_text,
            "rec_badge":  rec_badge,
            "rec_pos":    rec_pos,
            "forecast_text": forecast_text,
            "forecast_pos":  forecast_pos,
            "momentum":   "עולה" if up else "יורד",
            "summary_text": formatted_opinion
        }
    except Exception as e:
        return {"_error": "network"}

def render_cards(data, mode):
    if data is None:
        return '<div class="empty-msg">הפעל את הרדאר כדי לראות תוצאות</div>'
    if len(data) == 0:
        return '<div class="empty-msg">לא נמצאו מניות העונות לקריטריונים כרגע</div>'
    cls  = "card-long"    if mode == "long" else "card-short"
    pcls = "card-price-g" if mode == "long" else "card-price-r"
    cards = "".join(
        f'<div class="stock-card {cls}">'
        f'<div class="card-sym">{s["symbol"]}</div>'
        f'<div class="{pcls}">{s["price"]}</div>'
        f'<div class="card-chg">{s["chg"]}</div></div>'
        for s in data
    )
    return f'<div class="card-grid">{cards}</div>'

def render_analysis(d):
    if not d or not isinstance(d, dict):
        return ''
    
    tag_cls = "tag-green" if d.get("up", True) else "tag-red"
    chg_color = "#16a34a" if d.get("up") else "#dc2626"
    
    rsi_pos = d.get("rsi_pos")
    ma_pos = d.get("ma_pos")
    earnings_pos = d.get("earnings_pos")
    forecast_pos = d.get("forecast_pos")
    rec_pos = d.get("rec_pos")
    
    def make_row(label, val_text, badge_text="", is_pos=None):
        badge_html = ""
        if badge_text:
            if is_pos is True:
                bg = "rgba(22, 163, 74, 0.15); color: #16a34a;"
            elif is_pos is False:
                bg = "rgba(220, 38, 38, 0.15); color: #dc2626;"
            else:
                bg = "rgba(255, 255, 255, 0.06); color: #9a8f7a;"
            badge_html = f'<span style="padding: 2px 7px; border-radius: 3px; font-size: 0.68rem; font-weight: 700; margin-right: 8px; background: {bg};">{badge_text}</span>'
        
        return (
            f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 11px 16px; border-bottom: 1px solid rgba(255,255,255,0.04); direction: rtl;">'
            f'<span style="font-size: 0.78rem; color: #7a7060; font-weight: 500;">{label}</span>'
            f'<div style="display: flex; align-items: center; gap: 4px; direction: ltr; text-align: left;">'
            f'{badge_html}'
            f'<span style="font-size: 0.78rem; color: #f0ede6; font-weight: 600; font-family: \'Inter\', sans-serif;">{val_text}</span>'
            f'</div></div>'
        )

    rows_html = (
        make_row("RSI (14)", f"{d.get('rsi_val_num', 0):.1f}", d.get("rsi_status", ""), rsi_pos) +
        make_row("ממוצעים נעים", d.get("ma_status", ""), "3 ימי מסחר", ma_pos) +
        make_row("סנטימנט אופציות", d.get("options_text", ""), "פעילות נגזרים", None) +
        make_row("דוחות כספיים", d.get("earnings", ""), d.get("earnings_badge", ""), earnings_pos) +
        make_row("צפי נתונים פיננסיים", d.get("forecast_text", ""), "תחזית", forecast_pos) +
        make_row("הערכת אנליסטים", d.get("rec_text", ""), d.get("rec_badge", ""), rec_pos)
    )

    html = (
        f'<div class="result-card" style="border: 1px solid rgba(201,168,76,0.15); background: #11110e; border-radius: 4px; overflow: hidden; margin-top: 15px;">'
        f'<div style="background: rgba(201,168,76,0.04); padding: 14px 16px; border-bottom: 1px solid rgba(201,168,76,0.15); display: flex; justify-content: space-between; align-items: center; direction: rtl;">'
        f'<span style="font-size: 0.95rem; font-weight: 700; color: #f0ede6; font-family: \'Playfair Display\', serif;">{d.get("ticker", "")} &nbsp; <span style="font-family: \'Inter\'; color:#c9a84c;">{d.get("price", "")}</span>'
        f'<small style="color: {chg_color}; font-size: 0.75rem; margin-right: 6px; font-family: \'Inter\'; font-weight:600;">{d.get("chg", "")}</small></span>'
        f'<span class="result-tag {tag_cls}" style="font-size: 0.65rem; font-weight: 700; padding: 3px 9px; border-radius: 3px;">{d.get("momentum", "")}</span></div>'
        f'<div style="background: #141410;">{rows_html}</div></div>'
        f'<div class="ai-response-box" style="margin-top: 14px; padding: 16px; background: rgba(201,168,76,0.04); border: 1px solid rgba(201,168,76,0.15); border-right: 4px solid #c9a84c; border-radius: 4px;">'
        f'<div class="ai-response-label" style="font-size: 0.7rem; font-weight: 700; color: #c9a84c; letter-spacing: 0.05em; margin-bottom: 6px;">📋 ניתוח ומסקנות מודל — THE MIND CHANGER</div>'
        f'<div class="ai-response-text" style="font-size: 0.82rem; color: #f0ede6; line-height: 1.7; font-weight:400; direction: rtl; text-align: right;">{d.get("summary_text", "")}</div></div>'
    )
    return html

for k in ["long_results", "short_results", "analysis", "ai_answer"]:
    if k not in st.session_state:
        st.session_state[k] = None

with st.spinner("טוען נתוני שוק..."):
    quotes  = fetch_quotes()
    indices = fetch_indices()
    stocks  = fetch_live_stocks()

quotes_json  = json.dumps(quotes,  ensure_ascii=False)
indices_json = json.dumps(indices, ensure_ascii=False)
stocks_json  = json.dumps(stocks,  ensure_ascii=False)

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
.live-card-title{{font-family:'Playfair Display',serif;font-size:0.92rem;color:#f0ede6;font-weight:700}}
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
    <p>המידע המוצג כאן מיועד למטרות לימוד בלבד ואינו מהווה ייעוץ השקעות. כל החלטת השקעה היא באחריותך הבלעדית.<br><br>בגלל שהאתר בנוי בצורה חינמית, אם לא מצליחים לקבל נתונים, יש לחכות כמה שניות וללחוץ על כפתור החיפוש שנית.</p>
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
        <div class="live-card-title">שוק בזמן אמת</div>
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
const QUOTES  = {quotes_json};
const INDICES = {indices_json};
const STOCKS  = {stocks_json};
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
    <li><div class="crit-dot dot-green"></div>נפח מסחר: מעל 300K</li>
    <li><div class="crit-dot dot-green"></div>מבנה נרות: היום ואתמול ירוקים, סגירה גבוהה יותר ותבנית פטיש גמישה</li>
    <li><div class="crit-dot dot-green"></div>מיקום לממוצעים: חיתוך ביניים (לא מתחת לכולם יחד, ולא מעל כולם)</li>
    <li><div class="crit-dot dot-green"></div>איזון נגזרים: נטיית Calls</li>
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

        if stop_long:
            st.stop()
        if run_long:
            st.session_state.long_results = do_scan("long")
            
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
                with st.spinner("מבצע סינון עומק מחזורי ומוודא תבנית פטיש קשיחה..."):
                    deep_filtered = []
                    session = get_session()
                    for item in st.session_state.long_results:
                        if not item.get("strict_hammer", False):
                            continue
                        try:
                            ticker_sym = item["symbol"]
                            ticker_obj = yf.Ticker(ticker_sym, session=session)
                            hist = ticker_obj.history(period="1mo", interval="1d", auto_adjust=True)
                            hist = hist.dropna(subset=["Volume"])
                            if len(hist) >= 20:
                                avg_vol_3d = hist["Volume"].iloc[-3:].mean()
                                avg_vol_20d = hist["Volume"].rolling(20).mean().iloc[-1]
                                if avg_vol_3d > avg_vol_20d:
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
    <li><div class="crit-dot dot-red"></div>נפח מסחר: מעל 300K</li>
    <li><div class="crit-dot dot-red"></div>מבנה נרות: 3 ימים יורדים ברצף או כוכב נופל אדום ולאחריו נר אדום נמוך יותר</li>
    <li><div class="crit-dot dot-red"></div>סינון עומק (כפתור זהב): מוודא נפח עולה ויותר Puts מ-Calls</li>
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

        if stop_short:
            st.stop()
        if run_short:
            st.session_state.short_results = do_scan("short")
            
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
                with st.spinner("מבצע סינון עומק מחזורי ובודק יחס אופציות (Puts > Calls)..."):
                    deep_filtered_short = []
                    session = get_session()
                    for item in st.session_state.short_results:
                        try:
                            ticker_sym = item["symbol"]
                            
                            # סינון חדש: בודק יחס אופציות (פוטים גדול מקולים)
                            calls_oi, puts_oi = fetch_options_sentiment(ticker_sym)
                            
                            if puts_oi > calls_oi:
                                ticker_obj = yf.Ticker(ticker_sym, session=session)
                                hist = ticker_obj.history(period="1mo", interval="1d", auto_adjust=True)
                                hist = hist.dropna(subset=["Volume"])
                                if len(hist) >= 20:
                                    avg_vol_3d = hist["Volume"].iloc[-3:].mean()
                                    avg_vol_20d = hist["Volume"].rolling(20).mean().iloc[-1]
                                    if avg_vol_3d > avg_vol_20d:
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
  <div class="panel-sub">הזן סימול וקבל ניתוח טכני אמיתי</div>
</div>""", unsafe_allow_html=True)
        ticker_val = st.text_input("סימול מניה", placeholder="AAPL, TSLA, NVDA...", label_visibility="collapsed")
        
        btn_col1, btn_col2 = st.columns([3, 1])
        with btn_col1:
            st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
            run_ai = st.button("נתח מניה", key="analyze_trigger")
            st.markdown('</div>', unsafe_allow_html=True)
        with btn_col2:
            st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
            stop_ai = st.button("עצור 🛑", key="stop_ai_trigger")
            st.markdown('</div>', unsafe_allow_html=True)

        if stop_ai:
            st.stop()
        if run_ai:
            if ticker_val:
                ticker_clean = ticker_val.upper().strip()
                with st.spinner(f"מחלץ נתוני שוק חיים עבור {ticker_clean}..."):
                    res = analyze_ticker(ticker_clean)

                    retry_count = 0
                    while isinstance(res, dict) and res.get("_error") == "network" and retry_count < 2:
                        time.sleep(2)
                        res = analyze_ticker(ticker_clean)
                        retry_count += 1

                    if res and not (isinstance(res, dict) and "_error" in res):
                        st.session_state.analysis = res
                    else:
                        st.session_state.analysis = None
                        if isinstance(res, dict) and res.get("_error") == "invalid":
                            st.error(f"הסימול '{ticker_clean}' לא נמצא. ודא שכתבת אותו נכון (לדוגמה: AAPL, TSLA, BRK-B).")
                        else:
                            st.error("יאהו פיננס עמוס כרגע ולא הצליח להחזיר נתונים אחרי כמה ניסיונות. המתן רגע ולחץ שוב על 'נתח מניה'.")
                        
        if st.session_state.analysis:
            analysis_html = render_analysis(st.session_state.analysis)
            st.markdown(analysis_html, unsafe_allow_html=True)

    with col2:
        st.markdown("""
<div class="panel-card" style="margin-top:15px; border-bottom-left-radius:0; border-bottom-right-radius:0; padding-bottom:10px;">
  <div class="panel-title">שאלות כלליות</div>
  <div class="panel-sub">שאל שאלות פיננסיות וקבל הסברים</div>
</div>""", unsafe_allow_html=True)
        qa_val = st.text_input("שאלה לגבי אינדיקטורים", placeholder="כמה כסף זה ב-3 שנים אם אני משקיע...", label_visibility="collapsed")
        
        btn_col1, btn_col2 = st.columns([3, 1])
        with btn_col1:
            st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
            run_qa = st.button("שאל", key="qa_trigger")
            st.markdown('</div>', unsafe_allow_html=True)
        with btn_col2:
            st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
            stop_qa = st.button("עצור 🛑", key="stop_qa_trigger")
            st.markdown('</div>', unsafe_allow_html=True)

        if stop_qa:
            st.stop()
        if run_qa:
            if qa_val:
                q = qa_val.strip()
                
                if not GENAI_AVAILABLE or GEMINI_API_KEY == "הכנס_כאן_את_המפתח_החדש":
                    st.session_state.ai_answer = (
                        "<b>⚠️ חיבור חסר למערכת ה-AI:</b><br/><br/>"
                        "כדי שהמערכת תוכל לתקשר עם ה-API של גוגל ולענות על שאלות חופשיות, עליך להדביק את מפתח ה-API החוקי שלך בהגדרות הסודות של השרת.<br/><br/>"
                        "<i>(עד אז, המערכת תספק תשובות בסיסיות רק למונחים כמו RSI, שורט או ממוצעים).</i>"
                    )
                else:
                    with st.spinner("הבינה המלאכותית מנתחת את שאלתך..."):
                        try:
                            genai.configure(api_key=GEMINI_API_KEY)
                            
                            available_models = []
                            for m in genai.list_models():
                                if 'generateContent' in m.supported_generation_methods:
                                    available_models.append(m.name)
                                    
                            if not available_models:
                                st.session_state.ai_answer = "<b>שגיאה:</b> המפתח שסיפקת תקין, אך אין לו הרשאות למודלי יצירת טקסט של Gemini ב-Google Cloud."
                            else:
                                chosen_model = available_models[0]
                                for preferred in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro', 'models/gemini-1.0-pro']:
                                    if preferred in available_models:
                                        chosen_model = preferred
                                        break
                                        
                                model = genai.GenerativeModel(chosen_model)
                                prompt_text = f"אתה מומחה פיננסי בכיר במערכת 'The Mind Changer'. ענה על השאלה הבאה בצורה מקצועית, ברורה, מדויקת, ובשפה העברית (עד 3-4 פסקאות).\n\nהשאלה של המשתמש: {q}"
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
מדד הפחד והגרידיות (Fear & Greed Index) שפותח על ידי רשת <b>CNN Business</b> משמש כלי מרכזי לניתוח סנטימנט השוק ואיתור מצבי קיצון פסיכולוגיים בקרב המשקיעים בוול סטריט. המדד נע בסולם שבין <b>0 ל-100</b> ומבוסס על שקלול של 7 אינדיקטורים שונים, ביניהם: מומנטום המחירים בשוק, עוצמת מחירי המניות, יחס חוזי אופציות ה-Put/Call, תנודתיות השוק (מדד ה-VIX) והביקוש לאגרות חוב בטוחות.
</p>
<h4 style="color: #c9a84c; font-size: 0.9rem; margin-bottom: 6px;">כיצד מפרשים את נתוני המדד במסחר?</h4>
<ul style="list-style: none; padding-right: 0; font-size: 0.82rem; color: #7a7060; line-height: 1.6;">
<li style="margin-bottom: 8px;"><b style="color: #dc2626;">• פחד קיצוני (0-25):</b> מעיד על פאניקה מסיבית ומימושים כבדים בשוק. סוחרים מנוסים רואים במצב זה פוטנציאל גבוה להיווצרות תחתית בגרף והזדמנות קניות יוצאת דופן במחירי רצפה (כפי שאמר באפט: "היה גרידי כשאחרים מפחדים").</li>
<li style="margin-bottom: 8px;"><b style="color: #9a8f7a;">• מצב ניטרלי (45-55):</b> משקף שיווי משקל בריא, מסחר יציב בתוך תעלות ומגמות מאוזנות ללא אופוריה או פחד חריג.</li>
<li style="margin-bottom: 8px;"><b style="color: #16a34a;">• גרידיות קיצונית (75-100):</b> מאותת על אופוריה מוגזמת, כניסת קונים אגרסיבית (FOMO) ומתיחת יתר של המחירים בשוק. מצב זה מזהיר מפני בועה מקומית ופוטנציאל גבוה לתיקון אלים או קריסה קרובה כלפי מטה.</li>
</ul>
</div>"""
        st.markdown(html_text, unsafe_allow_html=True)

with tab_market_dir:
    st.markdown("""
<div class="panel-card" style="margin-top:15px; border-bottom-left-radius:0; border-bottom-right-radius:0;">
  <div class="panel-title">התמונה הגדולה: מדד ה-QQQ</div>
  <div class="panel-sub">סריקה וניתוח משולב של מדד הנאסד"ק לאיתור מגמת השוק וסינון עסקאות</div>
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

    if stop_qqq:
        st.stop()
        
    if run_qqq:
        with st.spinner("סורק נתונים חיים מהבורסה... (אופציות, מתנדים ומחיר)"):
            try:
                session = get_session()
                qqq = yf.Ticker("QQQ", session=session)
                
                try:
                    df = qqq.history(period="2y", interval="1d", auto_adjust=True)
                except:
                    df = pd.DataFrame()
                
                if df.empty:
                    try:
                        df = yf.download("QQQ", period="2y", interval="1d", progress=False)
                    except:
                        pass
                
                if not df.empty and isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                    
                if df.empty or "Close" not in df.columns:
                    st.error("הבורסה חסמה זמנית את הבקשות לגרפים (Rate Limit). המתן כמה דקות ונסה שוב.")
                    st.stop()
                    
                df = df.dropna(subset=['Close', 'Open', 'High', 'Low'])
                
                calls_oi, puts_oi = fetch_options_sentiment("QQQ")
                
                total_oi = calls_oi + puts_oi
                if total_oi > 0:
                    call_pct = (calls_oi / total_oi * 100)
                    put_pct = (puts_oi / total_oi * 100)
                    opt_status = "קולים" if call_pct > put_pct else "פוטים"
                else:
                    call_pct, put_pct = 50.0, 50.0
                    opt_status = "לא זמין"
                
                rsi_val = calculate_rsi(df['Close'])
                if rsi_val > 70:
                    rsi_status = "קניית יתר"
                elif rsi_val < 30:
                    rsi_status = "מכירת יתר"
                else:
                    rsi_status = "ניטרלי"
                    
                if len(df) >= 200:
                    c1, c2, c3 = float(df['Close'].iloc[-1]), float(df['Close'].iloc[-2]), float(df['Close'].iloc[-3])
                    o1, o2, o3 = float(df['Open'].iloc[-1]), float(df['Open'].iloc[-2]), float(df['Open'].iloc[-3])
                    h2, l2 = float(df['High'].iloc[-2]), float(df['Low'].iloc[-2])
                    
                    g1, g2, g3 = (c1 > o1), (c2 > o2), (c3 > o3)
                    r1, r2, r3 = (c1 < o1), (c2 < o2), (c3 < o3)
                    
                    body_2 = abs(c2 - o2)
                    lower_shadow_2 = min(o2, c2) - l2
                    upper_shadow_2 = h2 - max(o2, c2)
                    
                    is_hammer_yesterday = (body_2 > 0) and (lower_shadow_2 >= 2 * body_2) and (upper_shadow_2 <= body_2)
                    is_shooting_star_yesterday = (body_2 > 0) and (upper_shadow_2 >= 2 * body_2) and (lower_shadow_2 <= body_2)
                    
                    is_red_hammer_or_star = r2 and (is_hammer_yesterday or is_shooting_star_yesterday)
                    
                    is_long = (g1 and g2 and g3) or (g1 and g2 and c1 > c2) or (g1 and is_hammer_yesterday)
                    is_short = (r1 and r2 and r3) or (r1 and r2 and c1 < c2) or (r1 and is_red_hammer_or_star)
                    
                    if is_long:
                        pa_status = "לונג"
                    elif is_short:
                        pa_status = "שורט"
                    else:
                        pa_status = "מעורב"
                        
                    ma9 = float(df['Close'].rolling(9).mean().iloc[-1])
                    ma100 = float(df['Close'].rolling(100).mean().iloc[-1])
                    ma200 = float(df['Close'].rolling(200).mean().iloc[-1])
                    
                    if r1 and r2 and (c1 < ma100 or c1 < ma200):
                        ma_status = "שורט"
                    elif g1 and g2 and (c1 > ma9):
                        ma_status = "לונג"
                    else:
                        ma_status = "מעורב"
                else:
                    pa_status = "חסר נתונים"
                    ma_status = "חסר נתונים"
                    
                if opt_status == "קולים" and rsi_status in ["מכירת יתר", "ניטרלי"] and pa_status == "לונג" and ma_status == "לונג":
                    verdict = "לונג"
                elif opt_status == "פוטים" and rsi_status in ["קניית יתר", "ניטרלי"] and pa_status == "שורט" and ma_status == "שורט":
                    verdict = "שורט"
                else:
                    verdict = "מעורב"
                    
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
                        <div style="font-size: 0.75rem; color: #7a7060;">מבנה ב-3 הימים האחרונים (כולל זיהוי פטישים)</div>
                    </div>
                    <div style="background: #141410; border: 1px solid rgba(201,168,76,0.15); border-radius: 4px; padding: 20px; text-align: center;">
                        <div style="font-size: 0.8rem; color: #9a8f7a; margin-bottom: 10px;">4. ממוצעים נעים</div>
                        <div style="font-size: 1.2rem; font-weight: 700; color: #c9a84c; margin-bottom: 5px;">{ma_status}</div>
                        <div style="font-size: 0.75rem; color: #7a7060;">תמיכות והתנגדויות</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if verdict == "לונג":
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, rgba(22,163,74,0.12) 0%, rgba(10,10,8,1) 100%); border: 1px solid #16a34a; padding: 40px; text-align: center; border-radius: 8px; margin-top: 15px; box-shadow: 0 0 40px rgba(22,163,74,0.15);">
                        <div style="font-size: 4rem; margin-bottom: 10px;">🚀 🟢</div>
                        <div style="font-size: 3.5rem; font-family: 'Playfair Display', serif; font-weight: 900; color: #16a34a; text-shadow: 0 0 20px rgba(22,163,74,0.4); letter-spacing: 0.05em;">השוק לונג</div>
                        <div style="font-size: 0.9rem; color: #9a8f7a; margin-top: 10px;">התנאים מצביעים על מומנטום חיובי ושליטת קונים בנאסד"ק. חפש הזדמנויות לונג.</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif verdict == "שורט":
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, rgba(220,38,38,0.12) 0%, rgba(10,10,8,1) 100%); border: 1px solid #dc2626; padding: 40px; text-align: center; border-radius: 8px; margin-top: 15px; box-shadow: 0 0 40px rgba(220,38,38,0.15);">
                        <div style="font-size: 4rem; margin-bottom: 10px;">🩸 🔴</div>
                        <div style="font-size: 3.5rem; font-family: 'Playfair Display', serif; font-weight: 900; color: #dc2626; text-shadow: 0 0 20px rgba(220,38,38,0.4); letter-spacing: 0.05em;">השוק בשורט</div>
                        <div style="font-size: 0.9rem; color: #9a8f7a; margin-top: 10px;">התנאים מצביעים על חולשה מהותית ושליטת מוכרים בנאסד"ק. חפש הזדמנויות שורט.</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, rgba(201,168,76,0.05) 0%, rgba(10,10,8,1) 100%); border: 1px solid rgba(201,168,76,0.3); padding: 40px; text-align: center; border-radius: 8px; margin-top: 15px;">
                        <div style="font-size: 3rem; margin-bottom: 10px;">⚖️</div>
                        <div style="font-size: 2.2rem; font-family: 'Playfair Display', serif; font-weight: 900; color: #c9a84c; letter-spacing: 0.05em;">מגמה מעורבת</div>
                        <div style="font-size: 0.9rem; color: #9a8f7a; margin-top: 10px;">אין כרגע איתות מובהק וחד משמעי לכיוון השוק. מומלץ להמתין למבנה ברור יותר.</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"אירעה שגיאה. ייתכן שאין מספיק נתונים זמינים מהבורסה כרגע. פירוט למפתח: {str(e)}")

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
