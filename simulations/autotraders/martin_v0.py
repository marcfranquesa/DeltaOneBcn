# Copyright 2021 Optiver Asia Pacific Pty. Ltd.
#
# This file is part of Ready Trader Go.
#
#     Ready Trader Go is free software: you can redistribute it and/or
#     modify it under the terms of the GNU Affero General Public License
#     as published by the Free Software Foundation, either version 3 of
#     the License, or (at your option) any later version.
#
#     Ready Trader Go is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public
#     License along with Ready Trader Go.  If not, see
#     <https://www.gnu.org/licenses/>.
import asyncio
import itertools

from typing import List

from ready_trader_go import (
    BaseAutoTrader,
    Instrument,
    Lifespan,
    MAXIMUM_ASK,
    MINIMUM_BID,
    Side,
)

import pandas as pd
import numpy as np
from scipy.stats import norm

# Definim parametres per Avellaneda Stoikov (com els trobem?)

gamma = 1
alpha = 0.1
n_sigma = 2

def place_orders(data, open_lots):
    # Calculem VWA i stdev
    vwap = (data['price'] * data['volume']).sum() / data['volume'].sum()
    std_dev = data['price'].std()

    # Calculem preus i vol d optimitzacio optim
    price = vwap + alpha * np.sign(open_lots) * std_dev
    quantity = gamma * (price - data['price'].iloc[-1]) / std_dev

    # Probabilitat de que una ordre sigui filled
    prob_fill = norm.cdf(n_sigma * np.abs(quantity))

    # Posa ordres
    if open_lots == 0:
        # no lots open
        if np.random.rand() < prob_fill:
            order = {'price': price, 'lots': np.sign(quantity)}
        else:
            order = None
    else:
        # obre lots, posicio de tancar si es profitable, sino fa hold
        if np.sign(open_lots) == np.sign(quantity):
            # mateixa direccio, hold posicio
            order = None
        elif np.abs(open_lots) > np.abs(quantity):
            # tanca la part de la posicio amb benefici
            if np.random.rand() < prob_fill:
                order = {'price': price, 'lots': -np.sign(open_lots) * np.abs(quantity)}
            else:
                order = None
        else:
            # tanqca posicio sencera
            if np.random.rand() < prob_fill:
                order = {'price': price, 'lots': -open_lots}
            else:
                order = None

    return order
