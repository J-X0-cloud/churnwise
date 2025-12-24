/** Currency with k / M suffixes: $4.20k, $18.9k, $1.26M. */
export function money(v: number, decimals?: number): string {
  const sign = v < 0 ? "-" : "";
  const a = Math.abs(v);
  if (a >= 1e6) return `${sign}$${(a / 1e6).toFixed(decimals ?? 2)}M`;
  if (a >= 1e4) return `${sign}$${(a / 1e3).toFixed(decimals ?? 1)}k`;
  if (a >= 1e3) return `${sign}$${(a / 1e3).toFixed(decimals ?? 2)}k`;
  return `${sign}$${Math.round(a).toLocaleString("en-US")}`;
}

/** Axis labels: whole numbers and no trailing zeros. */
export function moneyAxis(v: number): string {
  if (Math.abs(v) >= 1e6) return `$${Number((v / 1e6).toPrecision(6))}M`.replace("$-", "-$");
  return money(v, 0);
}

/** Signed currency for movements: +$18.9k / -$4.2k. */
export function signedMoney(v: number): string {
  return v >= 0 ? `+${money(v)}` : money(v);
}

export function pct(v: number, digits = 1, signed = false): string {
  return `${signed && v > 0 ? "+" : ""}${v.toFixed(digits)}%`;
}

export function num(v: number): string {
  return Math.round(v).toLocaleString("en-US");
}

export function wholeDollars(v: number): string {
  return `$${Math.round(v).toLocaleString("en-US")}`;
}
