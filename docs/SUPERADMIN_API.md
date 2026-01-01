# Guardian Bot — SuperAdmin API Documentation

This document describes the SuperAdmin API endpoints added in this release. It includes request and response examples and step-by-step Postman instructions so you or your team can test and use the API safely.

Base URL
--------
- Default local base URL used in examples: `http://localhost:8001`
- API base path: `/api/v1`

Default development SuperAdmin (only created automatically in non-production):
- username: `superadmin`
- password: `supersecurepassword`
- email: `admin@example.com`

IMPORTANT: Change that password immediately after first login.

Authentication
--------------
The API uses JWT access tokens and refresh tokens.

- Obtain tokens: POST `/api/v1/auth/token` (form fields: `username`, `password`).
- Use access token: set header `Authorization: Bearer <access_token>` for protected endpoints.
- Refresh access token: POST `/api/v1/auth/refresh` (body: `refresh_token` as JSON or form, depending on your client).

Note: `/api/v1/auth/token` expects an OAuth2 password form (x-www-form-urlencoded or form-data). The returned JSON includes `access_token` and `refresh_token`.

Endpoints
---------

1) POST /api/v1/auth/token
---------------------------
Description: Obtain access and refresh tokens using username/password.

Request (x-www-form-urlencoded / form-data):
- username: string
- password: string

curl example:

```bash
curl -X POST \
  -F "username=superadmin" \
  -F "password=supersecurepassword" \
  http://localhost:8001/api/v1/auth/token
```

Successful Response (200):

```json
{
  "access_token": "<JWT_ACCESS_TOKEN>",
  "refresh_token": "<JWT_REFRESH_TOKEN>",
  "token_type": "bearer",
  "user": {
    "id": "<user_id>",
    "username": "superadmin",
    "email": "admin@example.com",
    "is_superadmin": true,
    "permissions": {"view_dashboard": true, "manage_admins": true}
  }
}
```

Errors:
- 401: Incorrect username or password
- 400: Inactive user

2) POST /api/v1/auth/refresh
-----------------------------
Description: Exchange a valid refresh token for a new access token and refresh token pair.

Request (JSON):

```json
{ "refresh_token": "<JWT_REFRESH_TOKEN>" }
```

curl example:

```bash
curl -X POST http://localhost:8001/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<JWT_REFRESH_TOKEN>"}'
```

Successful Response (200): same structure as `/auth/token`.

Errors:
- 401: Invalid or expired refresh token

3) GET /api/v1/superadmin/stats
--------------------------------
Description: Return aggregated statistics across all groups (SuperAdmin only).

Headers:
- Authorization: `Bearer <access_token>`

curl example:

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN" http://localhost:8001/api/v1/superadmin/stats
```

Sample Response (200):

```json
{
  "total_groups": 12,
  "total_members": 4521,
  "total_bans": 123,
  "total_warnings": 542,
  "active_moderations": 665,
  "messages_today": 10234
}
```

4) GET /api/v1/superadmin/admins
--------------------------------
Description: List admin users (SuperAdmin only).

Query parameters:
- skip (optional)
- limit (optional)

Headers:
- Authorization: `Bearer <access_token>`

curl example:

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN" "http://localhost:8001/api/v1/superadmin/admins?skip=0&limit=100"
```

Sample Response (200):

```json
[
  {
    "id": "653a1b...",
    "username": "superadmin",
    "email": "admin@example.com",
    "is_active": true,
    "is_superadmin": true,
    "permissions": {"view_dashboard": true},
    "created_at": "2025-12-12T00:00:00Z",
    "last_login": null
  }
]
```

5) POST /api/v1/superadmin/admins
---------------------------------
Description: Create a new admin user (SuperAdmin only).

Headers:
- Authorization: `Bearer <access_token>`
- Content-Type: `application/json`

Request body (JSON):

```json
{
  "username": "friend",
  "email": "friend@example.com",
  "password": "strongpassword123",
  "is_superadmin": true,
  "permissions": {"manage_groups": true, "view_logs": true}
}
```

curl example:

```bash
curl -X POST http://localhost:8001/api/v1/superadmin/admins \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"friend","email":"friend@example.com","password":"strongpassword123","is_superadmin":true}'
```

Successful Response (201/200): returns created admin details (see AdminUserResponse schema above).

Validation errors: 400 if username/email already exists or invalid permissions provided.

6) PUT /api/v1/superadmin/admins/{user_id}
-----------------------------------------
Description: Update an admin user (SuperAdmin only).

Headers:
- Authorization: `Bearer <access_token>`
- Content-Type: `application/json`

Request body (JSON) — include only fields you want to update:

```json
{
  "email": "new@example.com",
  "password": "newstrongpass",
  "is_active": true,
  "is_superadmin": false,
  "permissions": {"manage_groups": true}
}
```

curl example:

```bash
curl -X PUT http://localhost:8001/api/v1/superadmin/admins/653a1b... \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"permissions":{"manage_groups":true}}'
```

Response: updated admin object (200). Important: API prevents deleting/demoting the last superadmin.

7) DELETE /api/v1/superadmin/admins/{user_id}
--------------------------------------------
Description: Delete an admin user (SuperAdmin only). Cannot delete the last SuperAdmin.

Headers:
- Authorization: `Bearer <access_token>`

curl example:

```bash
curl -X DELETE http://localhost:8001/api/v1/superadmin/admins/653a1b... \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Response: `{"message":"Admin user deleted"}` on success.

8) GET /api/v1/superadmin/groups
--------------------------------
Description: List groups in the system (SuperAdmin only). Supports pagination with `skip` and `limit`.

Headers:
- Authorization: `Bearer <access_token>`

Sample response: array of group objects as stored in DB (example):

```json
[
  {
    "group_id": -1001234567890,
    "group_name": "Example Group",
    "welcome_msg": "Welcome!",
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

Postman: Step-by-step (recommended)
----------------------------------

1) Create a Postman Environment

- Add variables:
  - baseUrl = `http://localhost:8001`
  - username = `superadmin`
  - password = `supersecurepassword`
  - accessToken = `` (empty)
  - refreshToken = `` (empty)

2) Create a request to get tokens (Auth / Token)

- Method: POST
- URL: `{{baseUrl}}/api/v1/auth/token`
- Body: form-data or x-www-form-urlencoded
  - username = `{{username}}`
  - password = `{{password}}`

3) Extract tokens automatically

- In Postman, in the Tests tab for that request add a small script to store tokens in environment variables:

```javascript
const data = pm.response.json();
pm.environment.set('accessToken', data.access_token);
pm.environment.set('refreshToken', data.refresh_token);
```

4) Create a request that needs auth

- Add the Authorization header: `Authorization: Bearer {{accessToken}}`
- Example: GET `{{baseUrl}}/api/v1/superadmin/stats`

5) Refreshing access token

- Create POST `{{baseUrl}}/api/v1/auth/refresh` with JSON body: `{ "refresh_token": "{{refreshToken}}" }`
- In Tests tab, update accessToken and refreshToken from response.

6) Managing admins

- Use the access token (Authorization header) to call the `superadmin/admins` endpoints.
- Create admin: POST `{{baseUrl}}/api/v1/superadmin/admins` with JSON body (see examples above).

Common Postman tips
--------------------
- Use environment variables for `{{baseUrl}}` and tokens so you can switch between local and production easily.
- For `/auth/token` remember to use form-data or x-www-form-urlencoded (not a JSON body) since OAuth2PasswordRequestForm expects form-encoded fields.
- If you receive 401/403 responses:
  - Confirm `Authorization` header is `Bearer <token>` and token not expired.
  - Confirm the user has `is_superadmin:true` for SuperAdmin-only endpoints.

Security notes
--------------
- Never commit `.env` or tokens to version control.
- Use strong `API_SECRET_KEY` in production (set in `.env`).
- Consider rotating refresh tokens and using a token blacklist to support logout and revoke.

Appendix: example Postman Tests code snippets
-------------------------------------------

Store tokens after login (Tests tab):

```javascript
if (pm.response.code === 200) {
  const json = pm.response.json();
  pm.environment.set('accessToken', json.access_token);
  pm.environment.set('refreshToken', json.refresh_token);
}
```

Automatic Authorization helper (Pre-request script for other requests):

```javascript
// Put this in Pre-request Script for protected requests
if (!pm.environment.get('accessToken')) {
   // optionally throw or call the token endpoint programmatically
   console.log('accessToken missing - please login first');
}
```

Troubleshooting
---------------
- 401 Unauthorized: token missing or invalid — fetch new tokens with `/auth/token` or `/auth/refresh`.
- 403 Forbidden: user lacks SuperAdmin privileges — check the `is_superadmin` flag on the admin user document in MongoDB.
- 500 Server Error: check server logs (`journalctl` or uvicorn console) for stack traces and missing configuration like DB connections.

If you'd like, I can export a Postman Collection (JSON) pre-filled with these requests and environment variables so you can import it directly. Tell me whether you prefer a minimal collection (auth + stats + admin CRUD) or a full collection including groups and member operations.

---
Version: 1.0 — SuperAdmin API docs
