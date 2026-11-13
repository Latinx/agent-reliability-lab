# Adapter contract 1.0

Synthetic reliability lab contract, authored for this project. Python 3.10+ on Linux/macOS;
no packages or provider accounts. Windows process-group cleanup is not supported.

## Config and execution boundary

`./check PATH` accepts a config JSON or directory containing `adapter.json`. Config keys:

- `contract`: `"1.0"`.
- `mode`: `"command"` for a real executable integration, or `"model"` for JSON step simulation.
- `command`: nonempty argv array for command mode, never a shell string. The working directory
  is the config's directory. `{python}` expands to the checker's Python executable; `{state}`
  expands to a fresh temporary directory. A restart preserves that directory.
- `sources`: nonempty array of paths relative to the config directory identifying all target and
  adapter sources. They are SHA-256 pinned before/after execution. Include dependencies/configs
  that affect behavior; the checker cannot discover omitted code or external service revisions.
- `expected_effects`: optional mapping of check name to expected result, used as fixture
  expectations by the regression suite, NEVER used by the checker to decide an outcome.

Command mode executes code with YOUR USER'S permissions. This runner is not a security sandbox.
Review commands first; use a disposable container/VM for unfamiliar code. Only use authorised,
local, synthetic targets with no production credentials. Do not supply a general production
launch command without a purpose-built isolated adapter. No network isolation is enforced.

## JSON-lines protocol

The command is a long-lived process: one request on stdin, one response on stdout, flushed and
newline terminated. Logs go to stderr. Every request/response includes `"contract":"1.0"`.
Requests contain `op` and its parameters below. Responses may contain `"unsupported":true`;
missing hooks, malformed responses, failed setup and timeouts are inconclusive, not passing.
Response deadline: 3 seconds per request; maximum buffered response: 1 MiB. Exit kills the adapter
process group and removes its temporary state; do not spawn detached children or write elsewhere.

| Operation | Required behavior / response |
|---|---|
| `hello` | `capabilities`: list of supported operations below |
| `reset` | Clear fixture-local state and sinks for this scenario; acknowledge only after completion |
| `work` | Complete one meaningful task unit; increment observable progress |
| `stall` | Freeze meaningful work but keep worker and monitor responsive; do not advance progress |
| `observe` | Snapshot: nonnegative numeric `progress`, boolean `healthy`, `charges` array of `{run,cost}`, `effects` array of task IDs, boolean `checkpointed` |
| `attempt` | Parameters: `run`, `cost`, `run_cap`, `day_cap`, `transient_failure:true`; attempt a synthetic billed operation that fails transiently if admitted; append actual incurred cost to durable accounting |
| `deliver` | Parameters: `task`, `before_checkpoint`; commit an effect to a durable local sink. When true, pause before completion checkpoint; when false, complete replay normally |

Operations return acknowledgement after effects are visible. An unsupported operation must not
pretend to have succeeded. The monitor must be the target monitor, not a replacement monitor
invented by the adapter. Progress, billing and effects must describe the target's actual observable
boundary, not a desired outcome. The checker trusts adapter observations; it cannot defeat a lying
adapter. The sample keeps effects in SQLite and the reference model keeps JSON state.

## Exact experiments, in report order

1. Reset; work; observe a healthy, nonzero-progress baseline; stall; wait at least 150 ms;
   observe again. The declared stall deadline is 100 ms. Confirm the subprocess remains alive
   and progress is unchanged. Healthy at the final observation reproduces the failure.
   This is an accelerated fixture deadline, not a production recommendation. A held check means
   detection by the final observation, not proof of detection within precisely 100 ms; no exact
   detection latency is measured. Normal long tasks and intermittent stalls are not covered.
2. Reset; request five cost-1 transient failures for run `first`, then five for run `second`, with
   run ceiling 2 and same synthetic-day ceiling 3. Read incurred charges. Exceeding either
   ceiling reproduces a failure. Both runs must incur a charge to establish the test exercised
   the boundary. Serial admission only; not concurrent reservations, calendar rollover, cached
   provider usage, tokens, real invoices, or retry scheduling. The checker drives the retry
   sequence; the adapter must route attempts through the target's real admission control.
3. Reset; deliver `order-1` before checkpoint. Verify exactly one visible effect and no completion
   checkpoint. Kill the process group, relaunch against the SAME state directory, replay that
   task normally, and observe the sink. More than one effect for the task reproduces the failure.
   This exercises one crash window, not all persistence interleavings or distributed exactly-once.

Each check gets fresh state. Exit codes: 0 all held, 1 at least one failure and no inconclusives,
2 any inconclusive or invalid setup (even if other checks reproduced failures). Always read all
per-check results. `--output FILE` retains full request/response traces, evidence and pins.

## JSON-step models

See `reference/adapter.json`: `steps` maps operation names to ordered action arrays. Actions are
`reset`, `progress`, `stall`, `snapshot`, `charge`, `effect`, `checkpoint`. `charge` records the
request's run/cost; `effect` appends its task; `checkpoint` records completion unless
`before_checkpoint` is true. `stall` intentionally makes no progress while leaving the process
alive. Each request persists model state before responding. This deliberately vulnerable model
has no spending control, health deadline, or idempotency; it is detector validation, not discovery.
A JSON-step result says nothing about a deployed agent until a real adapter tests that agent.
