"use client";

import { useLocale } from "@/components/locale-provider";
import { getDemoContent } from "./p2p-demo-content";
import { P2PDemoSceneDirector } from "./P2PDemoSceneDirector";

export function P2PInvestigationDemo({ onClose }: { onClose: () => void }) {
  const { locale } = useLocale();
  const content = getDemoContent(locale);

  return <P2PDemoSceneDirector content={content} onClose={onClose} />;
}
