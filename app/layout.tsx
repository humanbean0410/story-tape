import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "故事磁带 · 场景与镜头预演",
  description: "从参考与拍摄意图，到可修改的场景方案、效果帧和动态分镜。",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
