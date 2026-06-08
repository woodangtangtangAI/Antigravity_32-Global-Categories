# -*- coding: utf-8 -*-
"""정량 데이터 수집 모듈 (FRED + yfinance)

기존 [세계 분석] macro_from202605.py의 수집 로직을 재활용합니다.
초기 실행 시 3년치 히스토리를 로드하고, 이후 매주 최신 데이터를 누적합니다.
"""
import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from datetime import datetime, timedelta

# 히스토리 기간 설정
HISTORY_YEARS = 3  # FRED: 최근 3년치
YF_HISTORY_PERIOD = "2y"  # yfinance: 최근 2년치 주봉

def get_fred_client():
    api_key = os.environ.get('FRED_API_KEY')
    if not api_key:
        print("[WARNING] FRED_API_KEY not set. Skipping FRED data.")
        return None
    return Fred(api_key=api_key)

def get_fred_safe(fred_client, series_id, name, category, unit, freq):
    """FRED에서 최근 3년치 데이터를 수집합니다. (uploader가 중복 제거)"""
    if fred_client is None:
        return pd.DataFrame()
    try:
        start_date = (datetime.now() - timedelta(days=365 * HISTORY_YEARS)).strftime('%Y-%m-%d')
        data = fred_client.get_series(series_id, observation_start=start_date)
        if not data.empty:
            df = pd.DataFrame({'Date': data.index, 'Value': data.values})
            df = df.dropna(subset=['Value'])
            df['Indicator'] = name
            df['Category'] = category
            df['Unit'] = unit
            df['Frequency'] = freq
            df['Source'] = 'FRED'
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            return df
    except Exception as e:
        print(f"  [FRED ERROR] {series_id}: {e}")
    return pd.DataFrame()

def get_yf_safe(ticker, name, category, unit, freq):
    """Yahoo Finance에서 최근 2년치 주봉 데이터를 수집합니다. (uploader가 중복 제거)"""
    try:
        data = yf.download(ticker, period=YF_HISTORY_PERIOD, interval="1wk", progress=False)
        if not data.empty:
            close_data = data['Close']
            if isinstance(close_data, pd.DataFrame):
                close_data = close_data.iloc[:, 0]
            df = pd.DataFrame({
                'Date': data.index.strftime('%Y-%m-%d'),
                'Value': close_data.round(4).values,
                'Indicator': name,
                'Category': category,
                'Unit': unit,
                'Frequency': freq,
                'Source': 'Y-Finance'
            })
            df = df.dropna(subset=['Value'])
            return df
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
