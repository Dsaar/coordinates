from math import radians, sin, cos, asin, sqrt


EARTH_RADIUS_KM = 6371
DEFAULT_DISTANCE_KM = 50


def distance_km(first, second):
    lon1, lat1 = map(radians, first)
    lon2, lat2 = map(radians, second)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    value = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    return EARTH_RADIUS_KM * 2 * asin(sqrt(value))


def median(values):
    values = sorted(values)
    middle = len(values) // 2

    if len(values) % 2:
        return values[middle]

    return (values[middle - 1] + values[middle]) / 2


def generate_clusters(
    records,
    max_distance_km=DEFAULT_DISTANCE_KM
):
    clusters = []

    for record_id, record in records.items():
        point = [
            float(record["longitude"]),
            float(record["latitude"])
        ]

        cluster = next(
            (
                item for item in clusters
                if any(
                    distance_km(
                        point,
                        member["point"]
                    ) <= max_distance_km
                    for member in item["members"]
                )
            ),
            None
        )

        if cluster is None:
            cluster = {"members": []}
            clusters.append(cluster)

        cluster["members"].append({
            "id": record_id,
            "record": record,
            "point": point
        })

    return build_response(clusters)


def build_response(clusters):
    result = {}

    for index, cluster in enumerate(clusters, 1):
        points = [item["point"] for item in cluster["members"]]
        lons = [point[0] for point in points]
        lats = [point[1] for point in points]

        data = {
            "median_coordinates": [
                median(lons),
                median(lats)
            ],
            "mean_coordinates": [
                sum(lons) / len(lons),
                sum(lats) / len(lats)
            ]
        }

        for item in cluster["members"]:
            data[item["id"]] = item["record"]

        result[f"cluster_{index}"] = data

    return result