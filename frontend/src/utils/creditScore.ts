import { ParsedEarning } from "./earningsUtils";

export function calculateDemoCreditScore(parsed: ParsedEarning[]): number {
  if (!parsed || parsed.length === 0) return 575;

  const monthlyTotals = new Map<string, number>();

  for (const p of parsed) {
    const y = p.date.getFullYear();
    const m = String(p.date.getMonth() + 1).padStart(2, "0");
    const key = `${y}-${m}`;
    monthlyTotals.set(key, (monthlyTotals.get(key) ?? 0) + p.amountUsd);
  }

  const avgMonthly =
    [...monthlyTotals.values()].reduce((a, b) => a + b, 0) / monthlyTotals.size;

  const minIncome = 100;
  const maxIncome = 2000;

  const clamped = Math.min(Math.max(avgMonthly, minIncome), maxIncome);

  return Math.round(
    300 + ((clamped - minIncome) / (maxIncome - minIncome)) * (850 - 300)
  );
}
