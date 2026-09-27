import httpx
from fastapi import HTTPException

from rate_limit import block_provider


IP_API_URL = "http://ip-api.com/json"
FREE_API_URL = "https://free.freeipapi.com/api/v1/json"

IP_API_FIELDS = (
    "status,message,query,country,"
    "city,lat,lon,as,proxy"
)

HTTP_ERRORS = {
    400: "bad request",
    403: "access forbidden",
    429: "rate limit reached",
    500: "internal server error",
    503: "service unavailable",
}


async def call_ip_api(ip: str) -> dict:
    response = await send_request(
        f"{IP_API_URL}/{ip}",
        "IP-API",
        {"fields": IP_API_FIELDS},
    )

    remaining = response.headers.get("X-Rl")
    ttl_header = response.headers.get("X-Ttl")

    print(
        f"IP-API X-Rl={remaining}, "
        f"X-Ttl={ttl_header}"
    )

    if (
        remaining == "0"
        or response.status_code == 429
    ):
        await block_provider(
            "ip_api",
            to_float(ttl_header, 60),
        )

    check_status(response, "IP-API")

    data = get_json(
        response,
        "IP-API",
    )

    if data.get("status") != "success":
        raise HTTPException(
            400,
            data.get(
                "message",
                "IP-API lookup failed",
            ),
        )

    asn, organization = parse_as(
        data.get("as")
    )

    return {
        "ipAddress": data.get("query", ip),
        "latitude": data.get("lat"),
        "longitude": data.get("lon"),
        "countryName": data.get("country"),
        "cityName": data.get("city"),
        "asn": asn,
        "asnOrganization": organization,
        "isProxy": data.get("proxy"),
    }


async def call_free_api(ip: str) -> dict:
    response = await send_request(
        f"{FREE_API_URL}/{ip}",
        "Free IP API",
    )

    if response.status_code == 429:
        await block_provider(
            "free_api",
            10,
        )

    check_status(
        response,
        "Free IP API",
    )

    data = get_json(
        response,
        "Free IP API",
    )

    asn, _ = parse_as(
        data.get("asn")
    )

    return {
        "ipAddress": data.get(
            "ipAddress",
            ip,
        ),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "countryName": data.get("countryName"),
        "cityName": data.get("cityName"),
        "asn": asn,
        "asnOrganization": data.get(
            "asnOrganization"
        ),
        "isProxy": data.get("isProxy"),
    }


async def send_request(
    url: str,
    provider: str,
    params=None,
) -> httpx.Response:
    try:
        async with httpx.AsyncClient() as client:
            return await client.get(
                url,
                params=params,
                timeout=5,
            )

    except httpx.TimeoutException as error:
        raise HTTPException(
            504,
            f"{provider} timed out",
        ) from error

    except httpx.RequestError as error:
        raise HTTPException(
            503,
            f"{provider} unavailable",
        ) from error


def check_status(
    response: httpx.Response,
    provider: str,
) -> None:
    status = response.status_code

    if status < 400:
        return

    if status in HTTP_ERRORS:
        raise HTTPException(
            status,
            f"{provider}: {HTTP_ERRORS[status]}",
        )

    raise HTTPException(
        502,
        f"{provider} returned HTTP {status}",
    )


def get_json(
    response: httpx.Response,
    provider: str,
) -> dict:
    try:
        data = response.json()

    except ValueError as error:
        raise HTTPException(
            502,
            f"{provider} returned invalid JSON",
        ) from error

    if not isinstance(data, dict):
        raise HTTPException(
            502,
            f"{provider} returned unexpected JSON",
        )

    return data


def parse_as(
    value,
) -> tuple[int | None, str | None]:
    parts = str(
        value or ""
    ).split(" ", 1)

    number = parts[0]

    if number.upper().startswith("AS"):
        number = number[2:]

    try:
        asn = int(number)

    except ValueError:
        asn = None

    organization = (
        parts[1]
        if len(parts) > 1
        else None
    )

    return asn, organization


def to_float(
    value,
    default: float,
) -> float:
    try:
        return float(value)

    except (TypeError, ValueError):
        return default