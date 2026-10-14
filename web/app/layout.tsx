import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "Cookie Cat · Experiment Odyssey", description: "A playable, evidence-first A/B testing lab." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
