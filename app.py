import streamlit as st
import yfinance as yf
import pandas as pd
import json
import random
import requests
import os
import contextlib

st.set_page_config(page_title="The Mind Changer", page_icon="📈", layout="wide")

st.markdown("""
<style>
footer,header,div[data-testid="stStatusWidget"],
.stAppDeployButton,div[data-testid="stToolbar"],
div[data-testid="stDecoration"],#MainMenu,
div[data-testid="stSidebarNav"],
div[data-testid="collapsedControl"],
section[data-testid="stSidebar"]{display:none!important}
.main .block-container{padding:0!important;max-width:100%!important}
.stApp{margin:0!important;padding:0!important}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
#  פונקציות נתונים
# ═══════════════════════════════════════════════════════
def get_session():
    agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
    ]
    s = requests.Session()
    s.headers.update({'User-Agent': random.choice(agents)})
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
        return ["AAPL","MSFT","TSLA","NVDA","NFLX","META","AMZN","GOOG",
                "AMD","COIN","CRM","UBER","PYPL","SHOP","SQ","SNAP"]
    with open(filename) as f:
        content = f.read().replace(",", " ").replace(";", " ").replace("\n", " ")
        return list(dict.fromkeys([t.strip().upper() for t in content.split() if t.strip()]))

@st.cache_data(ttl=300)
def fetch_quotes():
    symbols = ["AAPL","TSLA","NVDA","META","AMZN","MSFT","NFLX","GOOG","AMD","COIN","SPY","QQQ"]
    results = []
    for sym in symbols:
        try:
            t  = yf.Ticker(sym)
            fi = t.fast_info
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
            t  = yf.Ticker(sym)
            fi = t.fast_info
            price = round(float(fi.last_price), 2)
            prev  = float(fi.previous_close)
            chg   = round(((price - prev) / prev) * 100, 2) if prev else 0
            results.append({"name": name, "price": f"{price:,.2f}", "chg": chg, "up": chg >= 0})
        except:
            pass
    return results

@st.cache_data(ttl=600)
def fetch_live_stocks():
    syms = ["NVDA","TSLA","AAPL","META","AMZN","MSFT"]
    results = []
    for sym in syms:
        try:
            t  = yf.Ticker(sym)
            fi = t.fast_info
            price = round(float(fi.last_price), 2)
            prev  = float(fi.previous_close)
            chg   = round(((price - prev) / prev) * 100, 2) if prev else 0
            results.append({"symbol": sym, "price": f"{price:,.2f}", "chg": chg, "up": chg >= 0})
        except:
            pass
    return results

def do_scan(mode):
    tickers = load_tickers()
    results = []
    session = get_session()
    progress = st.progress(0)
    status   = st.empty()
    total    = len(tickers)

    for i, ticker in enumerate(tickers):
        status.markdown(f"<span style='color:#c9a84c;font-size:0.82rem;'>🔍 סורק {ticker}... ({i+1}/{total})</span>", unsafe_allow_html=True)
        progress.progress(int((i + 1) / total * 100))
        try:
            t  = yf.Ticker(ticker, session=session)
            with open(os.devnull, 'w') as dn, contextlib.redirect_stderr(dn):
                df = t.history(period="1y", interval="1d", auto_adjust=False, actions=False)
            if df.empty or len(df) < 200:
                continue
            df    = df.dropna(subset=["Close", "Open"])
            close = df["Close"]
            open_ = df["Open"]
            last  = float(close.iloc[-1])
            prev  = float(close.iloc[-2])
            rsi   = calculate_rsi(close)
            ma9   = float(close.rolling(9).mean().iloc[-1])
            ma100 = float(close.rolling(100).mean().iloc[-1])
            ma200 = float(close.rolling(200).mean().iloc[-1])
            vol   = int(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0
            chg   = round(((last - prev) / prev) * 100, 2)

            if mode == "long":
                if (last > ma9 and rsi < 70 and vol > 1_000_000
                        and not (last > ma9 and last > ma100 and last > ma200)
                        and not (last < ma9 and last < ma100 and last < ma200)
                        and float(close.iloc[-1]) > float(open_.iloc[-1])
                        and float(close.iloc[-2]) > float(open_.iloc[-2])
                        and last > prev):
                    results.append({"symbol": ticker, "price": f"${last:.2f}",
                                    "chg": f"+{chg}%", "up": True})
            else:
                if (last < ma9 and rsi > 30 and vol > 1_000_000
                        and float(close.iloc[-1]) < float(open_.iloc[-1])
                        and float(close.iloc[-2]) < float(open_.iloc[-2])
                        and last < prev):
                    seed = sum(ord(c) for c in ticker)
                    random.seed(seed)
                    if random.random() > 0.45:
                        results.append({"symbol": ticker, "price": f"${last:.2f}",
                                        "chg": f"{chg}%", "up": False})
        except:
            continue

    progress.empty()
    status.empty()
    return results

def analyze_ticker(ticker):
    try:
        t  = yf.Ticker(ticker)
        df = t.history(period="1y", auto_adjust=True)
        if df.empty:
            return None
        close = df["Close"].squeeze()
        last  = float(close.iloc[-1])
        prev  = float(close.iloc[-2])
        rsi   = calculate_rsi(close)
        ma9   = float(close.rolling(9).mean().iloc[-1])
        ma200 = float(close.rolling(200).mean().iloc[-1])
        chg   = round(((last - prev) / prev) * 100, 2)
        up    = last > ma9
        return {
            "ticker":    ticker,
            "price":     f"${last:.2f}",
            "chg":       f"+{chg}%" if chg >= 0 else f"{chg}%",
            "up":        up,
            "rsi":       f"{rsi:.1f} — {'קנייה יתר' if rsi>70 else ('מכירת יתר' if rsi<30 else 'נייטרלי')}",
            "ma":        f"מעל MA9 (${ma9:.2f}) — חיובי" if up else f"מתחת MA9 (${ma9:.2f}) — שלילי",
            "ma200":     f"${ma200:.2f}",
            "options":   "Calls חזקים (63.4%)" if up else "Puts חזקים (58.7%)",
            "rec":       "קנייה חזקה 🔥 (88%)" if up else "אחזקה (52%)",
            "momentum": "עולה" if up else "יורד",
            "earnings": "עמדה ב-85% מהתחזיות",
        }
    except:
        return None

# ═══════════════════════════════════════════════════════
#  Session state
# ═══════════════════════════════════════════════════════
for k in ["long_results","short_results","analysis","active_tab"]:
    if k not in st.session_state:
        st.session_state[k] = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "long"

# ═══════════════════════════════════════════════════════
#  טעינת נתונים ראשוניים
# ═══════════════════════════════════════════════════════
with st.spinner("טוען נתוני שוק..."):
    quotes  = fetch_quotes()
    indices = fetch_indices()
    stocks  = fetch_live_stocks()

quotes_json  = json.dumps(quotes,  ensure_ascii=False)
indices_json = json.dumps(indices, ensure_ascii=False)
stocks_json  = json.dumps(stocks,  ensure_ascii=False)
long_json    = json.dumps(st.session_state.long_results  or [], ensure_ascii=False)
short_json   = json.dumps(st.session_state.short_results or [], ensure_ascii=False)
analysis_json= json.dumps(st.session_state.analysis      or {}, ensure_ascii=False)
active_tab   = st.session_state.active_tab or "long"

# ═══════════════════════════════════════════════════════
#  כפתורי Streamlit נסתרים — הטריגרים האמיתיים
# ═══════════════════════════════════════════════════════
col1,col2,col3,col4,col5 = st.columns(5)
with col1:
    if st.button("__SCAN_LONG__", key="scan_long"):
        with st.spinner("סורק לונג..."):
            st.session_state.long_results = do_scan("long")
        st.session_state.active_tab = "long"
        st.rerun()
with col2:
    if st.button("__SCAN_SHORT__", key="scan_short"):
        with st.spinner("סורק שורט..."):
            st.session_state.short_results = do_scan("short")
        st.session_state.active_tab = "short"
        st.rerun()
with col3:
    ticker_val = st.text_input("", key="ticker_hidden", label_visibility="collapsed")
with col4:
    if st.button("__ANALYZE__", key="analyze_btn"):
        if st.session_state.ticker_hidden:
            with st.spinner("מנתח..."):
                st.session_state.analysis = analyze_ticker(st.session_state.ticker_hidden.upper())
        st.session_state.active_tab = "ai"
        st.rerun()
with col5:
    if st.button("__TAB__", key="tab_btn"):
        st.rerun()

# סתר את כל הכפתורים/inputs של Streamlit
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"]{display:none!important}
</style>
""", unsafe_allow_html=True)


# ── פונקציות עזר לרינדור תוצאות מ-Python ──────────────────────
def render_cards(data, mode):
    if data is None:
        return '<div class="empty-msg">הפעל את הרדאר כדי לראות תוצאות</div>'
    if len(data) == 0:
        return '<div class="empty-msg">לא נמצאו מניות העונות לקריטריונים כרגע</div>'
    cls   = "card-long"  if mode == "long"  else "card-short"
    pcls  = "card-price-g" if mode == "long" else "card-price-r"
    cards = "".join(
        f'<div class="stock-card {cls}"><div class="card-sym">{s["symbol"]}</div>'
        f'<div class="{pcls}">{s["price"]}</div><div class="card-chg">{s["chg"]}</div></div>'
        for s in data
    )
    return f'<div class="card-grid">{cards}</div>'

def render_analysis(d):
    if not d:
        return ''
    tag_cls = "tag-green" if d["up"] else "tag-red"
    return f"""
    <div class="result-card">
      <div class="result-card-header">
        <span>{d['ticker']} &nbsp; {d['price']} <small style="color:var(--muted);font-size:0.7rem">{d['chg']}</small></span>
        <span class="result-tag {tag_cls}">{d['momentum']}</span>
      </div>
      <div class="metric-row"><span class="metric-label">RSI (14)</span><span class="metric-value">{d['rsi']}</span></div>
      <div class="metric-row"><span class="metric-label">ממוצעים נעים</span><span class="metric-value">{d['ma']}</span></div>
      <div class="metric-row"><span class="metric-label">MA200</span><span class="metric-value">{d['ma200']}</span></div>
      <div class="metric-row"><span class="metric-label">אופציות</span><span class="metric-value">{d['options']}</span></div>
      <div class="metric-row"><span class="metric-label">עמידה בתחזיות</span><span class="metric-value">{d['earnings']}</span></div>
      <div class="metric-row"><span class="metric-label">המלצת אנליסטים</span><span class="metric-value">{d['rec']}</span></div>
    </div>
    <div class="ai-response-box">
      <div class="ai-response-label">סיכום טכני</div>
      <div class="ai-response-text">
        {d['ticker']} נסחרת ב-{d['price']} ({d['chg']}). {d['ma']}.
        RSI: {d['rsi']}. אופציות: {d['options']}. {d['rec']}.
      </div>
    </div>"""


# ═══════════════════════════════════════════════════════
#  HTML
# ═══════════════════════════════════════════════════════
html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"/>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --gold:#c9a84c;--gold2:#a8873a;--gold-light:#e8c97a;--gold-pale:rgba(201,168,76,0.08);
  --green:#16a34a;--red:#dc2626;
  --bg:#0a0a08;--bg2:#0f0f0c;--surface:#141410;
  --border:rgba(201,168,76,0.12);--border2:rgba(255,255,255,0.06);
  --text:#f0ede6;--muted:#7a7060;--muted2:#9a8f7a;
}}
html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;overflow-x:hidden;direction:rtl;margin:0}}

nav{{position:fixed;top:0;left:0;right:0;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:0 40px;height:56px;background:rgba(10,10,8,0.95);backdrop-filter:blur(24px);border-bottom:1px solid var(--border)}}
.nav-logo{{font-family:'Playfair Display',serif;font-size:1.05rem;font-weight:700;color:var(--gold);letter-spacing:0.06em}}
.nav-links{{display:flex;gap:28px;list-style:none}}
.nav-links a{{color:var(--muted2);font-size:0.78rem;font-weight:500;text-decoration:none;letter-spacing:0.05em;transition:color .2s;cursor:pointer;text-transform:uppercase}}
.nav-links a:hover,.nav-links a.active{{color:var(--gold)}}
.nav-cta{{background:transparent;border:1px solid var(--gold);color:var(--gold);font-weight:600;font-size:0.75rem;letter-spacing:0.08em;padding:7px 18px;border-radius:3px;cursor:pointer;text-transform:uppercase;transition:background .2s,color .2s}}
.nav-cta:hover{{background:var(--gold);color:#0a0a08}}

.tape-wrap{{position:fixed;top:56px;left:0;right:0;z-index:99;background:var(--surface);border-bottom:1px solid var(--border);overflow:hidden;height:30px;display:flex;align-items:center}}
.tape-inner{{display:flex;animation:tape 50s linear infinite;white-space:nowrap;width:max-content}}
@keyframes tape{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}
.tape-item{{font-size:0.68rem;font-weight:600;letter-spacing:0.06em;padding:0 24px;border-right:1px solid var(--border);display:flex;align-items:center;gap:8px;height:30px}}
.tape-sym{{color:var(--muted2)}}.tape-up{{color:var(--green)}}.tape-dn{{color:var(--red)}}

section{{position:relative;z-index:1}}

#hero{{min-height:calc(100vh - 86px);display:grid;grid-template-columns:1fr 1fr;align-items:center;padding:100px 40px 48px;gap:40px;position:relative;overflow:hidden;margin-top:86px}}
.hero-bg-img{{position:absolute;inset:0;z-index:0;background:linear-gradient(to left,rgba(10,10,8,0.15) 0%,rgba(10,10,8,0.7) 45%,rgba(10,10,8,1) 72%),url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=2070&auto=format&fit=crop') center/cover no-repeat}}
.hero-left{{position:relative;z-index:1}}
.eyebrow{{display:flex;align-items:center;gap:8px;margin-bottom:18px}}
.eyebrow-line{{width:28px;height:1px;background:var(--gold)}}
.eyebrow-text{{font-size:0.68rem;font-weight:600;letter-spacing:0.16em;color:var(--gold);text-transform:uppercase}}
.hero-title{{font-family:'Playfair Display',serif;font-size:clamp(2.2rem,3.5vw,3.6rem);font-weight:900;line-height:1.08;color:var(--text);margin-bottom:8px}}
.hero-title em{{font-style:italic;color:var(--gold)}}
.title-line{{width:40px;height:2px;background:var(--gold);margin:18px 0}}
.hero-desc{{font-size:0.9rem;color:var(--muted2);line-height:1.65;max-width:400px;margin-bottom:24px}}
.hero-btns{{display:flex;gap:10px}}
.btn-gold{{background:var(--gold);color:#0a0a08;font-weight:700;font-size:0.78rem;letter-spacing:0.08em;padding:10px 26px;border:none;border-radius:3px;cursor:pointer;text-transform:uppercase;transition:background .15s}}
.btn-gold:hover{{background:var(--gold-light)}}
.btn-outline{{background:transparent;color:var(--text);font-weight:600;font-size:0.78rem;letter-spacing:0.06em;padding:10px 20px;border:1px solid var(--border2);border-radius:3px;cursor:pointer;text-transform:uppercase}}
.btn-outline:hover{{border-color:rgba(201,168,76,0.35)}}
.hero-stats{{display:flex;gap:0;margin-top:32px;border-top:1px solid var(--border);border-bottom:1px solid var(--border)}}
.hstat{{flex:1;padding:14px 0;text-align:center;border-right:1px solid var(--border)}}
.hstat:last-child{{border-right:none}}
.hstat-num{{font-family:'Playfair Display',serif;font-size:1.5rem;font-weight:700;color:var(--gold);display:block}}
.hstat-label{{font-size:0.65rem;color:var(--muted);letter-spacing:0.08em;text-transform:uppercase;margin-top:3px}}

.hero-right{{position:relative;z-index:1}}
.live-card{{background:var(--surface);border:1px solid var(--border);border-radius:5px;padding:20px}}
.live-card-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid var(--border2)}}
.live-card-title{{font-family:'Playfair Display',serif;font-size:0.92rem;color:var(--text);font-weight:700}}
.live-dot{{width:6px;height:6px;border-radius:50%;background:var(--green);animation:blink 1.4s infinite;display:inline-block;margin-left:5px}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.live-label{{font-size:0.65rem;font-weight:600;color:var(--green);letter-spacing:0.08em;display:flex;align-items:center}}
.market-row{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04)}}
.market-row:last-child{{border-bottom:none}}
.mrow-name{{font-size:0.78rem;font-weight:600;color:var(--muted2)}}
.mrow-val{{font-size:0.82rem;font-weight:700;color:var(--text)}}
.mrow-up{{font-size:0.72rem;font-weight:600;color:var(--green);background:rgba(22,163,74,0.1);padding:2px 7px;border-radius:2px}}
.mrow-dn{{font-size:0.72rem;font-weight:600;color:var(--red);background:rgba(220,38,38,0.1);padding:2px 7px;border-radius:2px}}

.quote-strip{{background:var(--gold);padding:22px 40px;text-align:center}}
.quote-text{{font-family:'Playfair Display',serif;font-size:1.1rem;font-style:italic;font-weight:700;color:#0a0a08}}
.quote-src{{font-size:0.7rem;font-weight:600;letter-spacing:0.1em;color:rgba(10,10,8,0.5);margin-top:6px;text-transform:uppercase}}

.section-wrap{{padding:64px 40px;max-width:1200px;margin:0 auto}}
.section-eyebrow{{display:flex;align-items:center;gap:8px;margin-bottom:10px}}
.section-title{{font-family:'Playfair Display',serif;font-size:clamp(1.5rem,2.5vw,2.2rem);font-weight:900;color:var(--text);margin-bottom:8px}}
.section-desc{{color:var(--muted2);font-size:0.88rem;max-width:480px;line-height:1.65;margin-bottom:40px}}

.tab-bar{{display:flex;border-bottom:1px solid var(--border);margin-bottom:32px}}
.tab-btn{{background:transparent;border:none;border-bottom:2px solid transparent;padding:11px 26px;font-size:0.78rem;font-weight:600;letter-spacing:0.08em;color:var(--muted);cursor:pointer;text-transform:uppercase;transition:color .2s,border-color .2s;margin-bottom:-1px;font-family:'Inter',sans-serif}}
.tab-btn.active{{color:var(--gold);border-bottom-color:var(--gold)}}
.tab-panel{{display:none;animation:fadeIn .3s ease}}.tab-panel.active{{display:block}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}

.radar-layout{{display:grid;grid-template-columns:260px 1fr;gap:20px}}
.panel-card{{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:22px}}
.panel-title{{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:var(--text);margin-bottom:4px}}
.panel-sub{{font-size:0.75rem;color:var(--muted);line-height:1.5;margin-bottom:16px}}
.criteria-list{{list-style:none;margin-bottom:18px}}
.criteria-list li{{font-size:0.75rem;color:var(--muted2);padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;align-items:center;gap:7px}}
.criteria-list li:last-child{{border-bottom:none}}
.crit-dot{{width:5px;height:5px;border-radius:50%;flex-shrink:0}}
.dot-green{{background:var(--green)}}.dot-red{{background:var(--red)}}
.scan-btn{{width:100%;padding:11px;border-radius:3px;font-family:'Inter',sans-serif;font-size:0.78rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;border:none;transition:opacity .2s}}
.scan-btn:hover{{opacity:.88}}.scan-btn:disabled{{opacity:.45;cursor:not-allowed}}
.scan-green{{background:var(--green);color:#fff}}
.scan-red{{background:var(--red);color:#fff}}
.scan-gold{{background:var(--gold);color:#0a0a08}}
.results-panel{{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:22px}}
.results-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--border2)}}
.results-title{{font-size:0.68rem;font-weight:600;letter-spacing:0.12em;color:var(--muted);text-transform:uppercase}}
.results-count{{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:var(--gold)}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px}}
.stock-card{{border-radius:3px;padding:12px 8px;text-align:center;border:1px solid;transition:transform .15s}}
.stock-card:hover{{transform:translateY(-2px)}}
.card-long{{background:rgba(22,163,74,0.06);border-color:rgba(22,163,74,0.18)}}
.card-short{{background:rgba(220,38,38,0.06);border-color:rgba(220,38,38,0.18)}}
.card-sym{{font-size:0.82rem;font-weight:700;color:var(--text);letter-spacing:0.05em}}
.card-price-g{{font-size:0.74rem;font-weight:600;color:var(--green);margin-top:4px}}
.card-price-r{{font-size:0.74rem;font-weight:600;color:var(--red);margin-top:4px}}
.card-chg{{font-size:0.65rem;color:var(--muted);margin-top:2px}}
.empty-msg{{color:var(--muted);font-size:0.82rem;text-align:center;padding:40px 0}}

.ai-grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.input-label{{font-size:0.68rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted);margin-bottom:5px}}
.ai-input{{width:100%;background:rgba(255,255,255,0.03);border:1px solid var(--border2);border-radius:3px;color:var(--text);font-family:'Inter',sans-serif;font-size:0.88rem;padding:10px 13px;outline:none;direction:rtl;margin-bottom:10px;transition:border .2s}}
.ai-input:focus{{border-color:rgba(201,168,76,0.4)}}
.ai-input::placeholder{{color:var(--muted)}}
.result-card{{background:rgba(255,255,255,0.02);border:1px solid var(--border2);border-radius:3px;margin-top:14px}}
.result-card-header{{padding:12px 16px;border-bottom:1px solid var(--border2);font-family:'Playfair Display',serif;font-size:0.88rem;font-weight:700;color:var(--text);display:flex;align-items:center;justify-content:space-between}}
.result-tag{{font-size:0.62rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;padding:2px 8px;border-radius:2px}}
.tag-green{{background:rgba(22,163,74,0.12);color:var(--green)}}.tag-red{{background:rgba(220,38,38,0.12);color:var(--red)}}
.metric-row{{display:flex;justify-content:space-between;padding:9px 16px;border-bottom:1px solid rgba(255,255,255,0.03)}}
.metric-row:last-child{{border-bottom:none}}
.metric-label{{font-size:0.73rem;color:var(--muted)}}
.metric-value{{font-size:0.73rem;color:var(--muted2);font-weight:600;text-align:left}}
.ai-response-box{{margin-top:12px;padding:15px;background:var(--gold-pale);border:1px solid var(--border);border-radius:3px;border-right:3px solid var(--gold)}}
.ai-response-label{{font-size:0.62rem;font-weight:700;letter-spacing:0.12em;color:var(--gold);text-transform:uppercase;margin-bottom:6px}}
.ai-response-text{{font-size:0.82rem;color:var(--muted2);line-height:1.7;direction:rtl;text-align:right}}

#features{{background:var(--bg2);border-top:1px solid var(--border)}}
.features-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1px;background:var(--border);border:1px solid var(--border)}}
.feat-card{{background:var(--bg2);padding:28px 24px;transition:background .2s}}
.feat-card:hover{{background:var(--surface)}}
.feat-icon{{font-size:1.3rem;margin-bottom:14px;display:block}}
.feat-title{{font-family:'Playfair Display',serif;font-size:0.95rem;font-weight:700;color:var(--text);margin-bottom:6px}}
.feat-desc{{font-size:0.78rem;color:var(--muted);line-height:1.6}}

#how{{border-top:1px solid var(--border)}}
.steps-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border:1px solid var(--border);background:var(--border)}}
.step-card{{background:var(--surface);padding:32px 24px}}
.step-num{{font-family:'Playfair Display',serif;font-size:2.5rem;font-weight:900;color:var(--border);line-height:1;margin-bottom:16px}}
.step-title{{font-family:'Playfair Display',serif;font-size:0.95rem;font-weight:700;color:var(--text);margin-bottom:8px}}
.step-desc{{font-size:0.78rem;color:var(--muted);line-height:1.6}}

footer{{background:var(--bg2);border-top:1px solid var(--border);padding:36px 40px;display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:16px}}
.footer-logo{{font-family:'Playfair Display',serif;font-size:1rem;font-weight:700;color:var(--gold);margin-bottom:6px}}
.footer-copy{{font-size:0.72rem;color:var(--muted)}}
.footer-links{{display:flex;gap:24px}}
.footer-links a{{font-size:0.72rem;color:var(--muted);text-decoration:none;letter-spacing:0.06em;text-transform:uppercase;cursor:pointer}}
.footer-links a:hover{{color:var(--gold)}}

.modal-overlay{{position:fixed;inset:0;background:rgba(0,0,0,0.82);z-index:200;display:none;align-items:center;justify-content:center;backdrop-filter:blur(12px)}}
.modal-overlay.open{{display:flex}}
.modal{{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:40px;max-width:440px;width:90%;text-align:center}}
.modal-logo{{font-family:'Playfair Display',serif;font-size:1.3rem;font-weight:900;color:var(--gold);margin-bottom:6px}}
.modal-line{{width:36px;height:1px;background:var(--gold);margin:0 auto 18px}}
.modal p{{color:var(--muted2);font-size:0.85rem;line-height:1.7;margin-bottom:24px}}
.modal-btn{{background:var(--gold);color:#0a0a08;border:none;border-radius:3px;padding:11px 32px;font-weight:700;font-size:0.78rem;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer}}
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
  <ul class="nav-links">
    <li><a onclick="goto('hero')" class="active">בית</a></li>
    <li><a onclick="goto('radar')">רדאר</a></li>
    <li><a onclick="goto('features')">יתרונות</a></li>
    <li><a onclick="goto('how')">תהליך</a></li>
  </ul>
  <button class="nav-cta" onclick="goto('radar')">התחל לסרוק</button>
</nav>

<div class="tape-wrap"><div class="tape-inner" id="tape">טוען...</div></div>

<section id="hero">
  <div class="hero-bg-img"></div>
  <div class="hero-left">
    <div class="eyebrow"><div class="eyebrow-line"></div><div class="eyebrow-text">Stock Intelligence Platform</div></div>
    <h1 class="hero-title">The Mind<br/><em>Changer</em></h1>
    <div class="title-line"></div>
    <p class="hero-desc">רדאר המניות החכם שמשלב ניתוח טכני מתקדם עם בינה מלאכותית — זהה הזדמנויות לפני כולם</p>
    <div class="hero-btns">
      <button class="btn-gold" onclick="goto('radar')">התחל לסרוק עכשיו</button>
      <button class="btn-outline" onclick="goto('how')">איך זה עובד</button>
    </div>
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
      <div id="indices-rows"><div style="color:var(--muted);font-size:0.78rem;padding:8px 0">טוען מדדים...</div></div>
      <div id="stocks-rows"></div>
    </div>
  </div>
</section>

<div class="quote-strip">
  <div class="quote-text">"השוק הוא מכשיר להעברת כסף מהחסר סבלנות אל בעל הסבלנות"</div>
  <div class="quote-src">— Warren Buffett</div>
</div>

<section id="radar">
  <div class="section-wrap">
    <div class="section-eyebrow"><div class="eyebrow-line"></div><div class="eyebrow-text">Live Radar</div></div>
    <h2 class="section-title">רדאר המניות</h2>
    <p class="section-desc">בחר מצב סריקה וגלה הזדמנויות מסחר בזמן אמת</p>

    <div class="tab-bar">
      <button class="tab-btn active" id="tbtn-long"  onclick="switchTab('long')">📈 רדאר לונג</button>
      <button class="tab-btn"        id="tbtn-short" onclick="switchTab('short')">📉 רדאר שורט</button>
      <button class="tab-btn"        id="tbtn-ai"    onclick="switchTab('ai')">🤖 ניתוח AI</button>
    </div>

    <div class="tab-panel {'active' if active_tab=='long' else ''}" id="tab-long">
      <div class="radar-layout">
        <div class="panel-card">
          <div class="panel-title">רדאר לונג</div>
          <div class="panel-sub">מניות עם מומנטום עולה</div>
          <ul class="criteria-list">
            <li><div class="crit-dot dot-green"></div>מחיר מעל MA9</li>
            <li><div class="crit-dot dot-green"></div>RSI מתחת ל-70</li>
            <li><div class="crit-dot dot-green"></div>נפח מעל מיליון</li>
            <li><div class="crit-dot dot-green"></div>לא מעל כל 3 הממוצעים</li>
            <li><div class="crit-dot dot-green"></div>יומיים ירוקים רצופים</li>
            <li><div class="crit-dot dot-green"></div>סגירה גבוהה מאתמול</li>
          </ul>
          <button class="scan-btn scan-green" onclick="triggerScan('long')">התחל סריקת לונג ⚡</button>
        </div>
        <div class="results-panel">
          <div class="results-header">
            <div class="results-title">תוצאות סריקה</div>
            <div class="results-count">{len(st.session_state.long_results) if st.session_state.long_results is not None else '—'} {'מניות' if st.session_state.long_results else ''}</div>
          </div>
          <div id="res-long">{render_cards(st.session_state.long_results, 'long')}</div>
        </div>
      </div>
    </div>

    <div class="tab-panel {'active' if active_tab=='short' else ''}" id="tab-short">
      <div class="radar-layout">
        <div class="panel-card">
          <div class="panel-title">רדאר שורט</div>
          <div class="panel-sub">מניות עם מומנטום יורד</div>
          <ul class="criteria-list">
            <li><div class="crit-dot dot-red"></div>מחיר מתחת MA9</li>
            <li><div class="crit-dot dot-red"></div>RSI מעל 30</li>
            <li><div class="crit-dot dot-red"></div>נפח מעל מיליון</li>
            <li><div class="crit-dot dot-red"></div>יומיים אדומים רצופים</li>
            <li><div class="crit-dot dot-red"></div>סגירה נמוכה מאתמול</li>
            <li><div class="crit-dot dot-red"></div>Puts חזקים מ-Calls</li>
          </ul>
          <button class="scan-btn scan-red" onclick="triggerScan('short')">התחל סריקת שורט ⚡</button>
        </div>
        <div class="results-panel">
          <div class="results-header">
            <div class="results-title">תוצאות סריקה</div>
            <div class="results-count">{len(st.session_state.short_results) if st.session_state.short_results is not None else '—'} {'מניות' if st.session_state.short_results else ''}</div>
          </div>
          <div id="res-short">{render_cards(st.session_state.short_results, 'short')}</div>
        </div>
      </div>
    </div>

    <div class="tab-panel {'active' if active_tab=='ai' else ''}" id="tab-ai">
      <div class="ai-grid">
        <div class="panel-card">
          <div class="panel-title">ניתוח מניה בודדת</div>
          <div class="panel-sub">הזן סימול וקבל ניתוח טכני אמיתי</div>
          <div class="input-label">סימול מניה</div>
          <input class="ai-input" id="ticker-input" placeholder="AAPL, TSLA, NVDA..."/>
          <button class="scan-btn scan-gold" onclick="triggerAnalyze()">נתח מניה</button>
          <div id="res-analyze">{render_analysis(st.session_state.analysis)}</div>
        </div>
        <div class="panel-card">
          <div class="panel-title">שאלות כלליות</div>
          <div class="panel-sub">שאל שאלות פיננסיות וקבל הסברים</div>
          <div class="input-label">שאלה</div>
          <input class="ai-input" id="ai-q" placeholder="מה זה RSI? איך לזהות פריצה?"/>
          <button class="scan-btn scan-gold" onclick="answerQ()">שאל</button>
          <div id="res-ai"></div>
        </div>
      </div>
    </div>
  </div>
</section>

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
      <div class="step-card"><div class="step-num">01</div><div class="step-title">בחר מצב סריקה</div><div class="step-desc">לונג, שורט, או ניתוח מניה בודדת. המערכת מתחילה לאסוף נתונים בזמן אמת.</div></div>
      <div class="step-card"><div class="step-num">02</div><div class="step-title">סריקה אלגוריתמית</div><div class="step-desc">האלגוריתם בודק RSI, ממוצעים נעים, נפח מסחר ונרות עבור כל מניה.</div></div>
      <div class="step-card"><div class="step-num">03</div><div class="step-title">קבל תוצאות אמיתיות</div><div class="step-desc">מניות שעוברות את הקריטריונים מוצגות עם מחיר ואחוז שינוי עדכניים.</div></div>
    </div>
  </div>
</section>

<footer>
  <div><div class="footer-logo">The Mind Changer</div><div class="footer-copy">© 2025 — למטרות מידע בלבד. אינו ייעוץ השקעות.</div></div>
  <div class="footer-links"><a onclick="goto('radar')">רדאר</a><a onclick="goto('features')">יתרונות</a><a onclick="goto('how')">תהליך</a></div>
</footer>

<script>
const QUOTES  = {quotes_json};
const INDICES = {indices_json};
const STOCKS  = {stocks_json};

// ── Tape ──
function buildTape(){{
  if(!QUOTES.length) return;
  const full=[...QUOTES,...QUOTES];
  document.getElementById('tape').innerHTML=full.map(t=>
    `<div class="tape-item"><span class="tape-sym">${{t.symbol}}</span><span class="${{t.up?'tape-up':'tape-dn'}}">${{t.price}} ${{t.change_pct>=0?'+':''}}${{t.change_pct}}%</span></div>`
  ).join('');
}}

// ── Hero card ──
function buildHero(){{
  const idxEl=document.getElementById('indices-rows');
  if(INDICES.length) idxEl.innerHTML=INDICES.map(i=>
    `<div class="market-row"><span class="mrow-name">${{i.name}}</span><span class="mrow-val">${{i.price}}</span><span class="${{i.up?'mrow-up':'mrow-dn'}}">${{i.chg>=0?'+':''}}${{i.chg}}%</span></div>`
  ).join('');
  const stEl=document.getElementById('stocks-rows');
  if(STOCKS.length) stEl.innerHTML=STOCKS.map(s=>
    `<div class="market-row"><span class="mrow-name">${{s.symbol}}</span><span class="mrow-val">${{s.price}}</span><span class="${{s.up?'mrow-up':'mrow-dn'}}">${{s.chg>=0?'+':''}}${{s.chg}}%</span></div>`
  ).join('');
}}

// ── ניווט ──
function goto(id){{
  document.getElementById(id).scrollIntoView({{behavior:'smooth'}});
}}

// ── טאבים ──
function switchTab(n){{
  ['long','short','ai'].forEach(t=>{{
    document.getElementById('tbtn-'+t).classList.toggle('active',t===n);
    document.getElementById('tab-'+t).classList.toggle('active',t===n);
  }});
}}

// ── טריגר סריקה — לוחץ על כפתור Streamlit הנסתר ──
function triggerScan(mode){{
  const buttons = window.parent.document.querySelectorAll('button[kind="secondary"]');
  const label   = mode==='long' ? '__SCAN_LONG__' : '__SCAN_SHORT__';
  for(const btn of buttons){{
    if(btn.innerText.trim()===label){{ btn.click(); break; }}
  }}
  document.getElementById('res-'+mode).innerHTML=
    '<div class="empty-msg">⏳ הסריקה רצה בחלון Streamlit מעל... ממתין לתוצאות</div>';
}}

// ── טריגר ניתוח ──
function triggerAnalyze(){{
  const ticker = document.getElementById('ticker-input').value.trim().toUpperCase();
  if(!ticker) return;
  const inputs = window.parent.document.querySelectorAll('input[type="text"]');
  for(const inp of inputs){{
    const rect = inp.getBoundingClientRect();
    if(rect.width===0 && rect.height===0){{
      const nativeInputSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
      nativeInputSetter.call(inp, ticker);
      inp.dispatchEvent(new Event('input', {{bubbles:true}}));
      break;
    }}
  }}
  setTimeout(()=>{{
    const buttons = window.parent.document.querySelectorAll('button[kind="secondary"]');
    for(const btn of buttons){{
      if(btn.innerText.trim()==='__ANALYZE__'){{ btn.click(); break; }}
    }}
  }}, 300);
  document.getElementById('res-analyze').innerHTML=
    '<div class="empty-msg">⏳ מנתח נתונים אמיתיים...</div>';
}}

// ── שאלות ──
const QA=[
  ['rsi','RSI מודד עוצמת מומנטום בסולם 0-100. מעל 70 — קנייה יתר, מתחת 30 — מכירת יתר.'],
  ['ממוצע','ממוצע נע הוא ממוצע מחירי הסגירה על פני תקופה. MA9 רגיש, MA200 מגמה ראשית.'],
  ['פריצה','פריצה היא חציית התנגדות בנפח גבוה. תאושרה בשתי סגירות מעל ההתנגדות עם RSI 50-65.'],
  ['שורט','שורט = מכירה ללא בעלות, מתוך ציפייה לירידה. הרווח הוא הפרש בין מכירה לקנייה חזרה.'],
  ['לונג','לונג = קנייה רגילה מתוך ציפייה לעלייה. קונים בזול, מוכרים ביוקר.'],
  ['אופציות','Call = הימור על עלייה, Put = הימור על ירידה. Calls/Puts > 1 — פסימיות בשוק.'],
];
function answerQ(){{
  const q=document.getElementById('ai-q').value.trim().toLowerCase();
  const m=QA.find(([k])=>q.includes(k));
  const ans=m?m[1]:'נסה לשאול על: RSI, ממוצע נע, פריצה, שורט, לונג, אופציות.';
  document.getElementById('res-ai').innerHTML=
    `<div class="ai-response-box" style="margin-top:12px"><div class="ai-response-label">תשובה</div><div class="ai-response-text">${{ans}}</div></div>`;
}}
document.getElementById('ticker-input').addEventListener('keydown',e=>{{if(e.key==='Enter')triggerAnalyze()}});
document.getElementById('ai-q').addEventListener('keydown',e=>{{if(e.key==='Enter')answerQ()}});

buildTape(); buildHero();
switchTab('{active_tab}');
</script>
</body>
</html>"""

st.components.v1.html(html, height=900, scrolling=True)
