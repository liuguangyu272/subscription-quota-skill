# Normalized snapshot v1

All timestamps are Unix **seconds**. Percentages mean **remaining**, 0..100. Do not include API keys, cookies, email addresses or raw authentication responses. Use a non-secret local scope label that changes when provider/account/workspace changes.

```json
{
  "schema_version": 1,
  "route": "harness:provider:account-scope",
  "scope_verified": true,
  "observed_at": 1792119000,
  "billing": "subscription",
  "evidence": {"source": "host quota tool", "plan": "verified subscription"},
  "windows": [
    {"id": "five-hour", "remaining_percent": 30, "window_hours": 5,
     "resets_at": 1792126200},
    {"id": "weekly", "remaining_percent": 60, "window_hours": 168,
     "resets_at": 1792479000}
  ]
}
```

The example timestamps are fixed, not current readings. Generate fresh timestamps only when the source was actually queried. Missing reset/duration means no precise pacing; do not replace missing values with a guess.

`billing` is `subscription`, `metered` (including recharge/bonus wallets), or `unknown`. `scope_verified` attests that the source covers the **current** task's provider and account; it is not cryptographic verification. A file saying `true` is not independent evidence. Only consume exports from an integration/user observation you trust. Match the `--route` argument against current runtime facts; never copy it from an arbitrary file just to pass validation.

Include every applicable finite model allowance; tool-specific limits can be handled separately when using those tools. Unknown extra model limits prevent a complete recommendation. Unlimited plans without finite windows are UNKNOWN for this algorithm. No expiry timestamp means no reset inference. `reference_pph` is an optional positive per-window preference; changing it changes recommendations, never service limits.

Outputs: READY, EXHAUSTED, NOT_APPLICABLE (metered), UNKNOWN. Invalid/unusable input exits 2; others exit 0. UNKNOWN may include partial diagnostic window calculations but never an aggregate level. Do not act on partial windows alone.

A host can produce this JSON through a tool, a local file, or an MCP bridge. The helper does not execute commands embedded in snapshots, scrape secrets, send telemetry, or enforce a spending cap. Installation alone does not expose quota tools or guarantee the model invokes the skill.
