# Trade Execution System

## Project Description

This is a prototype trade execution system that implements a trade approval process for financial instruments such as forward contracts. The system is designed to streamline and standardise the trade approval process, making it easier for users to submit trade details for approval and then follow a structured workflow until the trade is either executed or cancelled.

The system supports several core actions:
- **Submit:** Create a new trade request. The requester provides trade details.
- **Approve:** Approve a submitted trade. This action must be performed by an authorised approver.
- **Cancel:** Cancel a trade request. This action can be done by either the requester or the approver.
- **Update:** Update trade details which requires reapproval. Only the owner of the trade can update it.
- **SendToExecute:** Send the approved trade to the counterparty for execution. Only an authorised user can perform this.
- **Book:** Book the trade into the system once it has been executed by the counterparty. Can be done by the trade owner (requestor or admin)

Each trade includes detailed information such as the trading entity, counterparty, direction (Buy or Sell), style (e.g. Forward), currency, notional amount, and underlying eligible currencies. It also includes important dates (trade date, value date, and delivery date) with the rule that Trade Date ≤ Value Date ≤ Delivery Date. Once a trade is executed, a strike (agreed rate) is added.

The API is built using FastAPI and SQLAlchemy as the ORM. 

## How it Works

When a user submits a trade, the system first validates the trade details (including date ordering). It then transitions the trade to a PENDING_APPROVAL state. An authorised approver (admin) can then approve or cancel the trade.  
- **Update** actions moves the trade into a NEEDS_REAPPROVAL state, requiring reapproval from the authorised user.  
- Once approved, the trade can be sent for execution and then booked, transitioning through SENT_TO_COUNTERPARTY and finally EXECUTED state.  
Each action is recorded in a history log which can be queried to view the changes over time.

## How to Run Locally

### Prerequisites

- Python 3.9 or later
- Poetry

### Installation

1. Clone the repository:
   ```bash
   git clone 
   cd trade-execution-system
   ```

2. Install the dependencies using Poetry:
   ```bash
   poetry install
   ```

Running the Application
To run the application locally, simply execute:

   ```bash
   poetry run start
   ```
This command starts the FastAPI server using Uvicorn with live reloading enabled. The API will be available at http://localhost:8000. Swagger docs can be found at http://localhost:8000/docs.


### Run With Docker

   ```bash
   docker compose up --build 
   ```

### Run Tests

   ```bash
   poetry run pytest
   ```

  Or
   ```bash
   PYTHONPATH=$(pwd) poetry run pytest
   ```