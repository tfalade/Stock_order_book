"""Classes, functions, and variables to support Order.
"""

from enum import Enum


class OrderOption(Enum):
    """Type of the Order.
    """
    buy = 'buy'
    sell = 'sell'


class StockOrder(object):
    """Stock object to build an order
    
    :param int timestamp: time the message was generated fromm the market
    :param str order_id: unique ID to modify order
    :param enum side_option: order option, either to buy or sell
    :param float stock_price: price of the listed stock
    :param int stock_size: size of the stock either to buy or sell
    """
    def __init__(self, order_id, timestamp, side_option, stock_price, stock_size):
        self.order_id = order_id
        self.timestamp = timestamp
        self.side_option = side_option
        self.stock_price = stock_price
        self.stock_size = stock_size