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
    def __init__(self, exchange, starting_balance):
        self.exchange = exchange
        self.balance = starting_balance
        self.futures_position = 0
        self.orders = []
        self.active_orders = 0

    def place_order(self, price, size, is_buy=True, is_futures=False):
        if is_buy and self.balance < price * size:
            print("Not enough funds to place buy order.")
            return
        if not is_buy and not is_futures and size > self.exchange.asks.get(price, 0):
            print("Not enough asks to fill sell order.")
            return
        if is_futures and abs(size) > abs(self.futures_position):
            print("Not enough futures contracts to fill hedge order.")
            return

        order = {"price": price, "size": size, "is_buy": is_buy, "is_futures": is_futures}
        self.orders.append(order)
        self.active_orders += 1
        if is_futures:
            self.futures_position += size
        else:
            self.balance -= price * size
        print(f"Order placed: {'buy' if is_buy else 'sell'} {size} at {price}")

    def cancel_order(self, order):
        self.orders.remove(order)
        self.active_orders -= 1

    def execute_orders(self):
        for order in self.orders[:]:
            if order["is_futures"]:
                if order["size"] > 0:
                    bid = self.exchange.get_bid()
                    if bid > order["price"]:
                        self.exchange.place_bid(order["price"], order["size"])
                        self.futures_position -= order["size"]
                        self.cancel_order(order)
                        print(f"Hedge order filled: buy {order['size']} futures contracts at {order['price']}")
                else:
                    ask = self.exchange.get_ask()
                    if ask < order["price"]:
                        self.exchange.place_ask(order["price"], abs(order["size"]))
                        self.futures_position += abs(order["size"])
                        self.cancel_order(order)
                        print(f"Hedge order filled: sell {abs(order['size'])} futures contracts at {order['price']}")
            elif order["is_buy"]:
                if self.exchange.asks.get(order["price"], 0) >= order["size"]:
                    self.exchange.place_ask(order["price
