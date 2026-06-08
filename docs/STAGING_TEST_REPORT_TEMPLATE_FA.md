# قالب گزارش تست Staging

این فایل template گزارش اجرای staging است. مقدار واقعی secret، password، token، API key یا connection string را در این گزارش ننویسید.

## 1. مشخصات اجرا

- تاریخ تست: `<YYYY-MM-DD>`
- ساعت شروع: `<HH:MM>`
- ساعت پایان: `<HH:MM>`
- مسئول تست: `<NAME_OR_ROLE>`
- ناظر/تاییدکننده: `<NAME_OR_ROLE>`
- branch: `<BRANCH_NAME>`
- commit: `<COMMIT_SHA>`
- build/artifact backend: `<BACKEND_ARTIFACT_OR_TAG>`
- build/artifact frontend: `<FRONTEND_ARTIFACT_OR_TAG>`
- تصمیم نهایی:
  - [ ] pass
  - [ ] pass with risk
  - [ ] fail

## 2. مشخصات محیط Staging

- backend URL: `<STAGING_BACKEND_URL>`
- frontend URL: `<STAGING_FRONTEND_URL>`
- KPI URL: `<STAGING_KPI_URL>`
- database name: `<STAGING_DB_NAME>`
- database host category: `<LOCAL_NETWORK_OR_MANAGED_DB>`
- reverse proxy: `<YES_NO_AND_NAME>`
- log location backend: `<BACKEND_LOG_PATH>`
- log location frontend/proxy: `<FRONTEND_OR_PROXY_LOG_PATH>`
- log location KPI: `<KPI_LOG_PATH>`

Env review:

- [ ] `FLASK_ENV=staging`
- [ ] `FLASK_DEBUG=0`
- [ ] `SECRET_KEY` set and not printed
- [ ] `JWT_SECRET_KEY` set and not printed
- [ ] `DATABASE_URL` points to staging DB
- [ ] `CORS_ALLOWED_ORIGINS` contains only staging frontend origin
- [ ] `VITE_API_BASE_URL` points to staging backend
- [ ] `KPI_API_KEY` set and not printed

## 3. Migration Result

Commands executed:

```text
flask db current
flask db upgrade
flask db current
```

Result:

- [ ] pass
- [ ] fail
- revision before: `<REVISION_BEFORE>`
- revision after: `<REVISION_AFTER>`
- notes: `<NOTES>`

Schema checks:

- [ ] active batch fields exist.
- [ ] `AuditLog` table exists.
- [ ] `ImportBatch.published_at` exists.
- [ ] `ImportBatch.replaced_by_batch_id` exists.
- [ ] no migration was run against production DB.

## 4. Backend Smoke Result

| Check | Expected | Result | Notes |
|---|---|---|---|
| `POST /auth/login` staff/admin | 200 | `<PASS_FAIL>` | `<NOTES>` |
| `POST /auth/login` contractor | 200 | `<PASS_FAIL>` | `<NOTES>` |
| `GET /auth/me` | 200 | `<PASS_FAIL>` | `<NOTES>` |
| `GET /invoices/` contractor scoped | 200 and scoped data | `<PASS_FAIL>` | `<NOTES>` |
| `GET /invoices/filters/options` | 200 | `<PASS_FAIL>` | `<NOTES>` |
| `POST /admin/uploads` contractor | 403 | `<PASS_FAIL>` | `<NOTES>` |
| `POST /admin/uploads` staff/admin no file | validation error | `<PASS_FAIL>` | `<NOTES>` |

## 5. Frontend Smoke Result

| Check | Expected | Result | Notes |
|---|---|---|---|
| Login page opens | visible form | `<PASS_FAIL>` | `<NOTES>` |
| Contractor login | redirects to invoices/dashboard | `<PASS_FAIL>` | `<NOTES>` |
| Staff/admin login | admin access available | `<PASS_FAIL>` | `<NOTES>` |
| Dashboard | invoice list loads | `<PASS_FAIL>` | `<NOTES>` |
| Invoice detail | detail rows load | `<PASS_FAIL>` | `<NOTES>` |
| Admin upload page | visible for staff/admin | `<PASS_FAIL>` | `<NOTES>` |
| Admin upload page for contractor | blocked/redirected | `<PASS_FAIL>` | `<NOTES>` |

## 6. Import Result

| Import | Test file | Expected | Result | Batch ID | Notes |
|---|---|---|---|---|---|
| `codtafsiltamin` | `<FILE_NAME>` | success | `<PASS_FAIL>` | `<BATCH_ID>` | `<NOTES>` |
| `contractors-1` | `<FILE_NAME>` | success | `<PASS_FAIL>` | `<BATCH_ID>` | `<NOTES>` |
| `contractors-2` | `<FILE_NAME>` | success | `<PASS_FAIL>` | `<BATCH_ID>` | `<NOTES>` |
| invalid header file | `<FILE_NAME>` | controlled failure | `<PASS_FAIL>` | `<BATCH_ID_OR_NA>` | `<NOTES>` |
| second import | `<FILE_NAME>` | active batch switch | `<PASS_FAIL>` | `<BATCH_ID>` | `<NOTES>` |

Data checks:

- [ ] Active rows belong to latest successful batch.
- [ ] Failed import did not replace active data.
- [ ] `ImportError` rows are visible for invalid file.
- [ ] Uploaded file names or sensitive data are not stored in audit.

## 7. Rollback Result

| Check | Expected | Result | Notes |
|---|---|---|---|
| Rollback to previous `codtafsiltamin` batch | active contractor rows switch | `<PASS_FAIL>` | `<NOTES>` |
| Rollback to previous `contractors-1` batch | active summaries/details switch | `<PASS_FAIL>` | `<NOTES>` |
| Rollback to previous `contractors-2` batch | active details switch | `<PASS_FAIL>` | `<NOTES>` |
| Contractor rollback attempt | 403 | `<PASS_FAIL>` | `<NOTES>` |
| Invalid rollback target | controlled failure | `<PASS_FAIL>` | `<NOTES>` |
| Audit success row | present | `<PASS_FAIL>` | `<NOTES>` |
| Audit failure row | present | `<PASS_FAIL>` | `<NOTES>` |

## 8. Backup/Restore Result

Backup:

- command template used: `pg_dump -h <DB_HOST> -p <DB_PORT> -U <DB_USER> -Fc -f <BACKUP_FILE> <DB_NAME>`
- backup file location: `<BACKUP_FILE_SAFE_LOCATION>`
- result:
  - [ ] pass
  - [ ] fail

Restore drill:

- restore DB name: `<RESTORE_DB_NAME>`
- command template used: `pg_restore -h <DB_HOST> -p <DB_PORT> -U <DB_USER> -d <RESTORE_DB_NAME> <BACKUP_FILE>`
- result:
  - [ ] pass
  - [ ] fail

Checks:

- [ ] restore was not run against production.
- [ ] restored DB opens.
- [ ] key record counts match expected values.
- [ ] active batch state matches backup point.

## 9. Security Checks

| Check | Expected | Result | Notes |
|---|---|---|---|
| CORS staging origin | allowed | `<PASS_FAIL>` | `<NOTES>` |
| CORS unknown origin | not allowed | `<PASS_FAIL>` | `<NOTES>` |
| contractor to admin endpoint | 403 | `<PASS_FAIL>` | `<NOTES>` |
| rollback contractor attempt | 403 | `<PASS_FAIL>` | `<NOTES>` |
| stale demoted staff token | 403 | `<PASS_FAIL>` | `<NOTES>` |
| deleted user token | rejected | `<PASS_FAIL>` | `<NOTES>` |
| inactive contractor access token | rejected | `<PASS_FAIL>` | `<NOTES>` |
| inactive contractor refresh token | rejected | `<PASS_FAIL>` | `<NOTES>` |
| response secret leakage | none | `<PASS_FAIL>` | `<NOTES>` |
| Gitleaks/security workflow | pass or scheduled | `<PASS_FAIL>` | `<NOTES>` |

## 10. KPI Result

| Check | Expected | Result | Notes |
|---|---|---|---|
| `GET /api/health` | healthy | `<PASS_FAIL>` | `<NOTES>` |
| KPI request without key | rejected | `<PASS_FAIL>` | `<NOTES>` |
| KPI yearly query | returns data/empty valid response | `<PASS_FAIL>` | `<NOTES>` |
| CSV export | file returned | `<PASS_FAIL>` | `<NOTES>` |
| XLSX export | file returned | `<PASS_FAIL>` | `<NOTES>` |

## 11. Defects Found

| ID | Severity | Area | Description | Owner | Status |
|---|---|---|---|---|---|
| `<DEFECT_ID>` | `<LOW_MED_HIGH_BLOCKER>` | `<AREA>` | `<DESCRIPTION>` | `<OWNER>` | `<OPEN_FIXED_ACCEPTED>` |

## 12. Known Risks Accepted

| Risk | Severity | Reason accepted | Follow-up |
|---|---|---|---|
| `<RISK>` | `<LOW_MED_HIGH>` | `<REASON>` | `<FOLLOW_UP>` |

## 13. Next Actions

- [ ] `<ACTION_1>`
- [ ] `<ACTION_2>`
- [ ] `<ACTION_3>`

## 14. Sign-Off

- QA lead decision: `<PASS_PASS_WITH_RISK_FAIL>`
- Release manager decision: `<PASS_PASS_WITH_RISK_FAIL>`
- Security reviewer decision: `<PASS_PASS_WITH_RISK_FAIL>`
- Approved for production preparation:
  - [ ] yes
  - [ ] no
- Final notes: `<NOTES>`
