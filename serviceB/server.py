from fastapi import FastAPI
#import uvicorn
from memory import IpMemory

app = FastAPI()


@app.get("/getAll")
async def GetData():
    print(f"START: Get Data. Length: {await IpMemory.aquireTheLock(IpMemory.lengthofData)}")
    #return IpMemory.getData()
    return await IpMemory.aquireTheLock(IpMemory.getData)


@app.post("/AddIp")
async def AddIp(request_data: dict):
    print("START: Add IP")
    ip = request_data.get("ipAddress")

    #myBool = IpMemory.doesIpExist(ip)
    myBool = await IpMemory.aquireTheLock(IpMemory.doesIpExist, ip)
    print(f"ip exists {myBool}")
    if myBool: return {"success": False, "message": "IP address already exists"}

    #newId = IpMemory.addIpAndGeoData(request_data)
    newId = await IpMemory.aquireTheLock(IpMemory.addIpAndGeoData, request_data)
    return {"success": True, "new_id": newId, "data_length":await IpMemory.aquireTheLock(IpMemory.lengthofData)}


@app.delete("/delete/{iid}")
async def delete(iid):
    print(f"START: delete {iid}")
    if not await IpMemory.aquireTheLock(IpMemory.doesKeyExist, iid):
        return {"success": False, "message": "IP address does not exists"}

    #IpMemory.deleteKeyValuePair(iid)
    await IpMemory.aquireTheLock(IpMemory.deleteKeyValuePair, iid)
    return {
        "success": True,
        "data_length": await IpMemory.aquireTheLock(IpMemory.lengthofData)
    }


#if __name__ == "__main__":
    #uvicorn.run("server:app", host="0.0.0.0", port=8082, workers=1)