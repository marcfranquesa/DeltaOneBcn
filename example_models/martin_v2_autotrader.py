import time
import random

class Exchange:
    def __init__(self):
        self.bids = {}
        self.asks = {}
        self.last_trade = None

    def place_bid(self, price, size):
        self.bids[price] = self.bids.get(price, 0) + size

    def place_ask(self, price, size):
        self.asks[price] = self.asks.get(price, 0) + size

    def match(self):
        best_bid = max(self.bids.keys())
        best_ask = min(self.asks.keys())
        if best_bid >= best_ask:
            trade_price = best_ask
            trade_size = min(self.bids[best_bid], self.asks[best_ask])
            self.bids[best_bid] -= trade_size
            self.asks[best_ask] -= trade_size
            self.last_trade = (trade_price, trade_size)
            print(f"Trade executed at {trade_price} for size {trade_size}")

    def get_bid(self):
        return max(self.bids.keys())

    def get_ask(self):
        return min(self.asks.keys())

class TradingBot:
    def __init__(self):
        self.active_orders = []
        self.profit = 0

    def find_min_ask(self, market_data):
        asks = market_data['asks']
        if len(asks) > 0:
            return min(asks)
        return None

    def find_closest_bid(self, market_data, price):
        bids = market_data['bids']
        if len(bids) > 0:
            closest_bid = min(bids, key=lambda x: abs(x - price))
            if closest_bid != price:
                return closest_bid
        return None

    def process_tick(self, market_data):
        min_ask = self.find_min_ask(market_data)
        if min_ask is None:
            return

        closest_bid = self.find_closest_bid(market_data, min_ask)
        if closest_bid is None:
            return

        if len(self.active_orders) < 10:
            sell_order = {'type': 'sell', 'price': min_ask, 'quantity': 1}
            buy_order = {'type': 'buy', 'price': closest_bid, 'quantity': 1}

            self.active_orders.append(sell_order)
            self.active_orders.append(buy_order)

            self.profit -= (min_ask - closest_bid)

            print(f"New orders placed. Sell: {min_ask}, Buy: {closest_bid}")
        else:
            print("Max active orders reached. Cannot place new orders.")
