# Pipeshub Assignment: Order Management System (OMS)

This project is an Order Management System (OMS) developed as part of the PipeShub SDE Internship assignment. It simulates order processing, throttling, and logging within a specified time window. The system uses a SQLite database for persistent storage of order responses.

## Table of Contents

- [Documentation](https://github.com/akshayyy22/pipeshub_assignment/blob/main/#documentation)
- [How to Run](https://github.com/akshayyy22/pipeshub_assignment/blob/main/#how-to-run)
- [Project Details](https://github.com/akshayyy22/pipeshub_assignment/blob/main/#project-details)
- [Classes and Functions](https://github.com/akshayyy22/pipeshub_assignment/blob/main/#classes-and-functions)
- [Database Schema](https://github.com/akshayyy22/pipeshub_assignment/blob/main/#database-schema)
- [Testing](https://github.com/akshayyy22/pipeshub_assignment/blob/main/#testing)

## Documentation

Detailed documentation is available within the code as comments. Key functionalities and design choices are explained inline.

## How to Run

1.  **Run the main application:**

    ```bash
    python final.py
    ```

2.  **Interact with the SQLite database:**

    ```bash
    sqlite3 oms.db
    ```

3.  **Query the `order_responses` table:**

    ```sql
    SELECT * FROM order_responses;
    ```

## Project Details

The OMS simulates processing order requests within a defined time window, applying a throttle to limit the number of orders sent per second, and logging order responses to a SQLite database. It includes features for order queuing, modification, and cancellation.


## Classes and Functions

*   **`Logon`**: Represents a logon request.
*   **`Logout`**: Represents a logout request.
*   **`OrderRequest`**: Represents an order request with symbol ID, price, quantity, side, and order ID.
*   **`RequestType`**: An Enum representing the type of request (New, Modify, Cancel).
*   **`ResponseType`**: An Enum representing the type of response (Accept, Reject).
*   **`OrderResponse`**: Represents an order response with order ID and response type.
*   **`setup_db()`**: Creates the `order_responses` table in the SQLite database if it doesn't exist.
*   **`insert_response_to_db()`**: Inserts an order response into the `order_responses` table.
*   **`OrderManagement`**: Manages order processing, throttling, and logging.
    *   `__init__(self, start_time, end_time, throttle_limit)`: Initializes the OrderManagement class by setting up the database and initializing the order queue, thread locks, order maps, and other variables. It also starts the sender and logon/logout threads.
    *   `is_within_time_window(self)`: Checks if the current time is within the configured start and end times.
    *   `check_logon_logout(self)`: Sends logon and logout messages based on the current time and the configured time window.
    *   `process_queue(self)`: Processes the order queue, sending orders to the exchange based on the throttle limit.
    *   `onData(self, request, req_type=RequestType.New)`: Adds a new order to the queue, modifies an existing order, or cancels an order based on the request type.
    *   `onDataResponse(self, response)`: Handles order responses, logs the latency, and updates the order map.
    *   `send(self, request)`: Simulates sending an order to the exchange.
    *   `sendLogon(self)`: Simulates sending a logon message.
    *   `sendLogout(self)`: Simulates sending a logout message.

## Database Schema

The SQLite database `oms.db` contains one table:

*   **`order_responses`**:
    *   `order_id` (INTEGER PRIMARY KEY): The order ID.
    *   `response_type` (TEXT): The response type (Accept or Reject).
    *   `latency` (REAL): The latency of the response.
    *   `timestamp` (TEXT): The timestamp of the response.

## Testing

The `test_final.py` file contains unit tests for the Order Management System. These tests verify order acceptance, rejection (outside the time window), modification, and cancellation. To run the tests:

```bash
python test_final.py


