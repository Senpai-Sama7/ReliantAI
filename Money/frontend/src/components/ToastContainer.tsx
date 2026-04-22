// Toast notification container — renders in a fixed overlay
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';
import type { Toast, ToastVariant } from '../hooks/useToast';

const iconMap: Record<ToastVariant, React.ReactNode> = {
  success: <CheckCircle className="w-4 h-4 shrink-0" />,
  error: <XCircle className="w-4 h-4 shrink-0" />,
  warning: <AlertTriangle className="w-4 h-4 shrink-0" />,
  info: <Info className="w-4 h-4 shrink-0" />,
};

const colorMap: Record<ToastVariant, string> = {
  success: 'border-green-500/40 bg-green-950/80 text-green-200',
  error: 'border-red-500/40 bg-red-950/80 text-red-200',
  warning: 'border-yellow-500/40 bg-yellow-950/80 text-yellow-200',
  info: 'border-blue-500/40 bg-blue-950/80 text-blue-200',
};

interface Props {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}

export default function ToastContainer({ toasts, onDismiss }: Props) {
  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-6 right-6 z-[9999] flex flex-col gap-2 max-w-sm w-full"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
    >
      {toasts.map(t => (
        <div
          key={t.id}
          className={`flex items-start gap-3 px-4 py-3 border backdrop-blur-sm rounded-sm text-sm font-body animate-slide-up ${colorMap[t.variant]}`}
        >
          {iconMap[t.variant]}
          <span className="flex-1">{t.message}</span>
          <button
            onClick={() => onDismiss(t.id)}
            className="opacity-60 hover:opacity-100 transition-opacity"
            aria-label="Dismiss"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}
