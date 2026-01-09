import pandas as pd
import numpy as np
import scipy.stats

def black_scholes_call(S, K, T, r, sigma):
    """
    Calculate Black-Scholes call option price

    Parameters:
    S: Current stock price
    K: Strike price
    T: Time to expiry (in years)
    r: Risk-free rate (annualized)
    sigma: Volatility (annualized using √252 factor)
    """
    from scipy.stats import norm

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return call_price


def black_scholes_put(S, K, T, r, sigma):
    """
    Calculate Black-Scholes put option price

    Parameters:
    S: Current stock price
    K: Strike price
    T: Time to expiry (in years)
    r: Risk-free rate (annualized)
    sigma: Volatility (annualized using √252 factor)
    """
    from scipy.stats import norm

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return put_price


def calculate_delta(S, K, T, r, sigma, option_type='call'):
    """Calculate option delta"""
    from scipy.stats import norm

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    if option_type == 'call':
        return norm.cdf(d1)
    else:  # put
        return -norm.cdf(-d1)


def calculate_vega(S, K, T, r, sigma):
    """Calculate option vega (same for calls and puts)"""
    from scipy.stats import norm

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    # Vega is per 1% change in volatility
    return S * norm.pdf(d1) * np.sqrt(T) / 100