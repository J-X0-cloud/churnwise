/**
 * Server-side client for the Churnwise engine. Pages call it while rendering; it never runs in the browser,
 * so `API_URL` can point at a private address.
 */
import { cache } from "react";

import type { DashboardSnapshot, ScenarioView } from "@/types/revenue";

const DEFAULT_API_URL = "http://localhost:8000";

export class EngineError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "EngineError";
  }
}

function baseUrl(): string {
  return (process.env.API_URL || DEFAULT_API_URL).replace(/\/+$/, "");
}

async function engineFetch<T>(path: string): Promise<T> {
  if (typeof window !== "undefined") throw new EngineError("engineFetch is server-only");
  const url = `${baseUrl()}${path}`;
  let response: Response;
  try {
    response = await fetch(url, { cache: "no-store", headers: { accept: "application/json" } });
  } catch (cause) {
    const error = new EngineError(`Churnwise engine unreachable at ${baseUrl()} (set API_URL)`);
    error.cause = cause;
    throw error;
  }
  if (!response.ok) throw new EngineError(`GET ${path} failed with ${response.status}`, response.status);
  return (await response.json()) as T;
}

/**
 * Every tab, range and scenario of the sample workspace in one snapshot. Wrapped in `cache` so a page and
 * the components it renders share one request.
 */
export const getDashboard = cache(() => engineFetch<DashboardSnapshot>("/api/dashboard"));

export function scenarioByKey(snapshot: DashboardSnapshot, key: ScenarioView["key"]): ScenarioView {
  const found = snapshot.forecast.scenarios.find((s) => s.key === key);
  if (!found) throw new EngineError(`scenario ${key} missing from the engine response`);
  return found;
}
