"use client";

import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2f6bff] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "bg-[#2f6bff] text-white shadow-sm shadow-[#2f6bff]/20 hover:bg-[#2457d6]",
        secondary:
          "border border-[#2f6bff] bg-white text-[#2f6bff] hover:bg-[#eaf1ff]",
        outline:
          "border border-[#e6ebf2] bg-white text-[#667085] hover:border-[#2f6bff] hover:text-[#2f6bff]",
        ghost: "text-[#667085] hover:bg-[#f7f9fc] hover:text-[#111827]",
        danger: "bg-[#e5484d] text-white hover:bg-[#c9363b]",
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
