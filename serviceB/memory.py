import asyncio
from uuid import uuid4


class IpMemory:
    def __init__(self):
        self._data = {}
        self._used_ips = set()
        self._lock = asyncio.Lock()

    async def get_all(self):
        async with self._lock:
            return dict(self._data)

    async def add(self, record: dict):
        async with self._lock:
            ip = record["ipAddress"]

            if ip in self._used_ips:
                return None

            record_id = str(uuid4())[:8]

            self._data[record_id] = record
            self._used_ips.add(ip)

            return record_id

    async def delete(self, record_id: str):
        async with self._lock:
            record = self._data.pop(record_id, None)

            if record is None:
                return False

            self._used_ips.discard(record["ipAddress"])
            return True

    async def count(self):
        async with self._lock:
            return len(self._data)