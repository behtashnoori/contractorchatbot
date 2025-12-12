## Credential Management
- Generate unique username per contractor (`ct-<detail_code>`), enforce lowercase.
- Initial password: 12-char random (letters + digits); delivered to contractor via secure channel (encrypted email or SMS).
- Force password reset on first login (`users.must_change_password` flag).
- Store passwords using Argon2id hash with per-user salt.
- Implement account lockout after 5 failed attempts (15-minute cooldown).
- Audit login attempts: `auth_logs(user_id, ip, user_agent, success, timestamp)`.

## Access Control
- Contractors scoped by `contractor_id` injected from token.
- Admin role for internal staff (separate `admins` table) with ability to upload files and view batch status.
- Future multi-role support (e.g., finance, supervisor) via role-based claims in JWT.

## Upload Workflow
- Admin UI requires MFA (TOTP).
- Validate Excel headers; block upload if unexpected columns detected.
- Scan files for malware using Windows Defender CLI (if required by policy).
- Keep last 5 batches accessible for rollback; archive older ones.
- Provide download of processed dataset as CSV for audit.

## Observability
- Structured logging with correlation id (`batch_id`, `request_id`).
- Metrics:
  - Import success/failure counts (`Prometheus` or `StatsD`).
  - API latency per endpoint.
  - Login failure rate.
- Alerts when import failure occurs or login failures spike.

## Backup & Recovery
- Nightly database backups (pg_dump) stored in secure storage with 30-day retention.
- Optionally version uploaded Excel files in object storage (Azure Blob/S3).
- Disaster recovery document specifying steps to restore DB and reprocess latest batches.

## Compliance & Privacy
- Store minimal personal data (contractor contact info optional).
- Log access to invoice data, retain logs for 1 year.
- Provide mechanism to deactivate contractor accounts quickly.
- HTTPS enforced end-to-end; use company-issued TLS certificates.

## Testing & QA
- Run security scans (Bandit for Python, npm audit).
- Pen-test login and upload endpoints.
- Verify rate limiting and lockout policies in staging before release.







