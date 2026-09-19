from uuid import uuid4
import asyncio

class IpMemory:
    data = {} # {euwewuy: geoData1, eriuwyv: geoData2}
    UsedIps = set() # {10.10.0.4, 1.1.2.2, 30.40.50.60}
    memLock = asyncio.Lock()

    @classmethod
    async def aquireTheLock(cls, func, *args):
        async with cls.memLock:
            value = await func(*args)
        return value

    @classmethod
    async def getData(cls):
        return cls.data

    @classmethod
    async def lengthofData(cls):
        return len(cls.data)
    
    @classmethod
    async def doesKeyExist(cls, key):
        return key in cls.data

    @classmethod
    async def doesIpExist(cls, ip):
        """checks if ip exists in memory and returns boolean"""
        return ip in cls.UsedIps

    @classmethod
    async def addIpAndGeoData(cls, requestData):
        newId = str(uuid4())[:8]
        cls.data[newId] = requestData
        cls.UsedIps.add(requestData["ipAddress"])
        return newId
    
    @classmethod
    async def deleteKeyValuePair(cls, key):
        del cls.data[key]