import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex h-10 shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-full px-4 py-2 text-sm font-semibold transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-45 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow-[0_12px_34px_rgba(255,8,204,0.28)] hover:bg-primary/90 hover:shadow-[0_16px_42px_rgba(255,8,204,0.36)]",
        secondary:
          "bg-secondary text-secondary-foreground shadow-[0_12px_34px_rgba(0,174,239,0.22)] hover:bg-secondary/85",
        outline:
          "border border-white/15 bg-white/[0.06] text-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] hover:border-primary/55 hover:bg-white/[0.10] hover:text-white",
        ghost: "text-muted-foreground hover:bg-white/[0.08] hover:text-white",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        accent:
          "bg-accent text-accent-foreground shadow-[0_12px_34px_rgba(255,166,3,0.24)] hover:bg-accent/90",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-6",
        icon: "size-10 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
