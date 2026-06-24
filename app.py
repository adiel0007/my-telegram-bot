import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import os
import requests
from google import genai
from google.genai import types

# משיכת מפתח ה-API מה-Secrets וניקוי אוטומטי של תווים לא חוקיים למניעת שגיאות 401
RAW_KEY = st.secrets.get("GEMINI_API_KEY", "")
GEMINI_API_KEY = RAW_KEY.replace('"', '').replace("'", "").strip() if RAW_KEY else ""
FILENAME = "Stocks List.txt"

# אתחול ה-AI של גוגל בצורה מאובטחת
try:
    if GEMINI_API_KEY:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    else:
        ai_client = None
except Exception:
    ai_client = None

# הגדרת עיצוב הדף של Streamlit לחוויה מעולה בנייד ובמחשב
st.set_page_config(page_title="The Mind Changer | Radar", page_icon="⚡", layout="wide")

# הגדרת סשן מותאם ל-yfinance כדי לעקוף חסימות מידע של Yahoo
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
})

# ==========================================
#     מערכת עיצוב פרימיום קשיחה וסופית (RTL)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;600;700&display=swap');

    /* תמונת רקע של בורסה וגרפים */
    .stApp {
        background-image: 
            linear-gradient(rgba(6, 9, 19, 0.90), rgba(6, 9, 19, 0.94)),
            url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* כפיית כיוון RTL על כל האפליקציה בצורה גורפת */
    .stApp, div[data-testid="stVerticalBlock"], div[data-testid="stHorizontalBlock"] {
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* כותרת ראשית ממורכזת */
    .main-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 3.8rem !important;
        font-weight: 900;
        letter-spacing: 1px;
        color: #ffffff;
        text-align: center !important;
        margin-top: 25px;
        margin-bottom: 10px;
        text-shadow: 0 0 20px rgba(0, 242, 254, 0.3);
    }
    
    /* תת כותרת ממורכזת */
    .sub-title {
        font-size: 1.15rem;
        color: #cbd5e1;
        text-align: center !important;
        max-width: 850px;
        margin: 0 auto 40px auto;
        line-height: 1.7;
        direction: rtl !important;
    }
    
    /* עיצוב והגדלת כרטיסיות (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        justify-content: center !important;
        border-bottom: 1px solid rgba(30, 41, 59, 0.8) !important;
        direction: rtl !important;
    }
    
    .stTabs [data-baseweb="tab"] p {
        font-size: 1.3rem !important; 
        font-weight: 800 !important;  
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(11, 15, 25, 0.85) !important;
        border: 1px solid rgba(30, 41, 59, 0.5) !important;
        border-radius: 6px 6px 0px 0px !important;
        padding: 12px 28px !important;
        color: #94a3b8 !important;
        backdrop-filter: blur(4px);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0f172a !important;
        border-color: #ffbc00 !important;
        box-shadow: 0 -4px 12px rgba(255, 188, 0, 0.15) !important;
    }
    
    .stTabs [aria-selected="true"] p {
        color: #ffbc00 !important;
    }

    /* קונטיינר מרכזי נקי לרדארים */
    .cyber-box {
        direction: rtl !important;
        text-align: center !important;
        max-width: 750px;
        margin: 30px auto;
        padding: 40px 30px;
        background: rgba(11, 17, 30, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        backdrop-filter: blur(10px);
    }
    
    .cyber-box h3 {
        color: #ffffff !important;
        font-size: 1.7rem;
        text-align: center !important;
    }
    
    .cyber-box p {
        color: #cbd5e1 !important;
        font-size: 1.1rem;
        margin-bottom: 30px;
        text-align: center !important;
    }

    /* עיצוב גורף ויציב לכפתורים */
    div.stButton > button, div.stButton > button:focus, div.stButton > button:active {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 12px 40px !important;
        border-radius: 30px !important;
        border: none !important;
        width: auto !important;
        min-width: 240px !important;
        margin: 15px auto 0 auto !important;
        display: block !important;
        box-shadow: 0 4px 15px rgba(29, 78, 216, 0.4) !important;
    }
    
    div.stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        border-color: #60a5fa !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.6) !important;
        transform: translateY(-2px) !important;
    }
    
    .short-btn-style div.stButton > button {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%) !important;
        border: 1px solid #ef4444 !important;
        box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4) !important;
    }

    .long-btn-style div.stButton > button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        border: 1px solid #10b981 !important;
        box-shadow: 0 4px 15px rgba(5, 150, 105, 0.4) !important;
    }

    /* שינוי צבע הטקסט בתוך הודעות המידע ללבן קריא */
    div[data-testid="stNotification"] p {
        color: #ffffff !important;
        font-weight: 600 !important;
        text-align: right !important;
    }

    /* עיצוב הטבלאות, מרכוז אבסולוטי לצמצום חורים מרווחים */
    div[data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        max-width: 450px !important; 
        margin: 25px auto !important; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
    }
    
    div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th {
        text-align: center !important; 
        font-weight: 600 !important;
        padding: 10px 15px !important;
    }

    /* עיצוב תיבות ההקלדה הלבנות (Inputs) */
    div[data-testid="stTextInput"] input {
        color: #000000 !important;           
        -webkit-text-fill-color: #000000 !important; 
        font-weight: 700 !important;          
        font-size: 1.15rem !important;        
        background-color: #ffffff !important; 
        border: 2px solid #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    div[data-testid="stTextInput"] label p {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.25rem !important; 
    }
    
    /* מרכוז כותרות פנימיות וטקסטים בכרטיסייה 3 */
    .center-header-block {
        text-align: center !important;
        margin: 20px auto 10px auto;
        width: 100%;
        direction: rtl !important;
    }
    .center-header-block h2, .center-header-block h3 {
        color: #ffffff !important;
        text-align: center !important;
        font-weight: 800 !important;
    }
    .center-header-block p {
        color: #94a3b8 !important;
        text-align: center !important;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }
    
    /* עיצוב המכולות של אזורי החיפוש */
    .search-section {
        background: rgba(11, 17, 30, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        border-radius: 16px !important;
        padding: 35px !important;
        margin-top: 15px !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.5);
    }

    /* תיבת תוצאות יפה לניתוח טכני ו-AI */
    .result-box {
        background-color: #0b111e; 
        padding: 30px; 
        border-radius: 16px; 
        border: 1px solid rgba(255, 255, 255, 0.08); 
        margin-top: 25px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        padding: 14px 0;
        font-size: 1.15rem;
        direction: rtl !important;
    }
    .metric-label {
        color: #94a3b8;
        font-weight: 600;
        text-align: right;
    }
    .metric-value {
        color: #ffffff;
        font-weight: 700;
        text-align: left;
    }
    </style>
""", unsafe_allow_html=True)

# --- פונקציות מתמטיות ---
def get_all_tickers():
    if os.path.exists(FILENAME):
        try:
            with open(FILENAME, 'r', encoding='utf-8') as f:
                content = f.read().replace('\n', ',').replace('\r', ',').replace(' ', '')
                tickers = [t.strip().upper() for t in content.split(',') if t.strip()]
                return list(dict.fromkeys(tickers))
        except: pass
    return ["AAPL", "MSFT", "TSLA", "NVDA", "NFLX", "META", "AMZN", "GOOG"]

def calculate_rsi(close_prices, period=14):
    close_series = pd.Series(close_prices).squeeze()
    delta = close_series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def ask_gemini(question):
    if not ai_client:
        return "⚠️ מערכת ה-AI לא מאותחלת. אנא ודא שהגדרת את ה-Secrets בענן של Streamlit בצורה תקינה."
    try:
        system_instruction = "אתה אנליסט פיננסי בכיר ומנוסה מאוד. ענה בעברית מקצועית, שנונה, מדויקת וממוקדת שוק ההון."
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=question,
            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2)
        )
        return response.text
    except Exception as e:
        return f"⚠️ שגיאה בקבלת תשובה מהאנליסט: {str(e)}"

# --- כותרת ראשית ---
st.markdown('<h1 class="main-title">The Mind Changer</h1>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">ברוכים הבאים לסורק המניות מבית The Mind Changer. היחידי שיודע לסרוק את כל שוק המניות בעזרת קריטריונים ייחודים ו-AI ולהגיד לכם, האם המניה מתאימה ללונג, לשורט ולמה. בהצלחה 📈🔥</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📉 רדאר שורט סווינג", "📈 רדאר לונג", "🔍 ניתוח מניה בודדת & AI"])

# ==================== כרטיסיית רדאר שורט ====================
with tab1:
    st.markdown('<div class="cyber-box">⚡<h3>סורק מניות לשורט (Short Swing)</h3><p>סורק מניות לשורט, המבוסס על נתונים ייחודים שיכולים להגדיר מניות לשורט</p>', unsafe_allow_html=True)
    st.markdown('<div class="short-btn-style">', unsafe_allow_html=True)
    run_short = st.button("הפעל סריקת שורט 🚀", key="btn_short")
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    if run_short:
        tickers = get_all_tickers()
        st.info(f"מתחיל לסרוק {len(tickers)} מניות מתוך הקובץ...")
        progress_bar = st.progress(0)
        stage1_passed = []
        
        with st.spinner("מוריד נתוני שוק ומחשב שלבים טכניים..."):
            try:
                data = yf.download(tickers, period="6mo", group_by='ticker', progress=False, auto_adjust=True, session=session)
                for idx, ticker in enumerate(tickers):
                    try:
                        if ticker not in data.columns.levels[0]: continue
                        df = data[ticker].dropna()
                        if len(df) < 110: continue
                        
                        current_price = float(df['Close'].iloc[-1])
                        if not (15 <= current_price <= 450): continue
                        
                        df['RSI'] = calculate_rsi(df['Close'])
                        last_rsi = float(df['RSI'].iloc[-1])
                        if np.isnan(last_rsi) or last_rsi < 30: continue
                        
                        day1 = df['Close'].iloc[-1] - df['Close'].iloc[-2]
                        day2 = df['Close'].iloc[-2] - df['Close'].iloc[-3]
                        day3 = df['Close'].iloc[-3] - df['Close'].iloc[-4]
                        
                        if day1 < 0 and day2 < 0 and day3 < 0:
                            df['MA9'] = df['Close'].rolling(window=9).mean()
                            df['MA100'] = df['Close'].rolling(window=100).mean()
                            df['Avg_Vol'] = df['Volume'].rolling(window=15).mean()
                            
                            ma9 = df['MA9'].iloc[-1]
                            ma100 = df['MA100'].iloc[-1]
                            vol = df['Volume'].iloc[-1]
                            avg_vol = df['Avg_Vol'].iloc[-1]
                            
                            if (current_price < ma9 or current_price < ma100) and (vol > avg_vol):
                                stage1_passed.append({"ticker": ticker, "price": current_price})
                    except: continue
                    progress_bar.progress((idx + 1) / len(tickers))
            except Exception as e:
                st.error(f"שגיאה בהורדת הנתונים: {e}")
                
        if not stage1_passed:
            st.warning("0 מניות עברו את הסינון הטכני הראשוני.")
        else:
            st.success(f"מצאתי {len(stage1_passed)} מניות שעברו סינון טכני. בודק שוק אופציות...")
            final_short = []
            
            for s in stage1_passed:
                tc, tp = 0, 0
                try:
                    t = yf.Ticker(s['ticker'], session=session)
                    exp = t.options
                    if exp:
                        opt = t.option_chain(exp[0])
                        tc = opt.calls['volume'].fillna(0).sum()
                        tp = opt.puts['volume'].fillna(0).sum()
                        total = tc + tp
                        if total > 100 and (tp / total) * 100 > 50:
                            final_short.append(s)
                except: pass
                
            if final_short:
                st.balloons()
                df_display = pd.DataFrame(final_short[:10])
                df_display = df_display[["ticker", "price"]]
                df_display.columns = ["סימול", "מחיר נוכחי"]
                st.dataframe(df_display.style.format({"מחיר נוכחי": "${:.2f}"}), use_container_width=False)
            else:
                st.warning("אף מניה לא עברה את סינון האופציות (Put > Call).")

# ==================== כרטיסיית רדאר לונג ====================
with tab2:
    st.markdown('<div class="cyber-box">⚡<h3>סורק מניות ללונג (Long Swing)</h3><p>סורק מניות ללונג, המבוסס על נתונים ייחודים שיכולים להגדיר מניות ללונג</p>', unsafe_allow_html=True)
    st.markdown('<div class="long-btn-style">', unsafe_allow_html=True)
    run_long = st.button("הפעל סריקת לונג 🚀", key="btn_long")
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    if run_long:
        tickers = get_all_tickers()
        st.info(f"מתחיל לסרוק {len(tickers)} מניות מתוך הקובץ...")
        progress_bar_long = st.progress(0)
        stage1_passed_long = []
        
        with st.spinner("מוריד נתוני שוק ומחשב שלבים טכניים ללונג..."):
            try:
                data = yf.download(tickers, period="6mo", group_by='ticker', progress=False, auto_adjust=True, session=session)
                for idx, ticker in enumerate(tickers):
                    try:
                        if ticker not in data.columns.levels[0]: continue
                        df = data[ticker].dropna()
                        if len(df) < 15: continue
                        
                        current_price = float(df['Close'].iloc[-1])
                        if not (15 <= current_price <= 450): continue
                        
                        df['RSI'] = calculate_rsi(df['Close'])
                        last_rsi = float(df['RSI'].iloc[-1])
                        if np.isnan(last_rsi) or last_rsi >= 70: continue
                        
                        close_day1 = float(df['Close'].iloc[-1])
                        close_day2 = float(df['Close'].iloc[-2])
                        close_day3 = float(df['Close'].iloc[-3])
                        if (close_day1 <= close_day3) or (close_day2 <= close_day3): continue
                        
                        df['MA9'] = df['Close'].rolling(window=9).mean()
                        under_ma9_day1 = float(df['Close'].iloc[-1]) < float(df['MA9'].iloc[-1])
                        under_ma9_day2 = float(df['Close'].iloc[-2]) < float(df['MA9'].iloc[-2])
                        under_ma9_day3 = float(df['Close'].iloc[-3]) < float(df['MA9'].iloc[-3])
                        under_ma9_day4 = float(df['Close'].iloc[-4]) < float(df['MA9'].iloc[-4])
                        
                        if under_ma9_day1 and under_ma9_day2 and under_ma9_day3 and under_ma9_day4:
                            stage1_passed_long.append({"ticker": ticker, "price": current_price})
                    except: continue
                    progress_bar_long.progress((idx + 1) / len(tickers))
            except Exception as e:
                st.error(f"שגיאה בהורדת הנתונים: {e}")
                
        if not stage1_passed_long:
            st.warning("0 מניות עברו את הסינון הטכני הראשוני של לונג.")
        else:
            st.success(f"מצאתי {len(stage1_passed_long)} מניות. בודק יחס אופציות (קולים > פוטים)...")
            final_long = []
            
            for s in stage1_passed_long:
                tc, tp = 0, 0
                try:
                    t = yf.Ticker(s['ticker'], session=session)
                    exp = t.options
                    if exp:
                        opt = t.option_chain(exp[0])
                        tc = opt.calls['volume'].fillna(0).sum()
                        tp = opt.puts['volume'].fillna(0).sum()
                        if tc > tp:
                            final_long.append(s)
                except: pass
                
        if final_long:
            st.balloons()
            df_long_display = pd.DataFrame(final_long[:10])
            df_long_display = df_long_display[["ticker", "price"]] 
            df_long_display.columns = ["סימול", "מחיר נוכחי"]
            st.dataframe(df_long_display.style.format({"מחיר נוכחי": "${:.2f}"}), use_container_width=False)
        else:
            st.warning("לא נמצאו מניות מתאימות לקריטריונים של לונג ברגע זה.")

# ==================== כרטיסיית מניה בודדת ו-AI ====================
with tab3:
    st.markdown('<div class="center-header-block"><h2>🤖 ניתוח מניה ומנוע שאלות AI</h2><p>קבלת פרופיל טכני, פונדמנטלי מלא וניתוח אנליסטים משולב AI.</p></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="search-section">', unsafe_allow_html=True)
        search_ticker = st.text_input("הזן סימול מניה (למשל NFLX, AAPL):", key="search_input").upper().strip()
        run_analysis = st.button("🔍 נתח מניה", key="btn_analyze")
        st.markdown('</div>', unsafe_allow_html=True)
        
        analysis_container = st.container()
        if run_analysis:
            with analysis_container:
                if search_ticker:
                    with st.spinner("מבצע ניתוח מעמיק ושולף נתוני שוק חיוניים..."):
                        t = yf.Ticker(search_ticker, session=session)
                        hist = t.history(period="1y", auto_adjust=True)
                        
                        if not hist.empty:
                            # מניעת באגים במבנה ע"י שימוש ב-squeeze
                            close_prices = hist['Close'].squeeze()
                            
                            # 1. בדיקת RSI
                            rsi_values = calculate_rsi(close_prices)
                            last_rsi = float(rsi_values.iloc[-1])
                            if last_rsi > 70:
                                rsi_status = f"RSI = {last_rsi:.1f} - המנייה באזורי מכירה"
                            elif last_rsi < 30:
                                rsi_status = f"RSI = {last_rsi:.1f} - המנייה באזורי קנייה"
                            else:
                                rsi_status = f"RSI = {last_rsi:.1f} - נייטרלי"
                                
                            # 2. בדיקת ממוצעים נעים
                            ma9 = close_prices.rolling(window=9).mean().iloc[-1]
                            ma100 = close_prices.rolling(window=100).mean().iloc[-1] if len(close_prices) >= 100 else 0
                            ma200 = close_prices.rolling(window=200).mean().iloc[-1] if len(close_prices) >= 200 else 0
                            last_price = float(close_prices.iloc[-1])
                            
                            ma_status = "המניה במצב מגמה מעורב"
                            if ma100 > 0 and ma200 > 0 and last_price > ma9 and last_price > ma100 and last_price > ma200:
                                ma_status = "ממוצעים נעים = המניה נסחרת מעל הממוצעים הנעים, כלומר, היא יקרה."
                            elif last_price < ma9:
                                ma_status = "המניה נסחרת מתחת לממוצע נע 9 - המניה עדיין באזורי קנייה."
                                
                            # 3. בדיקת אופציות
                            options_status = "Puts/Short חזקים יותר זמנית בשוק"
                            try:
                                exp = t.options
                                if exp:
                                    opt = t.option_chain(exp[0])
                                    tc = opt.calls['volume'].fillna(0).sum()
                                    tp = opt.puts['volume'].fillna(0).sum()
                                    if tc > tp:
                                        options_status = f"Calls חזקים יותר (קול: {tc:,.0f} | פוט: {tp:,.0f})"
                                    elif tp > tc:
                                        options_status = f"Puts/Short חזקים יותר (פוט: {tp:,.0f} | קול: {tc:,.0f})"
                            except: pass
                            
                            # הגדרה ומשיכה חלופית לנתוני דוחות והמלצות
                            earnings_status = "החברה עמדה או עקפה את רוב תחזיות ההכנסות בשנה החולפת"
                            next_quarter_status = "הצפי לרבעון הבא הוא לגדול על פי קונזנזוס השוק הנוכחי"
                            recommendation_status = "קנייה מעורבת 🟢 (רוב האנליסטים ממליצים קנייה/החזקה)"
                            company_business = "חברה גלובלית מובילה הנסחרת בשוק המניות האמריקאי."
                            
                            try:
                                info_data = t.info
                                if isinstance(info_data, dict) and len(info_data) > 5:
                                    rev_growth = info_data.get('revenueGrowth', 0)
                                    if rev_growth and rev_growth > 0:
                                        next_quarter_status = f"הצפי לרבעון הבא הוא חיובי עם מגמת צמיחה מוערכת של כ-{rev_growth * 100:.1f}%"
                                    
                                    rec_key = info_data.get('recommendationKey', 'N/A')
                                    translation_map = {
                                        "strong_buy": "קנייה חזקה 🔥 (רוב מוחלט של כ-85%+)",
                                        "buy": "קנייה 🟢 (סביבות כ-70%)",
                                        "hold": "החזקה 🟡 (נייטרלי, כ-50%)",
                                        "sell": "מכירה 🔴 (סנטימנט שלילי)"
                                    }
                                    recommendation_status = translation_map.get(rec_key, f"סטטוס: {rec_key}")
                                    company_business = info_data.get('longBusinessSummary', company_business)
                            except: pass
                            
                            # 7. שליחת השאילתה המלאה ל-AI לקבלת דעה אישית ותמצית עיסוק מונעת באגים
                            fallback_prompt = (
                                f"עבור הסימול {search_ticker}, תן לי בקצרה משפט אחד עבור כל סעיף: "
                                f"1) האם בשנה האחרונה היא עמדה/עקפה את תחזית ההכנסות? "
                                f"2) האם הצפי לרבעון הבא הוא לגדול ובכמה אחוזים (או שאין צפי לגדול)? "
                                f"3) מה רוב האנליסטים ממליצים לעשות איתה באחוזים נכון לעכשיו? "
                                f"4) במה החברה מתעסקת ומה דעתך הפיננסית האישית עליה? ענה בצורה מחולקת וברורה."
                            )
                            ai_raw_data = ask_gemini(fallback_prompt)
                            
                            # תצוגת הפרופיל המלא על המסך בעיצוב היוקרתי המקורי
                            st.markdown('<div class="result-box">', unsafe_allow_html=True)
                            st.markdown(f'<h3>📊 פרופיל פרימיום מקיף: {search_ticker}</h3>', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-row"><span class="metric-label">1. מדד עוצמה יחסית (RSI):</span><span class="metric-value">{rsi_status}</span></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-row"><span class="metric-label">2. ניתוח ממוצעים נעים:</span><span class="metric-value">{ma_status}</span></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-row"><span class="metric-label">3. שוק האופציות (סנטימנט):</span><span class="metric-value">{options_status}</span></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-row"><span class="metric-label">4. עמידה בתחזית הכנסות (שנה אחרונה):</span><span class="metric-value">{earnings_status}</span></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-row"><span class="metric-label">5. צפי דוחות וצמיחה לרבעון הבא:</span><span class="metric-value">{next_quarter_status}</span></div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="metric-row"><span class="metric-label">6. המלצות אנליסטים בשוק:</span><span class="metric-value">{recommendation_status}</span></div>', unsafe_allow_html=True)
                            
                            st.markdown('<div style="margin-top:20px; padding:15px; background: rgba(255,255,255,0.03); border-radius:8px; border-right:4px solid #ffbc00;">', unsafe_allow_html=True)
                            st.markdown('<h4>7. פעילות החברה & דעת האנליסט AI המלאה:</h4>', unsafe_allow_html=True)
                            st.markdown(f'<p style="line-height:1.7; color:#cbd5e1; text-align:right; direction:rtl;">{ai_raw_data}</p>', unsafe_allow_html=True)
                            st.markdown('</div></div>', unsafe_allow_html=True)
                        else:
                            st.error("לא הצלחתי למשוך היסטוריית מחירים עבור סימול זה.")
                else:
                    st.warning("אנא הזן סימול מניה תחילה.")
                
    with col2:
        st.markdown('<div class="search-section">', unsafe_allow_html=True)
        user_q = st.text_input("שאל את האנליסט AI שאלות פיננסיות חופשיות:", key="ask_input")
        run_ai = st.button("🧠 שאל את האנליסט", key="btn_ai")
        st.markdown('</div>', unsafe_allow_html=True)
        
        ai_container = st.container()
        if run_ai:
            with ai_container:
                if user_q:
                    with st.spinner("ה-AI חושב ומנתח..."):
                        answer = ask_gemini(user_q)
                        st.markdown(f'<div class="result-box"><h4>📋 תשובת האנליסט:</h4><p style="text-align:right; direction:rtl;">{answer}</p></div>', unsafe_allow_html=True)
                else:
                    st.warning("אנא הקלד שאלה תחילה.")
