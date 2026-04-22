import { classNames } from '../../utils/formatters';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export function Button({
  children, variant = 'primary', size = 'md', isLoading = false,
  leftIcon, rightIcon, className, disabled, ...props
}: ButtonProps) {
  const variants = {
    primary: 'bg-accent text-bg hover:bg-accent/90 disabled:opacity-40',
    secondary: 'bg-surface border border-border text-text-primary hover:border-border-hover disabled:opacity-40',
    danger: 'bg-danger/10 text-danger border border-danger/20 hover:bg-danger/20 disabled:opacity-40',
    ghost: 'text-text-secondary hover:text-text-primary hover:bg-surface disabled:opacity-40',
  };
  const sizes = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-5 py-2.5 text-sm',
  };

  return (
    <button
      className={classNames(
        'inline-flex items-center justify-center font-medium rounded-lg transition-colors cursor-pointer',
        'disabled:cursor-not-allowed focus:outline-none',
        variants[variant], sizes[size], className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
      {!isLoading && leftIcon && <span className="mr-2">{leftIcon}</span>}
      {children}
      {!isLoading && rightIcon && <span className="ml-2">{rightIcon}</span>}
    </button>
  );
}
