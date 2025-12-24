import { addMonths, differenceInCalendarDays, format, getDayOfYear, startOfMonth } from "date-fns";

export { addMonths, differenceInCalendarDays, startOfMonth };

export const dayOfYear = getDayOfYear;

/** "Oct" or "Jan '26" (year shown on January and wherever the caller asks). */
export function monthLabel(d: Date, withYear = false): string {
  return format(d, "MMM") + (withYear ? ` '${format(d, "yy")}` : "");
}

export const dayLabel = (d: Date) => format(d, "MMM d");
export const monthYear = (d: Date) => format(d, "MMM yyyy");
export const longMonthYear = (d: Date) => format(d, "MMMM yyyy");
export const longDate = (d: Date) => format(d, "MMM d, yyyy");

/** Monday–Friday. */
export const isWeekday = (d: Date) => d.getDay() >= 1 && d.getDay() <= 5;
