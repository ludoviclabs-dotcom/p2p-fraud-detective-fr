"use client";

import type { DemoContent } from "./p2p-demo-content";
import type { P2PConsoleEventId } from "./p2p-demo-data";

export function P2PCommandConsole({
  events,
  content,
}: {
  events: P2PConsoleEventId[];
  content: DemoContent;
}) {
  const lines = events.map((event) => content.consoleEvents[event]).filter(Boolean);

  return (
    <aside className="p2p-demo-command-console" aria-label={content.labels.console}>
      <div className="p2p-demo-console-head">
        <span>{content.labels.console}</span>
        <span className="p2p-demo-console-dot" aria-hidden />
      </div>
      <div className="p2p-demo-console-lines">
        {lines.map((line, index) => (
          <div
            key={`${line}-${index}`}
            className={`p2p-demo-console-line ${index === lines.length - 1 ? "active" : ""}`}
            style={{ animationDelay: `${index * 70}ms` }}
          >
            {line}
          </div>
        ))}
        <span className="p2p-demo-console-cursor" aria-hidden />
      </div>
    </aside>
  );
}
