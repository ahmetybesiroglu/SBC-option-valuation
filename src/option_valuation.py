import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from scipy.stats import norm
import os

def calculate_volatility(ticker, start_date, end_date, frequency='daily'):
    data = yf.download(ticker, start=start_date, end=end_date, interval='1d')

    if data.empty:
        raise ValueError(f"No data found for {ticker} from {start_date} to {end_date}")

    adj_close = data['Adj Close']

    if frequency == 'daily':
        prices = adj_close
        annual_factor = np.sqrt(252)
    elif frequency == 'weekly':
        prices = adj_close.resample('W-FRI').last()
        annual_factor = np.sqrt(52)
    elif frequency == 'monthly':
        prices = adj_close.resample('M').last()
        annual_factor = np.sqrt(12)
    else:
        raise ValueError("Invalid frequency. Use 'daily', 'weekly', or 'monthly'.")

    log_returns = np.log(prices / prices.shift(1)).dropna()
    volatility = log_returns.std() * annual_factor
    return round(volatility * 100, 2)

def fetch_treasury_yield(ticker, date):
    target_date = datetime.strptime(date, '%Y-%m-%d')
    start_date = target_date - timedelta(days=7)
    end_date = target_date + timedelta(days=1)
    data = yf.download(ticker, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    
    if data.empty:
        raise ValueError(f"No data found for {ticker} around {date}")
    
    if date in data.index.strftime('%Y-%m-%d'):
        latest_yield = data.loc[date, 'Close']
    else:
        latest_yield = data['Close'].iloc[-1]
    
    return round(latest_yield, 2)

def black_scholes(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    option_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return option_price

def load_config(config_path):
    with open(config_path, 'r') as file:
        config = json.load(file)
    return config

def calculate_years_to_maturity(valuation_date, expiration_date, vesting_end_date):
    valuation_date = datetime.strptime(valuation_date, '%Y-%m-%d')
    expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d')
    vesting_end_date = datetime.strptime(vesting_end_date, '%Y-%m-%d')
    
    ytm_valuation_expiration = (expiration_date - valuation_date).days / 365
    ytm_valuation_vesting = (vesting_end_date - valuation_date).days / 365
    years_to_maturity = round((ytm_valuation_expiration + ytm_valuation_vesting) / 2)
    return int(years_to_maturity)

def main():
    # Load configuration file
    config_path = 'config/config.json'
    print(f"Loading configuration from {config_path}")
    config = load_config(config_path)
    print(f"Configuration loaded: {config}")

    # Extract configuration values
    stock_price = config['stock_price']
    strike_price = config['strike_price']
    valuation_date = config['valuation_date']
    expiration_date = config['expiration_date']
    vesting_end_date = config['vesting_end_date']
    tickers = config['public_comps']
    frequency = config.get('frequency', 'daily')  # Use 'daily' as default frequency if not provided
    
    # Calculate years to maturity
    print("Calculating years to maturity...")
    years_to_maturity = calculate_years_to_maturity(valuation_date, expiration_date, vesting_end_date)
    print(f"Years to maturity: {years_to_maturity}")

    # Calculate start and end dates for historical data
    valuation_date_dt = datetime.strptime(valuation_date, '%Y-%m-%d')
    start_date = valuation_date_dt.replace(year=valuation_date_dt.year - years_to_maturity).strftime('%Y-%m-%d')
    end_date = valuation_date_dt.strftime('%Y-%m-%d')
    print(f"Fetching historical data from {start_date} to {end_date}")

    # Calculate volatility for each ticker
    volatilities = []
    for ticker in tickers:
        try:
            volatility = calculate_volatility(ticker, start_date, end_date, frequency)
            volatilities.append({'Ticker': ticker, f"{start_date} to {end_date}": volatility})
            print(f"Volatility for {ticker}: {volatility}")
        except Exception as e:
            print(f"Error for {ticker} from {start_date} to {end_date}: {e}")

    # Create volatility DataFrame
    volatility_df = pd.DataFrame(volatilities)
    
    # Ensure that the columns used for mean calculation are numeric
    for col in volatility_df.columns[1:]:
        volatility_df[col] = pd.to_numeric(volatility_df[col], errors='coerce')

    # Calculate the mean of volatilities
    average_volatility = volatility_df.mean(axis=0, numeric_only=True).mean() / 100

    # Add average volatility to the DataFrame
    average_row = {'Ticker': 'Average'}
    average_values = volatility_df.mean(axis=0, numeric_only=True).round(2).to_dict()
    average_row.update(average_values)
    average_df = pd.DataFrame([average_row])
    volatility_df = pd.concat([volatility_df, average_df], ignore_index=True)
    print(volatility_df)

    # Calculate risk-free rate
    treasury_tickers = {
        "1-year": "^IRX",
        "5-year": "^FVX",
        "10-year": "^TNX",
        "30-year": "^TYX"
    }

    yields = []
    for ticker_name, ticker_symbol in treasury_tickers.items():
        try:
            print(f"Fetching treasury yield for {ticker_name}...")
            latest_yield = fetch_treasury_yield(ticker_symbol, valuation_date)
            yields.append({"Ticker": ticker_name, "Yield": latest_yield})
            print(f"Yield for {ticker_name}: {latest_yield}")
        except Exception as e:
            print(f"Error fetching data for {ticker_name} on {valuation_date}: {e}")
            yields.append({"Ticker": ticker_name, "Yield": None})

    # Create yield DataFrame
    yield_df = pd.DataFrame(yields)
    
    known_maturities = {ticker_name: int(ticker_name.split('-')[0]) for ticker_name in treasury_tickers}
    max_maturity = max(known_maturities.values())
    intermediate_maturities = [i for i in range(1, max_maturity + 1) if i not in known_maturities.values()]

    all_maturities = sorted(set(list(known_maturities.values()) + intermediate_maturities))
    interpolated_results = {maturity: [] for maturity in all_maturities}

    known_yields = []
    for ticker_name, maturity in known_maturities.items():
        yield_value = yield_df.loc[yield_df['Ticker'] == ticker_name, 'Yield'].values[0]
        if yield_value is not None:
            known_yields.append((maturity, yield_value))
    
    if known_yields:
        known_yields = sorted(known_yields)
        known_maturity_years, known_yield_values = zip(*known_yields)
        interpolated_yields = np.interp(intermediate_maturities, known_maturity_years, known_yield_values)
    
        for maturity in all_maturities:
            if maturity in known_maturity_years:
                interpolated_results[maturity].append(known_yield_values[known_maturity_years.index(maturity)])
            else:
                interpolated_results[maturity].append(round(interpolated_yields[intermediate_maturities.index(maturity)], 2))
    else:
        for maturity in all_maturities:
            interpolated_results[maturity].append(None)

    interpolated_df = pd.DataFrame(interpolated_results, index=[valuation_date])
    interpolated_df = interpolated_df.transpose()
    interpolated_df.index.name = 'Maturity'
    interpolated_df.columns.name = 'Date'
    interpolated_df.index = [f"{maturity}-year" for maturity in interpolated_df.index]

    # Print the interpolated DataFrame and available maturities
    print("Interpolated DataFrame:")
    print(interpolated_df)

    # Check if the required maturity exists in the DataFrame
    required_maturity = f"{years_to_maturity}-year"
    print(f"Looking for maturity: {required_maturity}")

    if required_maturity not in interpolated_df.index:
        raise KeyError(f"Maturity {required_maturity} not found in the interpolated DataFrame. Available maturities: {interpolated_df.index}")

    risk_free_rate = interpolated_df.loc[required_maturity, valuation_date] / 100
    print(f"Risk-free rate for {required_maturity}: {risk_free_rate}")

    # Calculate option valuation
    option_valuation = black_scholes(stock_price, strike_price, years_to_maturity, risk_free_rate, average_volatility)
    print(f"Option valuation: {option_valuation}")

    # Prepare input data
    input_data = {
        "Grant date": datetime.strptime(config['grant_date'], '%Y-%m-%d').strftime('%-m/%-d/%Y'),
        "Valuation date": datetime.strptime(config['valuation_date'], '%Y-%m-%d').strftime('%-m/%-d/%Y'),
        "Expiration date": datetime.strptime(config['expiration_date'], '%Y-%m-%d').strftime('%-m/%-d/%Y'),
        "Vesting end date": datetime.strptime(config['vesting_end_date'], '%Y-%m-%d').strftime('%-m/%-d/%Y'),
        "Stock price": stock_price,
        "Strike/Exercise price": strike_price,
        "Years to maturity (YTM)": years_to_maturity,
        "Risk free rate": round(risk_free_rate,4),
        "Volatility": round(average_volatility,4),
        "Option Valuation": round(option_valuation,2)
    }

    # Convert input data to a DataFrame with two columns
    input_df = pd.DataFrame(list(input_data.items()), columns=["", "Value"])
    print("Resulting DataFrame:")
    print(input_df)

    # Save to Excel
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'option_valuation_results.xlsx')
    print(f"Saving results to {output_file}")

    with pd.ExcelWriter(output_file) as writer:
        input_df.to_excel(writer, sheet_name='Black Scholes', index=False)
        volatility_df.to_excel(writer, sheet_name='Volatility', index=False)
        interpolated_df.to_excel(writer, sheet_name='Risk Free Rate')

    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    main()
