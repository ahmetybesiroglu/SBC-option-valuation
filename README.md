
# Stock-Based Compensation Valuation Tool

## Overview

The Stock-Based Compensation Valuation Tool is designed to help companies issuing stock options to employees determine the fair value of these options for accounting purposes and financial reporting. This script uses the Black-Scholes model to calculate the value of stock options, leveraging historical volatility data and current treasury yields fetched from Yahoo Finance.

## Features

- **Volatility Calculation:** Calculate volatility for specified tickers over a given time period.
- **Treasury Yield Fetching:** Retrieve and interpolate treasury yields for different maturities.
- **Option Valuation:** Use the Black-Scholes model to determine the fair value of stock options.

## Prerequisites

Ensure you have Python installed (preferably version 3.6 or higher). You can download it from [python.org](https://www.python.org/).

## Setup

### Option 1: Clone the Repository

Clone this repository to your local machine using the following command:

```bash
git clone https://github.com/ahmetybesiroglu/SBC-option-valuation.git
cd SBC-option-valuation
```

### Option 2: Download the Repository

1. Go to the repository's page on GitHub: [SBC-option-valuation](https://github.com/ahmetybesiroglu/SBC-option-valuation).
2. Click the green `Code` button.
3. Select `Download ZIP`.
4. Extract the ZIP file to your desired location.
5. Navigate to the extracted folder.

### Create and Activate a Virtual Environment

It's a good practice to use a virtual environment to manage dependencies. You can create and activate a virtual environment with the following commands:

For Windows:
```bash
python3 -m venv env
env\Scripts\Activate
```

For macOS and Linux:
```bash
python3 -m venv env
source env/bin/activate
```

### Install Dependencies

Install the required dependencies using the provided `requirements.txt` file:

```bash
pip3 install -r requirements.txt
```

### Configuration

Edit the `config/config.json` file to specify the necessary parameters. Here is an example of what the file looks like:

```json
{
  "public_comps": ["AAPL", "GOOG", "MSFT"],
  "grant_date": "2022-07-10",
  "valuation_date": "2022-07-10",
  "expiration_date": "2025-07-10",
  "vesting_end_date": "2032-01-10",
  "stock_price": 150,
  "strike_price": 100,
  "frequency": "daily"
}
```

#### Configuration Parameters

- **stock_price:** Current stock price of the company issuing the options.
- **strike_price:** Exercise price of the stock options.
- **valuation_date:** Date on which the valuation is performed.
- **expiration_date:** Expiration date of the stock options.
- **vesting_end_date:** Date when the stock options fully vest.
- **public_comps:** List of public companies' ticker symbols to be used for volatility calculation.
- **grant_date:** Date when the stock options are granted.
- **frequency:** Frequency used for calculating volatility. Options are `daily` (default), `weekly`, or `monthly`.

## Running the Script

Run the script to calculate the option valuation:

```bash
python3 src/option_valuation_calculator.py
```

### Expected Output

The script will perform the following steps:
1. **Calculate Volatility:** Fetch historical stock prices for the specified public companies and calculate their volatilities.
2. **Fetch Treasury Yields:** Retrieve current treasury yields for different maturities and interpolate missing yields.
3. **Calculate Option Valuation:** Use the Black-Scholes model to determine the fair value of the stock options.

The results will be saved in an Excel file located in the `output` directory.

## Methodology

### Years to Maturity Calculation

The methodology for calculating the years to maturity involves the following steps:
1. **Vesting and Expiration Dates:** Use the expiration and vesting end dates from the configuration.
2. **Time Calculation:** Calculate the time in years from the valuation date to the expiration date and from the valuation date to the vesting end date.
3. **Average Time:** Compute the average of these two times to get the years to maturity.

### Yield Rate and Volatility Inputs

The calculated years to maturity is used to find the appropriate yield rate and volatility as follows:
1. **Volatility Calculation:** Calculate the historical volatility of the specified public companies over the defined date range historically.
2. **Yield Rate Calculation:** Fetch the appropriate treasury yield based on the years to maturity.

### Volatility Calculation

The methodology for calculating volatility is as follows:

1. **Data Retrieval**: Historical stock price data is retrieved from Yahoo Finance for the specified tickers and date ranges.
2. **Adjusting Data Frequency**: The adjusted close prices are resampled to the specified frequency (daily, weekly, or monthly).
3. **Log Returns Calculation**: The logarithmic returns are calculated using the formula:

   $$\text{log returns} = log(\frac{{\text{current price}}}{\text{previous price}})$$

4. **Volatility Calculation**: The standard deviation of the log returns over the entire date range is calculated and annualized using the appropriate factor based on the frequency:
   - Daily: $\sqrt{252}$
   - Weekly: $\sqrt{52}$
   - Monthly: $\sqrt{12}$
5. **Annualized Volatility**: The calculated standard deviation is multiplied by the annual factor to get the annualized volatility, which is then expressed as a percentage.

This approach ensures that the volatility represents the price variation over the entire specified date range, giving a comprehensive view of the stock's historical volatility.

## Detailed Workflow

1. **Load Configuration:** The script loads the configuration parameters from the `config/config.json` file.
2. **Calculate Years to Maturity:** Computes the average time to maturity based on the expiration and vesting dates.
3. **Fetch Historical Data:** Downloads historical adjusted closing prices for the specified public companies.
4. **Calculate Volatility:** Determines the historical volatility of each company's stock price and computes an average volatility.
5. **Fetch Treasury Yields:** Retrieves treasury yields from Yahoo Finance and interpolates missing values for intermediate maturities.
6. **Calculate Risk-Free Rate:** Uses the interpolated treasury yields to find the appropriate risk-free rate for the option's time to maturity.
7. **Option Valuation:** Uses the Black-Scholes formula to calculate the fair value of the stock options.
8. **Save Results:** Outputs the input data, calculated volatilities, and interpolated risk-free rates into an Excel file.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add some feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## Contact

For further questions, please contact [ahmetybesiroglu@gmail.com](mailto:ahmetybesiroglu@gmail.com).
