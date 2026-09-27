from fastapi import HTTPException

from providers import (
    call_free_api,
    call_ip_api,
)
from rate_limit import reserve_request


async def resolve_ip(ip: str) -> dict:
    last_error = None

    for provider in ("ip_api", "free_api"):
        if not await reserve_request(provider):
            continue

        try:
            if provider == "ip_api":
                return await call_ip_api(ip)

            return await call_free_api(ip)

        except HTTPException as error:
            if error.status_code == 400:
                raise

            last_error = error

    if last_error:
        raise last_error

    raise HTTPException(
        status_code=429,
        detail="Both geolocation providers are rate limited",
    )