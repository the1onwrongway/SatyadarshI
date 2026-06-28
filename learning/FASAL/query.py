import duckdb
import time

parquet_path = "data/ahmedabad_nov2025.parquet"

# DuckDB can query Parquet directly — no loading into memory first
con = duckdb.connect()  # in-memory database, no file needed

print("=== Query 1: Basic summary ===")
start = time.time()
result = con.execute(f"""
    SELECT
        COUNT(*)                        AS total_pixels,
        ROUND(AVG(ndvi), 4)             AS avg_ndvi,
        ROUND(MIN(ndvi), 4)             AS min_ndvi,
        ROUND(MAX(ndvi), 4)             AS max_ndvi,
        ROUND(AVG(red), 4)              AS avg_red,
        ROUND(AVG(nir), 4)              AS avg_nir
    FROM read_parquet('{parquet_path}')
""").df()
print(result.to_string(index=False))
print(f"Time: {time.time() - start:.3f}s\n")


print("=== Query 2: Land cover breakdown ===")
start = time.time()
result = con.execute(f"""
    SELECT
        land_cover,
        COUNT(*)                                AS pixel_count,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct,
        ROUND(AVG(ndvi), 4)                     AS avg_ndvi
    FROM read_parquet('{parquet_path}')
    GROUP BY land_cover
    ORDER BY pixel_count DESC
""").df()
print(result.to_string(index=False))
print(f"Time: {time.time() - start:.3f}s\n")


print("=== Query 3: Top 10 greenest pixels ===")
start = time.time()
result = con.execute(f"""
    SELECT
        ROUND(latitude, 6)   AS latitude,
        ROUND(longitude, 6)  AS longitude,
        ROUND(ndvi, 4)       AS ndvi,
        land_cover
    FROM read_parquet('{parquet_path}')
    ORDER BY ndvi DESC
    LIMIT 10
""").df()
print(result.to_string(index=False))
print(f"Time: {time.time() - start:.3f}s\n")


print("=== Query 4: Urban pixels with surprisingly high NIR ===")
start = time.time()
result = con.execute(f"""
    SELECT
        COUNT(*) AS count,
        ROUND(AVG(ndvi), 4) AS avg_ndvi,
        ROUND(AVG(nir), 4)  AS avg_nir
    FROM read_parquet('{parquet_path}')
    WHERE land_cover = 'urban_bare'
      AND nir > 0.3
""").df()
print(result.to_string(index=False))
print(f"Time: {time.time() - start:.3f}s\n")


print("=== Query 5: Spatial slice — city center band ===")
start = time.time()
result = con.execute(f"""
    SELECT
        ROUND(longitude, 3)  AS lon_bin,
        ROUND(AVG(ndvi), 4)  AS avg_ndvi,
        COUNT(*)             AS pixels
    FROM read_parquet('{parquet_path}')
    WHERE latitude BETWEEN 22.98 AND 23.02
    GROUP BY lon_bin
    ORDER BY lon_bin
""").df()
print(result.to_string(index=False))
print(f"Time: {time.time() - start:.3f}s\n")

con.close()