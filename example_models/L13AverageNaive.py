from datetime import datetime
import itertools
import asyncio
import math
import time

from typing import List, Tuple

from ready_trader_go import (
    BaseAutoTrader,
    Instrument,
    Lifespan,
    MAXIMUM_ASK,
    MINIMUM_BID,
    Side,
)

LOT_SIZE = 10
POSITION_LIMIT = 100
TICK_SIZE_IN_CENTS = 100
MIN_BID_NEAREST_TICK = (
    (MINIMUM_BID + TICK_SIZE_IN_CENTS) // TICK_SIZE_IN_CENTS * TICK_SIZE_IN_CENTS
)
MAX_ASK_NEAREST_TICK = MAXIMUM_ASK // TICK_SIZE_IN_CENTS * TICK_SIZE_IN_CENTS


class AutoTrader(BaseAutoTrader):
    def __init__(self, loop: asyncio.AbstractEventLoop, team_name: str, secret: str):
        """Initialise a new instance of the AutoTrader class."""

        super().__init__(loop, team_name, secret)
        self.order_ids = itertools.count(1)
        self.ask_id = (
            self.ask_price
        ) = self.bid_id = self.bid_price = self.position = self.size = 0

        self.bids = set()
        self.asks = set()
        self.tick_storage_limit = 5000

        self.order_volume = 1
        self.theo_price = 0

        self.start_second = 0
        self.current_time = 0
        self.time_diff = 0
        self.action_count = 0

    def on_error_message(self, client_order_id: int, error_message: bytes) -> None:
        """Called when the exchange detects an error."""
        self.logger.warning(
            "error with order %d: %s", client_order_id, error_message.decode()
        )
        self.on_order_status_message(client_order_id, 0, 0, 0)

    def on_order_book_update_message(
        self,
        instrument: int,
        sequence_number: int,
        ask_prices: List[int],
        ask_volumes: List[int],
        bid_prices: List[int],
        bid_volumes: List[int],
    ) -> None:
        """Called periodically to report the status of an order book."""

        if instrument == Instrument.FUTURE:

            # Dont amend orders if near action limit.
            if self.action_count <= 14:
                if self.action_count == 0:
                    self.start_second = time.time()

                if 0 not in bid_prices:
                    self.theo_price = (
                        int(
                            (
                                (
                                    (
                                        (
                                            bid_prices[0] * bid_volumes[0]
                                            + bid_prices[1] * bid_volumes[1]
                                            + bid_prices[2] * bid_volumes[2]
                                        )
                                        / (
                                            bid_volumes[0]
                                            + bid_volumes[1]
                                            + bid_volumes[2]
                                        )
                                        + (
                                            ask_prices[0] * ask_volumes[0]
                                            + ask_prices[1] * ask_volumes[1]
                                            + ask_prices[2] * ask_volumes[2]
                                        )
                                        / (
                                            ask_volumes[0]
                                            + ask_volumes[1]
                                            + ask_volumes[2]
                                        )
                                    )
                                    / 2
                                )
                            )
                            / 100
                        )
                        * 100
                    )

                    # Use the current best bid and ask as new bid and ask quotes, skewing by inventory qty.
                    new_bid_price = (
                        ((self.theo_price - 100) - self.position * 100)
                        if bid_prices[0] != 0
                        else 0
                    )
                    new_ask_price = (
                        ((self.theo_price + 100) - self.position * 100)
                        if ask_prices[0] != 0
                        else 0
                    )

                    # If the new quoted price differs from the existing quoted price, cancel the old order.
                    if self.bid_id != 0 and new_bid_price not in (self.bid_price, 0):
                        self.send_cancel_order(self.bid_id)
                        self.bid_id = 0
                        self.action_count += 1
                    if self.ask_id != 0 and new_ask_price not in (self.ask_price, 0):
                        self.send_cancel_order(self.ask_id)
                        self.ask_id = 0
                        self.action_count += 1

                    # if self.prices_etf:
                    #     # Debug output.
                    #     print("New bid:", new_bid_price, "New Ask:", new_ask_price)
                    #     print("Old bid:", self.bid_price, "Old ask:", self.ask_price)
                    #     print("Best bid:", bid_prices[0], "Best ask:", ask_prices[0], "Position:", self.position)
                    #     print("Theo price:", self.theo_price, "Actual price:", self.prices_fut[-1])

                    # Determine bid volume according to current position.
                    if self.bid_id == 0 and new_bid_price != 0 and self.position < 95:
                        # if self.position < 20:
                        #     self.order_volume = 45
                        # elif self.position >= 20 and self.position < 50:
                        #     self.order_volume = 25
                        # elif self.position >= 50 and self.position < 80:
                        #     self.order_volume = 10
                        # elif self.position >= 80:
                        #     self.order_volume = 5
                        # else:
                        #     self.order_volume = 0

                        self.bid_id = next(self.order_ids)
                        self.bid_price = new_bid_price
                        self.send_insert_order(
                            self.bid_id,
                            Side.BUY,
                            new_bid_price,
                            self.order_volume,
                            Lifespan.GOOD_FOR_DAY,
                        )
                        self.bids.add(self.bid_id)
                        self.action_count += 1

                    # Determine ask volume according to current position.
                    if self.ask_id == 0 and new_ask_price != 0 and self.position > -95:
                        # if self.position > -20:
                        #     self.order_volume = 45
                        # elif self.position <= -20 and self.position > -50:
                        #     self.order_volume = 25
                        # elif self.position <= 50 and self.position > -80:
                        #     self.order_volume = 10
                        # elif self.position <= -80:
                        #     self.order_volume = 5
                        # else:
                        #     self.order_volume = 0

                        self.ask_id = next(self.order_ids)
                        self.ask_price = new_ask_price
                        self.send_insert_order(
                            self.ask_id,
                            Side.SELL,
                            new_ask_price,
                            self.order_volume,
                            Lifespan.GOOD_FOR_DAY,
                        )
                        self.asks.add(self.ask_id)
                        self.action_count += 1

            elif self.action_count > 14:
                self.current_time = time.time()
                self.time_diff = self.current_time - self.start_second
                if self.time_diff < 1:
                    time.sleep(1.01 - self.time_diff)
                    # time.sleep(self.ms_til_next_second())
                self.action_count = 0

    def on_order_status_message(
        self, client_order_id: int, fill_volume: int, remaining_volume: int, fees: int
    ) -> None:
        """Called when the status of one of your orders changes.

        The fill_volume is the number of lots already traded, remaining_volume
        is the number of lots yet to be traded and fees is the total fees for
        this order. Remember that you pay fees for being a market taker, but
        you receive fees for being a market maker, so fees can be negative.

        If an order is cancelled its remaining volume will be zero.
        """
        if remaining_volume == 0:
            if client_order_id == self.bid_id:
                self.bid_id = 0
            elif client_order_id == self.ask_id:
                self.ask_id = 0

            self.bids.discard(client_order_id)
            self.asks.discard(client_order_id)

    def on_order_filled_message(
        self, client_order_id: int, price: int, volume: int
    ) -> None:
        """Called when one of your orders is filled, partially or fully.

        The price is the price at which the order was (partially) filled,
        which may be better than the order's limit price. The volume is
        the number of lots filled at that price.
        """
        self.logger.info(
            "received order filled for order %d with price %d and volume %d",
            client_order_id,
            price,
            volume,
        )
        if client_order_id in self.bids:
            self.position += volume
            self.send_hedge_order(
                next(self.order_ids), Side.ASK, MIN_BID_NEAREST_TICK, volume
            )
        elif client_order_id in self.asks:
            self.position -= volume
            self.send_hedge_order(
                next(self.order_ids), Side.BID, MAX_ASK_NEAREST_TICK, volume
            )

    def on_trade_ticks_message(
        self,
        instrument: int,
        sequence_number: int,
        ask_prices: List[int],
        ask_volumes: List[int],
        bid_prices: List[int],
        bid_volumes: List[int],
    ) -> None:
        """Called periodically when there is trading activity on the market.

        The five best ask (i.e. sell) and bid (i.e. buy) prices at which there
        has been trading activity are reported along with the aggregated volume
        traded at each of those price levels.

        If there are less than five prices on a side, then zeros will appear at
        the end of both the prices and volumes arrays.
        """
        self.logger.info(
            "received trade ticks for instrument %d with sequence number %d",
            instrument,
            sequence_number,
        )

    def ms_til_next_second(self):
        """Return number of milliseconds (expressed as seconds) until next second."""

        delay = math.trunc((1000000 - datetime.utcnow().microsecond) / 1000)

        return delay / 1000
