from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
from google.adk.agents import Agent


def get_stock_price(ticker: str) -> dict:
    """Get the current price and today's change for a stock ticker.

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL" or "MSFT".

    Returns:
        A dict with status and either the price data or an error message.
    """
    try:
        info = yf.Ticker(ticker).fast_info
        price = info["last_price"]
        prev_close = info["previous_close"]
        change = price - prev_close
        pct_change = (change / prev_close) * 100
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "price": round(price, 2),
            "change": round(change, 2),
            "percent_change": round(pct_change, 2),
            "currency": info.get("currency", "USD"),
        }
    except Exception as e:
        return {"status": "error", "error_message": f"Could not fetch price for {ticker}: {e}"}


def get_company_info(ticker: str) -> dict:
    """Get company profile info: name, sector, industry, and market cap.

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL".

    Returns:
        A dict with status and either company info or an error message.
    """
    try:
        info = yf.Ticker(ticker).info
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "summary": (info.get("longBusinessSummary", "") or "")[:400],
        }
    except Exception as e:
        return {"status": "error", "error_message": f"Could not fetch info for {ticker}: {e}"}


def compare_stock_performance(tickers: list[str], period: str = "1mo") -> dict:
    """Compare percent price change for multiple stock tickers over a period.

    Args:
        tickers: List of ticker symbols, e.g. ["AAPL", "MSFT", "GOOGL"].
        period: Lookback window, one of "5d", "1mo", "3mo", "6mo", "1y", "ytd".

    Returns:
        A dict with status and each ticker's percent return over the period.
    """
    try:
        results = {}
        for t in tickers:
            hist = yf.Ticker(t).history(period=period)
            if hist.empty:
                results[t.upper()] = None
                continue
            start = hist["Close"].iloc[0]
            end = hist["Close"].iloc[-1]
            pct = ((end - start) / start) * 100
            results[t.upper()] = round(float(pct), 2)
        return {"status": "success", "period": period, "percent_returns": results}
    except Exception as e:
        return {"status": "error", "error_message": f"Could not compare {tickers}: {e}"}


def get_company_news(ticker: str, max_articles: int = 5) -> dict:
    """Get recent news headlines for a stock ticker.

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL".
        max_articles: Maximum number of headlines to return (default 5).

    Returns:
        A dict with status and a list of headlines with source and publish date.
    """
    try:
        articles = yf.Ticker(ticker).news or []
        headlines = []
        for a in articles[:max_articles]:
            content = a.get("content", {})
            headlines.append({
                "title": content.get("title", "N/A"),
                "publisher": (content.get("provider") or {}).get("displayName", "N/A"),
                "published": content.get("pubDate", "N/A"),
            })
        return {"status": "success", "ticker": ticker.upper(), "headlines": headlines}
    except Exception as e:
        return {"status": "error", "error_message": f"Could not fetch news for {ticker}: {e}"}


def get_next_earnings_date(ticker: str) -> dict:
    """Get the next scheduled earnings call date and EPS estimates for a stock.

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL".

    Returns:
        A dict with status and the next earnings date plus analyst EPS estimates.
    """
    try:
        cal = yf.Ticker(ticker).calendar or {}
        dates = cal.get("Earnings Date", [])
        if not dates:
            return {"status": "success", "ticker": ticker.upper(), "next_earnings_date": None,
                     "note": "No upcoming earnings date found."}
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "next_earnings_date": str(dates[0]),
            "eps_estimate_avg": cal.get("Earnings Average", "N/A"),
            "eps_estimate_low": cal.get("Earnings Low", "N/A"),
            "eps_estimate_high": cal.get("Earnings High", "N/A"),
        }
    except Exception as e:
        return {"status": "error", "error_message": f"Could not fetch earnings date for {ticker}: {e}"}


def get_similar_companies(ticker: str, max_results: int = 5) -> dict:
    """Recommend similar/competitor companies in the same industry as a stock.

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL".
        max_results: Maximum number of similar companies to return (default 5).

    Returns:
        A dict with status, the industry name, and peer companies ranked by
        relative market weight within that industry.
    """
    try:
        info = yf.Ticker(ticker).info
        industry_key = info.get("industryKey")
        if not industry_key:
            return {"status": "error", "error_message": f"No industry data found for {ticker}."}

        top = yf.Industry(industry_key).top_companies
        peers = [
            {"ticker": sym, "name": row["name"], "rating": row.get("rating")}
            for sym, row in top.iterrows()
            if sym.upper() != ticker.upper()
        ][:max_results]

        return {
            "status": "success",
            "ticker": ticker.upper(),
            "industry": info.get("industry", industry_key),
            "similar_companies": peers,
        }
    except Exception as e:
        return {"status": "error", "error_message": f"Could not find similar companies for {ticker}: {e}"}


def get_analyst_price_targets(ticker: str) -> dict:
    """Get Wall Street analyst price targets and consensus recommendation for a stock.

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL".

    Returns:
        A dict with status, current/low/mean/median/high price targets, the
        consensus recommendation (e.g. "buy"), and number of analysts covering it.
    """
    try:
        t = yf.Ticker(ticker)
        targets = t.analyst_price_targets or {}
        info = t.info
        if not targets:
            return {"status": "error", "error_message": f"No analyst price targets found for {ticker}."}
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "current_price": targets.get("current"),
            "target_low": targets.get("low"),
            "target_mean": round(targets.get("mean"), 2) if targets.get("mean") else None,
            "target_median": targets.get("median"),
            "target_high": targets.get("high"),
            "recommendation": info.get("recommendationKey", "N/A"),
            "num_analysts": info.get("numberOfAnalystOpinions", "N/A"),
        }
    except Exception as e:
        return {"status": "error", "error_message": f"Could not fetch price targets for {ticker}: {e}"}


def compare_to_benchmark(ticker: str, benchmark: str = "^GSPC", period: str = "1mo") -> dict:
    """Compare a stock's performance against a market benchmark (e.g. the S&P 500).

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL".
        benchmark: Benchmark index ticker, default "^GSPC" (S&P 500). Other
            options: "^DJI" (Dow), "^IXIC" (Nasdaq).
        period: Lookback window, one of "5d", "1mo", "3mo", "6mo", "1y", "ytd".

    Returns:
        A dict with status, the stock's return, the benchmark's return, and
        the difference (alpha) over the period.
    """
    try:
        def pct_return(symbol: str) -> float | None:
            hist = yf.Ticker(symbol).history(period=period)
            if hist.empty:
                return None
            start, end = hist["Close"].iloc[0], hist["Close"].iloc[-1]
            return round(float((end - start) / start * 100), 2)

        stock_return = pct_return(ticker)
        benchmark_return = pct_return(benchmark)
        if stock_return is None or benchmark_return is None:
            return {"status": "error", "error_message": f"Could not compute returns for {ticker} or {benchmark}."}

        return {
            "status": "success",
            "ticker": ticker.upper(),
            "benchmark": benchmark.upper(),
            "period": period,
            "stock_return_pct": stock_return,
            "benchmark_return_pct": benchmark_return,
            "alpha_pct": round(stock_return - benchmark_return, 2),
        }
    except Exception as e:
        return {"status": "error", "error_message": f"Could not compare {ticker} to {benchmark}: {e}"}


def get_dividend_info(ticker: str) -> dict:
    """Get dividend yield, rate, and payout details for a stock.

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL".

    Returns:
        A dict with status, dividend yield/rate, payout ratio, and the most
        recent ex-dividend date. Note some growth stocks pay no dividend.
    """
    try:
        info = yf.Ticker(ticker).info
        ex_div_ts = info.get("exDividendDate")
        ex_div_date = (
            datetime.fromtimestamp(ex_div_ts, tz=timezone.utc).date().isoformat()
            if ex_div_ts else None
        )
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "dividend_yield_pct": info.get("dividendYield"),
            "annual_dividend_rate": info.get("dividendRate"),
            "payout_ratio": info.get("payoutRatio"),
            "ex_dividend_date": ex_div_date,
            "pays_dividend": bool(info.get("dividendRate")),
        }
    except Exception as e:
        return {"status": "error", "error_message": f"Could not fetch dividend info for {ticker}: {e}"}


def analyze_portfolio(tickers: list[str], weights: list[float], period: str = "1y") -> dict:
    """Analyze a multi-stock portfolio's return, risk, and diversification.

    Builds a hypothetical buy-and-hold portfolio from the given tickers and
    weights, then computes the combined return, annualized volatility, and
    the pairwise correlation between holdings (low correlation = more
    diversified).

    Args:
        tickers: List of ticker symbols, e.g. ["NVDA", "AAPL", "JPM"].
        weights: Allocation weight per ticker, same order as tickers, e.g.
            [0.5, 0.3, 0.2]. Need not sum to 1; they will be normalized.
        period: Lookback window, one of "1mo", "3mo", "6mo", "1y", "3y", "5y".

    Returns:
        A dict with status, normalized weights, portfolio total return,
        annualized volatility, each asset's individual return, and a
        correlation matrix between the holdings' daily returns.
    """
    try:
        if len(tickers) != len(weights):
            return {"status": "error", "error_message": "tickers and weights must be the same length."}

        weights_sum = sum(weights)
        if weights_sum <= 0:
            return {"status": "error", "error_message": "weights must sum to a positive number."}
        norm_weights = [w / weights_sum for w in weights]
        upper_tickers = [t.upper() for t in tickers]

        price_data = {}
        for t in upper_tickers:
            hist = yf.Ticker(t).history(period=period)
            if hist.empty:
                return {"status": "error", "error_message": f"No price history found for {t}."}
            price_data[t] = hist["Close"]

        prices = pd.concat(price_data, axis=1, join="inner")
        if len(prices) < 2:
            return {"status": "error", "error_message": "Not enough overlapping trading data for these tickers."}

        weight_series = pd.Series(norm_weights, index=upper_tickers)
        normalized = prices / prices.iloc[0]
        portfolio_value = (normalized * weight_series).sum(axis=1)
        total_return_pct = round(float((portfolio_value.iloc[-1] / portfolio_value.iloc[0] - 1) * 100), 2)

        daily_returns = prices.pct_change().dropna()
        portfolio_daily_returns = (daily_returns * weight_series).sum(axis=1)
        annualized_volatility_pct = round(float(portfolio_daily_returns.std() * (252 ** 0.5) * 100), 2)

        individual_returns_pct = {
            t: round(float((normalized[t].iloc[-1] - 1) * 100), 2) for t in upper_tickers
        }
        corr = daily_returns.corr().round(2)
        correlation_matrix = {row: {col: float(corr.loc[row, col]) for col in corr.columns} for row in corr.index}

        return {
            "status": "success",
            "period": period,
            "normalized_weights": {t: round(w, 3) for t, w in zip(upper_tickers, norm_weights)},
            "portfolio_total_return_pct": total_return_pct,
            "portfolio_annualized_volatility_pct": annualized_volatility_pct,
            "individual_asset_returns_pct": individual_returns_pct,
            "correlation_matrix": correlation_matrix,
        }
    except Exception as e:
        return {"status": "error", "error_message": f"Could not analyze portfolio: {e}"}


def calculate_hypothetical_investment(ticker: str, amount: float, start_date: str) -> dict:
    """Calculate what a hypothetical past investment would be worth today.

    Args:
        ticker: Stock ticker symbol, e.g. "AAPL".
        amount: Dollar amount hypothetically invested, e.g. 10000.
        start_date: Investment start date in "YYYY-MM-DD" format, e.g. "2020-01-01".

    Returns:
        A dict with status, the investment's current value, total return,
        and annualized return (CAGR).
    """
    try:
        hist = yf.Ticker(ticker).history(start=start_date)
        if hist.empty:
            return {"status": "error", "error_message": f"No price history found for {ticker} since {start_date}."}

        start_price = float(hist["Close"].iloc[0])
        current_price = float(hist["Close"].iloc[-1])
        shares = amount / start_price
        current_value = shares * current_price
        total_return_pct = (current_value - amount) / amount * 100

        years = (hist.index[-1] - hist.index[0]).days / 365.25
        cagr_pct = ((current_value / amount) ** (1 / years) - 1) * 100 if years > 0 else None

        return {
            "status": "success",
            "ticker": ticker.upper(),
            "invested_amount": amount,
            "start_date": hist.index[0].date().isoformat(),
            "end_date": hist.index[-1].date().isoformat(),
            "start_price": round(start_price, 2),
            "current_price": round(current_price, 2),
            "current_value": round(current_value, 2),
            "total_return_pct": round(total_return_pct, 2),
            "cagr_pct": round(cagr_pct, 2) if cagr_pct is not None else None,
        }
    except Exception as e:
        return {"status": "error", "error_message": f"Could not calculate hypothetical investment for {ticker}: {e}"}


root_agent = Agent(
    name="finance_analyst_agent",
    model="gemini-2.5-flash",
    description="A financial analyst agent that looks up stock prices, company fundamentals, and compares performance across stocks.",
    instruction=(
        "You are a helpful financial analyst assistant for a business school class demo. "
        "Use the available tools to fetch real, live stock market data via Yahoo Finance. "
        "When asked to compare stocks, call compare_stock_performance. "
        "Always cite the actual numbers returned by the tools. "
        "Keep responses concise and business-relevant. "
        "This is for educational purposes only, not investment advice."
    ),
    tools=[
        get_stock_price,
        get_company_info,
        compare_stock_performance,
        get_company_news,
        get_next_earnings_date,
        get_similar_companies,
        get_analyst_price_targets,
        compare_to_benchmark,
        get_dividend_info,
        analyze_portfolio,
        calculate_hypothetical_investment,
    ],
)
