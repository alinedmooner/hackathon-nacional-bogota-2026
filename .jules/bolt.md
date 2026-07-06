## 2026-07-06 - [MongoDB O(1) Counting Optimization]
**Learning:** [Using `count_documents({})` with an empty filter on MongoDB results in an O(N) collection scan which is inefficient for large datasets, whereas `estimated_document_count()` uses collection metadata for an O(1) operation.]
**Action:** [Always use `estimated_document_count()` instead of `count_documents({})` when counting all documents in a collection without any filters to optimize MongoDB query performance.]
