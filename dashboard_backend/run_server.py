import os
import uvicorn

if __name__ == "__main__":
    # PUBLIC_INTERFACE
    # Entrypoint for launching FastAPI app on the expected port.
    port = int(os.environ.get("PORT", 3001))
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=bool(os.environ.get("DEV", "0") == "1")
    )
