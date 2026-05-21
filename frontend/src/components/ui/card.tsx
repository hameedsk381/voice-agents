import * as React from "react"

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    glow?: boolean;
}

export function Card({ className, children, glow = false, ...props }: CardProps) {
    return (
        <div
            className={`glass-card p-6 ${glow ? "hover:shadow-[0_0_30px_rgba(0,212,170,0.08)]" : ""} ${className || ""}`}
            {...props}
        >
            {children}
        </div>
    )
}

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={`flex flex-col space-y-1.5 mb-4 ${className || ""}`} {...props}>
            {children}
        </div>
    )
}

export function CardTitle({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <h3 className={`text-base font-semibold leading-none tracking-tight text-[var(--text-primary)] ${className || ""}`} {...props}>
            {children}
        </h3>
    )
}

export function CardDescription({ className, children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
    return (
        <p className={`text-xs text-[var(--text-secondary)] ${className || ""}`} {...props}>
            {children}
        </p>
    )
}

export function CardContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={`text-sm text-[var(--text-secondary)] ${className || ""}`} {...props}>
            {children}
        </div>
    )
}

export function CardFooter({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={`flex items-center pt-4 mt-4 border-t border-[var(--border-subtle)] ${className || ""}`} {...props}>
            {children}
        </div>
    )
}
