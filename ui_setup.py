# Plotting
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Tkinter stuff
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

def setup_ui(self):
    # -----------------------------
    # Main frame
    # -----------------------------
    main_frame = ttk.Frame(self.root, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

    self.root.columnconfigure(0, weight=1)
    self.root.rowconfigure(0, weight=1)

    # Two-column layout
    main_frame.columnconfigure(0, weight=0)   # LEFT (controls)
    main_frame.columnconfigure(1, weight=1)   # RIGHT (analytics)
    main_frame.rowconfigure(8, weight=1)

    # =========================================================
    # LEFT COLUMN — CONTROLS
    # =========================================================

    # IB Connection
    conn_frame = ttk.LabelFrame(main_frame, text="Interactive Brokers Connection", padding="5")
    conn_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

    ttk.Label(conn_frame, text="Host:").grid(row=0, column=0, padx=(0, 5))
    self.host_var = tk.StringVar(value="127.0.0.1")
    ttk.Entry(conn_frame, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=(0, 10))

    ttk.Label(conn_frame, text="Port:").grid(row=0, column=2, padx=(0, 5))
    self.port_var = tk.StringVar(value="7497")
    ttk.Entry(conn_frame, textvariable=self.port_var, width=10).grid(row=0, column=3, padx=(0, 10))

    self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.connect_ib)
    self.connect_btn.grid(row=0, column=4, padx=(0, 10))

    self.disconnect_btn = ttk.Button(
        conn_frame, text="Disconnect", command=self.disconnect_ib, state="disabled"
    )
    self.disconnect_btn.grid(row=0, column=5)

    # Earnings Setup
    earnings_frame = ttk.LabelFrame(main_frame, text="Earnings Analysis Setup", padding="5")
    earnings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

    ttk.Label(earnings_frame, text="Ticker:").grid(row=0, column=0, padx=(0, 5))
    self.ticker_var = tk.StringVar(value="NVDA")
    ttk.Entry(earnings_frame, textvariable=self.ticker_var, width=10).grid(row=0, column=1, padx=(0, 10))

    ttk.Label(earnings_frame, text="Earnings Date:").grid(row=0, column=2, padx=(0, 5))
    self.earnings_date_var = tk.StringVar(value="2025-08-27")
    ttk.Entry(
        earnings_frame, textvariable=self.earnings_date_var, width=12
    ).grid(row=0, column=3, padx=(0, 10))

    ttk.Label(earnings_frame, text="Days to Expiry:").grid(row=0, column=4, padx=(0, 5))
    self.days_to_expiry_var = tk.StringVar(value="30")
    ttk.Entry(
        earnings_frame, textvariable=self.days_to_expiry_var, width=8
    ).grid(row=0, column=5, padx=(0, 10))

    self.analyze_btn = ttk.Button(
        earnings_frame,
        text="Analyze IV Crush",
        command=self.analyze_iv_crush,
        state="disabled",
    )
    self.analyze_btn.grid(row=0, column=6)

    # =========================================================
    # RIGHT COLUMN — ANALYTICS / OUTPUTS
    # =========================================================

    right_panel = ttk.Frame(main_frame)
    right_panel.grid(row=0, column=1, rowspan=7, sticky=(tk.N, tk.S, tk.E, tk.W), padx=(10, 0))
    right_panel.columnconfigure(0, weight=1)

    # ---- Current Metrics
    metrics_frame = ttk.LabelFrame(right_panel, text="Current Metrics", padding="5")
    metrics_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

    ttk.Label(metrics_frame, text="Stock Price:").grid(row=0, column=0)
    self.stock_price_label = ttk.Label(metrics_frame, text="N/A", font=("Arial", 10, "bold"))
    self.stock_price_label.grid(row=0, column=1, padx=(0, 20))

    ttk.Label(metrics_frame, text="VIX Level:").grid(row=0, column=2)
    self.vix_level_label = ttk.Label(metrics_frame, text="N/A", font=("Arial", 10, "bold"))
    self.vix_level_label.grid(row=0, column=3, padx=(0, 20))

    ttk.Label(metrics_frame, text="Current IV:").grid(row=0, column=4)
    self.current_iv_label = ttk.Label(metrics_frame, text="N/A", font=("Arial", 10, "bold"))
    self.current_iv_label.grid(row=0, column=5)

    # ---- IV Crush
    crush_frame = ttk.LabelFrame(right_panel, text="IV Crush Analysis", padding="5")
    crush_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

    ttk.Label(crush_frame, text="Pre-Earnings IV:").grid(row=0, column=0)
    self.pre_iv_label = ttk.Label(crush_frame, text="N/A", font=("Arial", 10, "bold"))
    self.pre_iv_label.grid(row=0, column=1, padx=(0, 20))

    ttk.Label(crush_frame, text="Post-Earnings IV:").grid(row=0, column=2)
    self.post_iv_label = ttk.Label(crush_frame, text="N/A", font=("Arial", 10, "bold"))
    self.post_iv_label.grid(row=0, column=3, padx=(0, 20))

    ttk.Label(crush_frame, text="IV Crush %:").grid(row=0, column=4)
    self.iv_crush_label = ttk.Label(
        crush_frame, text="N/A", font=("Arial", 11, "bold"), foreground="red"
    )
    self.iv_crush_label.grid(row=0, column=5)

    # ---- Spot vs Strike
    spot_frame = ttk.LabelFrame(right_panel, text="Spot vs Strike Analysis", padding="5")
    spot_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

    ttk.Label(spot_frame, text="Strike Price:").grid(row=0, column=0)
    self.strike_price_label = ttk.Label(
        spot_frame, text="N/A", font=("Arial", 11, "bold"), foreground="blue"
    )
    self.strike_price_label.grid(row=0, column=1, padx=(0, 20))

    ttk.Label(spot_frame, text="Pre-Earnings Spot:").grid(row=0, column=2)
    self.pre_spot_label = ttk.Label(spot_frame, text="N/A", font=("Arial", 11, "bold"))
    self.pre_spot_label.grid(row=0, column=3, padx=(0, 20))

    ttk.Label(spot_frame, text="Post-Earnings Spot:").grid(row=0, column=4)
    self.post_spot_label = ttk.Label(spot_frame, text="N/A", font=("Arial", 11, "bold"))
    self.post_spot_label.grid(row=0, column=5)

    # ---- Greeks
    greeks_frame = ttk.LabelFrame(right_panel, text="Greeks Analysis", padding="5")
    greeks_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

    ttk.Label(greeks_frame, text="Pre Δ:").grid(row=0, column=0)
    self.pre_delta_label = ttk.Label(greeks_frame, text="N/A", font=("Arial", 10, "bold"))
    self.pre_delta_label.grid(row=0, column=1, padx=(0, 20))

    ttk.Label(greeks_frame, text="Post Δ:").grid(row=0, column=2)
    self.post_delta_label = ttk.Label(greeks_frame, text="N/A", font=("Arial", 10, "bold"))
    self.post_delta_label.grid(row=0, column=3, padx=(0, 20))

    ttk.Label(greeks_frame, text="Δ Change:").grid(row=0, column=4)
    self.delta_change_label = ttk.Label(greeks_frame, text="N/A", font=("Arial", 10, "bold"))
    self.delta_change_label.grid(row=0, column=5)

    # ---- Status
    status_frame = ttk.LabelFrame(right_panel, text="Status", padding="5")
    status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

    self.status_text = scrolledtext.ScrolledText(status_frame, height=6)
    self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
    status_frame.columnconfigure(0, weight=1)

    # =========================================================
    # BOTTOM — PLOT (FULL WIDTH)
    # =========================================================

    plot_frame = ttk.LabelFrame(main_frame, text="IV Crush Visualization", padding="5")
    plot_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W))

    plot_frame.columnconfigure(0, weight=1)
    plot_frame.rowconfigure(0, weight=1)

    self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(16, 6))
    self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
    self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))