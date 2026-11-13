# Agent reliability lab

**Synthetic lab, built by me, not a client engagement.** Tests silent stalls first, retry
spending ceilings second, and duplicate effects after restart third. No pentesting, paid APIs,
Docker, package installation, or production credentials. Checker 0.1.0 / adapter contract 1.0.

## Start here (Python 3.10+, Linux/macOS)

From the cloned repository root (`agent-reliability-lab/` inside the consulting workspace):

```sh
./check sample --output sample-evidence.json      # expected exit 0: three held checks
./check reference --output reference-evidence.json  # expected exit 1: three known failures
python3 -m unittest discover -s tests -v          # one-command regression suite
```

The sample is **one minimal local order workflow**, independently implemented with SQLite;
it is not a framework integration or a real customer agent. The reference is a JSON-step model.
Allow under five minutes after clone with Python already installed; no dependency downloads.

**Your workflow:** read [CONTRACT.md](CONTRACT.md), implement its JSON-lines command adapter,
and point `./check /path/to/adapter.json --output evidence.json` at it. The five-minute claim is
for the supplied sample, NOT the effort to integrate an arbitrary foreign workflow. Read commands
before executing: adapters run with your permissions; this is NOT a security sandbox. Use a
throwaway VM/container for unfamiliar code. Missing evidence is inconclusive, never a pass.
Exit 0 = held under tested conditions; 1 = reproduced failure; 2 = inconclusive/setup error.

[REPORT.md](REPORT.md) contains measured outcomes, exact source pins, method limits and a
falsifier. No failure reproduced does not mean no bugs. Never use this tool's result as a
production reliability certification. See contract limits before interpreting results.
