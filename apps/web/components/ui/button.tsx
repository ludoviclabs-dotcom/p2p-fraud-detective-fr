"use client";

import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1f3a6e] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "bg-[#1f3a6e] text-white hover:bg-[#0f1b33] dark:bg-[#e5a93a] dark:text-[#0f1b33] dark:hover:bg-[#d49627]",
        secondary:
          "border border-[#1f3a6e] bg-white text-[#1f3a6e] hover:bg-[#f4f6fa]",
        outline:
          "border border-[#e1e5ee] bg-white text-[#5a6478] hover:border-[#1f3a6e] hover:text-[#1f3a6e]",
        ghost: "text-[#5a6478] hover:bg-[#f4f6fa] hover:text-[#0f1b33]",
        danger: "bg-[#a23e48] text-white hover:bg-[#8a2f37]",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4",
        lg: "h-12 px-6 text-base",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  ),
);
Button.displayName = "Button";
