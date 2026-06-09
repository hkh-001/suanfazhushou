import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AlgoMentor AI",
  description: "AlgoMentor AI 算法学习助手"
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
