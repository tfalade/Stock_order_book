import Book
import Stock_order
import os
import sys
import config


class StockPrice(object):
    """Buidling an object that binds all the input and processing of the stock order together"""

    def __init__(self, stock_input_file, stock_size, output_to_file=None):
        """
        :param str stock_input_file:
        :param str output_to_file:
        :param int stock_size:
        """
        self.stock_input_file = stock_input_file
        self.my_book = Book.ProcessOrder(stock_size, output_to_file)

    def run_book(self):
        """
        Calculate money to be spent buying stock or gained selling stock
        Print out the values to standard output
        """
       
        with open(self.stock_input_file, 'r') as handler:

            #Read from a file and update my_book:
            for stock_input in handler:
                self.my_book.process_all(stock_input)


# Read from a file.
FILE_TO_PROCESS = os.path.abspath(os.path.abspath(config.ROOT_DIR) + '/Test_data/pricer_test.in')

if __name__ == '__main__':
    my_stock_size = int(sys.argv[1])

    if my_stock_size < 1:
        raise ValueError('Input stock size has to be greater than zero')

    StockPrice(FILE_TO_PROCESS, my_stock_size).run_book()


