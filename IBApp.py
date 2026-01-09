# EClient sends a request to IB,
from ibapi.client import EClient
# EWrapper receives a response from IB,
from ibapi.wrapper import EWrapper
# Contract tells IB what instrument we are trading
from ibapi.contract import Contract


class IBApp(EWrapper, EClient):
    # Initialize a client with a default connection of false.
    def __init__(self):
        EClient.__init__(self, self)
        self.connected = False
        self.historical_data = {} # important for storing requests

    # Error filtering
    def error(self, reqId, errorCode, errorString, *args):
        # Filter out irrelevant warnings about fractional shares
        if errorCode == 2176 and "fractional share" in errorString.lower():
            return  # Ignore this specific warning
        print(f"Error {errorCode}: {errorString}")
        if args:
            print(f"Additional error info: {args}")

    def nextValidId(self, orderId):
        self.connected = True
        print("Connected to IB")

    def historicalData(self, reqId, bar):
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        self.historical_data[reqId].append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })

    def historicalDataEnd(self, reqId, start, end):
        print(f"Historical data received for reqId {reqId}")
