"use client";

import Chatbot from "@/components/Chatbot";
import Footer from "@/components/Footer";
import Header from "@/components/Header";
import { LanguageProvider } from "@/components/LanguageProvider";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
};

export default function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const isAgentDashboard = pathname === "/agent-dashboard";

  return (
    <LanguageProvider>
      {!isAgentDashboard && <Header />}
      <div className="flex-1">{children}</div>
      {!isAgentDashboard && <Chatbot />}
      {!isAgentDashboard && <Footer />}
    </LanguageProvider>
  );
}
