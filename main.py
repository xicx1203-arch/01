import os
import yfinance as yf
import pandas as pd
import smtplib
import google.generativeai as genai
from email.mime.text import MIMEText
from email.header import Header

# --- 從 Secrets 讀取資料 ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PWD = os.getenv('GMAIL_PWD')

genai.configure(api_key=GEMINI_API_KEY)

def get_stock_data():
    mag_7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
    try:
        data = yf.download(mag_7, period="2d", progress=False)
        stats = "【今日美股數據清單】\n"
        for ticker in mag_7:
            latest = data['Close'][ticker].iloc[-1]
            prev = data['Close'][ticker].iloc[-2]
            diff = ((latest - prev) / prev) * 100
            stats += f"{'📈' if diff > 0 else '📉'} {ticker}: ${latest:.2f} ({'+' if diff > 0 else ''}{diff:.2f}%)\n"
        return stats
    except Exception as e:
        return f"數據抓取失敗: {e}"

def get_ai_analysis(raw_data):
    try:
        # 自動偵測模型名，避免 404
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if "1.5-flash" in m), available_models[0])
        model = genai.GenerativeModel(target_model)
        prompt = f"你是一位美股分析師，請針對數據寫一段繁體中文簡評：\n{raw_data}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"【AI 目前忙碌，附上原始數據】\n\n{raw_data}"

def send_gmail(content):
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = f"AI 管家 <{GMAIL_USER}>"
    msg['To'] = GMAIL_USER
    msg['Subject'] = Header('📊 每日美股自動分析報告', 'utf-8')
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PWD)
        server.sendmail(GMAIL_USER, [GMAIL_USER], msg.as_string())
        server.quit()
        print("✅ 郵件成功寄出！")
    except Exception as e:
        print(f"❌ 寄送失敗: {e}")

if __name__ == "__main__":
    data = get_stock_data()
    report = get_ai_analysis(data)
    send_gmail(report)
