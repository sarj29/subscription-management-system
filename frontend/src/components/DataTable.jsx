import React, { useState, useMemo } from 'react';
import { Search, ChevronLeft, ChevronRight, Inbox } from 'lucide-react';

export default function DataTable({
  columns,
  data = [],
  loading = false,
  searchPlaceholder = 'Search...',
  searchField,
  filterOptions = [],
  filterKey,
  onFilterChange,
  actions,
  emptyMessage = 'No records found',
  pageSize = 8,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [activeFilter, setActiveFilter] = useState('all');

  const filteredData = useMemo(() => {
    let result = [...data];

    // Filter dropdown
    if (filterKey && activeFilter !== 'all') {
      result = result.filter((item) => String(item[filterKey]) === activeFilter);
    }

    // Text Search
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      result = result.filter((item) => {
        if (searchField && item[searchField]) {
          return String(item[searchField]).toLowerCase().includes(q);
        }
        return Object.values(item).some(
          (val) => val && String(val).toLowerCase().includes(q)
        );
      });
    }

    return result;
  }, [data, searchTerm, activeFilter, filterKey, searchField]);

  const totalPages = Math.ceil(filteredData.length / pageSize) || 1;
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, currentPage, pageSize]);

  return (
    <div className="card-table">
      <div className="table-toolbar">
        <div className="table-search-group">
          <div className="search-bar" style={{ width: '100%' }}>
            <Search size={16} color="var(--text-muted)" />
            <input
              type="text"
              placeholder={searchPlaceholder}
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
            />
          </div>

          {filterOptions.length > 0 && (
            <select
              className="table-select"
              value={activeFilter}
              onChange={(e) => {
                setActiveFilter(e.target.value);
                setCurrentPage(1);
                if (onFilterChange) onFilterChange(e.target.value);
              }}
            >
              <option value="all">All Statuses</option>
              {filterOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          )}
        </div>

        {actions && <div className="header-actions">{actions}</div>}
      </div>

      <div className="data-table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col, idx) => (
                <th key={idx} style={{ width: col.width, textAlign: col.align || 'left' }}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={columns.length}>
                  <div className="state-container">
                    <div className="spinner" />
                    <p style={{ color: 'var(--text-muted)' }}>Loading records...</p>
                  </div>
                </td>
              </tr>
            ) : paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length}>
                  <div className="state-container">
                    <div className="empty-icon">
                      <Inbox size={32} />
                    </div>
                    <p style={{ fontWeight: 600 }}>{emptyMessage}</p>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Try adjusting your search criteria or add a new record.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rIdx) => (
                <tr key={row.id || rIdx}>
                  {columns.map((col, cIdx) => (
                    <td key={cIdx} style={{ textAlign: col.align || 'left' }}>
                      {col.render ? col.render(row) : row[col.accessor]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {!loading && filteredData.length > 0 && (
        <div className="table-pagination">
          <span>
            Showing {(currentPage - 1) * pageSize + 1} to{' '}
            {Math.min(currentPage * pageSize, filteredData.length)} of {filteredData.length} records
          </span>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              className="btn btn-outline"
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => p - 1)}
              style={{ padding: '0.35rem 0.65rem' }}
            >
              <ChevronLeft size={16} /> Prev
            </button>
            <button
              className="btn btn-outline"
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => p + 1)}
              style={{ padding: '0.35rem 0.65rem' }}
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
