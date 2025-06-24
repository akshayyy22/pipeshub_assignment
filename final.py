import time
import threading
from datetime import datetime
from collections import deque
import sqlite3
from enum import Enum

class Logon:
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Logout:
    def __init__(self, username):
        self.username = username

class OrderRequest:
    def __init__(self, symbol_id, price, qty, side, order_id):
        self.m_symbolId = symbol_id
        self.m_price = price
        self.m_qty = qty
        self.m_side = side
        self.m_orderId = order_id

class RequestType(Enum):
    Unknown = 0
    New = 1
    Modify = 2
    Cancel = 3

class ResponseType(Enum):  # I have changed to Enum because I was getting an error
    Unknown = 0
    Accept = 1
    Reject = 2

class OrderResponse:
    def __init__(self, order_id, response_type):
        self.m_orderId = order_id
        self.m_responseType = response_type

# I used DB here. We can also do it without DB (Alternate methods are: 1. Log to a CSV file or maybe 2. Plain text log file)
# But I think there will be trade-offs like harder to query/filter, no proper structure
def setup_db():
    conn = sqlite3.connect("oms.db")
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS order_responses (
            order_id INTEGER PRIMARY KEY,
            response_type TEXT,
            latency REAL,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_response_to_db(order_id, response_type, latency):
    conn = sqlite3.connect("oms.db")
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO order_responses (order_id, response_type, latency, timestamp)
        VALUES (?, ?, ?, datetime('now'))
    ''', (order_id, ResponseType(response_type).name, latency))
    conn.commit()
    conn.close()

# Order management
class OrderManagement:
    def __init__(self, start_time, end_time, throttle_limit):
        setup_db()
        self.start_time = start_time 
        self.end_time = end_time     
        self.throttle_limit = throttle_limit
        self.order_queue = deque()
        self.queue_lock = threading.Lock()
        self.order_map = {}  
        self.responses = []
        self.running = True
        self.last_second = int(time.time())
        self.orders_this_second = 0
        self.sender_thread = threading.Thread(target=self.process_queue)
        self.sender_thread.daemon = True
        self.sender_thread.start()
        self.check_logon_logout_thread = threading.Thread(target=self.check_logon_logout)
        self.check_logon_logout_thread.daemon = True
        self.check_logon_logout_thread.start()

    # So basically in the below, it checks and sends the orders only if exchange is between configured start and end times (hardcoded in the main function)
    def is_within_time_window(self):
        now = datetime.now()
        today = now.date()
        start_dt = datetime(today.year, today.month, today.day, *self.start_time)
        end_dt = datetime(today.year, today.month, today.day, *self.end_time)
        return start_dt <= now <= end_dt

    # It will call sendLogon() at the beginning of the time window and Logout at the end of the time window.
    def check_logon_logout(self):
        has_logged_on = False
        while self.running:
            now_within = self.is_within_time_window()
            if now_within and not has_logged_on:
                self.sendLogon()
                has_logged_on = True
            elif not now_within and has_logged_on:
                self.sendLogout()
                has_logged_on = False
            time.sleep(1)

    # So basically this function is used to make sure it takes only 2 orders per second (throttle mentioned in the main function hardcoded) and sends the remaining to the queue.
    def process_queue(self):
        while self.running:
            now = int(time.time())
            if now != self.last_second:
                with self.queue_lock:
                    self.orders_this_second = 0
                    while self.order_queue and self.orders_this_second < self.throttle_limit:
                        order = self.order_queue.popleft()
                        self.send(order)
                        self.order_map[order.m_orderId] = time.time()
                        self.orders_this_second += 1
            self.last_second = now
            time.sleep(0.01)

    def onData(self, request, req_type=RequestType.New):
        # Checks the condition we created previously about the time window
        if not self.is_within_time_window():
            # Originally I was just returning the rejected order (just printed) that came outside the allowed time window.
            # Now, rejected orders are also logged to the SQLite database, just like accepted/rejected orders from the exchange.
            # This makes auditing and debugging more complete and traceable.
            print(f"Order {request.m_orderId} rejected due to time window.")
            latency = 0.0  # No actual send time
            insert_response_to_db(request.m_orderId, ResponseType.Reject.value, latency)
            self.responses.append((request.m_orderId, ResponseType.Reject.value, latency))
            return

        with self.queue_lock:
            if req_type == RequestType.New:
                self.order_queue.append(request)

            elif req_type == RequestType.Modify:
                new_queue = deque()
                for o in self.order_queue:
                    if o.m_orderId == request.m_orderId:
                        o.m_price = request.m_price
                        o.m_qty = request.m_qty
                    new_queue.append(o)
                self.order_queue = new_queue

            elif req_type == RequestType.Cancel:
                self.order_queue = deque(
                    o for o in self.order_queue if o.m_orderId != request.m_orderId
                )

    def onDataResponse(self, response):
        order_id = response.m_orderId
        if order_id in self.order_map:
            latency = time.time() - self.order_map[order_id]
            self.responses.append((order_id, response.m_responseType, latency))
            insert_response_to_db(order_id, response.m_responseType, latency)
            del self.order_map[order_id]

    def send(self, request):
        print(f"Sent Order {request.m_orderId} to exchange at {datetime.now()}")

    def sendLogon(self):
        print(f"Logon sent at {datetime.now()}")

    def sendLogout(self):
        print(f"Logout sent at {datetime.now()}")

# MAIN FUNCTION
from datetime import datetime
import time

if __name__ == "__main__":
    # For testing purposes, I was using the current time
    # now = datetime.now()
    # start = (now.hour, now.minute)
    # end = (now.hour, now.minute + 1)

    # I hardcoded the time window between 10 AM to 1 PM IST (as it was mentioned in the assignment)
    start = (10, 0)
    end = (13, 0)

    # Throttle limit is set to 2 (making an assumption)
    oms = OrderManagement(start, end, throttle_limit=2)

    req1 = OrderRequest(1, 100.0, 10, 'B', 101)
    req2 = OrderRequest(1, 101.0, 5, 'S', 102)
    req3 = OrderRequest(1, 99.5, 7, 'B', 103)
    oms.onData(req1, RequestType.New)
    oms.onData(req2, RequestType.New)
    oms.onData(req3, RequestType.New)
    time.sleep(2)
    resp1 = OrderResponse(101, ResponseType.Accept)
    resp2 = OrderResponse(102, ResponseType.Reject)
    resp3 = OrderResponse(103, ResponseType.Accept)
    oms.onDataResponse(resp1)
    oms.onDataResponse(resp2)
    oms.onDataResponse(resp3)
    print("Responses:", oms.responses)

    oms.running = False

    # Without join(), my script may exit before threads finish execution. So by adding it, we ensure threads complete before exiting—safe and clean shutdown.
    oms.sender_thread.join()
    oms.check_logon_logout_thread.join()
