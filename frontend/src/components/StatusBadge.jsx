import React from 'react';

export default function StatusBadge({ status }) {
  if (!status) return null;
  const s = String(status).toLowerCase();

  let badgeClass = 'badge-draft';
  if (['active', 'paid'].includes(s)) badgeClass = 'badge-active';
  else if (['confirmed'].includes(s)) badgeClass = 'badge-confirmed';
  else if (['quotation', 'paused'].includes(s)) badgeClass = 'badge-quotation';
  else if (['closed', 'cancelled', 'reversed'].includes(s)) badgeClass = 'badge-closed';
  else if (['recorded'].includes(s)) badgeClass = 'badge-recorded';

  return (
    <span className={`badge ${badgeClass}`}>
      <span className="status-dot" style={{ backgroundColor: 'currentColor' }} />
      {s.charAt(0).toUpperCase() + s.slice(1)}
    </span>
  );
}
