# VinMecLumina

## Hướng dẫn cài đặt nhanh

1. Clone repository về máy:

```bash
git clone <URL_REPO>
cd VinMecLumina
```

2. Tạo môi trường ảo với `uv`:

```bash
uv venv 
```

3. Kích hoạt môi trường ảo trong Git Bash:

```bash
source .venv/Scripts/activate
```

4. Cài đặt các thư viện từ `requirements.txt`:

```bash
uv pip install -r requirements.txt
```

5. Sau khi chạy xong, nếu cần tắt môi trường ảo:

```bash
deactivate
```

---

> Lưu ý: nếu dùng PowerShell thì lệnh kích hoạt sẽ là:
>
> ```powershell
> .\.venv\Scripts\Activate.ps1
> ```

## Chay REST API (FastAPI)

1. Kich hoat moi truong ao:

```bash
source .venv/Scripts/activate
```

2. Chay API server:

```bash
uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

Truoc khi chay API, can cau hinh API key authentication:

```bash
export LUMINA_API_KEYS="user_a:key_a,user_b:key_b"
```

Trong Windows PowerShell:

```powershell
$env:LUMINA_API_KEYS = "user_a:key_a,user_b:key_b"
```

Can cau hinh Redis (state duoc luu trong Redis de dat stateless design):

```bash
export LUMINA_REDIS_URL="redis://localhost:6379/0"
```

Trong Windows PowerShell:

```powershell
$env:LUMINA_REDIS_URL = "redis://localhost:6379/0"
```

3. Mo Swagger UI:

- http://127.0.0.1:8000/docs

### Endpoint chinh

- `POST /api/v1/analyze`: Phan tich ket qua xet nghiem (theo `patient_id` hoac `initial_state`).
- `POST /api/v1/chat`: Hoi dap theo hoi thoai, co ho tro `conversation_id`.
- `POST /api/v1/chat/stream`: Hoi dap dang stream (SSE).
- `GET /api/v1/conversations/{conversation_id}`: Lay lich su hoi thoai hien tai.
- `GET /health`: Liveness check.
- `GET /ready`: Readiness check.

Tat ca endpoint trong `/api/v1/*` yeu cau header:

```text
X-API-Key: <your-api-key>
```

### Guardrails da bat

- API key authentication: bat buoc cho `/api/v1/*`
- Rate limiting: `10 requests / minute / user`
- Cost guard: mac dinh `10 USD / month / user`
- Structured JSON logging: request log theo JSON cho moi request
- Graceful shutdown: server ngung nhan request moi, cho request dang xu ly hoan tat trong thoi gian grace

Bien moi truong co the tuy chinh:

- `LUMINA_API_KEYS`: danh sach `user:key` (bat buoc)
- `LUMINA_REDIS_URL`: Redis connection URL, mac dinh `redis://redis:6379/0`
- `LUMINA_CONVERSATION_TTL_SECONDS`: TTL hoi thoai trong Redis, mac dinh `86400`
- `LUMINA_RATE_LIMIT_PER_MINUTE`: mac dinh `10`
- `LUMINA_MONTHLY_COST_LIMIT_USD`: mac dinh `10`
- `LUMINA_DEFAULT_REQUEST_COST_USD`: mac dinh `0.05`
- `LUMINA_ANALYZE_COST_USD`: mac dinh `0.05`
- `LUMINA_INPUT_COST_PER_1K_USD`: mac dinh `0.005`
- `LUMINA_OUTPUT_COST_PER_1K_USD`: mac dinh `0.015`
- `LUMINA_SHUTDOWN_GRACE_SECONDS`: mac dinh `10`
- `LUMINA_APP_NAME`: app name trong metadata
- `LUMINA_APP_VERSION`: app version trong metadata

### Vi du goi API

Phan tich va tao conversation:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/analyze" \
	-H "X-API-Key: key_a" \
	-H "Content-Type: application/json" \
	-d '{
		"patient_id": "P001",
		"llm_provider": "azure",
		"create_conversation": true
	}'
```

Chat tiep theo (giu lich su bang `conversation_id`):

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/chat" \
	-H "X-API-Key: key_a" \
	-H "Content-Type: application/json" \
	-d '{
		"conversation_id": "<your-conversation-id>",
		"message": "Tai sao HbA1c cua toi cao?",
		"llm_provider": "azure"
	}'
```

Stream response (SSE):

```bash
curl -N -X POST "http://127.0.0.1:8000/api/v1/chat/stream" \
	-H "X-API-Key: key_a" \
	-H "Content-Type: application/json" \
	-d '{
		"conversation_id": "<your-conversation-id>",
		"message": "Giai thich ngan gon ve LDL",
		"llm_provider": "azure"
	}'
```

## Docker (multi-stage build)

Build image:

```bash
docker build -t vinmec-lumina-api:latest .
```

Run API container:

```bash
docker run --rm -p 8000:8000 \
  -e LUMINA_REDIS_URL=redis://host.docker.internal:6379/0 \
  -e LUMINA_API_KEYS=user_a:key_a,user_b:key_b \
  -e OPENAI_API_KEY=<your-openai-api-key> \
  vinmec-lumina-api:latest
```

## Docker Compose (API + Redis)

```bash
docker compose up --build
```

Khi dung compose, Redis va API chay cung network va API tu dong dung `LUMINA_REDIS_URL=redis://redis:6379/0`.
