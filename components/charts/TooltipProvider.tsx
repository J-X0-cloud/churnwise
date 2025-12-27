"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef } from "react";
import type { PointerEvent, ReactNode } from "react";

interface TooltipApi {
  show: (text: string, x: number, y: number) => void;
  hide: () => void;
}

const TooltipContext = createContext<TooltipApi>({ show: () => undefined, hide: () => undefined });

/**
 * A single text tooltip that follows the pointer. Updates go straight to the DOM node so moving across a
 * dense chart never re-renders React.
 */
export function TooltipProvider({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);

  const api = useMemo<TooltipApi>(
    () => ({
      show(text, x, y) {
        const el = ref.current;
        if (!el) return;
        if (el.textContent !== text) el.textContent = text;
        let left = x + 14;
        if (left + el.offsetWidth > window.innerWidth - 8) left = x - el.offsetWidth - 14;
        el.style.transform = `translate(${left}px, ${y + 16}px)`;
        el.style.opacity = "1";
      },
      hide() {
        if (ref.current) ref.current.style.opacity = "0";
      },
    }),
    [],
  );

  useEffect(() => {
    window.addEventListener("scroll", api.hide, { passive: true });
    return () => window.removeEventListener("scroll", api.hide);
  }, [api]);

  return (
    <TooltipContext.Provider value={api}>
      {children}
      <div className="tt" ref={ref} aria-hidden="true" />
    </TooltipContext.Provider>
  );
}

export const useTooltip = () => useContext(TooltipContext);

/** Spread onto any element to give it a hover tooltip. */
export function useTip() {
  const { show, hide } = useTooltip();
  return useCallback(
    (text: string) => ({
      onPointerMove: (e: PointerEvent) => show(text, e.clientX, e.clientY),
      onPointerLeave: hide,
    }),
    [show, hide],
  );
}
