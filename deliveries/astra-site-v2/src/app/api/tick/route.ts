import { NextResponse } from "next/server";
import snapshot from "@/data/market-snapshot.json";

/**
 * Live gold tick. Tries the product's market source; if it is unreachable the
 * captured snapshot is returned instead, so the UI always has a real number.
 */
export async function GET() {
  const fallback = snapshot.tick;
  const base = process.env.ASTRA_MARKET_BASE ?? "https://biquote.io";
  try {
    const r = await fetch(`${base}/api/XAUUSD`, {
      headers: { Accept: "application/json", "User-Agent": "astra-site/1.0" },
      signal: AbortSignal.timeout(6000),
      cache: "no-store",
    });
    if (!r.ok) throw new Error(String(r.status));
    const j = (await r.json()) as Record<string, unknown>;
    const mid = Number(j.mid ?? j.bid ?? 0);
    if (!Number.isFinite(mid) || mid <= 0) throw new Error("bad payload");
    return NextResponse.json({
      bid: Number(j.bid ?? mid),
      ask: Number(j.ask ?? mid),
      mid,
      spread: Number(j.spread ?? 0),
      source: String(j.source ?? "market"),
      at: new Date().toISOString(),
    });
  } catch {
    return NextResponse.json({ ...fallback, at: snapshot.captured_at, stale: true });
  }
}
