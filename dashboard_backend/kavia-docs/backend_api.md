# SLT Dashboard Backend API Documentation

This document describes the REST and WebSocket APIs, endpoints, authentication, business logic, monitoring, roles/permissions, and error/response models for the Senior Leadership Team Dashboard Backend.  

---

## Table of Contents

- [Overview](#overview)
- [Authentication & Security](#authentication--security)
- [Roles & Permissions](#roles--permissions)
- [Monitoring & Logging](#monitoring--logging)
- [Endpoints by Domain](#endpoints-by-domain)
  - [Ingestion](#ingestion)
  - [Parsing](#parsing)
  - [Classification](#classification)
  - [KPI](#kpi)
  - [Dashboard](#dashboard)
  - [Export](#export)
  - [Templates](#templates)
  - [Scheduling](#scheduling)
  - [Realtime](#realtime)
  - [User Management](#user-management)
  - [Health & Metrics](#health--metrics)
- [Error & Validation Models](#error--validation-models)
- [Business Logic Highlights](#business-logic-highlights)
- [Usage Examples](#usage-examples)
- [Appendix: WebSocket Usage](#appendix-websocket-usage)

---

## Overview

The backend exposes API endpoints for uploading and parsing files (Excel, PPT, PDF, Word), tagging/classification, KPI computation, dashboard/template configuration, exporting, scheduling, monitoring, and user/team/project management. It features secure authentication (JWT), RBAC per endpoint, Prometheus metrics, and a real-time WebSocket API for live updates.

---

## Authentication & Security

- **Registration**: `/api/auth/register` - Registers a new user (email must be unique).
- **Login**: `/api/auth/token` - Returns JWT access token (password required).
- All major API endpoints require `Authorization: Bearer <token>`.
- JWT token is validated and user account checked for `is_active` status.

### Security Mechanisms

- **RBAC**: Endpoints can check `is_superuser` or more granular roles (extensible via `security.py`).
- **Rate Limiting**: Configurable per endpoint to prevent abuse (see code decorators).
- **Exception Handling**: Consistent error responses (HTTPException, validation, unhandled errors).

---

## Roles & Permissions

- **Admin**: Full access (can save dashboards, create templates).
- **Regular Users**: Can view/list dashboards, templates, teams, projects.
- **RBAC Decorators**: Used for fine-grained control, e.g. `require_roles(["admin"])`. Most writes are admin-only by default.

---

## Monitoring & Logging

- **Metrics**: `/metrics` exposes Prometheus metrics: request counts, latencies, MongoDB health.
- **Health Check**: `/healthz` runs deep health probe (checks database connectivity).
- **Log Format**: Structured JSON logs for all traffic/errors.
- **Legacy Health**: `/` provides a basic "Healthy" message (does NOT check DB).

---

## Endpoints by Domain

### Ingestion

- `POST /api/ingestion/upload`  
  Upload Excel, PowerPoint, PDF, Word files.  
  Returns: `{ filename, status }`
- `GET /api/ingestion/folders`  
  List all mapped ingestion folders.
- `POST /api/ingestion/folders`  
  Map a folder for ingestion.  
  Body: `{ path, alias }`

### Parsing

- `POST /api/parsing/parse?filename=<fname>`  
  Parse an uploaded file.  
  Returns parsed content, stubbed for invalid files/types.  
  Supported: Excel, DOCX, PDF, PPTX.

### Classification

- `POST /api/classification/tag`  
  Assigns smart/manual tags and rules to a parsed file.  
  Body: `{ filename, tags, rules?, overwrite? }`  
  Returns: classified tags.  
  Requires authentication and backend parsing result.

### KPI

- `POST /api/kpi/compute`  
  Compute KPIs for given file (supports Excel, PPT, PDF, Word).  
  Body: `{ filename, rules? }`  
  Returns KPI values.

### Dashboard

- `POST /api/dashboard/config`  
  Save/update dashboard configuration (admin only).
- `GET /api/dashboard/configs`  
  List all dashboard summary configs.
- `GET /api/dashboard/config/{dashboard_id}`  
  Load full config for specific dashboard.

### Export

- `POST /api/export/dashboard`  
  Export dashboard as PDF/PPT/HTML.  
  Body: `{ dashboard_id, format }`  
  Returns export URL.

### Templates

- `POST /api/templates/`  
  Create/save a dashboard template (admin only).
- `GET /api/templates/`  
  List all templates.

### Scheduling

- `POST /api/scheduling/`  
  Schedule dashboard export + (future) email delivery.  
  Body: `{ dashboard_id, cron, email, export_format? }`
- `GET /api/scheduling/`  
  List all schedule jobs.
- `GET /api/scheduling/status/{schedule_id}`  
  Returns run status/error for delivery schedule.

### Realtime

- **WebSocket:** `/ws/dashboard/updates`  
  Clients connect for push updates (see Appendix for details, subscribe format, push message contract).  
  Usage: see `/realtime-help` for docs.

### User Management

- `GET /api/user/me`  
  Get current user info.
- `GET /api/user/teams`  
  List all teams.
- `GET /api/user/team/{team_id}`  
  Details for a team.
- `GET /api/user/projects`  
  List all projects.
- `GET /api/user/project/{project_id}`  
  Details for a project.

### Health & Metrics

- `GET /healthz`  
  Full healthcheck (includes DB).
- `GET /metrics`  
  Prometheus scrape metrics.

---

## Error & Validation Models

All endpoints use consistent error models:

- 400: Bad Request (validation failed, missing fields)
- 401: Unauthorized (token missing/invalid)
- 403: Insufficient privileges (RBAC)
- 404: Resource/File not found
- 422: Validation Errors (see FastAPI error model, `ValidationError`)
- 429: Rate limit exceeded
- 500: Internal server error

All errors are returned as `{ "detail": <reason> }`.

---

## Business Logic Highlights

- **RBAC**: Many create/update endpoints check for `is_superuser`. Extend with finer roles if needed.
- **Rate limiting**: Defaults e.g. 10/min on writes for safety.
- **Advanced Tagging/Classification**: Use rules and content-based heuristics (see `/api/classification/tag`).
- **KPI computation**: File-type-aware; Excel: column stats, PDF: summary/page, Word: word/action, PPT: slides/team.
- **Export**: Ensures robust reporting, versioning, and audit tracking.

---

## Usage Examples

### Authentication Flow

```
# Register user
POST /api/auth/register
{ "email": "u@ex.co", "password": "mypass", "full_name": "..." }

# Login
POST /api/auth/token
Content-Type: application/x-www-form-urlencoded
username=...&password=...

# Use JWT in header
Authorization: Bearer <access_token>
```

### Ingestion & Parsing

```
# Upload an Excel file
POST /api/ingestion/upload
(form-data: file=example.xlsx)

# Parse
POST /api/parsing/parse?filename=example.xlsx
Headers: Authorization: Bearer <token>
```

### WebSocket Real-time

For live updates, connect via:
```
const ws = new WebSocket("ws://<host>/ws/dashboard/updates")
ws.send(JSON.stringify({event: "subscribe", dashboard_id: "<id>"}))
ws.onmessage = (evt) => { const data = JSON.parse(evt.data); /* handle update */ }
```
See [Appendix](#appendix-websocket-usage).

### Scheduling a Report

```
POST /api/scheduling/
{
  "dashboard_id": "DASH1",
  "cron": "0 12 * * 1",       # Every Monday at noon
  "email": "someone@yourorg.com"
}
```

---

## Appendix: WebSocket Usage

- **Endpoint**: `/ws/dashboard/updates`
- **Contract**: Send `{event: "subscribe", dashboard_id: "<id>"}` to subscribe. Server will send `{event: ..., data: ...}` messages for real-time updates.
- **Authentication**: Can be required (extend code to enforce token check).
- **Disconnects**: Handle reconnect in frontend. Subscriptions are per-connection.

---

## Security, Rate Limiting & Error Handling Details

- All endpoints have basic DDoS prevention via in-memory rate limit (`security.py`).
- Production deployments should add persistent rate limiting (Redis).
- Role checks can be extended via utility decorators (`require_roles`).

---

## Monitoring

- Scrape `/metrics` for real-time service health and request tracing.
- Query `/healthz` to check API + DB is live.

---

**For further details and the OpenAPI schema, see [`interfaces/openapi.json`](../interfaces/openapi.json).**
