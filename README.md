# About This Project
Firstly, I would like to note that this program does not claim profitablility. It was developed to pair with an independent research paper I was working on that disscussed the relationship between the implied volatility before and after earnings announcements while considering potential risk factors from additional exposures to the underlying asset.

CLICK HERE TO READ PAPER (will link once I devlop a website)

With that aside, we can get into initializing the project!

# Initialization
To get started with the Earnings Trading Dashboard, follow these steps:
```bash
git clone <https://github.com/AirWard1234/IV-Crush-Analysis-Dashboard>
```
Install dependencies
Make sure you have Python 3.9+ installed. Then run:
```bash
pip install -r requirements.txt
```

Key dependencies include:
```
ibapi — Interactive Brokers Python API
pandas — data handling
numpy — numerical computations
matplotlib — plotting charts
tkinter — GUI interface (usually included with Python)
```
1. Set up IB connection
2. Ensure that Trader Workstation (TWS) or IB Gateway is running and configured
3. Enable API connections: Edit → Global Configuration → API → Settings → Enable ActiveX and Socket Clients
4. Make sure the port number matches what you plan to use in the app (default: 7497 for paper trading)
5. Add 127.0.0.1 to Trusted IPs if needed
6. Launch the Dashboard python main.py

The GUI will open, where you can:
- Enter your stock ticker
- Select the earnings date
- Adjust days to expiry for options analysis
- Connect to IB and run the IV crush analysis
- Explore the Analysis
  
Once connected and the analysis is complete, the dashboard will display:
- Stock price movements around earnings
- Implied volatility before and after earnings
- ATM option pricing and straddle values
- Greeks (Delta, Vega) and changes
- Graphical visualizations for quick interpretation
