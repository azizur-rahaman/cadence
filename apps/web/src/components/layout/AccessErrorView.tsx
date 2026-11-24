"use client";

import { ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

interface AccessErrorViewProps {
  status: number;
  code?: string;
  message: string;
  requestId?: string;
  onReset?: () => void;
  resetLabel?: string;
}

export function AccessErrorView({
  status,
  code,
  message,
  requestId,
  onReset,
  resetLabel = "Return to your team",
}: AccessErrorViewProps) {
  const title =
    status === 403
      ? "Access forbidden (403)"
      : status === 404
        ? "Team not found (404)"
        : `Request error (${status})`;

  return (
    <Card className="mx-auto mt-10 max-w-lg border-danger/30 bg-surface">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-danger-bg text-danger">
          <ShieldAlert className="h-5 w-5" aria-hidden="true" />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-base font-semibold text-foreground">{title}</h2>
          <p className="mt-1 text-sm text-[#475569]">{message}</p>
          {code || requestId ? (
            <p className="mt-2 font-mono text-xs text-[#64748B]">
              {code ? `Code: ${code}` : null}
              {code && requestId ? " · " : null}
              {requestId ? `Request ID: ${requestId}` : null}
            </p>
          ) : null}
          {onReset ? (
            <div className="mt-4">
              <Button variant="secondary" size="sm" onClick={onReset}>
                {resetLabel}
              </Button>
            </div>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
