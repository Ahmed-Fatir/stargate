# Startgate File Retrieval Service - API Documentation

Base URL: `http://<host>:<port>`

## Authentication

All endpoints except `/health` require a Bearer token in the `Authorization` header.

```
Authorization: Bearer <API_TOKEN>
```

Unauthorized requests return:

```json
{
  "detail": "Invalid authentication token"
}
```

**Status code:** `401 Unauthorized`

---

## Endpoints

### GET /health

Public health check. No authentication required.

**Request:**

```bash
curl http://localhost:8000/health
```

**Response (200):**

```json
{
  "status": "healthy",
  "service": "Startgate"
}
```

`status` is `"healthy"` if at least one configured service path is accessible, otherwise `"unhealthy"`.

---

### GET /status

Authenticated detailed status for administrators. Returns information about all configured services.

**Request:**

```bash
curl http://localhost:8000/status \
  -H "Authorization: Bearer <API_TOKEN>"
```

**Response (200):**

```json
{
  "status": "healthy",
  "service": "Startgate File Retrieval Service",
  "configured_services": ["system", "app", "btblk"],
  "service_details": {
    "system": { "accessible": true },
    "app": { "accessible": true },
    "btblk": { "accessible": false }
  },
  "allowed_database_prefix": "experio_cabinet_"
}
```

`status` is `"healthy"` when all services are accessible, `"degraded"` when one or more are not.

---

### POST /{service}/files

Retrieve one or more files from a specific service filestore.

**Path parameters:**

| Parameter | Type   | Description                                                    |
|-----------|--------|----------------------------------------------------------------|
| `service` | string | Service name. One of: `system`, `app`, `btblk`, `decimal`, `srm`, `portal` (only configured services are available) |

**Query parameters:**

| Parameter    | Type | Default | Description                                                                 |
|--------------|------|---------|-----------------------------------------------------------------------------|
| `always_zip` | bool | `false` | When `true`, the response is always a ZIP file, even for a single file result |

**Request body (JSON):**

| Field  | Type     | Description                                                         |
|--------|----------|---------------------------------------------------------------------|
| `files` | string[] | List of file specs in the format `<database>-<filehash>`. Max 100 items (configurable). |

**File spec format:** `experio_cabinet_<name>-<40_char_sha1_hash>`

**Validation rules:**
- `files` list cannot be empty
- Maximum 100 files per request (configurable via `MAX_FILES_PER_REQUEST`)
- Database name must start with `experio_cabinet_`
- File hash must be exactly 40 hexadecimal characters (SHA-1)

---

#### Example: Single file request

**Request:**

```bash
curl -X POST http://localhost:8000/app/files \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      "experio_cabinet_demo-a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    ]
  }'
```

**Response (200) - File found:**

Returns the raw file as a binary stream.

| Header              | Value                                                                    |
|---------------------|--------------------------------------------------------------------------|
| `Content-Type`      | `application/octet-stream`                                               |
| `Content-Disposition` | `attachment; filename=experio_cabinet_demo-a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2` |

---

#### Example: Single file request with always_zip

**Request:**

```bash
curl -X POST "http://localhost:8000/app/files?always_zip=true" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      "experio_cabinet_demo-a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    ]
  }'
```

**Response (200):**

Returns a ZIP archive containing the single file.

| Header              | Value                                          |
|---------------------|-------------------------------------------------|
| `Content-Type`      | `application/zip`                               |
| `Content-Disposition` | `attachment; filename=startgate_app_files.zip` |

---

#### Example: Multiple files request

**Request:**

```bash
curl -X POST http://localhost:8000/app/files \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      "experio_cabinet_demo-a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
      "experio_cabinet_demo-b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3"
    ]
  }'
```

**Response (200) - Multiple files found:**

Returns a ZIP archive containing all found files.

| Header              | Value                                          |
|---------------------|-------------------------------------------------|
| `Content-Type`      | `application/zip`                               |
| `Content-Disposition` | `attachment; filename=startgate_app_files.zip` |

Each file inside the ZIP is named using its original file spec (`<database>-<filehash>`).

---

#### Example: No files found

**Request:**

```bash
curl -X POST http://localhost:8000/app/files \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      "experio_cabinet_demo-0000000000000000000000000000000000000000"
    ]
  }'
```

**Response (200):**

```json
{
  "success": false,
  "files_found": 0,
  "files_requested": 1,
  "total_size": 0,
  "file_details": [
    {
      "database": "experio_cabinet_demo",
      "file_hash": "0000000000000000000000000000000000000000",
      "found": false,
      "file_size": null,
      "error": "File not found"
    }
  ]
}
```

---

#### Example: Validation error

**Request with invalid database prefix:**

```bash
curl -X POST http://localhost:8000/app/files \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "files": ["invalid_db-a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"]
  }'
```

**Response (422):**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "files"],
      "msg": "Value error, Database not allowed: invalid_db",
      "input": ["invalid_db-a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"]
    }
  ]
}
```

---

#### Example: Invalid service

**Request:**

```bash
curl -X POST http://localhost:8000/invalid/files \
  -H "Authorization: Bearer <API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "files": ["experio_cabinet_demo-a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"]
  }'
```

**Response (400):**

```json
{
  "detail": "Service 'invalid' not configured. Available services: system, app, btblk"
}
```

---

## Response Behavior Summary

| Scenario                            | Response type        | Content-Type              |
|-------------------------------------|----------------------|---------------------------|
| No files found                      | JSON (FileResponse)  | `application/json`        |
| 1 file found, `always_zip=false`    | Raw binary stream    | `application/octet-stream`|
| 1 file found, `always_zip=true`     | ZIP archive          | `application/zip`         |
| 2+ files found                      | ZIP archive          | `application/zip`         |

---

## Environment Variables

| Variable                | Required | Default   | Description                          |
|-------------------------|----------|-----------|--------------------------------------|
| `API_TOKEN`             | Yes      | -         | Bearer token for authentication      |
| `SYSTEM_FILESTORE_PATH` | No*      | -         | Path to system filestore             |
| `APP_FILESTORE_PATH`    | No*      | -         | Path to app filestore                |
| `BTBLK_FILESTORE_PATH`  | No*      | -         | Path to btblk filestore              |
| `DECIMAL_FILESTORE_PATH`| No*      | -         | Path to decimal filestore            |
| `SRM_FILESTORE_PATH`    | No*      | -         | Path to srm filestore                |
| `PORTAL_FILESTORE_PATH` | No*      | -         | Path to portal filestore             |
| `HOST`                  | No       | `0.0.0.0` | Server bind address                  |
| `PORT`                  | No       | `8000`    | Server port                          |
| `LOG_LEVEL`             | No       | `INFO`    | Logging level                        |
| `MAX_FILES_PER_REQUEST` | No       | `100`     | Max files allowed per request        |

*At least one `*_FILESTORE_PATH` must be configured.

---

## File Storage Structure

Files are stored following this path pattern:

```
<FILESTORE_PATH>/<database>/<first_2_chars_of_hash>/<full_hash>
```

Example for hash `a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2` in database `experio_cabinet_demo` on the `app` service:

```
/path/to/app/filestore/experio_cabinet_demo/a1/a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
```
