from fastapi import FastAPI
import connector
#import uvicorn

app = FastAPI()
BaseUrl = "http://svc-b-cont:8080"


@app.get("/")
async def GetData():
    print(f"START: Get Data")
    return await connector.MakeRequest(
        BaseUrl + "/getAll", 2, "ServiceB-GetAll"
    )

@app.get("/favicon.ico")
def favicon():
    print(f"START: favicon")
    return "ok"


@app.get("/resolve-ip/{ip}")
async def AddIp(ip: str):
    print(f"START: Add IP {ip}")
    ip = connector.ValidateIp(ip)

    ResponseDict = await connector.MakeRequest(
        f"https://free.freeipapi.com/api/v1/json/{ip}", 4, "FreeIpAPI"
    )
    print(f"free api worked: {connector.FreeIpApiKeyPicker(ResponseDict)}")
    return await connector.MakeRequest(
        BaseUrl + "/AddIp", 8, "ServiceB-AddIp", meth='POST',
        JsonData=connector.FreeIpApiKeyPicker(ResponseDict)
    )


@app.get("/delete/{iid}")
async def delete(iid):
    print(f"START: delete {iid}")
    return await connector.MakeRequest(
        BaseUrl + f"/delete/{iid}", 2, "ServiceB-Delete", meth='DELETE'
    )

#if __name__ == "__main__":
    #uvicorn.run("server:app", host="0.0.0.0", port=8081, workers=1)