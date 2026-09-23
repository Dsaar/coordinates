# Project Coordinates

A distributed IP geolocation and geographic clustering system built with **FastAPI**, **Python**, **HTTPX**, and **Docker Compose**.

The project is split into three services:

- **Service A** — public API and orchestration
- **Service B** — in-memory storage and geographic clustering
- **Service C** — external IP geolocation API integration

## Architecture

```text
                         Client
                           |
                           v
                  +-------------------+
                  |     Service A     |
                  | API / Orchestrator|
                  +---------+---------+
                            |
                 +----------+----------+
                 |                     |
                 v                     v
        +----------------+    +----------------+
        |   Service C    |    |   Service B    |
        | IP Geolocation |    | Storage + Geo  |
        |    Adapter     |    |   Clustering   |
        +-------+--------+    +-------+--------+
                |                     |
                v                     v
       Free IP API             In-memory data
```

Service A coordinates the workflow. Service C resolves IP addresses through the external Free IP API. Service B stores the resolved records and generates geographic clusters.

## Project Structure

```text
coordinates/
│
├── compose.yaml
│
├── serviceA/
│   ├── Dockerfile
│   ├── connector.py
│   └── server.py
│
├── serviceB/
│   ├── Dockerfile
│   ├── clustering.py
│   ├── memory.py
│   └── server.py
│
└── serviceC/
    ├── Dockerfile
    ├── connector.py
    └── server.py
```

### Service A

Responsible for:

- Client-facing API endpoints
- IP validation
- Request orchestration
- Communication with Services B and C
- Downstream error handling

### Service B

Responsible for:

- In-memory IP storage
- Duplicate IP detection
- Record deletion
- Geographic clustering
- Mean and median cluster coordinates

### Service C

Responsible for:

- Calling the external Free IP API
- Filtering the external response
- Handling external API errors and timeouts

# API Endpoints

## Service A

Service A is exposed on port `8081`.

### `GET /`

Returns all records stored by Service B.

```http
GET http://localhost:8081/
```

### `GET /resolve-ip/{ip}`

Validates, resolves, and stores a single IP address.

```http
GET http://localhost:8081/resolve-ip/8.8.8.8
```

Workflow:

1. Service A validates the IP.
2. Service A requests geographic information from Service C.
3. Service C calls the Free IP API.
4. Service A sends the result to Service B.
5. Service B stores the record.

### `POST /resolve-ip-list`

Validates, resolves, and stores multiple IP addresses.

```http
POST http://localhost:8081/resolve-ip-list
Content-Type: application/json
```

Request:

```json
[
  "8.8.8.8",
  "1.1.1.1",
  "208.67.222.222"
]
```

Each IP is processed individually. A failure for one IP does not stop the remaining IPs from being processed.

`/resolve-ip-list` belongs to Service A because it is an orchestration workflow. Service C only resolves IP addresses, while Service B only stores and processes the resulting data.

### `DELETE /delete/{id}`

Deletes a stored record through Service B.

```http
DELETE http://localhost:8081/delete/a1234567
```

## Service B

Service B is exposed on port `8082`.

### `GET /getAll`

Returns all records currently stored in memory.

```http
GET http://localhost:8082/getAll
```

### `POST /AddIp`

Adds a resolved geographic IP record.

```http
POST http://localhost:8082/AddIp
Content-Type: application/json
```

Example body:

```json
{
  "ipAddress": "8.8.8.8",
  "latitude": 37.4056,
  "longitude": -122.0775,
  "countryName": "United States",
  "cityName": "Mountain View",
  "asn": 15169,
  "asnOrganization": "Google LLC",
  "isProxy": false
}
```

Duplicate IP addresses are rejected.

### `DELETE /delete/{record_id}`

Deletes a record from memory.

```http
DELETE http://localhost:8082/delete/a1234567
```

### `GET /generate-geo-clusters`

Generates geographic clusters from all records currently stored in memory.

```http
GET http://localhost:8082/generate-geo-clusters
```

Each cluster contains:

- `median_coordinates`
- `mean_coordinates`
- the original stored records belonging to the cluster

Example:

```json
{
  "cluster_1": {
    "median_coordinates": [-122.0775, 37.4056],
    "mean_coordinates": [-122.0812, 37.4081],
    "a1234567": {
      "ipAddress": "8.8.8.8",
      "latitude": 37.4056,
      "longitude": -122.0775
    }
  }
}
```

## Service C

Service C is exposed on port `8083`.

### `GET /`

Health check.

```http
GET http://localhost:8083/
```

### `GET /resolve-ip/{ip}`

Resolves an IP address using the external Free IP API.

```http
GET http://localhost:8083/resolve-ip/8.8.8.8
```

Service C calls:

```text
https://free.freeipapi.com/api/v1/json/{ip}
```

Only the fields required by the application are retained:

- `ipAddress`
- `latitude`
- `longitude`
- `countryName`
- `cityName`
- `asn`
- `asnOrganization`
- `isProxy`

# Geographic Clustering

Service B uses the **Haversine formula** to calculate geographic distance between longitude/latitude points.

The default clustering threshold is:

```text
50 km
```

A record can join an existing cluster when it is within the configured distance of any member of that cluster.

This produces a single-linkage-style behavior: connected points can belong to the same cluster even when the first and last points in a chain are more than the threshold apart.

For each cluster the service calculates:

- **Mean coordinates** — average longitude and average latitude
- **Median coordinates** — median longitude and median latitude

Coordinates are returned as:

```text
[longitude, latitude]
```

# Data Storage

Service B uses an in-memory data store.

Records are stored using a generated record ID:

```text
record_id -> geographic record
```

A separate set of IP addresses is used to prevent duplicates.

Because storage is in memory, records are lost when Service B restarts. This is intentional for the assignment.

# Async Design

The project uses asynchronous programming for I/O-bound operations.

Service-to-service communication uses `httpx.AsyncClient`.

Service B's memory methods are asynchronous and use an `asyncio.Lock` to protect shared state:

```python
async with self._lock:
    ...
```

The clustering functions remain synchronous because they operate on already-loaded data and perform CPU calculations rather than I/O.

# IP Validation

Service A uses Pydantic's `IPvAnyAddress` to validate IPv4 and IPv6 addresses before sending requests to Service C.

Invalid IPs are rejected before an external API request is made.

# Error Handling

The services handle errors at their appropriate boundaries.

### Service A

Handles:

- Invalid IP addresses
- Service B timeouts
- Service C timeouts
- Downstream HTTP/network errors

### Service B

Handles:

- Duplicate IP addresses
- Missing record IDs

### Service C

Handles:

- External API timeouts
- Network errors
- Non-success external API responses

# Configuration

Service A receives internal service URLs through environment variables in `compose.yaml`:

```yaml
environment:
  SERVICE_B_URL: http://svc-b-cont:8080
  SERVICE_C_URL: http://svc-c-cont:8080
```

The application reads them with `os.getenv()`.

No `.env` file is required for the current configuration.

# Docker

Each service has its own Dockerfile based on:

```text
python:3.11-slim
```

All services listen internally on port `8080`.

| Service | Container Port | Host Port |
|---|---:|---:|
| Service A | 8080 | 8081 |
| Service B | 8080 | 8082 |
| Service C | 8080 | 8083 |

All containers communicate through a shared Docker bridge network.

# Running the Project

## Prerequisites

- Docker
- Docker Compose

## Start

From the project root:

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

## View logs

```bash
docker compose logs
```

For a specific service:

```bash
docker compose logs service-a-container
docker compose logs service-b-container
docker compose logs service-c-container
```

# Swagger / OpenAPI Documentation

FastAPI provides interactive API documentation:

- Service A: `http://localhost:8081/docs`
- Service B: `http://localhost:8082/docs`
- Service C: `http://localhost:8083/docs`

The `/docs` interface can be used to test the endpoints directly.

# Example End-to-End Test

Start the application:

```bash
docker compose up --build
```

Resolve an IP:

```bash
curl http://localhost:8081/resolve-ip/8.8.8.8
```

Resolve multiple IPs:

```bash
curl -X POST http://localhost:8081/resolve-ip-list   -H "Content-Type: application/json"   -d '[
    "8.8.8.8",
    "1.1.1.1",
    "208.67.222.222"
  ]'
```

View stored records:

```bash
curl http://localhost:8081/
```

Generate clusters:

```bash
curl http://localhost:8082/generate-geo-clusters
```

Delete a record:

```bash
curl -X DELETE http://localhost:8081/delete/<record_id>
```

# Design Principles

The project follows a lightweight separation-of-concerns approach.

```text
Service A
→ API and orchestration

Service B
→ Storage and geographic processing

Service C
→ External API integration

memory.py
→ In-memory storage

clustering.py
→ Geographic calculations

connector.py
→ HTTP communication
```

The architecture avoids unnecessary abstraction layers and keeps each service focused on a specific responsibility.

# Assignment Constraints

The implementation is designed to satisfy the project constraints:

- No nested application subfolders
- Maximum 5 files per service folder
- Maximum 150 lines per source file
- Maximum 500 lines of Python code

# Summary

The project provides:

- IP validation
- Single IP resolution
- Batch IP resolution
- External IP geolocation
- In-memory storage
- Duplicate IP prevention
- Record deletion
- Geographic distance calculation
- Geographic clustering
- Mean and median cluster coordinates
- Async service communication
- Dockerized services
- Docker Compose orchestration
- FastAPI Swagger documentation
- Service-level error handling
