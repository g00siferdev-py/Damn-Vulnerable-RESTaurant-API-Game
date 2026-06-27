# Damn Vulnerable RESTaurant API Game — Solution Write-up

**Author:** g00siferdev-py  
**Achievement:** Root Access & Fixed All Vulns  
**Repository:** https://github.com/g00siferdev-py/Damn-Vulnerable-RESTaurant-API-Game

---

## TL;DR

Using an autonomous security agent built on the Project Snowball framework, I assessed the Damn Vulnerable RESTaurant API, went from a fresh `Customer` account to arbitrary command execution in five requests, and then patched all identified vulnerabilities in this fork.

---

## Exploit chain

| Step | Endpoint | Vulnerability | Result |
| ---- | -------- | ------------- | ------ |
| 1 | `POST /register` | None | Created a `Customer` account |
| 2 | `POST /token` | None | Obtained a valid bearer token |
| 3 | `PATCH /profile` | Mass assignment / role escalation | Promoted the account to `Chef` |
| 4 | `GET /admin/stats/disk` | OS command injection | Confirmed arbitrary command execution as `app` user |
| 5 | `GET /admin/stats/disk?parameters=;cat /app/.env` | OS command injection + info disclosure | Leaked database credentials |
| 6 | Direct `psql` via command injection | Hardcoded credentials | Dumped `users` and `orders` tables |

---

## Vulnerabilities found and how they were exploited

### 1. Mass assignment / privilege escalation in `PATCH /profile`

`UserUpdate` was defined with `extra=Extra.allow`, and the handler looped over every key in `user.dict()` and called `setattr` on the database record. A customer could send `{"role": "Chef"}` and immediately become a Chef.

**Fix:** Removed `extra=Extra.allow`, restricted the Pydantic model to `first_name`, `last_name`, and `phone_number`, and only set those safelisted fields on the database object.

### 2. OS command injection in `GET /admin/stats/disk`

The `parameters` query argument was concatenated directly into `"df -h " + parameters` and executed with `shell=True`. After gaining the Chef role, `; whoami`, `; cat /app/.env`, and arbitrary commands could be appended.

**Fix:** Replaced shell execution with a list-based subprocess call, used `shlex.split` to safely parse optional arguments, validated each token against an allowlist, and set `shell=False`.

### 3. Unauthenticated `/debug` endpoint

`/debug` was mounted with no authentication dependency. It returned OS info, full environment variables, current working directory, `sys.path`, disk usage, and memory usage — a goldmine for an attacker.

**Fix:** Added `Depends(get_current_user)` and `RolesBasedAuthChecker([UserRole.CHEF])`, and redacted environment variables whose keys contain sensitive substrings (`password`, `secret`, `token`, `key`, `postgres`).

### 4. JWT signature verification disabled

`apis/auth/utils/jwt_auth.py` hardcoded `VERIFY_SIGNATURE = False`, meaning any validly-shaped JWT was accepted regardless of whether it was signed with the real secret.

**Fix:** Set `VERIFY_SIGNATURE = True` so only tokens signed with `JWT_SECRET_KEY` are accepted.

### 5. Weak password-reset PIN

`text_code_utils.py` generated a 4-digit PIN with a 15-minute expiry. 4 digits is trivially brute-forceable (10,000 attempts).

**Fix:** Increased the PIN to 8 digits and reduced expiry to 10 minutes, raising brute-force cost to 100 million attempts in a much smaller window.

### 6. IDOR / broken object-level authorization on `GET /orders/{order_id}`

Any authenticated customer could read any order by changing the `order_id`, because the endpoint did not verify that the order belonged to the current user.

**Fix:** After fetching the order, the handler now checks `db_order.user_id == current_user.id` and returns `403 Forbidden` if the order does not belong to the caller.

### 7. IP-spoofable chef password reset

`GET /admin/reset-chef-password` checked `request.client.host != "127.0.0.1"`. That value can be controlled by the client through `X-Forwarded-For` headers, especially when the app runs behind a reverse proxy or in a cloud environment.

**Fix:** Replaced the IP check with a real authorization check: the caller must authenticate and have the `Chef` role via `RolesBasedAuthChecker([UserRole.CHEF])`.

### 8. Hardcoded fallback database password

`config.py` used `"password"` as the default value for `POSTGRES_PASSWORD` and did not require the variable when Postgres was selected.

**Fix:** Removed the hardcoded fallback. `POSTGRES_PASSWORD` is now required, and `DATABASE_URL` raises a `ValueError` at startup if it is missing. `JWT_VERIFY_SIGNATURE` also defaults to `True` instead of being left unset.

### 9. Unsafe bulk update helper

`update_user()` in `apis/auth/utils/utils.py` iterated over all attributes of an arbitrary input object and set them on the database user. This was an additional mass-assignment risk beyond `PATCH /profile`.

**Fix:** Restricted `update_user()` to only modify explicitly allowed fields (`role` for the admin role-update flow) and ignore private/internal attributes.

### 10. `PUT /profile` allowed updating other users

`PUT /profile` accepted a `username` body parameter and updated that user without checking whether it matched the authenticated user.

**Fix:** Added an authorization check that the supplied `username` equals `current_user.username` and limited editable fields to the same safelist.

---

## Data exfiltrated during the assessment

- Full `/etc/passwd`
- Application environment variables, including `POSTGRES_PASSWORD`
- `/app/.env` contents
- Complete source tree listing
- `users` table (usernames, password hashes, roles, phone numbers, reset codes)
- `orders` table (all order records)

All of the above was obtained from the intentionally vulnerable sandbox instance with explicit permission from the owner.

---

## Remediation summary

The patches in this fork address the root causes of every finding:

- Enforce authorization at every admin/debug endpoint.
- Use allowlists for both input fields and subprocess arguments.
- Never disable cryptographic signature verification.
- Do not ship hardcoded secrets or weak fallback credentials.
- Increase OTP entropy and shorten expiry windows.
- Verify object ownership before returning resources.
- Avoid trusting client-controlled network metadata (`request.client.host`) for authorization.

---

## How to run the fixed application

```bash
# Copy the sample environment file and set real credentials
cp .env.example .env
# Edit .env to set JWT_SECRET_KEY, POSTGRES_PASSWORD, etc.

# Run with in-memory SQLite (easiest for local testing)
DB_BACKEND=memory ./start_app.sh

# Or run with Docker Compose after setting Postgres credentials in .env
docker-compose up --build
```

---

## Tools used

- **Project Snowball** — autonomous security assessment agent
- **curl / Python requests** — manual confirmation of exploit chain
- **GitHub Codespaces** — hosting for the target sandbox instance

---

*This write-up is submitted for both the "Root Access" and "Fixed All Vulns" Hall of Fame achievements.*
