# Finance Analyst Agent

A small [Google ADK](https://google.github.io/adk-docs/) agent that answers stock market questions using live Yahoo Finance data. Built as a class demo.

Built with Claude Code in seconds. Absolutely no warranty.

## What it can do

- Current price and daily change
- Company profile (sector, industry, market cap, P/E)
- Compare returns across multiple tickers or against a benchmark (S&P 500, Dow, Nasdaq)
- Recent news headlines
- Next earnings date and EPS estimates
- Similar companies in the same industry
- Analyst price targets and consensus rating
- Dividend yield and payout details
- Portfolio analysis (return, volatility, correlation)
- Hypothetical "what if I'd invested $X on date Y" returns

## Setup

Requires Python 3.10+.

```bash
pip install google-adk yfinance pandas
```

Create a `.env` file in the agent folder:

```
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your-gemini-api-key
```

Get a key from [Google AI Studio](https://aistudio.google.com/apikey). Don't commit `.env`.

## Project layout

```
finance_agent/
├── __init__.py   # contains: from . import agent
├── agent.py      # defines root_agent
└── .env
```

## Run

From the directory **above** `finance_agent/`:

```bash
adk web      # browser UI
adk run finance_agent   # terminal
```

## Example prompts

- "How is NVDA doing today?"
- "Compare AAPL, MSFT, and GOOGL over the last 3 months."
- "How has JPM performed against the S&P 500 this year?"
- "If I'd put $10,000 into AMZN on 2020-01-01, what would it be worth now?"
- "Analyze a portfolio of 50% NVDA, 30% AAPL, 20% JPM over the past year."

## Disclaimer

For educational purposes only. Not investment advice. Data comes from Yahoo Finance via `yfinance`, an unofficial library, so it may be delayed, incomplete, or occasionally unavailable.
