import AppShell from "@/components/AppShell";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Eastern Bank PLC",
  description: "Modern banking for individuals, businesses, and communities.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
