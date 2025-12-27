import Link from "next/link";

export function LogoMark() {
  return (
    <svg className="mark" viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="9" fill="#0f7a56" />
      <path
        d="M22.8 10.4A8.6 8.6 0 1 0 24.6 19"
        fill="none"
        stroke="#fff"
        strokeWidth={2.8}
        strokeLinecap="round"
      />
      <path
        d="M11.6 18.6l3.2-3.4 2.6 2.4 4.9-5.4"
        fill="none"
        stroke="#b9f5d8"
        strokeWidth={2.4}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="24.6" cy="19" r="1.9" fill="#f5c24c" />
    </svg>
  );
}

export function Brand() {
  return (
    <Link className="brand" href="/" aria-label="Churnwise home">
      <LogoMark />
      <span>churnwise</span>
    </Link>
  );
}
