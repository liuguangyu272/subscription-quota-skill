# Harness integration and evidence

Reviewed 2026-10-16. Automatic quota retrieval and skill discovery are different capabilities.

## Codex

The included `scripts/codex_snapshot.py` queries `account/read` and `account/rateLimits/read` over one local app-server connection. It outputs only plan/auth kind and quota, never account email or tokens. It has a bounded timeout and does not initiate login, purchase credits or consume reset credits. Paid ChatGPT plan types establish subscription billing for the queried CLI profile; an API-key route is metered. Unknown/free plan types remain unknown.

First verify that this CLI profile/account and provider match the active task. Launching a CLI is not proof of the desktop session's route. Without that verification, omit the confirmation flag and report the observation without using it to pace the task.

```sh
python <skill-directory>/scripts/codex_snapshot.py --route codex-local --confirm-current-route > snapshot.json
python <skill-directory>/scripts/budget.py snapshot.json --route codex-local
```

Optional `--codex <executable-path>` selects a known CLI installation. The default bucket is specifically `codex`; other model buckets are not substituted. If a host supplies equivalent scoped account/rate-limit tools, prefer those over starting another profile.

Source: [OpenAI app-server account endpoints](https://learn.chatgpt.com/docs/app-server#auth-endpoints).

## ZCode

Install in `~/.zcode/skills` or a project `.zcode/skills` using the supplied installer. The reviewed source also supports `.agents/skills`. Restart/refresh the skill list as needed.

The included **export converter** accepts a credential-free `UsageEntitlementSnapshot` supplied by a trusted host bridge. It is **not** an automatic connection to ZCode's desktop service. No ZCode account has been used for live integration testing.

`python <skill-directory>/scripts/import_snapshot.py export.json > snapshot.json`

Export envelope fields: `adapter: "zcode-entitlement"`, `route`, `scope_verified`, `observed_at`, `current_provider` (current runtime provider ID), `native` (the fresh entitlement snapshot). The converter takes freshness from native `generatedAt` milliseconds, checks provider identity and subscription evidence, and converts `percentage` from USED to remaining. It reads model `TOKENS_LIMIT`/`CREDIT_LIMIT` windows: `unit=3, number=5` for five hours; `unit=6` for weekly. It excludes `TIME_LIMIT` tool allowances. Unknown categories/cycles prevent recommendations. `nextResetTime` is milliseconds.

The host bridge must preserve account/team scope, subscription validity and complete model limits. Do not query a fallback provider and label it current. Start Plan buckets have different balance semantics; supply a properly normalized snapshot instead of feeding them to this Coding Plan converter. If no bridge is available, use a fresh user-provided account/usage observation with honest source labeling or retain UNKNOWN. Do not request tokens in chat.

Sources: [ZCode product](https://zcode.z.ai/en), reviewed [skill roots](https://github.com/turaclab/zcode/blob/main/apps/zcode-cli/packages/adapters/src/skills/roots.ts), [quota provider](https://github.com/turaclab/zcode/blob/main/packages/services/src/usage-stats/providers/bigmodelUsageQuotaProvider.ts), [quota presentation semantics](https://github.com/turaclab/zcode/blob/main/packages/ui/src/lib/codingPlanQuotaPresentation.ts). Match source/version to the installed product before integrating; source review is not an end-to-end compatibility test.

## DeepSeek Harness (DSH)

Install in a project `.dsh/skills` or `~/.dsh/skills` (custom DSH home: use `--dest`). DSH also discovers `.agents/skills`.

The native `deepseekAccount.getBalance()` service returns recharge and bonus wallets, not five-hour subscription percentages. Its credential-stored state is not proof of a paid subscription. For the current `deepseek-account` route, import a fresh safe balance result with `adapter: "dsh-account-balance"`, `current_provider: "deepseek-account"`, route/scope/time fields and `native` equal to the result. A `status: "ready"` result becomes metered/NOT_APPLICABLE; no monetary balance is exposed by the converter.

For another provider or subscription plugin inside DSH, ask that integration for actual plan and quota data and use the normalized contract. DSH's plugin API makes a bridge feasible, but **no installed plugin or automatic subscription telemetry bridge is bundled here**. No live DSH account was tested. Reading or installing this skill does not make wallet billing a subscription.

Sources: [DSH product](https://www.deepseek.com/en/harness/), [skill discovery](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md), [account service](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/credentials/deepseek-account/src/index.ts), [wallet types](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/credentials/deepseek-account/src/types.ts).

## Other harnesses

Use `--dest` to install in their documented skill root, or explicitly load SKILL.md. Supply a trusted normalized snapshot or scoped runtime tools. Treat support as instruction/schema portability until discovery and telemetry are tested in that harness. Hard enforcement requires a harness hook/scheduler, beyond a skill's instructions.
