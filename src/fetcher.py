# -*- coding: utf-8 -*-
"""정량 데이터 수집 모듈 (FRED + yfinance)

기존 [세계 분석] macro_from202605.py의 수집 로직을 재활용합니다.
"""
import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from datetime import datetime

# FRED API 초기화
def get_fred_client():
    api_key = os.environ.get('FRED_API_KEY')
    if not api_key:
        print("[WARNING] FRED_API_KEY not set. Skipping FRED data.")
        return None
    return Fred(api_key=api_key)

def get_fred_safe(fred_client, series_id, name, category, unit, freq):
    """FRED에서 최신 데이터 1건을 안전하게 수집합니다."""
    if fred_client is None:
        return pd.DataFrame()
    try:
        data = fred_client.get_series(series_id)
        if not data.empty:
            df = pd.DataFrame({'Date': data.index, 'Value': data.values})
            df['Indicator'] = name
            df['Category'] = category
            df['Unit'] = unit
            df['Frequency'] = freq
            df['Source'] = 'FRED'
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            return df.tail(1)
    except Exception as e:
        print(f"  [FRED ERROR] {series_id}: {e}")
    return pd.DataFrame()

def get_yf_safe(ticker, name, category, unit, freq):
    """Yahoo Finance에서 최신 종가 데이터 1건을 안전하게 수집합니다."""
    try:
        data = yf.download(ticker, period="5d", interval="1d", progress=False)
        if not data.empty:
            last_val = data['Close'].iloc[-1]
            last_date = data.index[-1]
            return pd.DataFrame({
                'Date': [last_date.strftime('%Y-%m-%d')],
                'Value': [round(float(last_val), 4)],
                'Indicator': [name],
                'Category': [category],
                'Unit': [unit],
                'Frequency': [freq],
                'Source': ['Y-Finance']
            })
    except Exception as e:
        print(f"  [YF ERROR] {ticker}: {e}")
    return pd.DataFrame()

def fetch_quantitative(category_config: dict) -> pd.DataFrame:
    """카테고리 1개의 정량 지표를 FRED + yfinance에서 수집합니다."""
    results = []
    fred_client = get_fred_client()
    
    for ind_name, info in category_config["quantitative"].get("FRED", {}).items():
        results.append(get_fred_safe(fred_client, info[0], ind_name, info[1], info[2], info[3]))
    
    for ind_name, info in category_config["quantitative"].get("YFINANCE", {}).items():
        results.append(get_yf_safe(info[0], ind_name, info[1], info[2], info[3]))
    
    valid = [d for d in results if not d.empty]
    if valid:
        return pd.concat(valid, ignore_index=True)
    return pd.DataFrame()
