from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Custom registry to avoid clashes/pollution
metrics_registry = CollectorRegistry()

# 1. API request counters & histograms
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests received.",
    ["method", "path", "status"],
    registry=metrics_registry,
)

HTTP_REQUEST_LATENCY_SECONDS = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
    registry=metrics_registry,
)

# 2. Database & cache health metrics
DB_POOL_CONNECTIONS = Gauge(
    "db_pool_connections",
    "Current active database connection pool stats.",
    ["state"],  # "active", "overflow"
    registry=metrics_registry,
)

CACHE_OPERATIONS_TOTAL = Counter(
    "cache_operations_total",
    "Cache read operations with hit/miss ratio.",
    ["operation", "result"],  # "read", "hit"/"miss"
    registry=metrics_registry,
)

# 3. AI cost and token consumption
AI_COST_TOTAL_USD = Counter(
    "ai_cost_total_usd",
    "Total dollars spent on AI model queries.",
    ["model_name", "feature"],
    registry=metrics_registry,
)

AI_TOKENS_TOTAL = Counter(
    "ai_tokens_total",
    "Total AI tokens consumed.",
    ["type", "model_name"],  # type: "prompt" or "completion"
    registry=metrics_registry,
)
