// src/utils/earningsUtils.ts

// Parse "11-15-2025" (MM-DD-YYYY)
export function parseUsDate(value: string): Date {
  const [m, d, y] = value.split("-").map(Number);
  return new Date(y, m - 1, d);
}

// Convert amounts like "$39" or "£100"
export function parseAmountToUsd(raw: string, gbpToUsd: number) {
  const isGbp = raw.includes("£");
  const numeric = parseFloat(raw.replace(/[^0-9.-]/g, ""));
  if (Number.isNaN(numeric)) return 0;
  return isGbp ? numeric * gbpToUsd : numeric;
}

// Convert raw API JSON → parsed earnings with real Date + USD
export function parseEarnings(rawData: any[], gbpToUsd: number) {
  return rawData
    .map((r) => ({
      date: parseUsDate(r.date),
      amountUsd: parseAmountToUsd(r.earnings, gbpToUsd),
    }))
    .filter((r) => !Number.isNaN(r.amountUsd));
}

// Your original credit score function (unchanged)
export function calculateCreditScore(parsed: any[]) {
  if (!parsed || parsed.length === 0) return 575;

  const monthlyTotals = new Map();

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
    400 + ((clamped - minIncome) / (maxIncome - minIncome)) * (850 - 300)
  );
}
