import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function StatCard({
  title,
  value,
  trend,
  trendPositive = true,
  subtitle,
  icon: Icon,
  color = 'var(--primary)',
  bgColor = 'var(--primary-light)',
}) {
  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <span className="stat-title">{title}</span>
        {Icon && (
          <div className="stat-icon-wrapper" style={{ backgroundColor: bgColor, color }}>
            <Icon size={22} />
          </div>
        )}
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-footer">
        {trend && (
          <span className={`stat-trend ${trendPositive ? 'positive' : 'negative'}`}>
            {trendPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            {trend}
          </span>
        )}
        {subtitle && <span>{subtitle}</span>}
      </div>
    </div>
  );
}
