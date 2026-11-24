import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { RoleType } from "./types";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatRoleLabel(role: RoleType): string {
  switch (role) {
    case "admin":
      return "Admin";
    case "team_member":
      return "Team Member";
    case "observer":
      return "Observer";
  }
}
