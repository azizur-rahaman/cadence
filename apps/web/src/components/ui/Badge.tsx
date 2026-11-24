import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export type BadgeVariant = "neutral" | "success" | "warning" | "danger" | "info";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  neutral: "bg-surface-secondary text-[#334155] border-border",
  success: "bg-success-bg text-[#166534] border-[#BBF7D0]",
  warning: "bg-warning-bg text-[#92400E] border-[#FDE68A]",
  danger: "bg-danger-bg text-[#991B1B] border-[#FECACA]",
  info: "bg-info-bg text-[#1E40AF] border-[#BFDBFE]",
};

export function Badge({ className, variant = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        VARIANT_CLASSES[variant],
        className,
      )}
      {...props}
    />
  );
}
