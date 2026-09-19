import httpx
from fastapi import HTTPException


API_URL = "https://free.freeipapi.com/api/v1/json"


def select_geo_fields(data: dict) -> dict:
    fields = {
        "ipAddress",
        "latitude",
        "longitude",
        "countryName",
        "cityName",
        "asn",
        "asnOrganization",
        "isProxy"
    }

    return {
        key: value
        for key, value in data.items()
        if key in fields
    }


async def resolve_ip(ip: str) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/{ip}",
                timeout=5
            )
    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=504,
            detail="Free IP API timed out"
        ) from error
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail="Free IP API unavailable"
        ) from error

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Free IP API returned {response.status_code}"
        )

    return select_geo_fields(response.json())