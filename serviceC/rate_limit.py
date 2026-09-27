import asyncio
import time


LIMITS = {
    "ip_api": (45, 60),
    "free_api": (10, 10),
}

request_times = {
    "ip_api": [],
    "free_api": [],
}

blocked_until = {
    "ip_api": 0.0,
    "free_api": 0.0,
}

rate_lock = asyncio.Lock()


async def reserve_request(provider: str) -> bool:
    max_requests, window = LIMITS[provider]

    async with rate_lock:
        now = time.monotonic()

        request_times[provider] = [
            sent_at
            for sent_at in request_times[provider]
            if now - sent_at < window
        ]

        if now < blocked_until[provider]:
            return False

        if len(request_times[provider]) >= max_requests:
            return False

        request_times[provider].append(now)
        return True


async def block_provider(
    provider: str,
    seconds: float,
) -> None:
    async with rate_lock:
        blocked_until[provider] = max(
            blocked_until[provider],
            time.monotonic() + seconds,
        )