import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AlgoMentor AI",
  description: "Phase 3 AI learning loop for AlgoMentor AI"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
