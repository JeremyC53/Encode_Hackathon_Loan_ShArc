// src/screens/EarningsScreen.tsx
import React, { useEffect, useMemo, useState } from "react";
import { createClient } from "@supabase/supabase-js";

type RawEarning = {
  date: string; // "11-15-2025"
  company: string;
  earnings: string; // "$39.51" or "£829.30"
};

type ParsedEarning = {
  date: Date;
  amountUsd: number;
};

type Range = "week" | "month" | "year";

const supabaseUrl = `https://${import.meta.env.VITE_SUPABASE_ID}.supabase.co`;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY as string;
const supabase = createClient(supabaseUrl, supabaseKey);

// ---------- small helpers / components ----------

type CenteredProps = {
  children: React.ReactNode;
  style?: React.CSSProperties;
};

const Centered = ({ children, style }: CenteredProps) => (
  <div
    style={{
      height: "100%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: 14,
      color: "#9ca3af",
      ...style,
    }}
  >
    {children}
  </div>
);

const SummaryCard: React.FC<{ label: string; value: string }> = ({
  label,
  value,
}) => (
  <div
    style={{
      backgroundColor: "#020617",
      borderRadius: 16,
      padding: 16,
      border: "1px solid rgba(148,163,184,0.3)",
    }}
  >
    <div style={{ fontSize: 13, color: "#9ca3af", marginBottom: 6 }}>
      {label}
    </div>
    <div style={{ fontSize: 20, fontWeight: 600 }}>{value}</div>
  </div>
);

const RangeSelector: React.FC<{
  range: Range;
  onChange: (r: Range) => void;
}> = ({ range, onChange }) => {
  const options: { id: Range; label: string }[] = [
    { id: "week", label: "Weekly" },
    { id: "month", label: "Monthly" },
    { id: "year", label: "Yearly" },
  ];

  return (
    <div
      style={{
        display: "inline-flex",
        backgroundColor: "#020617",
        borderRadius: 999,
        border: "1px solid rgba(55,65,81,0.8)",
        padding: 2,
      }}
    >
      {options.map((opt) => {
        const active = opt.id === range;
        return (
          <button
            key={opt.id}
            type="button"
            onClick={() => onChange(opt.id)}
            style={{
              borderRadius: 999,
              border: "none",
              padding: "4px 10px",
              fontSize: 12,
              cursor: "pointer",
              backgroundColor: active ? "#1d4ed8" : "transparent",
              color: active ? "#f9fafb" : "#9ca3af",
            }}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
};

// choose latest dummy_earnings_YYYYMMDD_x.json
function pickLatestEarningsFilename(names: string[]): string | null {
  const regex = /^dummy_earnings_(\d{8})_(\d+)\.json$/;

  let best: { date: string; index: number; name: string } | null = null;

  for (const name of names) {
    const match = name.match(regex);
    if (!match) continue;
    const [, dateStr, indexStr] = match;
    const index = Number.parseInt(indexStr, 10);

    if (
      !best ||
      dateStr > best.date ||
      (dateStr === best.date && index > best.index)
    ) {
      best = { date: dateStr, index, name };
    }
  }

  return best?.name ?? null;
}

function parseUsDate(value: string): Date {
  // "11-15-2025" (MM-DD-YYYY)
  const [m, d, y] = value.split("-").map((p) => Number.parseInt(p, 10));
  return new Date(y, m - 1, d);
}

// convert a value like "$39.51" or "£829.30" to USD using a GBP→USD rate
function parseAmountToUsd(value: string, gbpToUsd: number): number {
  const trimmed = value.trim();
  const isGbp = trimmed.includes("£");
  const numeric = Number.parseFloat(trimmed.replace(/[^0-9.-]+/g, ""));
  if (Number.isNaN(numeric)) return 0;

  if (!isGbp) {
    // treat everything that isn't £ as already USD
    return numeric;
  }
  // GBP → USD
  return numeric * gbpToUsd;
}

function formatCurrency(amount: number): string {
  const rounded = Number(amount.toFixed(2));
  return `$${rounded.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function formatShortDate(isoDate: string): string {
  // isoDate = "YYYY-MM-DD"
  const [year, month, day] = isoDate.split("-").map(Number);
  const d = new Date(year, month - 1, day);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function formatShortNumber(value: number): string {
  if (Math.abs(value) >= 1000) return (value / 1000).toFixed(1) + "k";
  return value.toFixed(0);
}

// build simple SVG points
function buildSvgPoints(
  values: { label: string; total: number }[],
  width: number,
  height: number,
  padding: number
) {
  if (values.length === 0) return { points: [], path: "", max: 0 };

  const maxVal = Math.max(...values.map((v) => v.total), 1);
  const innerW = width - padding * 2;
  const innerH = height - padding * 2;

  const step = values.length > 1 ? innerW / (values.length - 1) : 0;

  const points = values.map((v, i) => {
    const x = padding + i * step;
    const y = height - padding - (v.total / maxVal) * innerH; // flip y (0 at bottom)
    return { x, y, label: v.label, total: v.total };
  });

  const path = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
    .join(" ");

  return { points, path, max: maxVal };
}

// ---------- main component ----------

const EarningsScreen: React.FC = () => {
  const [rawData, setRawData] = useState<RawEarning[]>([]);
  const [range, setRange] = useState<Range>("year");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [gbpToUsd, setGbpToUsd] = useState<number>(1.25); // fallback 1 GBP ≈ 1.25 USD

  useEffect(() => {
    const fetchLatest = async () => {
      try {
        setLoading(true);
        setError(null);

        // 1) get today's GBP→USD rate (no key required)
        try {
          const resp = await fetch(
            "https://api.exchangerate.host/latest?base=GBP&symbols=USD"
          );
          if (resp.ok) {
            const data = await resp.json();
            const rate = data?.rates?.USD;
            if (typeof rate === "number" && rate > 0) {
              setGbpToUsd(rate);
            }
          }
        } catch (fxErr) {
          console.warn("FX fetch failed, using fallback 1.25", fxErr);
        }

        // 2) list earnings files in Supabase
        const { data: files, error: listError } = await supabase.storage
          .from("earnings")
          .list("", { limit: 1000 });

        if (listError) throw listError;
        if (!files || files.length === 0) {
          setError("No earnings files found.");
          setRawData([]);
          setLoading(false);
          return;
        }

        const latestName = pickLatestEarningsFilename(
          files.map((f: { name: string }) => f.name)
        );

        if (!latestName) {
          setError("No earnings files matching pattern found.");
          setRawData([]);
          setLoading(false);
          return;
        }

        // 3) download that file
        const { data: fileData, error: downloadError } = await supabase.storage
          .from("earnings")
          .download(latestName);

        if (downloadError || !fileData) throw downloadError;

        const text = await fileData.text();
        const json = JSON.parse(text) as RawEarning[];

        setRawData(json);
      } catch (err) {
        console.error(err);
        setError("Failed to load earnings data.");
      } finally {
        setLoading(false);
      }
    };

    fetchLatest();
  }, []);

  // parse & normalise to USD
  const parsed: ParsedEarning[] = useMemo(
    () =>
      rawData
        .map((r) => ({
          date: parseUsDate(r.date),
          amountUsd: parseAmountToUsd(r.earnings, gbpToUsd),
        }))
        .filter((r) => r.date && !Number.isNaN(r.amountUsd)) as ParsedEarning[],
    [rawData, gbpToUsd]
  );

  const { series, netTotal, monthlyTotal } = useMemo(() => {
    if (parsed.length === 0) {
      return {
        series: [] as { label: string; total: number }[],
        netTotal: 0,
        monthlyTotal: 0,
      };
    }

    // total across all time (already USD)
    const netTotal = parsed.reduce((acc, r) => acc + r.amountUsd, 0);

    const latestDate = parsed.reduce(
      (latest, r) => (r.date > latest ? r.date : latest),
      parsed[0].date
    );

    const windowDays = range === "week" ? 7 : range === "month" ? 30 : 365;
    const cutoff = new Date(
      latestDate.getTime() - (windowDays - 1) * 24 * 60 * 60 * 1000
    );

    // group by date → sum for that day
    const dailyMap = new Map<string, number>();

    parsed.forEach(({ date, amountUsd }) => {
      if (date < cutoff || date > latestDate) return;
      const key = date.toISOString().slice(0, 10); // YYYY-MM-DD
      dailyMap.set(key, (dailyMap.get(key) ?? 0) + amountUsd);
    });

    // sorted list of days within range
    const daily = Array.from(dailyMap.entries())
      .sort((a, b) => (a[0] < b[0] ? -1 : 1))
      .map(([key, total]) => ({
        label: formatShortDate(key),
        total: Number(total.toFixed(2)),
      }));

    // 👉 cumulative net earnings over time
    let running = 0;
    const series = daily.map((d) => {
      running += d.total;
      return {
        label: d.label,
        total: Number(running.toFixed(2)),
      };
    });

    // monthly earnings = last 30 days from latestDate
    const monthCutoff = new Date(
      latestDate.getTime() - 29 * 24 * 60 * 60 * 1000
    );
    const monthlyTotal = parsed
      .filter((r) => r.date >= monthCutoff && r.date <= latestDate)
      .reduce((acc, r) => acc + r.amountUsd, 0);

    return { series, netTotal, monthlyTotal };
  }, [parsed, range]);

  // build svg for current series
  const width = 500;
  const height = 220;
  const padding = 36;
  const { points, path, max } = buildSvgPoints(series, width, height, padding);
  const mid = max / 2;

  // helpers to compute y positions for axis labels
  const innerH = height - padding * 2;
  const maxY = padding;
  const midY = height - padding - (mid / (max || 1)) * innerH;
  const zeroY = height - padding;

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>Earnings</h1>
      <p style={{ color: "#9ca3af", marginBottom: 24 }}>
        Net earnings across your connected platforms (in USD).
      </p>

      {/* summary cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 16,
          marginBottom: 24,
        }}
      >
        <SummaryCard label="Net Earnings" value={formatCurrency(netTotal)} />
        <SummaryCard
          label="Monthly Earnings"
          value={formatCurrency(monthlyTotal)}
        />
        <SummaryCard label="Credit Score" value="742" />
      </div>

      {/* chart + controls */}
      <div
        style={{
          backgroundColor: "#020617",
          borderRadius: 16,
          padding: 16,
          border: "1px solid rgba(148,163,184,0.3)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 12,
            gap: 12,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 16,
                fontWeight: 600,
                marginBottom: 4,
              }}
            >
              Net Earnings Over Time
            </div>
            <div style={{ fontSize: 12, color: "#9ca3af" }}>
              Based on the latest earnings file in Supabase. All values in USD.
            </div>
          </div>

          <RangeSelector range={range} onChange={setRange} />
        </div>

        <div style={{ height: 260 }}>
          {loading && <Centered>Loading earnings…</Centered>}
          {!loading && error && (
            <Centered style={{ color: "#fca5a5" }}>{error}</Centered>
          )}
          {!loading && !error && series.length === 0 && (
            <Centered>No earnings data yet.</Centered>
          )}

          {!loading && !error && series.length > 0 && (
            <div
              style={{
                width: "100%",
                height: "100%",
                overflow: "hidden",
              }}
            >
              <svg
                viewBox={`0 0 ${width} ${height}`}
                style={{ width: "100%", height: "100%" }}
              >
                {/* Y axis */}
                <line
                  x1={padding}
                  x2={padding}
                  y1={maxY}
                  y2={zeroY}
                  stroke="#1f2937"
                />

                {/* horizontal grid lines for max, mid, zero */}
                <line
                  x1={padding}
                  x2={width - padding}
                  y1={maxY}
                  y2={maxY}
                  stroke="#111827"
                  strokeDasharray="4 4"
                />
                <line
                  x1={padding}
                  x2={width - padding}
                  y1={midY}
                  y2={midY}
                  stroke="#111827"
                  strokeDasharray="4 4"
                />
                <line
                  x1={padding}
                  x2={width - padding}
                  y1={zeroY}
                  y2={zeroY}
                  stroke="#1f2937"
                />

                {/* Y labels */}
                <text
                  x={padding - 6}
                  y={zeroY + 4}
                  textAnchor="end"
                  fontSize={10}
                  fill="#6b7280"
                >
                  0
                </text>
                <text
                  x={padding - 6}
                  y={midY + 3}
                  textAnchor="end"
                  fontSize={10}
                  fill="#6b7280"
                >
                  {formatShortNumber(mid || 0)}
                </text>
                <text
                  x={padding - 6}
                  y={maxY + 3}
                  textAnchor="end"
                  fontSize={10}
                  fill="#6b7280"
                >
                  {formatShortNumber(max || 0)}
                </text>

                {/* line path */}
                {path && (
                  <path d={path} fill="none" stroke="#60a5fa" strokeWidth={2} />
                )}

                {/* points */}
                {points.map((p, idx) => (
                  <g key={idx}>
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r={3}
                      fill="#60a5fa"
                      stroke="#1e3a8a"
                      strokeWidth={1}
                    />
                  </g>
                ))}

                {/* x labels */}
                {points.map((p, idx) => (
                  <text
                    key={`label-${idx}`}
                    x={p.x}
                    y={zeroY + 16}
                    textAnchor="middle"
                    fontSize={10}
                    fill="#9ca3af"
                  >
                    {p.label}
                  </text>
                ))}
              </svg>
            </div>
          )}
        </div>
      </div>

      {/* earnings table */}
      <div
        style={{
          marginTop: 24,
          backgroundColor: "#020617",
          borderRadius: 16,
          padding: 16,
          border: "1px solid rgba(148,163,184,0.3)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 12,
          }}
        >
          <div>
            <div
              style={{
                fontSize: 16,
                fontWeight: 600,
                marginBottom: 4,
              }}
            >
              Earnings Breakdown
            </div>
            <div style={{ fontSize: 12, color: "#9ca3af" }}>
              Raw entries from the latest Supabase earnings file.
            </div>
          </div>
        </div>

        {loading && <Centered>Loading earnings…</Centered>}

        {!loading && error && (
          <Centered style={{ color: "#fca5a5" }}>{error}</Centered>
        )}

        {!loading && !error && rawData.length === 0 && (
          <Centered>No earnings records found.</Centered>
        )}

        {!loading && !error && rawData.length > 0 && (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                minWidth: 480,
              }}
            >
              <thead>
                <tr style={{ backgroundColor: "#020617" }}>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "10px 14px",
                      fontSize: 13,
                      color: "#9ca3af",
                      borderBottom: "1px solid rgba(148,163,184,0.3)",
                    }}
                  >
                    Date
                  </th>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "10px 14px",
                      fontSize: 13,
                      color: "#9ca3af",
                      borderBottom: "1px solid rgba(148,163,184,0.3)",
                    }}
                  >
                    Company
                  </th>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "10px 14px",
                      fontSize: 13,
                      color: "#9ca3af",
                      borderBottom: "1px solid rgba(148,163,184,0.3)",
                    }}
                  >
                    Amount (USD)
                  </th>
                </tr>
              </thead>
              <tbody>
                {rawData
                  .map((row) => ({
                    date: parseUsDate(row.date),
                    company: row.company,
                    amountUsd: parseAmountToUsd(row.earnings, gbpToUsd),
                  }))
                  .filter((r) => !Number.isNaN(r.amountUsd))
                  .sort((a, b) => b.date.getTime() - a.date.getTime())
                  .map((row, idx) => (
                    <tr
                      key={`${row.company}-${row.date.toISOString()}-${idx}`}
                      style={{ backgroundColor: "#020617" }}
                    >
                      <td
                        style={{
                          padding: "10px 14px",
                          fontSize: 14,
                          borderBottom: "1px solid rgba(15,23,42,0.9)",
                        }}
                      >
                        {row.date.toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </td>
                      <td
                        style={{
                          padding: "10px 14px",
                          fontSize: 14,
                          borderBottom: "1px solid rgba(15,23,42,0.9)",
                        }}
                      >
                        {row.company}
                      </td>
                      <td
                        style={{
                          padding: "10px 14px",
                          fontSize: 14,
                          borderBottom: "1px solid rgba(15,23,42,0.9)",
                        }}
                      >
                        {formatCurrency(row.amountUsd)}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
export default EarningsScreen;
