The examples in this directory are based on code from the book
"Writing Testbenches", 1st edition, by Janick Bergeron.

Files rs232_rx.py and rs232_tx.py contain my translations into
myhdl/Python of Sample 5-48 and 5-57 in the book. The copyright of the
original Samples is held by Janick Bergeron.

I added a test bench, test_rs232.py, to verify the translation into
myhdl/Python, and to demonstrate some possibilities of myhdl and the
Python unit test framework. Run the test bench as follows:

    python test_rs232.py
