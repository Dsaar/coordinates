from fastapi import FastAPI
from pydantic import BaseModel
from memory import IpMemory
from clustering import generate_clusters


app = FastAPI(title="Service B")
memory = IpMemory()


class GeoRecord(BaseModel):
    ipAddress: str
    latitude: float
    longitude: float
    countryName: str | None = None
    cityName: str | None = None
    asn: int | None = None
    asnOrganization: str | None = None
    isProxy: bool | None = None


@app.get("/getAll")
async def get_all():
    return await memory.get_all()


@app.post("/AddIp")
async def add_ip(record: GeoRecord):
    record_id = await memory.add(
        record.model_dump()
    )

    if record_id is None:
        return {
            "success": False,
            "message": "IP address already exists"
        }

    return {
        "success": True,
        "new_id": record_id,
        "data_length": await memory.count()
    }


@app.delete("/delete/{record_id}")
async def delete(record_id: str):
    deleted = await memory.delete(record_id)

    if not deleted:
        return {
            "success": False,
            "message": "IP address does not exist"
        }

    return {
        "success": True,
        "data_length": await memory.count()
    }


@app.get("/generate-geo-clusters")
async def generate_geo_clusters():
    records = await memory.get_all()
    return generate_clusters(records)