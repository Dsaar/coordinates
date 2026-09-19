import httpx
from fastapi import HTTPException


def FreeIpApiKeyPicker(js):
    result = {}

    our_keys = {
        "ipAddress",
        "latitude",
        "longitude",
        "countryName",
        "cityName",
        "asn",
        "asnOrganization",
        "isProxy"
    }

    for key, value in js.items():
        if key in our_keys:
            result[key] = value

    return result


async def GetIpData(ip):
    url = f"https://free.freeipapi.com/api/v1/json/{ip}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=4)
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="FreeIpAPI timed out"
            )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"FreeIpAPI failed: {response.status_code}"
        )

    return FreeIpApiKeyPicker(response.json())