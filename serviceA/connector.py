import os
import httpx
from fastapi import HTTPException
from pydantic import BaseModel, IPvAnyAddress


SERVICE_B_URL = os.getenv(
    "SERVICE_B_URL",
    "http://svc-b-cont:8080"
)

SERVICE_C_URL = os.getenv(
    "SERVICE_C_URL",
    "http://svc-c-cont:8080"
)


class ValidIp(BaseModel):
    ip: IPvAnyAddress


def validate_ip(ip: str) -> str:
    try:
        return str(ValidIp(ip=ip).ip)
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid IP address: {ip}"
        ) from error


async def request(
    url: str,
    service_name: str,
    method: str = "GET",
    json_data=None,
    timeout: float = 5
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method,
                url,
                json=json_data,
                timeout=timeout
            )
        except httpx.TimeoutException as error:
            raise HTTPException(
                status_code=504,
                detail=f"{service_name} timed out"
            ) from error
        except httpx.HTTPError as error:
            raise HTTPException(
                status_code=502,
                detail=f"{service_name} unavailable"
            ) from error

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"{service_name} returned {response.status_code}"
        )

    return response.json()


async def resolve_ip(ip: str):
    return await request(
        f"{SERVICE_C_URL}/resolve-ip/{ip}",
        "ServiceC",
        timeout=5
    )


async def add_ip(geo_data: dict):
    return await request(
        f"{SERVICE_B_URL}/AddIp",
        "ServiceB",
        method="POST",
        json_data=geo_data,
        timeout=5
    )