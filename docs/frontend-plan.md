## Technology Stack
- React 18 with Vite setup.
- UI library: MUI or Ant Design (choose based on existing licensing).
- State & data:
  - React Query for API interaction + caching.
  - React Router for navigation (`/login`, `/dashboard`, `/invoice/:coverNumber`).
- Localization: `dayjs` with Jalali plugin, `react-i18next` for Persian strings.

## Pages & Components

### `/login`
- Form inputs: username, password.
- Validation, disabled state during request.
- On success, store tokens in `localStorage` (refresh) & memory (access).
- Error messaging for invalid credentials.

### `/dashboard`
- Guarded route (requires auth).
- Layout:
  - Header with contractor name, logout button.
  - Summary cards: total invoices, approved, pending, total amounts.
  - Filters panel:
    - Date range picker (Jalali).
    - Status multi-select.
    - Search input (cover number / automation number / supplier name).
  - Data table:
    - Columns: cover number, automation number, invoice date, summary status, gross amount, detail count.
    - Row actions: view details, export.
    - Pagination controls.

### `/invoice/:coverNumber`
- Fetch summary + detail from `/invoices/<cover_number>`.
- Display summary metadata (dates, amounts, permit numbers).
- Detail table listing each line from `invoices_detail`.
- Timeline or stepper showing statuses (summary vs detail).
- Attachments placeholder for future.

### Shared Components
- `AuthProvider` + hook for tokens and refresh handling.
- `FiltersBar`, `SummaryCard`, `InvoiceTable`, `StatusChip`.
- `ProtectedRoute` wrapper to redirect unauthenticated users.

## UX Considerations
- Right-to-left layout across app.
- Persist filters in URL query params.
- Loading & empty states for tables.
- Error boundary to capture API errors and show fallback message.

## Testing
- Component tests (React Testing Library) for login and dashboard filtering logic.
- Cypress e2e covering login, invoice listing, detail navigation.

## Build & Deployment
- Environment variables via `.env` (`VITE_API_BASE_URL`).
- Production build served via Flask static or separate CDN.







