import unittest
import time
from datetime import datetime
from final import OrderRequest, OrderResponse, OrderManagement, RequestType, ResponseType
import sqlite3

class TestOrderManagement(unittest.TestCase):

    def setUp(self):
        # Setup a test OrderManagement instance with a valid 1-minute time window starting now
        now = datetime.now()
        self.start = (now.hour, now.minute)
        self.end = (now.hour, now.minute + 1)
        self.oms = OrderManagement(self.start, self.end, throttle_limit=1)

    # Function to Print All the Order Responses in Database After Each Test.
    def print_db_contents(self):
        print("\n📦 Order Responses in DB:")
        try:
            conn = sqlite3.connect("oms.db")
            cur = conn.cursor()

            # Checking if order_responses table exists in the db...
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_responses'")
            if not cur.fetchone():
                print("⚠️  Table 'order_responses' does not exist yet.")
                conn.close()
                return
            cur.execute("SELECT * FROM order_responses")
            rows = cur.fetchall()
            for row in rows:
                print(row)  
            conn.close()
        except Exception as e:
            print("Error reading DB:", e)

    # I'm Sending a Valid Order Within the time Window which is Accepted and Stored.
    def test_order_acceptance(self):
        req = OrderRequest(1, 100.0, 10, 'B', 111)
        self.oms.onData(req, RequestType.New)
        time.sleep(1.5) 
        resp = OrderResponse(111, ResponseType.Accept)
        self.oms.onDataResponse(resp)
        self.assertEqual(len(self.oms.responses), 1)
        self.assertEqual(self.oms.responses[0][1], ResponseType.Accept)
        self.print_db_contents()

    # I'm Artificially setting time window to a period that is definitely not now to Fail the Request.
    def test_order_rejection_outside_window(self):
        self.oms.start_time = (0, 0)
        self.oms.end_time = (0, 1)
        req = OrderRequest(1, 100.0, 10, 'B', 112)
        self.oms.onData(req, RequestType.New)

        self.assertEqual(ResponseType(self.oms.responses[-1][1]), ResponseType.Reject)
        self.print_db_contents()
        
    # I'm Sending A New Order and Immediately modifying it Before the response is Received Then 
    # send an Accept response for the modified order and validate everything
    def test_order_modify_updates_order_in_queue(self):
        req = OrderRequest(1, 100.0, 10, 'B', 201)
        self.oms.onData(req, RequestType.New)
        self.print_db_contents()
        modified_req = OrderRequest(1, 105.0, 20, 'B', 201)
        self.oms.onData(modified_req, RequestType.Modify)
        time.sleep(1.5) 
        resp = OrderResponse(201, ResponseType.Accept)
        self.oms.onDataResponse(resp)
        self.assertEqual(len(self.oms.responses), 1)
        self.assertEqual(self.oms.responses[0][0], 201)
        self.assertEqual(self.oms.responses[0][1], ResponseType.Accept)
        self.print_db_contents()

    # I'm Cancelling an Order Before it's Processes prevents it from being sent.
    def test_order_cancel_removes_order_from_queue(self):
        req = OrderRequest(1, 100.0, 10, 'B', 202)
        self.oms.onData(req, RequestType.New)
        cancel_req = OrderRequest(1, 0.0, 0, 'B', 202)
        self.oms.onData(cancel_req, RequestType.Cancel)
        time.sleep(1.5)
        order_ids = [resp[0] for resp in self.oms.responses]
        self.assertNotIn(202, order_ids)
        self.print_db_contents()

    def tearDown(self):
        self.oms.running = False
        self.oms.sender_thread.join()
        self.oms.check_logon_logout_thread.join()

if __name__ == '__main__':
    unittest.main()
