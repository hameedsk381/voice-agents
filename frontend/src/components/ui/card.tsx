import * as React from "react"

export function Card({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div
            className={`rounded-xl border border-white/10 bg-[#0f0f10] text-gray-100 shadow-sm ${className || ""}`}
            {...props}
        >
            {children}
        </div>
    )
}

export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={`flex flex-col space-y-1.5 p-6 ${className || ""}`} {...props}>
            {children}
        </div>
    )
}

export function CardTitle({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <h3 className={`font-semibold leading-none tracking-tight ${className || ""}`} {...props}>
            {children}
        </h3>
    )
}

export function CardContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div className={`p-6 pt-0 ${className || ""}`} {...props}>
            {children}
        </div>
    )
}
