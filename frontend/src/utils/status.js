const APPROVED_STATUSES = new Set(['تاييد شده', 'تایید شده', 'approved']);
const REGISTERED_STATUSES = new Set(['ثبت شده', 'registered']);
const PENDING_STATUSES = new Set(['معلق', 'pending', 'در انتظار', 'جاری']);
const REJECTED_STATUSES = new Set(['عودت شده', 'rejected', 'رد شده']);

export function getStatusVisuals(status) {
  if (APPROVED_STATUSES.has(status)) {
    return { color: '#2E7D32', bgColor: '#E8F5E9', muiColor: 'success', kind: 'approved' };
  }
  if (REGISTERED_STATUSES.has(status)) {
    return { color: '#66BB6A', bgColor: '#F1F8E9', muiColor: 'success', kind: 'registered' };
  }
  if (PENDING_STATUSES.has(status)) {
    return { color: '#FF9800', bgColor: '#FFF8E1', muiColor: 'warning', kind: 'pending' };
  }
  if (REJECTED_STATUSES.has(status)) {
    return { color: '#F44336', bgColor: '#FCE4EC', muiColor: 'error', kind: 'rejected' };
  }
  return { color: '#2196F3', bgColor: '#E3F2FD', muiColor: 'info', kind: 'default' };
}
