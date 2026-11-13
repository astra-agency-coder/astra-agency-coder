# AI ASTRA AGENCY — Organisation Design

The structure below is the **founding structure**. The CEO may create, merge, or
retire departments as the business requires. No department is created without a
real need.

```
                        OWNER (human)
                             |
                       CEO  (astra-ceo)
                             |
   +------------+------------+------------+------------+------------+
   |            |            |            |            |            |
Engineering  Marketing   Business     Product    Operations   Quality   Research
 (CTO)       (CMO)      Development  (CPO)       (COO)       (CQO)    (CRO)
                        (CBDO)
```

## Why these seven
| Department | Rationale |
|---|---|
| Engineering | Every digital deliverable needs build, review and release discipline. |
| Marketing | Revenue requires distribution; also owns brand and content. |
| Business Development | Finds and qualifies real opportunities; owns the sales pipeline. |
| Product | Converts market needs into scoped, sellable products and services. |
| Operations | Runs the internal machinery: scheduling, records, cost, reporting. |
| Quality | Independent verification before anything reaches a customer. |
| Research & Analysis | Feeds the other six with market, technical and competitive data. |

## Reporting chain
- Department managers report to the CEO.
- Specialists are created by their manager and report to that manager.
- The CEO is the only role that may create a department manager.
- Only the CEO reports to the Owner.

## Span of control
- A manager should not run more than ~8 concurrent specialists.
- Specialists are created **on demand** for a task, then kept (idle, documented)
  or retired with a documented reason.

## Delegation mechanism (verified in this environment)
| Layer | Mechanism | Notes |
|---|---|---|
| CEO → manager | `task_tool_set` task tool, `subagent_type=<manager>` | synchronous, returns result to CEO |
| manager → specialist | same task tool from inside the manager's own run | nested delegation supported |
| Long-running / parallel work | child conversation via `/api/conversations` | independent session, own context |
| Resumption | task tool `resume=<task_id>` | preserves sub-agent context |
| Persistent org definitions | `.agents/agents/*.md` files | discovered automatically |

## Employment record
Every agent ever created is recorded in `company/roster.json` with: id, role,
department, reports-to, tools, model, status, created date, and notes.
See `ops/astra.py roster`.
