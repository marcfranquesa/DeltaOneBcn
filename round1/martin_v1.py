import pandas as pd
import numpy as np
from scipy.stats import norm

def calculate_optimal_spread(data, gamma=1, alpha=0.1):
    if data.empty:
        raise ValueError("Data cannot be empty.")

    vwap = (data['price'] * data['volume']).sum() / data['volume'].sum()
    std_dev = data['price'].std()
    spread = 2 * alpha * std_dev / (gamma * vwap)
    return spread

import time

def place_orders(data, open_lots, spread, gamma=1, n_sigma=2, order_count=0):
    if data.empty:
        raise ValueError("Data cannot be empty.")

    if order_count >= 10:
        return None

    vwap = (data['price'] * data['volume']).sum() / data['volume'].sum()
    mid_price = vwap + spread / 2
    bid_price = mid_price - spread / 2
    ask_price = mid_price + spread / 2

    quantity = gamma * (mid_price - data['price'].iloc[-1]) / spread
    prob_fill = norm.cdf(n_sigma * np.abs(quantity))

    if open_lots == 0:
        if np.random.rand() < prob_fill:
            if quantity > 0:
                order = {'price': ask_price, 'lots': quantity}
            else:
                order = {'price': bid_price, 'lots': -quantity}
        else:
            order = None
    else:
        if np.sign(open_lots) == np.sign(quantity):
            order = None
        elif np.abs(open_lots) > np.abs(quantity):
            if np.random.rand() < prob_fill:
                if quantity > 0:
                    order = {'price': ask_price, 'lots': -np.sign(open_lots) * np.abs(quantity)}
                else:
                    order = {'price': bid_price, 'lots': np.sign(open_lots) * np.abs(quantity)}
            else:
                order = None
        else:
            if np.random.rand() < prob_fill:
                if quantity > 0:
                    order = {'price': ask_price, 'lots': -open_lots}
                else:
                    order = {'price': bid_price, 'lots': open_lots}
            else:
                order = None

    if order is not None:
        order_count += 1
        time.sleep(0.02)  # add a delay to limit order rate
    return order, order_count




#%%
