import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 1. הגדרות דף ועיצוב המותג של The Mind Changer
st.set_page_config(page_title="The Mind Changer | Stock Radar", layout="wide")

# הזרקת ה-CSS המקורי של המותג ישירות לתוך Streamlit
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@400;600;700&display=swap');
    
    /* עיצוב כללי של האתר */
    .stApp {
        background-color: #0a0a08;
        color: #f0ede6;
        font-family: 'Inter', sans-serif;
        direction: rtl;
    }
    
    /* כותרות בסגנון Playfair */
    h1, h2, h3, .brand-title {
        font-family: 'Playfair Display', serif;
        color: #c9a84c !important; /* זהב */
    }
    
    /* עיצוב תיבות/כרטיסיות מניות */
    .stock-card {
        background: #141410;
        border: 1px solid rgba(201,168,76,0.15);
        border-radius: 6px;
        padding: 16px;
        text-align: center;
        margin-bottom: 12px;
        transition: transform 0.2s;
    }
    .stock-card:hover {
        transform: translateY(-3px);
        border-color: #c9a84c;
    }
    
    /* צבעים ייעודיים */
    .text-gold { color: #c9a84c; font-weight: bold; }
    .text-green { color: #16a34a; font-weight: bold; }
    .text-red { color: #dc2626; font-weight: bold; }
    .text-muted { color: #7a7060; font-size: 0.85rem; }
    
    /* התאמת כפתורים של Streamlit לעיצוב הזהב */
    div.stButton > button {
        background-color: #c9a84c !important;
        color: #0a0a08 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 10px 24px !important;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #e8c97a !important;
    }
</style>
""", unsafe_allow_html=True)

# המודאל / כותרת עליונה קבועה
st.markdown("""
<div style='text-align: center; padding: 20px 0; border-bottom: 1px solid rgba(201,168,76,0.12); margin-bottom: 30px;'>
    <h1 style='margin: 0; font-size: 3rem;'>The Mind <em>Changer</em></h1>
    <p class='text-muted'>Stock Intelligence Platform | רדאר מניות חכם מבוסס נתוני אמת</p>
</div>
""", unsafe_allow_html=True)

# 2. לוגיקת חישוב אינדיקטורים וסריקה (פונקציות Python אמיתיות)
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1fr + rs))

def scan_market(ticker_list, mode):
    results = []
    
    # יצירת פרוגרס בר אמיתי של Streamlit
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, ticker in enumerate(ticker_list):
        # עדכון סטטוס התקדמות
        percent_complete = int((idx + 1) / len(ticker_list) * 100)
        progress_bar.progress(percent_complete)
        status_text.markdown(f"<p class='text-muted'>סורק כעת: <span class='text-gold'>{ticker}</span> ({percent_complete}%)</p>", unsafe_allow_html=True)
        
        try:
            # משיכת נתונים היסטוריים (חודש אחורה מספיק לאינדיקטורים קצרים)
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
            
            if len(df) < 15:
                continue
                
            # חישוב אינדיקטורים
            df['MA9'] = df['Close'].rolling(window=9).mean()
            df['RSI'] = calculate_rsi(df['Close'], period=14)
            
            # נתונים נוכחיים
            current_price = df['Close'].iloc[-1]
            last_rsi = df['RSI'].iloc[-1]
            last_ma9 = df['MA9'].iloc[-1]
            
            # בדיקת נרות ירוקים/אדומים (היום לעומת אתמול, ואתמול לעומת שלשום)
            is_green_today = df['Close'].iloc[-1] > df['Open'].iloc[-1]
            is_green_yesterday = df['Close'].iloc[-2] > df['Open'].iloc[-2]
            is_red_today = df['Close'].iloc[-1] < df['Open'].iloc[-1]
            is_red_yesterday = df['Close'].iloc[-2] < df['Open'].iloc[-2]
            
            # סינון לפי רדאר לונג
            if mode == 'long':
                if (last_rsi < 70) and (current_price > last_ma9) and is_green_today and is_green_yesterday:
                    results.append({
                        'ticker': ticker,
                        'price': current_price,
                        'rsi': last_rsi,
                        'change': ((current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                    })
                    
            # סינון לפי רדאר שורט
            elif mode == 'short':
                if (last_rsi > 30) and (current_price < last_ma9) and is_red_today and is_red_yesterday:
                    results.append({
                        'ticker': ticker,
                        'price': current_price,
                        'rsi': last_rsi,
                        'change': ((current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                    })
        except Exception:
            # דילוג על מניות בעייתיות או שגיאות ב-API
            continue
            
    progress_bar.empty()
    status_text.empty()
    return results

# 3. רשימת מניות לסריקה (ניתן להרחיב ככל שתרצה)
WATCHLIST = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'NVDA', 'TSLA', 'META', 'AMD', 'NFLX', 'CRM', 'UBER', 'COIN', 'BABA', 'INTC', 'DIS']

# 4. חלוקה לטאבים (Tabs) כמו באתר המקורי שלך
tab1, tab2, tab3 = st.tabs(["📈 רדאר לונג", "📉 רדאר שורט", "🤖 ניתוח מניה בודדת"])

# --- טאב לונג ---
with tab1:
    st.markdown("### רדאר לונג")
    st.markdown("<p class='text-muted'>קריטריונים: מחיר מעל MA9 | RSI מתחת ל-70 | יומיים ירוקים רצופים</p>", unsafe_allow_html=True)
    
    if st.button("התחל סריקת לונג בזמן אמת ⚡", key="btn_long"):
        with st.spinner("מנתח נתוני שוק..."):
            matched_stocks = scan_market(WATCHLIST, 'long')
            
        if matched_stocks:
            st.markdown(f"#### נמצאו <span class='text-green'>{len(matched_stocks)}</span> מניות מתאימות:", unsafe_allow_html=True)
            cols = st.columns(4)
            for i, stock in enumerate(matched_stocks):
                with cols[i % 4]:
                    st.markdown(f"""
                    <div class='stock-card'>
                        <div style='font-size: 1.2rem; font-weight: bold;'>{stock['ticker']}</div>
                        <div class='text-green' style='font-size: 1.1rem; margin: 5px 0;'>${stock['price']:.2f}</div>
                        <div class='text-muted'>RSI: {stock['rsi']:.1f} | שינוי: {stock['change']:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("לא נמצאו מניות העונות לקריטריוני לונג ברגע זה.")

# --- טאב שורט ---
with tab2:
    st.markdown("### רדאר שורט")
    st.markdown("<p class='text-muted'>קריטריונים: מחיר מתחת ל-MA9 | RSI מעל 30 | יומיים אדומים רצופים</p>", unsafe_allow_html=True)
    
    if st.button("התחל סריקת שורט בזמן אמת ⚡", key="btn_short"):
        with st.spinner("מנתח נתוני שוק..."):
            matched_stocks = scan_market(WATCHLIST, 'short')
            
        if matched_stocks:
            st.markdown(f"#### נמצאו <span class='text-red'>{len(matched_stocks)}</span> מניות מתאימות:", unsafe_allow_html=True)
            cols = st.columns(4)
            for i, stock in enumerate(matched_stocks):
                with cols[i % 4]:
                    st.markdown(f"""
                    <div class='stock-card'>
                        <div style='font-size: 1.2rem; font-weight: bold;'>{stock['ticker']}</div>
                        <div class='text-red' style='font-size: 1.1rem; margin: 5px 0;'>${stock['price']:.2f}</div>
                        <div class='text-muted'>RSI: {stock['rsi']:.1f} | שינוי: {stock['change']:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("לא נמצאו מניות העונות לקריטריוני שורט ברגע זה.")

# --- טאב ניתוח מניה בודדת ---
with tab3:
    st.markdown("### ניתוח מניה ממוקד")
    ticker_input = st.text_input("הזן סימול מניה (למשל: AAPL, NVDA):", "").upper().strip()
    
    if st.button("נתח מניה 🔍") and ticker_input:
        try:
            with st.spinner(f"מושך נתונים עבור {ticker_input}..."):
                stock = yf.Ticker(ticker_input)
                df = stock.history(period="3mo")
                
                if df.empty:
                    st.error("לא נמצאו נתונים עבור הסימול שהוזן.")
                else:
                    # חישובים מהירים
                    current_price = df['Close'].iloc[-1]
                    prev_close = df['Close'].iloc[-2]
                    daily_change = ((current_price - prev_close) / prev_close) * 100
                    
                    df['RSI'] = calculate_rsi(df['Close'])
                    df['MA9'] = df['Close'].rolling(window=9).mean()
                    
                    last_rsi = df['RSI'].iloc[-1]
                    last_ma9 = df['MA9'].iloc[-1]
                    
                    # תצוגת נתונים מעוצבת
                    st.markdown(f"### סקירת מניית {ticker_input}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("מחיר אחרון", f"${current_price:.2f}", f"{daily_change:.2f}%")
                    with col2:
                        st.metric("RSI (14)", f"{last_rsi:.1f}")
                    with col3:
                        status = "חיובי (מעל MA9)" if current_price > last_ma9 else "שלילי (מתחת MA9)"
                        st.metric("סטטוס ממוצע נע 9", status)
                        
                    # גרף מחיר מובנה ורספונסיבי
                    st.markdown("#### גרף מחיר סגירה (3 חודשים אחרונים)")
                    st.line_chart(df['Close'])
        except Exception as e:
            st.error(f"אירעה שגיאה בעת ניתוח המניה: {e}")
