## 2026-07-06 - [MongoDB O(1) Counting Optimization]
**Learning:** [Using `count_documents({})` with an empty filter on MongoDB results in an O(N) collection scan which is inefficient for large datasets, whereas `estimated_document_count()` uses collection metadata for an O(1) operation.]
**Action:** [Always use `estimated_document_count()` instead of `count_documents({})` when counting all documents in a collection without any filters to optimize MongoDB query performance.]

## 2026-07-04 - [Replace count_documents({}) with estimated_document_count()]
**Learning:** `count_documents({})` scans all the documents in the collection when an empty query is passed, which has `O(N)` time complexity. This is extremely inefficient on large collections like `contratos-electronicos`. Replacing it with `estimated_document_count()` provides a huge performance boost as it queries the collection metadata instead, executing in `O(1)` time.
**Action:** Use `estimated_document_count()` instead of `count_documents({})` for `O(1)` time complexity execution whenever there are no filters.

## 2026-07-08 - [MongoDB Aggregation for Data Grouping]
**Learning:** Reading all records into Python application memory using `.find()` and looping over them is an O(N) operation that leads to significant latency, CPU usage, and high memory utilization (especially for large string replacements and object allocations).
**Action:** Always shift heavy data processing (like grouping, mapping strings to decimals, and summarizing) directly to the database layer via MongoDB Aggregation Pipelines (e.g. `$group`, `$addFields`) or SQL queries, executing them efficiently without transferring the raw datasets over the network into memory.

## 2024-07-09 - MongoDB Aggregation Pipeline Optimization for Pareto Analysis
**Learning:** In the MongoDB repositories, performing aggregation logic (like grouping and summing values) on the application side using `.find()` leads to O(N) memory consumption and high CPU usage due to downloading all matching documents.
**Action:** Consistently replace application-side loops (like finding and summing `valor_del_contrato` per `nombre_entidad` in `pareto`) with in-database MongoDB aggregation pipelines (`$match`, `$addFields` with `_TO_DOUBLE` macro, and `$group`), shifting the workload to the database engine and drastically reducing memory footprint.

## 2023-10-25 - Push parsing and grouping to Mongo Aggregation Pipelines
**Learning:** Doing heavy regex string parsing and sorting in Python for O(N) datasets using `find()` is an anti-pattern. Application memory and CPU (due to python string manipulations/regexes for money values like $10,000) can become huge bottlenecks.
**Action:** Use MongoDB aggregation pipelines with `$addFields` and macro variables like `_TO_DOUBLE` to do type coercion/cleaning at the DB engine level, alongside `$sort` and `$match`.

## 2024-07-12 - [Cache Socrata API Calls in paso1_service]
**Learning:** [Synchronous API calls to external services (like Socrata) inside endpoint handlers block the application, leading to high latency and timeouts (~30s). Wrapping these calls in `cache.cached()` shifts the bottleneck from real-time network IO to fast DB cache retrievals.]
**Action:** [Always verify if external API fetches can be cached using the existing `cache_service` to improve endpoint response times, especially for datasets that do not change frequently.]

## 2024-08-01 - MongoDB Aggregation Pipeline for Anomaly Detection Memory Optimization
**Learning:** Performing statistical computations (average, std dev, Q1, Q3) and fetching anomaly outliers in Python for a large dataset (O(N) memory usage for all documents) causes significant memory and CPU overhead.
**Action:** Replace Python-side computation on `aggregate()` loops with explicit MongoDB aggregation pipelines (e.g. `$avg`, `$stdDevPop`, `$sort` with `$skip` and `$limit`) to compute statistics and retrieve anomalies. This shifts the heavy workload and memory requirements to the database engine, improving backend performance to O(1) memory usage in Python.

## 2026-07-31 - [Angular Template Optimization]
**Learning:** Template functions execute on every change detection cycle. Pure Pipes cache results, and trackBy in *ngFor loops prevents unnecessary O(N) DOM re-renders.
**Action:** Use Pure Pipes for template formatting and always include trackBy in *ngFor directives.
