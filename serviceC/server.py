from fastapi import FastAPI
import connector


app = FastAPI(title="Service C")


@app.get("/")
async def health():
    return {
        "service": "Service C",
        "status": "ok"
    }


@app.get("/resolve-ip/{ip}")
async def resolve_ip(ip: str):
    return await connector.resolve_ip(ip)