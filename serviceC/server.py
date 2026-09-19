from fastapi import FastAPI
import connector

app = FastAPI()


@app.get("/")
async def GetData():
    return {"service": "ServiceC", "status": "ok"}


@app.get("/resolve-ip/{ip}")
async def ResolveIp(ip: str):
    print(f"START: ServiceC resolve IP {ip}")
    return await connector.GetIpData(ip)


@app.get("/favicon.ico")
def favicon():
    return "ok"