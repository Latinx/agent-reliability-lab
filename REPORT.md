# Agent reliability lab — initial evidence report

**Synthetic lab, built by me, not a client engagement.** Authored from this project's initial
implementation and the retained command results, not from a customer system or prior corpus.
No production reliability or security certification is implied.


> Publication note: the `target` paths recorded in `evidence/*.json` are written relative to the
> repository root. The runs were made in a local checkout; no other field of the evidence was edited.

## Scope and reproduction

Two targets, three scenarios per target, one recorded acceptance run each. The JSON-step reference
contains intentionally seeded failures. The independently implemented command sample is one minimal
local SQLite order workflow, not an existing third-party product. It validates adapter portability
across these two implementations, not universal compatibility with arbitrary agents.

```sh
./check sample --output evidence/sample.json
./check reference --output evidence/reference.json
python3 -m unittest discover -s tests -v
```

Expected exit codes: sample 0, reference 1, regression suite 0. The recorded suite passed all five
tests in 0.986 seconds. The recorded sample CLI invocation took 0.235142099 seconds (wall clock).
No dependencies were installed. Subsequent **user-reported cold-run verification**: sample exit 0,
reference exit 1, regression suite 5/5, no dependencies installed, approximately one second.
The local execution half of the stranger criterion is closed on that evidence; this cold run was
not rerun by the assistant. **Published** at <https://github.com/Latinx/agent-reliability-lab>, and then re-verified from a
clean clone of the first published revision (`a6c9854`): clone 501 ms; `./check sample` exit 0
(three held, 259 ms); `./check reference` exit 1 (three reproduced, 227 ms);
`python3 -m unittest discover -s tests` exit 0 (5/5, 1003 ms); no author home-directory path in the
published tree. The full clone-to-run criterion is **closed**.

Recorded environment: Python 3.13.5, Linux 6.18.58.1-microsoft-standard-WSL2.
Evidence report generated UTC: 2026-11-13T21:00:26.138355+00:00

## 1. Silent stall with a healthy monitor

Reference: **failure reproduced**. After meaningful progress, the checker froze work, left the
process alive, waited beyond the 100 ms fixture deadline and observed unchanged progress with
health still true. This is deliberately seeded liveness-only monitoring, not a newly discovered bug.

Sample: **check held under tested conditions**. Progress remained frozen and the process alive,
but its task-progress monitor reported unhealthy at the final observation. This is a bounded null
result, not proof against every possible stall. The runner observes only the final state; it does
not measure the exact transition time or establish detection within precisely 100 ms.

- reference: progress 1 → 1; monitor healthy true; observation after 0.150532 seconds; subprocess alive.
- sample: progress 1 → 1; monitor healthy false; observation after 0.150393 seconds; subprocess alive.

Impact: a liveness-only monitor can conceal blocked work. No real outage duration or lost revenue
was measured. Priority 1 fix: monitor task-specific progress with a workload-appropriate deadline
and explicit unhealthy status. Effort: small for this fixture; production effort requires scoping.
Regression: the suite requires the known bad monitor to reproduce failure and the sample to report
unhealthy while still alive. Long legitimate tasks and intermittent stalls are outside this test.

## 2. Retry sequence without an enforced spending ceiling

Reference: **failure reproduced**. Ten synthetic billed attempts incurred 10 cost units (5 per run),
exceeding both the per-run limit of 2 and shared synthetic-day limit of 3.

Sample: **check held under tested conditions**. The same requests incurred 2 units in the first run
and 1 in the second, total 3. Later requests incurred no additional charges in its SQLite ledger.

Impact: the seeded reference incurred 7 units beyond the shared cap in this bounded sequence.
These are integer synthetic cost units, NOT dollars, model tokens, provider invoices, or a forecast
of real loss. No paid API was contacted. Priority 2 fix: enforce admission before a billable action,
including retries, with durable run/day accounting. Effort: small in this serial fixture; concurrent
reservations and provider settlement need separate scoping. Regression asserts the observed totals
and makes absent billing evidence inconclusive. The checker drives retries; it does not establish
that a real agent's retry scheduler or provider enforces these caps.

## 3. Duplicate effect after process restart

Reference: **failure reproduced**. One effect committed without a completion checkpoint. After an
actual process-group kill and restart against preserved state, replay produced two `order-1` effects.

Sample: **check held under tested conditions**. The same crash window and replay left one visible
effect; a SQLite unique task key deduplicated delivery independently of the completion checkpoint.

Impact: one duplicate synthetic order, not an actual charge or customer action. Priority 3 fix:
use a durable idempotency key at the effect sink and replay against it after crashes. Effort: small
for the local SQLite sink, unknown for an external service without an idempotency primitive.
Regression asserts the exact visible effects before/after replay. Other crash windows, simultaneous
workers, remote sink failures and distributed exactly-once delivery are not tested.

## Conclusion and falsifier

The detector reproduces its three seeded reference failures. No failure was reproduced in the
sample under these three serial, isolated scenarios. This says its tested controls held, not that
the checker independently discovered bugs or that all agents are reliable. No check was skipped
or inconclusive in the two recorded acceptance runs. Regression tests separately establish that
missing hooks, absent billing and an uncommitted effect precondition do not become false passes.

**This report would be wrong if, with the pinned sample and the same scenarios, trustworthy target
observations showed a still-healthy stalled worker at the final observation, incurred cost above
either declared cap, or a second committed effect after the recorded restart, contrary to its traces.**

The adapter's truthful observation of the target is a trust boundary. These tests cannot independently
prove that an adapter is honest or that its source manifest includes every dependency. No network
isolation is enforced. Only locally reviewed fixtures were executed; unfamiliar integrations require
a disposable sandbox. See CONTRACT.md for request deadlines, exit codes, reset/cleanup and limits.

## Exact source identities (SHA-256)

The published source is <https://github.com/Latinx/agent-reliability-lab>; `v0.1.0` points to
`a9ef410` following the publication-path scrub. The hashes below identify the original tested
checker, adapter implementation and configuration; subsequent publication edits changed evidence
target-path labels and report prose, not those tested components. Retained `evidence/*.json`
contains the operation traces and pins. Checker **0.1.0**, adapter contract **1.0**. Hashes were
checked before and after target execution; they pin local files, not remote services or
undeclared dependencies.

| Component | SHA-256 |
|---|---|
| Checker / contract `check` | `da8c891e2da22a7c5e3300076319238114fad6883a179693b8775a435fc5f965` |
| Checker / contract `model.py` | `50aba3466056262dcc65637e85d9eb09e0a17408d299740cf3d258da35cec7c2` |
| Checker / contract `CONTRACT.md` | `8a86f5351b370cf9f6380949a174627db9b28b492ddfb35298b952c133e65f32` |
| reference config | `30b4a69b58109822224cc95766bad7c8b69532ba611f7d066833b41a331b2e3e` |
| reference: `adapter.json` | `30b4a69b58109822224cc95766bad7c8b69532ba611f7d066833b41a331b2e3e` |
| reference: `../model.py` | `50aba3466056262dcc65637e85d9eb09e0a17408d299740cf3d258da35cec7c2` |
| sample config | `976268039d3abba02ae3188a75d6df6e3a60a9dbae4ab01fb4020752d155f2ca` |
| sample: `worker.py` | `4bdb53300b34831e1ec16e190162dd03727a3f3e85be3f149abd0239f8b1fe47` |
| sample: `adapter.json` | `976268039d3abba02ae3188a75d6df6e3a60a9dbae4ab01fb4020752d155f2ca` |

## Time box and next decision

The initial implementation and recorded checks were completed in this working session, without
expanding to a framework integration. The budget remains three working days / 24 hands-on hours;
no comprehensive time ledger was kept, so no exact hours-used claim is made. The user-reported
clean clone closes distribution verification. The next work is the service page, scorecard and
prospect list, not expansion of the sample or implementation of the v2 guardrail candidate.
MIT licensing was added locally after publication; this is an unreleased change intended for a
future `v0.1.1`, not a claim that a new release exists. The `v0.1.0` tag is not moved.
