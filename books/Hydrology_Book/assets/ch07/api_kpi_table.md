| KPI | Sync API | Async API | Assessment |
|:----|:---------|:----------|:-----------|
| Total Requests | 2449 | 2449 | Same load |
| Completed | 297 | 596 | Async: +299 |
| Dropped | 2102 | 0 | Sync loses 86% |
| Avg Latency | 25.2s | 50ms | Async 505x faster |
| P99 Latency | 29.9s | 50ms | SLO Compliant |