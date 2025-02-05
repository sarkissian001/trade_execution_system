import uvicorn


def main():
    # TODO: Create a settings file to store those and pass by .env
    uvicorn.run(
        "trading_execution_system.main:app", host="0.0.0.0", port=8000, reload=True
    )


if __name__ == "__main__":
    main()
