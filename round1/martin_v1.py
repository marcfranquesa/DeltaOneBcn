import pandas as pd
import numpy as np
from scipy.stats import norm

# Definim parametres per Avellaneda Stoikov

gamma = 1
alpha = 0.1
n_sigma = 2

def calculate_optimal_spread(data):
    # Calculem vwap i stdev
    vwap = (data['price'] * data['volume']).sum() / data['volume'].sum()
    std_dev = data['price'].std()

    # calcul optimal bid-ask
    spread = 2 * alpha * std_dev / (gamma * vwap)

    return spread

def place_orders(data, open_lots, spread):
    # Calculem bid i ask prices
    vwap = (data['price'] * data['volume']).sum() / data['volume'].sum()
    mid_price = vwap + spread / 2
    bid_price = mid_price - spread / 2
    ask_price = mid_price + spread / 2

    # calculem quanitat optima
    quantity = gamma * (mid_price - data['price'].iloc[-1]) / spread

    # Probabilitat de que una ordre sigui filled
    prob_fill = norm.cdf(n_sigma * np.abs(quantity))

    # Posa ordres
    if open_lots == 0:
        # no lots open
        if np.random.rand() < prob_fill:
            if quantity > 0:
                order = {'price': ask_price, 'lots': quantity}
            else:
                order = {'price': bid_price, 'lots': -quantity}
        else:
            order = None
    else:
        # tancar o no lots oberts
        if np.sign(open_lots) == np.sign(quantity):
            # mateixa direccio, hold posicio
            order = None
        elif np.abs(open_lots) > np.abs(quantity):
            # tanca part profitable de la posicio
            if np.random.rand() < prob_fill:
                if quantity > 0:
                    order = {'price': ask_price, 'lots': -np.sign(open_lots) * np.abs(quantity)}
                else:
                    order = {'price': bid_price, 'lots': np.sign(open_lots) * np.abs(quantity)}
            else:
                order = None
        else:
            # tanca posicio sencera
            if np.random.rand() < prob_fill:
                if quantity > 0:
                    order = {'price': ask_price, 'lots': -open_lots}
                else:
                    order = {'price': bid_price, 'lots': open_lots}
            else:
                order = None

    return order
