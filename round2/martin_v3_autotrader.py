import time

# Initialize variables
active_orders = []
max_orders = 10
position = 0
tick_size = 0.01
spread = 0.02


def get_lowest_ask(order_book):
    lowest_ask = None
    for order in order_book:
        if order["type"] == "ask" and (
            lowest_ask is None or order["price"] < lowest_ask
        ):
            lowest_ask = order["price"]
    return lowest_ask


def get_highest_bid(order_book):
    highest_bid = None
    for order in order_book:
        if order["type"] == "bid" and (
            highest_bid is None or order["price"] > highest_bid
        ):
            highest_bid = order["price"]
    return highest_bid


def place_order(order_type, price, quantity):
    global active_orders
    order = {"type": order_type, "price": price, "quantity": quantity}
    active_orders.append(order)
    print(f"Placed {order_type} order: price={price}, quantity={quantity}")


def cancel_order(order):
    global active_orders
    active_orders.remove(order)
    print(f"Cancelled order: price={order['price']}, quantity={order['quantity']}")


# Main loop
while True:
    order_book = get_order_book()
    position = sum([order["quantity"] for order in active_orders])

    if len(active_orders) >= max_orders:
        cancel_order(active_orders[0])

    lowest_ask = get_lowest_ask(order_book)
    highest_bid = get_highest_bid(order_book)

    if position != 0 and highest_bid is not None:
        if abs(position) > tick_size:
            hedge_price = highest_bid - spread if position > 0 else highest_bid + spread
            hedge_quantity = min(abs(position), tick_size)
            place_order("bid", hedge_price, hedge_quantity)

    elif lowest_ask is not None:
        sell_price = lowest_ask
        sell_quantity = min(tick_size, abs(position))
        place_order("ask", sell_price, sell_quantity)

    time.sleep(0.5)
