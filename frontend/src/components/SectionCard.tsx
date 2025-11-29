import { ReactNode } from 'react';

interface SectionCardProps {
  title?: string;
  children: ReactNode;
  className?: string;
}

export default function SectionCard({ title, children, className = '' }: SectionCardProps) {
  return (
    <div className={`bg-[#E5E5E5] rounded-2xl p-6 shadow-md ${className}`}>
      {title && (
        <h3 className="font-['Poppins'] font-semibold text-[#14213D] text-lg mb-4">
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
