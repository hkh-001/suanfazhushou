import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AlgoMentor AI",
  description: "Phase 1 engineering skeleton for AlgoMentor AI"
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
