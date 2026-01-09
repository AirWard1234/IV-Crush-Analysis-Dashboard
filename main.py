# Interactive Brokers API
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import time

from ui_setup import setup_ui
from IBApp import IBApp
from option_math import black_scholes_call, black_scholes_put, calculate_delta, calculate_vega

def run_iv_crush_analysis(
    stock_data,
    iv_data,
    vix_data,
    earnings_date,
    days_to_expiry,
    risk_free_rate
):
    # --- Dates ---
    stock_dates = stock_data.index
    pre_date = stock_dates[stock_dates <= earnings_date].max()
    post_date = stock_dates[stock_dates > earnings_date].min()

    pre_spot = stock_data.loc[pre_date, 'close']
    post_spot = (stock_data.loc[post_date, 'open'] +
                 stock_data.loc[post_date, 'close']) / 2

    # --- IV ---
    if iv_data is not None:
        pre_iv = iv_data.loc[iv_data.index <= pre_date].iloc[-1]['implied_vol']
        post_iv = iv_data.loc[iv_data.index >= post_date].iloc[0]['implied_vol']
    else:
        pre_vix = vix_data.loc[vix_data.index <= pre_date].iloc[-1]['close'] if vix_data is not None else 20
        post_vix = vix_data.loc[vix_data.index >= post_date].iloc[0]['close'] if vix_data is not None else 20
        pre_iv = pre_vix / 100 * 1.5
        post_iv = post_vix / 100 * 1.2

    # --- Options ---
    T = days_to_expiry / 365
    K = pre_spot

    pre_call = black_scholes_call(pre_spot, K, T, risk_free_rate, pre_iv)
    pre_put = black_scholes_put(pre_spot, K, T, risk_free_rate, pre_iv)
    post_call = black_scholes_call(post_spot, K, T, risk_free_rate, post_iv)
    post_put = black_scholes_put(post_spot, K, T, risk_free_rate, post_iv)

    pre_straddle = pre_call + pre_put
    post_straddle = post_call + post_put

    # --- Greeks ---
    pre_delta = calculate_delta(pre_spot, K, T, risk_free_rate, pre_iv, 'call') + \
                calculate_delta(pre_spot, K, T, risk_free_rate, pre_iv, 'put')

    post_delta = calculate_delta(post_spot, K, T, risk_free_rate, post_iv, 'call') + \
                 calculate_delta(post_spot, K, T, risk_free_rate, post_iv, 'put')

    pre_vega = 2 * calculate_vega(pre_spot, K, T, risk_free_rate, pre_iv)
    post_vega = 2 * calculate_vega(post_spot, K, T, risk_free_rate, post_iv)

    return {
        "dates": (pre_date, post_date),
        "spot": (pre_spot, post_spot),
        "iv": (pre_iv, post_iv),
        "iv_crush_pct": (pre_iv - post_iv) / pre_iv * 100,
        "options": {
            "pre_call": pre_call,
            "pre_put": pre_put,
            "post_call": post_call,
            "post_put": post_put,
            "pre_straddle": pre_straddle,
            "post_straddle": post_straddle
        },
        "greeks": {
            "pre_delta": pre_delta,
            "post_delta": post_delta,
            "pre_vega": pre_vega,
            "post_vega": post_vega
        }
    }


class EarningsTradingDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Earnings Trading Dashboard - IV Crush Analysis")
        self.root.geometry("1600x1000")

        # Data storage
        self.stock_data = None
        self.vix_data = None
        self.iv_data = None
        self.earnings_date = None
        self.ticker = None

        # IB connection
        self.ib_app = IBApp()
        self.connected = False

        # Option pricing parameters
        self.risk_free_rate = 0.05  # 5% risk-free rate

        # Chart management
        self.ax1_twin = None  # Keep track of twin axis

        setup_ui(self)

    def create_equity_contract(self, symbol):
        """Create an equity contract for the given symbol"""
        contract = Contract()
        contract.symbol = symbol.upper()
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def create_vix_contract(self):
        """Create a VIX contract"""
        contract = Contract()
        contract.symbol = "VIX"
        contract.secType = "IND"
        contract.exchange = "CBOE"
        contract.currency = "USD"
        return contract


    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()

    def connect_ib(self):
        try:
            host = self.host_var.get()
            port = int(self.port_var.get())

            self.log_message(f"Connecting to IB at {host}:{port}...")

            # Start connection in separate thread
            def connect_thread():
                try:
                    self.ib_app.connect(host, port, 0)
                    self.ib_app.run()
                except Exception as e:
                    self.log_message(f"Connection error: {e}")

            thread = threading.Thread(target=connect_thread, daemon=True)
            thread.start()

            # Wait for connection and server version
            for i in range(100):  # Wait up to 10 seconds
                if self.ib_app.connected:
                    try:
                        server_version = self.ib_app.serverVersion()
                        if server_version is not None and server_version > 0:
                            break
                    except:
                        pass
                time.sleep(0.1)

            if self.ib_app.connected:
                try:
                    server_version = self.ib_app.serverVersion()
                    if server_version is not None and server_version > 0:
                        self.connected = True
                        self.connect_btn.config(state="disabled")
                        self.disconnect_btn.config(state="normal")
                        self.analyze_btn.config(state="normal")
                        self.log_message(
                            f"Successfully connected to Interactive Brokers (Server Version: {server_version})")
                    else:
                        self.log_message(
                            "Connected but server version not available. Please wait a moment and try again.")
                except Exception as e:
                    self.log_message(f"Connection established but server version check failed: {e}")
            else:
                self.log_message("Failed to connect to Interactive Brokers")

        except Exception as e:
            self.log_message(f"Connection error: {e}")

    def disconnect_ib(self):
        try:
            self.ib_app.disconnect()
            self.connected = False
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self.analyze_btn.config(state="disabled")

            # Clear any existing analysis results
            self.clear_analysis_results()

            self.log_message("Disconnected from Interactive Brokers")
        except Exception as e:
            self.log_message(f"Disconnect error: {e}")

    def clear_analysis_results(self):
        """Clear all analysis results and reset displays"""
        # Clear charts completely including any twin axes
        self.ax1.clear()
        self.ax2.clear()

        # Clear any twin axes that might exist
        if self.ax1_twin is not None:
            try:
                self.ax1_twin.remove()
            except:
                pass
            self.ax1_twin = None

        # Redraw the canvas
        self.canvas.draw()

        # Reset all metric displays
        self.stock_price_label.config(text="N/A", foreground="black")
        self.vix_level_label.config(text="N/A", foreground="black")
        self.current_iv_label.config(text="N/A", foreground="black")

        # Reset IV crush displays
        self.pre_iv_label.config(text="N/A", foreground="black")
        self.post_iv_label.config(text="N/A", foreground="black")
        self.iv_crush_label.config(text="N/A", foreground="red")

        # Reset option pricing displays
        self.pre_call_label.config(text="N/A", foreground="black")
        self.post_call_label.config(text="N/A", foreground="black")
        self.call_loss_label.config(text="N/A", foreground="black")

        self.pre_put_label.config(text="N/A", foreground="black")
        self.post_put_label.config(text="N/A", foreground="black")
        self.put_loss_label.config(text="N/A", foreground="black")

        # Reset straddle displays
        self.pre_straddle_label.config(text="N/A", foreground="blue")
        self.post_straddle_label.config(text="N/A", foreground="blue")
        self.straddle_loss_label.config(text="N/A", foreground="black")

        # Reset P/L displays
        self.long_pnl_label.config(text="N/A", foreground="black")
        self.short_pnl_label.config(text="N/A", foreground="black")

        # Reset spot/strike displays
        self.strike_price_label.config(text="N/A", foreground="blue")
        self.pre_spot_label.config(text="N/A", foreground="black")
        self.post_spot_label.config(text="N/A", foreground="black")

        # Reset Greeks displays
        self.pre_delta_label.config(text="N/A", foreground="black")
        self.post_delta_label.config(text="N/A", foreground="black")
        self.delta_change_label.config(text="N/A", foreground="black")
        self.pre_vega_label.config(text="N/A", foreground="black")
        self.post_vega_label.config(text="N/A", foreground="black")
        self.vega_change_label.config(text="N/A", foreground="black")

        # Reset data storage
        self.stock_data = None
        self.vix_data = None
        self.iv_data = None

        # Clear IB historical data cache
        if hasattr(self, 'ib_app') and self.ib_app:
            self.ib_app.historical_data.clear()

        self.log_message("Analysis results cleared - ready for new analysis")


    def analyze_iv_crush(self):
        if not self.connected or not self.ib_app.connected:
            messagebox.showerror("Error", "Not connected to Interactive Brokers")
            return

        # Check if we have a valid server version
        try:
            server_version = self.ib_app.serverVersion()
            if server_version is None or server_version <= 0:
                messagebox.showerror("Error", "Connection not fully established. Please wait and try again.")
                return
        except Exception as e:
            self.log_message(f"Connection error: {e}")
            messagebox.showerror("Error", "Connection not stable. Please reconnect.")
            return

        self.ticker = self.ticker_var.get().upper()
        earnings_date_str = self.earnings_date_var.get()

        try:
            self.earnings_date = datetime.strptime(earnings_date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
            return

        self.log_message(f"Starting IV crush analysis for {self.ticker} around earnings on {earnings_date_str}")

        # Clear previous visualizations and reset displays
        self.clear_analysis_results()

        # Calculate date range (3 days before and after earnings)
        start_date = self.earnings_date - timedelta(days=10)  # Extra buffer for data
        end_date = self.earnings_date + timedelta(days=10)

        # Clear previous data
        self.ib_app.historical_data.clear()

        # Query stock price data
        self.log_message(f"Querying stock price data for {self.ticker}...")
        stock_contract = self.create_equity_contract(self.ticker)

        # Clear any existing data for this request ID before making new request
        if 1 in self.ib_app.historical_data:
            del self.ib_app.historical_data[1]

        try:
            self.ib_app.reqHistoricalData(
                reqId=1,
                contract=stock_contract,
                endDateTime=end_date.strftime("%Y%m%d %H:%M:%S"),
                durationStr="3 W",
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
        except Exception as e:
            self.log_message(f"Error requesting stock data: {e}")
            messagebox.showerror("Error", f"Failed to request stock data: {e}")
            return

        # Wait for stock data
        timeout = 15
        start_time = time.time()
        while 1 not in self.ib_app.historical_data and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if 1 not in self.ib_app.historical_data:
            self.log_message("Failed to get stock price data")
            return

        # Process stock data
        stock_data = pd.DataFrame(self.ib_app.historical_data[1])
        stock_data['date'] = pd.to_datetime(stock_data['date'])
        stock_data.set_index('date', inplace=True)
        self.stock_data = stock_data
        self.log_message(f"Received {len(stock_data)} stock price data points")

        # Query VIX data
        self.log_message("Querying VIX data...")
        vix_contract = self.create_vix_contract()

        # Clear any existing VIX data for this request ID
        if 2 in self.ib_app.historical_data:
            del self.ib_app.historical_data[2]

        try:
            self.ib_app.reqHistoricalData(
                reqId=2,
                contract=vix_contract,
                endDateTime=end_date.strftime("%Y%m%d %H:%M:%S"),
                durationStr="3 W",
                barSizeSetting="1 day",
                whatToShow="TRADES",
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
        except Exception as e:
            self.log_message(f"Error requesting VIX data: {e}")
            # Continue without VIX data

        # Wait for VIX data
        start_time = time.time()
        while 2 not in self.ib_app.historical_data and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if 2 in self.ib_app.historical_data:
            vix_data = pd.DataFrame(self.ib_app.historical_data[2])
            vix_data['date'] = pd.to_datetime(vix_data['date'])
            vix_data.set_index('date', inplace=True)
            self.vix_data = vix_data
            self.log_message(f"Received {len(vix_data)} VIX data points")
        else:
            self.log_message("VIX data not available")
            self.vix_data = None

        # Query IV data for the stock
        self.log_message(f"Querying implied volatility data for {self.ticker}...")

        # Clear any existing IV data for this request ID
        if 3 in self.ib_app.historical_data:
            del self.ib_app.historical_data[3]

        try:
            self.ib_app.reqHistoricalData(
                reqId=3,
                contract=stock_contract,
                endDateTime=end_date.strftime("%Y%m%d %H:%M:%S"),
                durationStr="3 W",
                barSizeSetting="1 day",
                whatToShow="OPTION_IMPLIED_VOLATILITY",
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
        except Exception as e:
            self.log_message(f"Error requesting IV data: {e}")
            # Continue without direct IV data

        # Wait for IV data
        start_time = time.time()
        while 3 not in self.ib_app.historical_data and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if 3 in self.ib_app.historical_data:
            iv_data = pd.DataFrame(self.ib_app.historical_data[3])
            iv_data['date'] = pd.to_datetime(iv_data['date'])
            iv_data.set_index('date', inplace=True)

            # Scale IV data properly once here - IB provides DAILY IV that needs annualization
            raw_iv = iv_data['close']

            # Convert to decimal if in percentage form, then annualize with √252
            if raw_iv.max() > 5:
                # Data is in percentage form (e.g., 2.5 for 2.5% daily), convert to decimal then annualize
                daily_iv_decimal = raw_iv / 100.0  # Convert to decimal (0.025 for 2.5%)
                iv_data['implied_vol'] = daily_iv_decimal  # * np.sqrt(252)  # Annualize with √252
                self.log_message(
                    f"Received {len(iv_data)} IV data points - converted from daily % to annualized decimal")
            else:
                # Data is in decimal form (e.g., 0.025 for 2.5% daily), annualize directly
                iv_data['implied_vol'] = raw_iv  # * np.sqrt(252)  # Annualize with √252
                self.log_message(f"Received {len(iv_data)} IV data points - annualized daily decimal with √252")

            self.iv_data = iv_data
            annualization_factor = 1  # np.sqrt(252)
            self.log_message(f"Applied √252 = {annualization_factor:.2f} annualization factor")
            self.log_message(
                f"Annualized IV range: {iv_data['implied_vol'].min():.3f} - {iv_data['implied_vol'].max():.3f} (decimal)")
        else:
            self.log_message("Implied volatility data not available - will estimate from VIX")
            self.iv_data = None

        # Perform IV crush analysis
        self.perform_iv_crush_analysis()

    def perform_iv_crush_analysis(self):
        self.log_message("Performing IV crush analysis...")

        try:
            days_to_expiry = int(self.days_to_expiry_var.get())
        except ValueError:
            days_to_expiry = 30
            self.days_to_expiry_var.set("30")

        results = run_iv_crush_analysis(
            stock_data=self.stock_data,
            iv_data=self.iv_data,
            vix_data=self.vix_data,
            earnings_date=self.earnings_date,
            days_to_expiry=days_to_expiry,
            risk_free_rate=self.risk_free_rate
        )

        self.update_ui_from_results(results)
        self.create_visualizations()

    def update_ui_from_results(self, r):
        pre_spot, post_spot = r["spot"]
        pre_iv, post_iv = r["iv"]

        self.stock_price_label.config(text=f"${post_spot:.2f}")
        self.pre_iv_label.config(text=f"{pre_iv:.1%}")
        self.post_iv_label.config(text=f"{post_iv:.1%}")
        self.current_iv_label.config(text=f"{post_iv:.1%}")
        self.iv_crush_label.config(text=f"-{r['iv_crush_pct']:.1f}%")

        pre = r["options"]["pre_straddle"]
        post = r["options"]["post_straddle"]
        change = post - pre

        self.pre_straddle_label.config(text=f"${pre:.2f}")
        self.post_straddle_label.config(text=f"${post:.2f}")
        self.straddle_loss_label.config(
            text=f"{change:+.2f}",
            foreground="green" if change > 0 else "red"
        )

        self.pre_delta_label.config(text=f"{r['greeks']['pre_delta']:.3f}")
        self.post_delta_label.config(text=f"{r['greeks']['post_delta']:.3f}")
        self.delta_change_label.config(
            text=f"{r['greeks']['post_delta'] - r['greeks']['pre_delta']:+.3f}"
        )

        self.pre_vega_label.config(text=f"{r['greeks']['pre_vega']:.2f}")
        self.post_vega_label.config(text=f"{r['greeks']['post_vega']:.2f}")
        self.vega_change_label.config(
            text=f"{r['greeks']['post_vega'] - r['greeks']['pre_vega']:+.2f}"
        )

    def create_visualizations(self):
        """Create visualizations for the IV crush analysis"""
        # Clear all axes including any twin axes
        self.ax1.clear()
        self.ax2.clear()

        # Remove any existing twin axes
        if self.ax1_twin is not None:
            try:
                self.ax1_twin.remove()
            except:
                pass
            self.ax1_twin = None

        # Plot 1: Stock price and IV around earnings
        earnings_window = pd.date_range(start=self.earnings_date - timedelta(days=5),
                                        end=self.earnings_date + timedelta(days=5), freq='D')

        # Filter stock data for the window
        window_stock = self.stock_data[
            (self.stock_data.index >= self.earnings_date - timedelta(days=5)) &
            (self.stock_data.index <= self.earnings_date + timedelta(days=5))
            ]

        # Plot stock price
        self.ax1.plot(window_stock.index, window_stock['close'], 'b-', linewidth=2, label='Stock Price')
        self.ax1.axvline(x=self.earnings_date, color='red', linestyle='--', alpha=0.7, label='Earnings Date')
        self.ax1.set_xlabel('Date')
        self.ax1.set_ylabel('Stock Price ($)', color='blue')
        self.ax1.tick_params(axis='y', labelcolor='blue')
        self.ax1.set_title(f'{self.ticker} Stock Price Around Earnings')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend(loc='upper left')

        # Plot IV if available
        if self.iv_data is not None and len(self.iv_data) > 0:
            window_iv = self.iv_data[
                (self.iv_data.index >= self.earnings_date - timedelta(days=5)) &
                (self.iv_data.index <= self.earnings_date + timedelta(days=5))
                ]

            if len(window_iv) > 0:
                self.ax1_twin = self.ax1.twinx()
                # Convert decimal IV to percentage for display (data is already properly scaled and annualized)
                iv_percentage = window_iv['implied_vol'] * 100

                self.ax1_twin.plot(window_iv.index, iv_percentage, 'g-', linewidth=2,
                                   label=f'Implied Volatility (% annualized √252={np.sqrt(252):.1f})')
                self.ax1_twin.set_ylabel('Implied Volatility (% annualized)', color='green')
                self.ax1_twin.tick_params(axis='y', labelcolor='green')
                self.ax1_twin.legend(loc='upper right')

        # Plot 2: VIX around earnings (if available)
        if self.vix_data is not None:
            window_vix = self.vix_data[
                (self.vix_data.index >= self.earnings_date - timedelta(days=5)) &
                (self.vix_data.index <= self.earnings_date + timedelta(days=5))
                ]

            self.ax2.plot(window_vix.index, window_vix['close'], 'purple', linewidth=2, label='VIX')
            self.ax2.axvline(x=self.earnings_date, color='red', linestyle='--', alpha=0.7, label='Earnings Date')
            self.ax2.set_xlabel('Date')
            self.ax2.set_ylabel('VIX Level')
            self.ax2.set_title('VIX Around Earnings Date')
            self.ax2.grid(True, alpha=0.3)
            self.ax2.legend()
        else:
            # If no VIX data, show straddle price comparison
            option_types = ['Call', 'Put', 'Straddle']
            pre_prices = [float(self.pre_call_label.cget('text').replace('$', '')),
                          float(self.pre_put_label.cget('text').replace('$', '')),
                          float(self.pre_straddle_label.cget('text').replace('$', ''))]
            post_prices = [float(self.post_call_label.cget('text').replace('$', '')),
                           float(self.post_put_label.cget('text').replace('$', '')),
                           float(self.post_straddle_label.cget('text').replace('$', ''))]

            x = np.arange(len(option_types))
            width = 0.35

            # Use different colors for straddle
            colors_pre = ['lightblue', 'lightgreen', 'blue']
            colors_post = ['lightcoral', 'lightpink', 'red']

            bars1 = self.ax2.bar(x - width / 2, pre_prices, width, label='Pre-Earnings (High IV)',
                                 color=colors_pre, alpha=0.8)
            bars2 = self.ax2.bar(x + width / 2, post_prices, width, label='Post-Earnings (Low IV)',
                                 color=colors_post, alpha=0.8)

            # Add value labels on bars
            for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
                height1 = bar1.get_height()
                height2 = bar2.get_height()
                self.ax2.text(bar1.get_x() + bar1.get_width() / 2., height1 + 0.5,
                              f'${height1:.1f}', ha='center', va='bottom', fontsize=9)
                self.ax2.text(bar2.get_x() + bar2.get_width() / 2., height2 + 0.5,
                              f'${height2:.1f}', ha='center', va='bottom', fontsize=9)

            self.ax2.set_xlabel('Option Strategy')
            self.ax2.set_ylabel('Option Price ($)')
            self.ax2.set_title('ATM Options & Straddle: IV Crush Impact')
            self.ax2.set_xticks(x)
            self.ax2.set_xticklabels(option_types)
            self.ax2.legend()
            self.ax2.grid(True, alpha=0.3)

            #Add a text box showing the IV crush impact
            straddle_loss_text = self.straddle_loss_label.cget('text')
            self.ax2.text(0.02, 0.98, f'Straddle Loss: {straddle_loss_text}',
                         transform=self.ax2.transAxes, fontsize=12, fontweight='bold',
                         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        #Format dates on x-axis
        self.ax1.tick_params(axis='x', rotation=45)
        if self.vix_data is not None:
            self.ax2.tick_params(axis='x', rotation=45)

        #Update canvas
        self.fig.tight_layout()
        self.canvas.draw()

def main():
    root = tk.Tk()
    app = EarningsTradingDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()