"use client";

import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    const base =
      variant === "primary" || variant === "danger" ? "fx-btn" : "fx-btn-ghost";
    return (
      <button
        ref={ref}
        className={cn(base, size === "sm" ? "sm" : "", className)}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";
