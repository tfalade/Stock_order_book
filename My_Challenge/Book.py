"""Building the order book obects and operation that can be performed and listed in the book"""

import re
from operator import attrgetter
import Stock_order as buildOrder

"""Building reqular expression to match the entries in the book"""
BIDDING = '^([0-9]*) (A) ([a-z]*) (B) (\d+\.\d+) (\d*)\\n$'
ASKING = '^([0-9]*) (A) ([a-z]*) (S) (\d+\.\d+) (\d*)\\n$'
PROCESS_ORDER = '^([0-9]*) (R) ([a-z]*) (\d*)\\n$'


class ProcessOrder(object):
    """Build how oders are processed in the book"""
    
    def __init__(self, stock_size, output_dir):
        """Building a ProcessOrder object.
        :param int stock_size: the amount of stock to either buy or sell.
        :param str output_dir: the path where output log file will be stored
        """

        self.stock_size = stock_size
        self.bid_total = {}
        self.ask_total = {}
        self.made_from_stock = 'NA'
        self.spent_on_stock = 'NA'
        self.bid_total_shares = 0
        self.ask_total_shares = 0
        self.output_dir = output_dir

    def write_to_file(self, stock_input_to_log):
        """If file output path is set, log to a particular file. Otherwise, log to standard output.

        The file output path is primarily to make regression testing easier.
        """
        if self.output_dir:
            file = open(self.output_dir, 'a')
            file.write(stock_input_to_log + '\n')
            file.close()
        else:
            print(stock_input_to_log)

    def process_all(self, stock_input):
        """Updates instance of ProcessOrder with new stock_input.

        Validates the stock_input in the log file.

        :param str stock_input: stock_input in the log file.
        :raises AssertionError: If stock_input does not satisfy regular expressions.
        """
        # If stock_input is bid:
        if re.match(BIDDING, stock_input):
            self.process_bid(stock_input)
        # If stock_input is ask:
        elif re.match(ASKING, stock_input):
            self.process_ask(stock_input)
        # If stock_input is reduce:
        elif re.match(PROCESS_ORDER, stock_input):
            self.record_order_reduce(stock_input)
        # If stock_input is none of the above, it is invalid.
        else:
            raise AssertionError('Invalid stock_input')

    @staticmethod
    def build_order(stock_input, order_option):
        """Build an order from the input

        :param str stock_input: takes input from log file
        :param enum order_option: states the action, buying or selling stock
        """
        row = stock_input.rstrip('\n').split(' ')

        my_order = buildOrder.StockOrder(
            row[2],
            int(row[0]),
            order_option,
            float(row[4]),
            int(row[5])
        )

        return my_order

    def process_bid(self, stock_input):
        """Takes in a bid, logs the output to file or print the output

        :param str stock_input: input from the stock order log"""
        bid = self.build_order(stock_input, buildOrder.OrderOption.buy)
        self.bid_total[bid.order_id] = bid
        self.bid_total_shares += bid.stock_size

        if self.bid_total_shares >= self.stock_size:
            income = self.process_stock_option(self.bid_total.values(), True)

            if self.made_from_stock != income:
                self.made_from_stock = income
                log_stock_input = str(bid.timestamp) + ' S ' + '{:0.2f}'.format(income)
                self.write_to_file(log_stock_input)

    def process_ask(self, stock_input):
        """Handles an ask.

        Logs output to a file or to standard output.

        :param str stock_input:
        """
        ask = self.build_order(stock_input, buildOrder.OrderOption.sell)
        self.ask_total[ask.order_id] = ask
        self.ask_total_shares += ask.stock_size

        if self.ask_total_shares >= self.stock_size:
            expense = self.process_stock_option(self.ask_total.values(), False)

            if self.spent_on_stock != expense:
                self.spent_on_stock = expense
                log_stock_input = str(ask.timestamp) + ' B ' + '{:0.2f}'.format(expense)
                self.write_to_file(log_stock_input)

    def process_stock_option(self, orders, action):
        """Process number of orders to determine the max money made for bids, or the min money spent for asks,
        factoring in max result.
        :param list orders: Order list, it could be self.bid_total.values() or self.ask_total.values().
        :param bool action: If this is `True`, cumulative result generated from greatest to least.
        Else, result from least to greatest.
        :returns: Money made or money spent."""

        sorted(orders, key=attrgetter('stock_price'), reverse=action)

        current_outstanding_shares = self.stock_size
        current_accumulated = 0

        for _, order in enumerate(orders):
            if current_outstanding_shares > order.stock_size:
                current_accumulated += order.stock_price * order.stock_size
                current_outstanding_shares -= order.stock_size
            else:
                current_accumulated += order.stock_price * current_outstanding_shares
                break

        return round(current_accumulated, 2)


    def record_order_reduce(self, stock_input):
        """Record reduction"""

        def _handle_reduce(stock_input):
            """Takes an input to reduce the order in the Book
            :param str reduce_order: input that define the reduce order ont he Book
            :returns: a tuple of (timestamp, reduce_id, share_size)"""


            row = stock_input.rstrip('\n').split(' ')
            timestamp = row[0]
            order_id = row[2]
            stock_size = int(row[3])

            return timestamp, order_id, stock_size


        def _calculate_ask(timestamp, order_id, stock_size):
            """Process and reduce asks accordingly"""

            if self.ask_total[order_id].stock_size <= stock_size:
                del self.ask_total[order_id]
            else:
                ask = self.ask_total[order_id]
                ask.stock_size -= stock_size
                self.ask_total[order_id] = ask
            self.ask_total_shares = max(self.ask_total_shares - stock_size, 0)

        def _calculate_bid(timestamp, order_id, stock_size):
            """Process and reduce bids accordingly"""

            if self.bid_total[order_id].stock_size <= stock_size:
                del self.bid_total[order_id]
            else:
                bid = self.bid_total[order_id]
                bid.stock_size -= stock_size
                self.bid_total[order_id] = bid
            self.bid_total_shares = max(self.bid_total_shares - stock_size, 0)

        def _spent_on_share_size(timestamp):
            """Update the minimum expense.

            :param str timestamp:
            """
            if self.ask_total_shares < self.stock_size and self.spent_on_stock != 'NA':
                self.spent_on_stock = 'NA'
                self.write_to_file(timestamp + ' B ' + self.spent_on_stock)
            elif self.ask_total_shares >= self.stock_size:
                expense = self.process_stock_option(self.ask_total.values(), False)
                if self.spent_on_stock != expense:
                    self.spent_on_stock = expense
                    log_stock_input = str(timestamp) + ' B ' + '{:0.2f}'.format(expense)
                    self.write_to_file(log_stock_input)


        def _share_size_gain(timestamp):
            """Update the maximum income.

            :param str timestamp:
            """
            if self.bid_total_shares < self.stock_size and self.made_from_stock != 'NA':
                self.made_from_stock = 'NA'
                self.write_to_file(timestamp + ' S ' + self.made_from_stock)
            elif self.bid_total_shares >= self.stock_size:
                income = self.process_stock_option(self.bid_total.values(), True)
                if self.made_from_stock != income:
                    self.made_from_stock = income
                    log_stock_input = str(timestamp) + ' S ' + '{:0.2f}'.format(income)
                    self.write_to_file(log_stock_input)


        timestamp, order_id, stock_size = _handle_reduce(stock_input)

        if order_id in self.bid_total:
            _calculate_bid(timestamp, order_id, stock_size)
            _share_size_gain(timestamp)
        elif order_id in self.ask_total:
            _calculate_ask(timestamp, order_id, stock_size)
            _spent_on_share_size(timestamp)
        else:
            raise ValueError('order_id is not present among current bids or asks.')

    

    
