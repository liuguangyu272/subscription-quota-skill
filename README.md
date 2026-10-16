# Subscription Quota Skill

**Check the current billing route. Budget quota against time. Preserve useful work.**

A portable agent skill with a small Python pacing engine. It distinguishes subscription allowances from metered wallets, considers all applicable reset windows, and suggests how much optional exploration to undertake. It is independent of the existing [QuotaGuard Skill](https://github.com/liuguangyu272/quotaguard-skill).

## What works today

| Capability | Status |
|---|---|
| Provider-neutral remaining-percent / hours-to-reset calculation | Implemented and tested |
| Five-hour, weekly and other explicitly supplied finite windows | Implemented; most restrictive window wins |
| Codex local account type + quota read | Live-tested on Windows with a Plus account |
| ZCode skill packaging and Coding Plan export conversion | Source-reviewed, synthetic tests; **no automatic desktop connection or live account test** |
| DSH skill packaging and native wallet export classification | Source-reviewed, synthetic tests; **no automatic runtime connection or live account test** |
| Other subscription providers inside either harness | Normalized snapshot contract; requires a trusted provider bridge |
| Hard spending cap, automatic model switching, guaranteed savings | Not provided |

**Portable instructions do not create a universal quota API.** A harness is the app hosting the agent; its current model provider determines billing. DSH's reviewed native account interface exposes recharge/bonus wallets, not five-hour subscription windows. ZCode supports different quota cycles. The skill deliberately returns UNKNOWN when subscription, scope or timing cannot be established.

## Install

Python 3.11+; no pip dependencies. Download/clone this repository, then:

```sh
python install.py --harness zcode
python install.py --harness dsh
python install.py --harness codex
```

Run only the command for the intended harness. Default without a flag is `~/.agents/skills`. `--dest <parent-skills-directory>` supports project roots and custom homes. Existing skills are never overwritten. Refresh/restart the harness's skill list and ask it:

> Use subscription-quota. Check the current provider's billing mode and quota/reset windows, then plan this task using the verified hourly budget. If unavailable, say what is unknown and continue.

Installation does not guarantee automatic invocation or access to account telemetry. See [integration instructions](skill/subscription-quota/references/integrations.md) for each harness's data requirements. Do not uninstall or modify QuotaGuard to use this repository; choose which pacing preference you want for a task if both are installed.

## The rule

`hourly budget = remaining percentage / hours until reset`

The default reference adapts to window length: `100 / window hours` (20 percentage points/hour for five hours; ~0.595 for a week). Compare budget/reference: below 0.5 = TIGHT, below 1 = CONSERVATIVE, below 1.5 = COMFORTABLE, otherwise ABUNDANT. Set a window's `reference_pph` to 12 to retain the original QuotaGuard preference; it is not universal or an official provider limit.

Examples: 10% with two hours remaining gives 5 points/hour; 10% with fifteen minutes gives 40. The latter still has only 10% available. Under 10%, recommendations are capped at CONSERVATIVE. Zero is EXHAUSTED. Expired resets, stale readings, unknown billing and mismatched account scope produce UNKNOWN. Weekly restrictions cannot be overridden by a generous five-hour result.

Levels guide optional exploration and stage size. They never excuse missing requirements or tests, permit pointless quota consumption, or change hidden reasoning settings. This is a heuristic, not a prediction of tokens needed for the next task.

## Run helpers

```sh
python examples/demo.py
python -m unittest discover -s tests -v
python skill/subscription-quota/scripts/budget.py snapshot.json --route my-current-route
```

For live local Codex, verify the CLI profile matches the active session, then use `codex_snapshot.py --route my-current-route --confirm-current-route`. Without the flag, observations remain unverified and cannot produce a pacing recommendation. Never add it merely to silence UNKNOWN.

ZCode and DSH converters accept credential-free exports, not login files. See the [snapshot contract](skill/subscription-quota/references/snapshot.md). No secrets, telemetry or accounts are included in this repository. Synthetic demos are labeled and never presented as live integrations.

## Validation and limits

14 automated tests cover timing, weekly precedence, absolute quota, stale/scope/billing rejection, malformed numbers, native conversion and installation relocation/overwrite protection. A live Codex read on 2026-10-16 returned ChatGPT/Plus with 300-minute and 10,080-minute windows; no model generation or account mutation was performed by that probe. This validates the local reader, not another harness's current-session identity. ZCode/DSH live telemetry remains untested and requires a bridge. Linux/macOS execution and actual harness discovery were not end-to-end tested.

Sources and reviewed interfaces are linked in [integrations](skill/subscription-quota/references/integrations.md). MIT license. Not affiliated with OpenAI, Z.AI or DeepSeek.
