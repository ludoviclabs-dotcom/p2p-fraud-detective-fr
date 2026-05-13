import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export const Input = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement>
>(({ className, type = "text", ...props }, ref) => (
  <input
    ref={ref}
    type={type}
    className={cn(
      "h-10 w-full rounded-md border border-[#e1e5ee] bg-white px-3 text-sm",
      "placeholder:text-[#9aa3b2] focus-visible:outline-none focus-visible:ring-2",
      "focus-visible:ring-[#1f3a6e] focus-visible:ring-offset-0",
      "disabled:cursor-not-allowed disabled:opacity-50",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";
