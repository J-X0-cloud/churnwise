/** Single-path line icons; stroke and size come from the surrounding CSS (.si svg, .ico svg). */
const PATHS = {
  overview: "M3 13h4v8H3zM10 9h4v12h-4zM17 4h4v17h-4z",
  revenue: "M3 17l6-6 4 4 8-8M15 7h6v6",
  retention: "M4 4h4v4H4zM10 4h4v4h-4zM16 4h4v4h-4zM4 10h4v4H4zM10 10h4v4h-4zM4 16h4v4H4z",
  customers:
    "M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM2 21v-1a6 6 0 0 1 12 0v1M16 3.2a4 4 0 0 1 0 7.6M22 21v-1a6 6 0 0 0-4-5.6",
  forecast: "M3 20h18M5 16l4-5 3 3 3-4M15 10l2-2 2 1 2-3",
  recovery: "M3 10h18M5 6h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2zM7 15h4",
  events: "M4 4v16h16M8 14l3-3 3 3 5-6",
  merge: "M12 3v18M3 12h18M5.6 5.6l12.8 12.8",
  segments: "M4 6h16M7 12h10M10 18h4",
  report: "M4 5h16v12H4zM8 21h8M12 17v4",
  api: "M8 9l-4 3 4 3M16 9l4 3-4 3M13 6l-2 12",
  shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name }: { name: IconName }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d={PATHS[name]} />
    </svg>
  );
}

/** Icon in a tinted square, used on feature cards. */
export function FeatureIcon({ name }: { name: IconName }) {
  return (
    <span className="ico">
      <Icon name={name} />
    </span>
  );
}
