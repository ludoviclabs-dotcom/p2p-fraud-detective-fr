import type { Metadata } from "next";
import { ForensicHome } from "@/components/home/forensic-home";

export const metadata: Metadata = {
  title: "P2P Fraud Detective FR — Salle d'enquête",
};

export default function Home() {
  return <ForensicHome />;
}
