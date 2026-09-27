from fastapi import FastAPI
import connector


app = FastAPI(title="Service A")


@app.get("/")
async def get_data():
    return await connector.request(
        f"{connector.SERVICE_B_URL}/getAll",
        "ServiceB",
        timeout=2
    )


@app.get("/resolve-ip/{ip}")
async def resolve_ip(ip: str):
    valid_ip = connector.validate_ip(ip)
    geo_data = await connector.resolve_ip(valid_ip)

    return await connector.add_ip(geo_data)


@app.post("/resolve-ip-list")
async def resolve_ip_list(ip_list: list[str]):
    results = []

    for raw_ip in ip_list:
        try:
            valid_ip = connector.validate_ip(raw_ip)
            geo_data = await connector.resolve_ip(valid_ip)
            stored = await connector.add_ip(geo_data)

            results.append({
                "ip": valid_ip,
                "success": stored.get("success", True),
                "result": stored
            })

        except Exception as error:
            results.append({
                "ip": raw_ip,
                "success": False,
                "error": str(error)
            })

    return {
        "success": all(
            result["success"]
            for result in results
        ),
        "results": results
    }


@app.delete("/delete/{iid}")
async def delete(iid: str):
    return await connector.request(
        f"{connector.SERVICE_B_URL}/delete/{iid}",
        "ServiceB",
        method="DELETE",
        timeout=2
    )