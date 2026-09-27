# Project Coordinates

Backend project built with **FastAPI**, **Python**, **HTTPX**, and **Docker Compose**.

The system validates IP addresses, resolves their geolocation through two external providers, stores normalized results in memory, and can generate geographic clusters.

## Architecture

```text
Client
  |
  v
Service A
API / validation / orchestration
  |
  +-------------------+
  |                   |
  v                   v
Service C             Service B
Geolocation           Storage + clustering
  |
  +-------------------+
  |                   |
  v                   v
IP-API              FreeIPAPI
45 / minute         10 / 10 seconds
```

### Service A

Responsible for:
- Public API endpoints
- IP validation
- Calling Service C for geolocation
- Sending normalized data to Service B
- Propagating downstream HTTP errors

### Service B

Responsible for:
- In-memory storage
- Duplicate-IP detection
- Record deletion
- Geographic clustering
- Mean and median cluster coordinates

### Service C

Responsible for:
- Calling IP-API and FreeIPAPI
- Enforcing provider rate limits
- Reading and printing IP-API `X-Rl` and `X-Ttl`
- Provider fallback
- Normalizing both provider responses
- Provider HTTP and network error handling

## Project Structure

```text
coordinates/
├── compose.yaml
├── serviceA/
│   ├── Dockerfile
│   ├── connector.py
│   └── server.py
├── serviceB/
│   ├── Dockerfile
│   ├── clustering.py
│   ├── memory.py
│   └── server.py
└── serviceC/
    ├── Dockerfile
    ├── connector.py
    ├── providers.py
    ├── rate_limit.py
    └── server.py
```

# Geolocation Providers

## IP-API

Endpoint:

```text
http://ip-api.com/json/{ip}
```

Rate limit used by the project:

```text
45 requests per 60 seconds
```

Every IP-API response is checked for:

- `X-Rl` — requests remaining in the current window
- `X-Ttl` — seconds until the window resets

Both values are printed whenever IP-API is used.

When `X-Rl` is `0`, Service C blocks further IP-API requests for the number of seconds reported in `X-Ttl`.

## FreeIPAPI

Endpoint:

```text
https://free.freeipapi.com/api/v1/json/{ip}
```

Rate limit used by the project:

```text
10 requests per 10 seconds
```

Service C tracks recent FreeIPAPI calls locally. If FreeIPAPI itself returns `429`, the provider is temporarily blocked.

# Provider Selection and Fallback

For every lookup, Service C:

1. Checks whether IP-API can currently accept another request.
2. Uses IP-API when available.
3. If IP-API is blocked, rate limited, unavailable, or fails with a retryable error, Service C immediately tries FreeIPAPI.
4. If neither provider can currently accept the request, Service C returns HTTP `429`.

The code does not wait for a rate-limit window to reset when the other provider is available.

A `400` provider response is not retried against the second provider because the same invalid query would fail again and waste another request.

# Normalized Response

The two providers return different JSON structures. Service C converts both into the same format:

```json
{
  "ipAddress": "8.8.8.8",
  "latitude": 39.03,
  "longitude": -77.5,
  "countryName": "United States",
  "cityName": "Ashburn",
  "asn": 15169,
  "asnOrganization": "Google LLC",
  "isProxy": false
}
```

Service B only stores this normalized format and does not need to know which external provider supplied it.

# Error Handling

Service C explicitly handles:

| Status | Handling |
|---:|---|
| 400 | Bad request |
| 403 | Access forbidden |
| 429 | Rate limit reached |
| 500 | Provider internal error |
| 503 | Provider unavailable |

Other provider HTTP errors are returned as `502 Bad Gateway`.

Non-HTTP errors are also handled:

- Timeout → `504`
- Network/request failure → `503`
- Invalid JSON → `502`

When an error is retryable, Service C tries the other provider before failing the request.

# API Endpoints

## Service A — `localhost:8081`

### `GET /`

Returns all stored records.

```bash
curl http://localhost:8081/
```

### `GET /resolve-ip/{ip}`

Validates, resolves, and stores one IP address.

```bash
curl http://localhost:8081/resolve-ip/8.8.8.8
```

### `POST /resolve-ip-list`

Processes a JSON array of IP addresses.

```bash
curl -X POST http://localhost:8081/resolve-ip-list \
  -H "Content-Type: application/json" \
  -d '["8.8.8.8","1.1.1.1","9.9.9.9"]'
```

Each IP is processed independently. One failed item does not stop the rest.

The top-level `success` value is only `true` if every item succeeds.

### `DELETE /delete/{id}`

Deletes a stored record through Service B.

```bash
curl -X DELETE http://localhost:8081/delete/<record_id>
```

## Service B — `localhost:8082`

- `GET /getAll`
- `POST /AddIp`
- `DELETE /delete/{record_id}`
- `GET /generate-geo-clusters`

Example:

```bash
curl http://localhost:8082/generate-geo-clusters
```

## Service C — `localhost:8083`

### `GET /`

Health check.

### `GET /resolve-ip/{ip}`

Direct geolocation lookup through the provider-selection logic.

```bash
curl http://localhost:8083/resolve-ip/8.8.8.8
```

# Geographic Clustering

Service B uses the Haversine formula to calculate distance between coordinates.

Default cluster distance:

```text
50 km
```

Each cluster contains:

- `median_coordinates`
- `mean_coordinates`
- the stored records assigned to the cluster

Coordinates use:

```text
[longitude, latitude]
```

# Storage

Service B stores data in memory.

Duplicate IP addresses are not added.

Because storage is in memory, stored records are lost when Service B restarts.

# Running the Project

## Start

```bash
docker compose up --build
```

## Stop

```bash
docker compose down
```

## Check containers

```bash
docker compose ps
```

## Watch Service C logs

```bash
docker compose logs -f service-c-container
```

Example rate-limit output:

```text
IP-API X-Rl=44, X-Ttl=60
```

# Demo Tests

## Valid IP

```bash
curl http://localhost:8081/resolve-ip/8.8.8.8
```

## Invalid IP

```bash
curl -i http://localhost:8081/resolve-ip/not-an-ip
```

Expected: HTTP `400`.

## List endpoint

```bash
curl -X POST http://localhost:8081/resolve-ip-list \
  -H "Content-Type: application/json" \
  -d '["8.8.8.8","1.1.1.1"]'
```

## Provider fallback

Service C's logs can be used to demonstrate fallback:

- IP-API requests print `X-Rl` and `X-Ttl`.
- When IP-API can no longer be used, successful lookups continue through FreeIPAPI.

Do not intentionally keep exceeding the real provider limits.

# Docker Ports

| Service | Container | Host |
|---|---:|---:|
| Service A | 8080 | 8081 |
| Service B | 8080 | 8082 |
| Service C | 8080 | 8083 |

# Swagger

- Service A: `http://localhost:8081/docs`
- Service B: `http://localhost:8082/docs`
- Service C: `http://localhost:8083/docs`

# Design Responsibilities

```text
serviceA/server.py
  API endpoints and orchestration

serviceA/connector.py
  IP validation and service-to-service HTTP calls

serviceB/memory.py
  in-memory storage

serviceB/clustering.py
  geographic calculations

serviceC/connector.py
  provider selection and fallback

serviceC/providers.py
  provider calls, normalization, and provider error handling

serviceC/rate_limit.py
  rate-limit tracking and provider blocking
```

The design keeps provider-specific behavior inside Service C and avoids coupling Service A or Service B to either external API.
