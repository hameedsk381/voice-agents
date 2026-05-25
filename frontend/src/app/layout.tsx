import type { Metadata } from "next";
import { Inter, Sora, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Voise AI — AI Voice Agents Replace Call Centers",
  description:
    "Deploy AI outbound call agents for payment reminders, lead qualification, and appointment confirmation. Replace your call center with AI that speaks every Indian language.",
  keywords: [
    "AI voice agents",
    "outbound call automation",
    "AI call center",
    "voice AI for business",
    "payment reminder calls",
    "lead qualification AI",
    "Indian language voice AI",
  ],
  openGraph: {
    title: "Voise AI — AI Voice Agents Replace Call Centers",
    description: "Replace your call center with AI agents that speak every Indian language.",
    type: "website",
    locale: "en_IN",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en-IN" suppressHydrationWarning className={cn("font-body", inter.variable)}>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('voise-theme');document.documentElement.classList.add(t==='light'?'light':'dark');document.documentElement.style.colorScheme=t==='light'?'light':'dark';}catch(e){document.documentElement.classList.add('dark');}})();`,
          }}
        />
      </head>
      <body className={`${geistMono.variable} ${sora.variable} antialiased`}>
        <ThemeProvider>
          <TooltipProvider>
            <AuthProvider>{children}</AuthProvider>
          </TooltipProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
