// frontend/src/modules/portfolio/internal/tickerUniverse.js
// NEW FILE
//
// Mirrors ai-service/modules/market_data/internal/constants.py's
// TICKER_UNIVERSE. Kept as display metadata only (ticker + label) —
// the frontend never decides what's fetchable, it just offers what
// the backend already supports. If the backend universe changes,
// this file needs a matching edit; there's no single shared source
// across Python/JS in this stack, so keeping both short and obvious
// is the safeguard.

export const TICKER_UNIVERSE = [
  { ticker: 'RELIANCE.NS', label: 'Reliance Industries' },
  { ticker: 'TCS.NS', label: 'Tata Consultancy Services' },
  { ticker: 'INFY.NS', label: 'Infosys' },
  { ticker: 'HDFCBANK.NS', label: 'HDFC Bank' },
  { ticker: 'NIFTYBEES.NS', label: 'Nippon India ETF Nifty BeES' },
  { ticker: 'AAPL', label: 'Apple' },
  { ticker: 'MSFT', label: 'Microsoft' },
  { ticker: 'NVDA', label: 'NVIDIA' },
];