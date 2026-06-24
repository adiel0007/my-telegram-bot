import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import os
import time
from google import genai
from google.genai import types

# הגדרות בסיסיות
GEMINI_API_KEY = "AQ.Ab8RN6JI56jLqTcysBdf4I4sWDgn89UCTGLzoT0y2ZVVL0giuw" 
FILENAME = "Stocks List.txt"

# אתחול ה-AI של גוגל
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# הגדרת עיצוב הדף של Streamlit לחוויה מעולה בנייד ובמחשב
st.set_page_config(page_title="The Mind Changer | Radar", page_icon="⚡", layout="wide")

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
    .short-btn-style div.stButton > button:hover {
        background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
    }

    .long-btn-style div.stButton > button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        border: 1px solid #10b981 !important;
        box-shadow: 0 4px 15px rgba(5, 150, 105, 0.4) !important;
    }
    .long-btn-style div.stButton > button:hover {
        background: linear-gradient(135deg, #10b981 0%, #065f46 100%) !important;
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

    /* תיבת תוצאות */
    .result-box {
        background-color: #0f172a; 
        padding: 25px; 
        border-radius: 12px; 
        border: 1px solid #1e293b; 
        margin-top: 25px;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.6);
    }
    </style>
""", unsafe_allow_html=True)

# --- פונקציות מתמטיות וטעינה ---
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
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def ask_gemini(question):
    try:
        system_instruction = "אתה אנליסט פיננסי בכיר. ענה בעברית מקצועית, מדויקת וממוקדת שוק ההון."
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=question,
            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.3)
        )
        return response.text
    except Exception as e:
        return f"⚠️ שגיאה בחיבור ל-AI: {str(e)}"

# --- כותרת ראשית ---
st.markdown('<h1 class="main-title">The Mind Changer</h1>', unsafe_allow_html=True)

# --- ברכת ברוכים הבאים בעמוד הראשי ---
st.markdown('<div class="sub-title">ברוכים הבאים לסורק המניות מבית The Mind Changer. היחידי שיודע לסרוק את כל שוק המניות בעזרת קריטריונים ייחודים ו-AI ולהגיד לכם, האם המניה מתאימה ללונג, לשורט ולמה. בהצלחה 📈🔥</div>', unsafe_allow_html=True)

# חלוקה לכרטיסיות (Tabs)
tab1, tab2, tab3 = st.tabs(["📉 רדאר שורט סווינג", "📈 רדאר לונג", "🔍 ניתוח מניה בודדת & AI"])

# ==================== כרטיסיית רדאר שורט ====================
with tab1:
    st.markdown('<div class="cyber-box">⚡'
                '<h3>סורק מניות לשורט (Short Swing)</h3>'
                '<p>סורק מניות לשורט, המבוסס על נתונים ייחודים שיכולים להגדיר מניות לשורט</p>', unsafe_allow_html=True)
    
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
                data = yf.download(tickers, period="6mo", group_by='ticker', progress=False, auto_adjust=True)
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
                tc = 0
                tp = 0
                try:
                    t = yf.Ticker(s['ticker'])
                    exp = t.options
                    if exp:
                        opt = t.option_chain(exp[0])
                        tc = opt.calls['volume'].fillna(0).sum()
                        tp = opt.puts['volume'].fillna(0).sum()
                        total = tc + tp
                        if total > 100:
                            put_pct = (tp / total) * 100
                            if put_pct > 50:
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
    st.markdown('<div class="cyber-box">⚡'
                '<h3>סורק מניות ללונג (Long Swing)</h3>'
                '<p>סורק מניות ללונג, המבוסס על נתונים ייחודים שיכולים להגדיר מניות ללונג</p>', unsafe_allow_html=True)
    
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
                data = yf.download(tickers, period="6mo", group_by='ticker', progress=False, auto_adjust=True)
                for idx, ticker in enumerate(tickers):
                    try:
                        if ticker not in data.columns.levels[0]: continue
                        df = data[ticker].dropna()
                        if len(df) < 15: continue
                        
                        current_price = float(df['Close'].iloc[-1])
                        
                        # קריטריון 1: טווח מחיר 15-450 כולל ספליטים
                        if not (15 <= current_price <= 450): continue
                        
                        # קריטריון 2: מדד RSI חייב להיות מתחת ל-70 בנר יום האחרון
                        df['RSI'] = calculate_rsi(df['Close'])
                        last_rsi = float(df['RSI'].iloc[-1])
                        if np.isnan(last_rsi) or last_rsi >= 70: continue
                        
                        # קריטריון 3: מחיר סגירה של היום (1-) ואתמול (2-) גבוה מהיום השלישי שלפני האחרון (3-)
                        close_day1 = float(df['Close'].iloc[-1])
                        close_day2 = float(df['Close'].iloc[-2])
                        close_day3 = float(df['Close'].iloc[-3])
                        if (close_day1 <= close_day3) or (close_day2 <= close_day3): continue
                        
                        # קריטריון 4: היסחרות מתחת לממוצע נע 9 ב-4 ימי המסחר האחרונים ברציפות
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
                tc = 0
                tp = 0
                try:
                    t = yf.Ticker(s['ticker'])
                    exp = t.options
                    if exp:
                        opt = t.option_chain(exp[0])
                        tc = opt.calls['volume'].fillna(0).sum()
                        tp = opt.puts['volume'].fillna(0).sum()
                        
                        # קריטריון אופציות: יחס אופציות קול (Calls) גדול מפוט (Puts)
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
    st.markdown('<div class="center-header-block">'
                '<h2>🤖 ניתוח מניה ומנוע שאלות AI</h2>'
                '<p>בעמוד זה תוכלו לקבל ניתוח טכני מהיר ומיידי של מדדי מפתח עבור כל מניה בשוק, או להתייעץ ולקבל תשובות מקצועיות וממוקדות מאנליסט ה-AI הבכיר של המערכת.</p>'
                '</div>', unsafe_allow_html=True)
    
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
                    with st.spinner("מושך נתונים..."):
                        t = yf.download(search_ticker, period="6mo", auto_adjust=True)
                        if not t.empty:
                            t['RSI'] = calculate_rsi(t['Close'])
                            last_row = t.iloc[-1]
                            st.markdown('<div class="result-box">', unsafe_allow_html=True)
                            st.metric("מחיר נוכחי", f"${float(last_row['Close']):.2f}")
                            st.metric("מדד RSI", f"{float(last_row['RSI']):.1f}")
                            st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.error("המניה לא נמצאה.")
                else:
                    st.warning("אנא הזן סימול.")
                
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
                        st.markdown(f'<div class="result-box">'
                                    f'<h4>📋 תשובת האנליסט:</h4><p style="text-align:right; direction:rtl;">{answer}</p></div>', unsafe_allow_html=True)
                else:
                    st.warning("אנא הקלד שאלה תחילה.")
