/**
 * Staff-facing UI matches backend RBAC: role on /auth/me is staff | admin.
 */
export function hasStaffAccess(user) {
  const r = user?.role
  return r === 'staff' || r === 'admin'
}
