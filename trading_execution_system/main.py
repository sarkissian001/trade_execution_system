from fastapi import FastAPI
from trading_execution_system.api.v1.routes import trades, users

app = FastAPI(title="Trade Approval Process API")

app.include_router(trades.router, prefix="/api/v1/trades", tags=["trades"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
