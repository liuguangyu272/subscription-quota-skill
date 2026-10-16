---
name: subscription-quota
description: Check the active provider's billing mode, remaining quota and reset time before substantial agent work; pace optional work using verified subscription windows. Use for quota questions and multistage tasks in Codex, ZCode, DSH or another skill-capable harness. Simple questions need no extra quota query.
---

# Subscription-aware task pacing

Check the **current session's provider/account route**, not whether this computer has a subscription somewhere. Harness means the app running the agent; it does not determine billing. A login or API key alone does not establish a subscription. Never expose credentials or read authentication stores for this skill.

1. Identify the active provider, account/workspace scope and billing evidence using available runtime tools or a trusted local integration. If unavailable, retain `UNKNOWN`; do not infer billing from a model name, installed app, or another CLI's login. Read [integrations](references/integrations.md) for the current harness.
2. Obtain remaining quota and reset timestamps for **all applicable model windows**, including weekly limits. Use [snapshot contract](references/snapshot.md) when a host supplies data. Recharge wallets, token counters and context-window capacity are not resetting subscription allowances. Never invent a five-hour cycle or turn money into a remaining percentage.
3. Run `python <skill-directory>/scripts/budget.py <snapshot.json> --route <verified-current-route>`. Resolve resources relative to this skill's real installed directory. Python 3.11+ is required for helpers; if execution is unavailable, apply the same arithmetic only to verified data and disclose that limitation.
4. Use the most restrictive window to plan the next useful stage. Recheck at meaningful phase boundaries, after an account/provider change or when a reset becomes due. A snapshot older than five minutes needs refreshing before reuse. Avoid per-tool polling; one failed refresh leaves quota unknown while work continues in bounded stages.

## Pacing rule

`budget = remaining percentage / hours until reset`, measured in **percentage points per hour**.

Default reference is `100 / full window hours`: 20 for five hours, about 0.595 for a week. This is an even-spend heuristic, not a provider limit or a measured token rate. An explicit per-window `reference_pph` overrides it; set 12 for a five-hour window to retain the original personal preference. Do not apply 12 to every provider/window.

| Budget / reference | Level | Suggested task strategy |
|---|---|---|
| Below 0.5 | TIGHT | Focus on core deliverables; small verifiable stages; defer optional exploration. |
| 0.5 to below 1 | CONSERVATIVE | Continue core work; limit speculative branches and repeated searches. |
| 1 to below 1.5 | COMFORTABLE | Normal useful depth and relevant investigation. |
| At least 1.5 | ABUNDANT | Additional valuable exploration when warranted by the task. |

Below 10% absolute quota, cap the recommendation at CONSERVATIVE even near reset. At zero, report EXHAUSTED. An elapsed reset means UNKNOWN until refreshed, never presumed replenishment. A high rate in one window cannot override an exhausted or tight weekly window. The helper excludes unknown, stale and mismatched-scope data from recommendations.

All levels retain necessary tests and the user's full intended outcome. Prefer efficient tool use and smaller stages over dropping requirements. Never burn quota to meet a target, claim guaranteed savings, or announce completion because a threshold was reached. This is advisory pacing, **not a hard token limiter**. Do not claim to change the harness's model, hidden reasoning effort or concurrency settings; change exposed settings only with user authorization and supported controls. Quota does not authorize extra agents, purchases, resets or background automation.

Keep useful artifacts and a brief next-step record at natural checkpoints in long tasks. If an actual limit blocks progress, state completed and remaining work. Unknown billing should not interrupt the task or trigger repeated questions. Report source/freshness and limitations when relevant, without sending routine quota updates every turn.
