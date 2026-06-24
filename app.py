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
#      עיצוב עתידני מותאם אישית (Cyber Wall Street)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@300;400;600&display=swap');

    /* רקע עמוק עם אפקט רשת גרפים דיגיטלית של בורסה */
    .stApp {
        background-color: #060913;
        background-image: 
            linear-gradient(rgba(0, 242, 254, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 242, 254, 0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* כותרת ראשית - אפקט זוהר לבן-דיגיטלי */
    .main-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 4rem !important;
        font-weight: 900;
        letter-spacing: 2px;
        color: #ffffff;
        text-align: center;
        margin-top: 30px;
        margin-bottom: 10px;
        text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
    }
    
    /* תת כותרת ממורכזת ויוקרתית */
    .sub-title {
        font-size: 1.15rem;
        color: #94a3b8;
        text-align: center;
        max-width: 850px;
        margin: 0 auto 50px auto;
        line-height: 1.7;
        direction: rtl;
    }
    
    /* עיצוב כרטיסיות (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        justify-content: center;
        border-bottom: 1px solid #1e293b;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #0b0f19;
        border: 1px solid #1e293b;
        border-radius: 6px 6px 0px 0px;
        padding: 12px 28px;
        color: #64748b;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.25s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #f8fafc;
        background-color: #1e293b;
        border-color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #111827 !important;
        color: #ffbc00 !important;
        border-color: #ffbc00 !important;
        box-shadow: 0 -4px 12px rgba(255, 188, 0, 0.15);
    }

    /* קונטיינר מרכזי מהודק ומיושר לחלוטין */
    .tab-content-container {
        direction: rtl;
        text-align: center;
        max-width: 750px;
        margin: 40px auto;
        padding: 40px 30px;
        background: rgba(11, 15, 25, 0.9);
        border: 1px solid #1e293b;
        border-radius: 16px;
        box-sizing: border-box;
        box-shadow: 0 20px 40px rgba(0,0,0,0.7);
        backdrop-filter: blur(8px);
    }
    
    .tab-content-container h3 {
        color: #ffffff;
        font-size: 1.8rem;
        margin-bottom: 15px;
    }
    
    .tab-content-container p {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 35px;
        line-height: 1.6;
    }

    /* תיקון וכפייה של עיצוב הכפתור הממורכז - ביטול הרקע הלבן הדיפולטיבי */
    div.stButton > button {
        color: #000000 !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        padding: 14px 40px !important;
        border-radius: 30px !important;
        width: auto !important;
        min-width: 260px !important;
        margin: 0 auto !important;
        display: inline-block !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.3s ease !important;
    }
    
    /* התאמת צבע ייעודית לכפתור בתוך תיבת שורט */
    .short-container div.stButton > button {
        background: #ef4444 !important;
        border: 1px solid #f87171 !important;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.4) !important;
    }
    .short-container div.stButton > button:hover {
        background: #dc2626 !important;
        box-shadow: 0 0 25px rgba(239, 68, 68, 0.7) !important;
        transform: translateY(-2px);
    }

    /* התאמת צבע ייעודית לכפתור בתוך תיבת לונג */
    .long-container div.stButton > button {
        background: #10b981 !important;
        border: 1px solid #34d399 !important;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.4) !important;
    }
    .long-container div.stButton > button:hover {
        background: #059669 !important;
        box-shadow: 0 0 25px rgba(16, 185, 129, 0.7) !important;
        transform: translateY(-2px);
    }

    /* עיצוב טבלאות נתונים */
    .stDataFrame {
        background-color: #0b0f17;
        border: 1px solid #1e293b;
        border-radius: 8px;
        margin-top: 25px;
    }
    
    .rtl-text {
        direction: rtl;
        text-align: right;
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

# --- כותרת ראשית מעוצבת של האתר ---
st.markdown('<h1 class="main-title">The Mind Changer</h1>', unsafe_allow_html=True)

# --- ברכת ברוכים הבאים בעמוד הראשי ---
st.markdown('<div class="sub-title">ברוכים הבאים לסורק המניות מבית The Mind Changer. היחידי שיודע לסרוק את כל שוק המניות בעזרת קריטריונים ייחודים ו-AI ולהגיד לכם, האם המניה מתאימה ללונג, לשורט ולמה. בהצלחה</div>', unsafe_allow_html=True)

# חלוקה לכרטיסיות (Tabs)
tab1, tab2, tab3 = st.tabs(["📉 רדאר שורט סווינג", "📈 רדאר לונג", "🔍 ניתוח מניה בודדת & AI"])

# ==================== כרטיסיית רדאר שורט ====================
with tab1:
    # עטיפת התוכן והכפתור יחד בתוך קלאס קשיח אחד (short-container)
    st.markdown('<div class="short-container"><div class="tab-content-container">⚡'
                '<h3>🐻 סורק מניות לשורט (Short Swing)</h3>'
                '<p>סורק מניות לשורט, המבוסס על נתונים ייחודים שיכולים להגדיר מניות לשורט</p>', unsafe_allow_html=True)
    
    run_short = st.button("🚀 הפעל סריקת שורט")
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
                                stage1_passed.append({"ticker": ticker, "price": current_price, "rsi": last_rsi})
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
                                s['put_pct'] = put_pct
                                final_short.append(s)
                except: pass
                
            if final_short:
                final_short = sorted(final_short, key=lambda x: x['put_pct'], reverse=True)[:10]
                st.balloons()
                
                df_display = pd.DataFrame(final_short)
                df_display.columns = ["סימול", "מחיר נוכחי", "RSI נוכחי", "אחוז אופציות PUT"]
                st.dataframe(df_display.style.format({"מחיר נוכחי": "${:.2f}", "RSI נוכחי": "{:.1f}", "אחוז אופציות PUT": "{:.1f}%"}), use_container_width=True)
            else:
                st.warning("אף מניה לא עברה את סינון האופציות (Put > Call).")

# ==================== כרטיסיית רדאר לונג ====================
with tab2:
    st.markdown('<div class="long-container"><div class="tab-content-container">⚡'
                '<h3>🐂 סורק מניות ללונג (Long Swing)</h3>'
                '<p>סורק מניות ללונג, המבוסס על נתונים ייחודים שיכולים להגדיר מניות ללונג</p>', unsafe_allow_html=True)
    
    run_long = st.button("🚀 הפעל סריקת לונג")
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    if run_long:
        st.info("רדאר הלונג בבנייה קלה, בקרוב יוצגו כאן נתוני הקניות והדוחות המושלמים!")

# ==================== כרטיסיית מניה בודדת ו-AI ====================
with tab3:
    st.markdown('<div style="max-width:1000px; margin:20px auto;"><div class="rtl-text"><h3>🤖 ניתוח מניה ומנוע שאלות AI</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown('<div class="rtl-text" style="font-weight:bold; margin-bottom:10px;">ניתוח טכני מהיר:</div>', unsafe_allow_html=True)
        search_ticker = st.text_input("הזן סימול מניה (למשל NFLX, AAPL):", key="search_input").upper().strip()
        if st.button("🔍 נתח מניה"):
            if search_ticker:
                with st.spinner("מושך נתונים..."):
                    t = yf.download(search_ticker, period="6mo", auto_adjust=True)
                    if not t.empty:
                        t['RSI'] = calculate_rsi(t['Close'])
                        last_row = t.iloc[-1]
                        st.metric("מחיר נוכחי", f"${float(last_row['Close']):.2f}")
                        st.metric("מדד RSI", f"{float(last_row['RSI']):.1f}")
                    else:
                        st.error("המניה לא נמצאה.")
            else:
                st.warning("אנא הזן סימול.")
                
    with col2:
        st.markdown('<div class="rtl-text" style="font-weight:bold; margin-bottom:10px;">שאל את האנליסט AI:</div>', unsafe_allow_html=True)
        user_q = st.text_input("שאל שאלות פיננסיות וכלכליות חופשיות:", key="ask_input")
        if st.button("🧠 שאל את האנליסט"):
            if user_q:
                with st.spinner("ה-AI חושב ומנתח..."):
                    answer = ask_gemini(user_q)
                    st.markdown(f'<div class="rtl-text" style="background-color:#0b0f17; padding:20px; border-radius:8px; border:1px solid #1e293b;">'
                                f'<h4>📋 תשובת האנליסט:</h4><p>{answer}</p></div>', unsafe_allow_html=True)
            else:
                st.warning("אנא הקלד שאלה תחילה.")
    st.markdown('</div>', unsafe_allow_html=True)
