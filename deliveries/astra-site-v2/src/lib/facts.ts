/**
 * Company facts used across the site.
 *
 * `facts.json` is produced by `tools/gen_facts.py`, which reads test-run
 * artefacts and executes the suites. This module only *shapes* that output, so
 * a number on the page can never be typed by hand.
 *
 * Items whose suite could not run are marked `blocked` and rendered as such —
 * the site says what it could not verify instead of quietly omitting it.
 */
import market from "@/data/market-snapshot.json";
import rawFacts from "@/data/facts.json";

export type MarketSnapshot = typeof market;
export const marketSnapshot = market as MarketSnapshot;

export type Status = "verified" | "recorded" | "blocked";
export type Measured = {
  status: Status;
  passed?: number;
  total?: number;
  findings?: number;
  reason?: string;
  note?: string;
  at?: string | null;
  source?: string;
};

export const facts = rawFacts as unknown as {
  generated_at: string;
  readiness: Measured;
  engine: Measured;
  api: Measured;
  security: Measured;
  roster: { agents: number; departments: number; managers: number; source: string };
  repos: { total: number; ok: number; owner: string | null; source: string };
};

export const company = {
  name: "AI ASTRA AGENCY",
  founded: "2026",
  model: "autonomous AI-agent workforce",
  location: "cloud · operating 24/7",
  stack: [
    "Next.js", "React", "TypeScript", "Tailwind",
    "FastAPI", "Python", "Supabase", "PostgreSQL",
  ] as string[],
} as const;

export const workforce = {
  agents: facts.roster.agents,
  departments: facts.roster.departments,
  managers: facts.roster.managers,
  privateRepos: facts.repos.ok,
} as const;

export type Department = {
  key: string;
  manager: string;
  repo: string;
  headcount: number;
};

/** Measured from company/roster.json + company/departments/repos.json. */
export const departments: Department[] = [
  { key: "engineering", manager: "astra-cto", repo: "dept-engineering", headcount: 2 },
  { key: "security", manager: "astra-ciso", repo: "dept-security", headcount: 1 },
  { key: "product", manager: "astra-cpo", repo: "dept-product", headcount: 4 },
  { key: "quality", manager: "astra-cqo", repo: "dept-quality", headcount: 7 },
  { key: "creative", manager: "astra-ccr", repo: "dept-creative", headcount: 6 },
  { key: "marketing", manager: "astra-cmo", repo: "dept-marketing", headcount: 2 },
  { key: "research", manager: "astra-cro", repo: "dept-research", headcount: 4 },
  { key: "operations", manager: "astra-coo", repo: "dept-operations", headcount: 1 },
  { key: "analysis", manager: "astra-cao", repo: "dept-analysis", headcount: 1 },
  { key: "business-development", manager: "astra-cbdo", repo: "dept-business-development", headcount: 2 },
];
