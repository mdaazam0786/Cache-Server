# Caching Proxy Server

A lightweight HTTP caching proxy built with **FastAPI** and **Redis**. It sits in front of any upstream (origin) server, forwards incoming requests, and caches JSON responses in Redis — so repeated requests are served instantly without hitting the origin again.

---

## How It Works

```
Client  →  /proxy/<path>  →  Proxy Server  →  Redis (cache check)
                                          ↘  Origin Server (on cache miss)
```

1. A request arrives at `/proxy/<path>`.
2. For `GET` requests, the proxy checks Redis for a cached response.
   - **Cache Hit** — returns the cached response immediately.
   - **Cache Miss** — forwards the request to the configured origin server.
3. The origin's JSON response is wrapped in a standard envelope, stored in Redis with a TTL, and returned to the client.
4. `POST`, `PUT`, `DELETE`, and `PATCH` requests always bypass the cache and go straight to the origin (but their responses are still cached).

---

## Project Structure

```
Proxy-server/
├── app/
│   ├── main.py                    # App entry point — FastAPI setup & startup validation
│   ├── config.py                  # Environment-based configuration (pydantic-settings)
│   ├── models.py                  # Response models: UIBean<T> and ResponseData
│   ├── controller/
│   │   └── proxy_controller.py    # Route handlers: /proxy/** and /proxy/clear
│   ├── service/
│   │   ├── proxy_service.py       # Core logic: cache check, upstream forwarding, cache write
│   │   └── redis_service.py       # Redis client: save, get, clear_all
│   └── util/
│       └── origin_holder.py       # Singleton holding the upstream origin URL
├── Dockerfile                     # Container image definition
├── render.yaml                    # Render.com deployment config
├── requirements.txt               # Python dependencies
└── .env.example                   # Environment variable template
```

---

## API Endpoints

### `GET /proxy/clear`
Flushes all cached entries from Redis.

**Response:**
```json
{
  "data": null,
  "success": true,
  "message": "Cache cleared successfully",
  "response": "Cleared"
}
```

---

### `GET|POST|PUT|DELETE|PATCH /proxy/{path}`
Forwards the request to the origin server at the given path.

- The `/proxy` prefix is stripped before forwarding, so `/proxy/api/users` → `<PROXY_ORIGIN>/api/users`.
- Query parameters are preserved and forwarded as-is.
- Request headers are forwarded (excluding `host`, `accept-encoding`, `content-encoding`).
- Request body is forwarded for non-GET methods.
- The origin must return `application/json` — other content types return a 500 error.

**Cache Hit response:**
```json
{
  "data": { ...upstream response... },
  "success": true,
  "message": "Cache Hit",
  "response": null
}
```

**Cache Miss response:**
```json
{
  "data": { ...upstream response... },
  "success": true,
  "message": "Cache Miss",
  "response": "Upstream call successful"
}
```

**Error response (upstream failure or invalid content type):**
```json
{
  "data": null,
  "success": false,
  "message": "Upstream call failed",
  "response": "<error detail>"
}
```

---

## Response Envelope

All responses are wrapped in a `UIBean` envelope:

| Field      | Type    | Description                                      |
|------------|---------|--------------------------------------------------|
| `data`     | any     | The upstream response payload                    |
| `success`  | boolean | `true` on success, `false` on error              |
| `message`  | string  | `"Cache Hit"`, `"Cache Miss"`, or error message  |
| `response` | string  | Additional detail or raw error string            |

---

## Cache Behavior

| Method              | Cache Read | Cache Write |
|---------------------|------------|-------------|
| `GET`               | ✅ Yes     | ✅ Yes      |
| `POST/PUT/DELETE/PATCH` | ❌ No  | ✅ Yes      |

Cache keys are built as:
```
<CACHE_KEY_PREFIX><METHOD>:<path>?<query>
```

For example, a `GET /proxy/api/users?page=1` with the default prefix becomes:
```
CACHE_KEYGET:/proxy/api/users?page=1
```

Cached entries expire after `RESPONSE_TTL` days (default: 1 day).

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable                  | Required | Default      | Description                                      |
|---------------------------|----------|--------------|--------------------------------------------------|
| `PROXY_ORIGIN`            | ✅ Yes   | —            | Upstream server URL (e.g. `http://api.example.com`) |
| `PORT`                    | No       | `8081`       | Port the proxy server listens on                 |
| `REDIS_HOST`              | ✅ Yes   | —            | Redis server hostname                            |
| `REDIS_PORT`              | No       | `6379`       | Redis server port                                |
| `REDIS_DATABASE`          | No       | `0`          | Redis database index                             |
| `REDIS_CONNECTION_TIMEOUT`| No       | `2000`       | Connection timeout in milliseconds               |
| `REDIS_MAX_CONNECTIONS`   | No       | `50`         | Max connections in the Redis pool                |
| `CACHE_KEY`               | No       | `CACHE_KEY`  | Prefix for all Redis cache keys                  |
| `RESPONSE_TTL`            | No       | `1`          | Cache TTL in days                                |

The app will **exit at startup** if `PROXY_ORIGIN` or `REDIS_HOST` are not set.

---

## Running Locally

### Prerequisites
- Python 3.12+
- A running Redis instance

### Steps

```bash
# 1. Clone the repo
git clone <repo-url>
cd Proxy-server

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your PROXY_ORIGIN and REDIS_HOST

# 5. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
```

The server will be available at `http://localhost:8081`.  
Interactive API docs (Swagger UI) are at `http://localhost:8081/docs`.

---

## Running with Docker

```bash
# Build the image
docker build -t caching-proxy-server .

# Run the container
docker run -p 8081:8081 \
  -e PROXY_ORIGIN=http://your-origin-server.com \
  -e REDIS_HOST=host.docker.internal \
  caching-proxy-server
```

> **Note:** Use `host.docker.internal` as `REDIS_HOST` to reach a Redis instance running on your local machine from inside Docker (macOS/Windows). On Linux, use the host's IP or run Redis in the same Docker network.

---

## Deploying to Render

The `render.yaml` file is pre-configured for [Render.com](https://render.com) deployment using Docker.

1. Push the repo to GitHub.
2. Create a new **Web Service** on Render and connect the repo.
3. Render will detect `render.yaml` automatically.
4. Set the required environment variables in the Render dashboard:
   - `PROXY_ORIGIN` — your upstream server URL
   - `REDIS_HOST` — hostname of your Redis instance (e.g. a Render Redis service)
   - `PORT` — port to expose (Render typically sets this automatically)

---

## Dependencies

| Package             | Version  | Purpose                                      |
|---------------------|----------|----------------------------------------------|
| `fastapi`           | 0.111.0  | Web framework and routing                    |
| `uvicorn[standard]` | 0.29.0   | ASGI server                                  |
| `httpx`             | 0.27.0   | Async HTTP client for upstream requests      |
| `redis`             | 5.0.4    | Redis client with connection pool support    |
| `pydantic`          | 2.7.1    | Data validation and response models          |
| `pydantic-settings` | 2.2.1    | Environment variable configuration           |

---

## Logging

The server logs at `INFO` level by default. Key log events:

- Origin URL set at startup
- Cache key generated per request
- Final upstream URL being called
- Cache Hit / Cache Miss per request
- Upstream response payload
- Redis save/fetch errors
- Cache clear operations

Log format:
```
2024-01-01 12:00:00,000 [INFO] app.service.proxy_service - Cache key: GET:/proxy/api/users?
```
