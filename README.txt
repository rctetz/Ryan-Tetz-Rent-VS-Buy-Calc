RYAN'S MAMMOTH RENT VS BUY — LIVE MARKET EDITION

Mac / Windows / Linux:
1. Make sure Python 3 is installed.
2. Double-click app.py if your system permits, or open Terminal/Command Prompt in this folder.
3. Run: python3 app.py   (Windows may use: python app.py)
4. The dashboard opens at http://127.0.0.1:8765
5. Stop it by closing the terminal window or pressing Ctrl+C.

Why it uses a small local server:
A standalone HTML file cannot reliably fetch and parse multiple public websites because browsers block cross-origin page access. The included Python server fetches the public pages and sends only the extracted market figures to the dashboard. No data is uploaded anywhere.

Data caveats:
- Freddie Mac rate is a national weekly average, not a personalized condo quote.
- One-bedroom market rent is a listing-market benchmark and may be influenced by furnished or seasonal Mammoth rentals.
- The HOA figure is a planning benchmark inferred from a published local range, not a complete census of every active HOA.
- Condo insurance has no authoritative citywide live average. Keep the editable input based on a real quote and review the HOA master policy.
- All break-even outputs are deterministic model results, not guaranteed future outcomes.
