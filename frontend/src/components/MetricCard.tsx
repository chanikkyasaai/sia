import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string;
  icon?: LucideIcon;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

export default function MetricCard({ label, value, icon: Icon, variant = 'default' }: MetricCardProps) {
  const variantStyles = {
    default: 'bg-[#E5E5E5] text-[#000000]',
    success: 'bg-[#22C55E]/10 text-[#22C55E] border-[#22C55E]',
    warning: 'bg-[#FCA311]/10 text-[#FCA311] border-[#FCA311]',
    danger: 'bg-[#EF4444]/10 text-[#EF4444] border-[#EF4444]',
  };

  return (
    <div className={`${variantStyles[variant]} rounded-2xl px-6 py-4 flex items-center justify-between shadow-sm ${variant !== 'default' ? 'border-2' : ''}`}>
      <div>
        <p className="font-['Inter'] text-xs opacity-70 mb-1">{label}</p>
        <p className="font-['Inter'] font-semibold text-xl">{value}</p>
      </div>
      {Icon && <Icon size={28} strokeWidth={2} />}
    </div>
  );
}
