---
name: diagnosing-bugs
description: Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose"/"debug this", or reports something broken/throwing/failing/slow.
---

# Diagnosing Bugs

A discipline for hard bugs. Skip phases only when explicitly justified.

When exploring the codebase, read `CONTEXT.md` (if it exists) to get a clear mental model of the relevant modules, and check ADRs in the area you're touching.

## Redact

This skill has you show commands, outputs and captured artifacts. **Redact every secret first** — write `<REDACTED>` in its place. Build loops against env vars, so the credential stays in the environment rather than in what you show. Captured artifacts carry auth headers: quote only the lines that carry the signal.

If the redacted output is not enough to diagnose the bug, say so and ask the user.

## Phase 0 — Triage

Before building anything, spend a few minutes on the cheap moves:

1. **Read the full error.** The whole message, backtrace and any chained causes, not just the first line.
2. **Check what changed.** `git log` / `git diff` on the affected area, recent dependency or config changes, recent deploys. A bug that appeared after a known change is often explained by that change.
3. **Look at the code the error points to.**

Then decide:

- **Fast path:** take it when the cause is evident and the fix is local, e.g. a typo, wrong type, missing import, an obvious off-by-one at the line the backtrace names, or a failing test whose message states the problem. Fix it, add or update a test if there's a natural place for one, run the relevant tests, and stop. State in one line why you took the fast path.
- **Full loop:** take it when the cause isn't evident, the bug is intermittent, it involves concurrency, timing, state or data, it's a performance regression, or a fast-path fix already failed. Proceed to Phase 1.

If a fast-path fix doesn't make the symptom go away, don't try a second guess. Switch to the full loop.

## Phase 1 — Build a feedback loop

**This is the skill.** Everything else is mechanical. If you have a **tight** pass/fail signal for the bug — one that goes red on _this_ bug — you will find the cause; bisection, hypothesis-testing, and instrumentation all just consume it. If you don't have one, no amount of staring at code will save you. It's worth spending most of your effort here.

Reading code to find *where* to build the loop is expected; you need to know the code path to find a seam. What to avoid is acting on a theory about the cause before you have a loop to test it against.

### Ways to construct one

Pick whichever reaches the bug most directly; roughly in order of preference:

1. **Failing test** at whatever seam reaches the bug — unit, integration, e2e.
2. **Direct invocation** of the failing entry point: an HTTP request against a running dev server, a CLI run with a fixture input diffed against a known-good output, or a script that calls the function or service.
3. **Replay from evidence.** Reconstruct the triggering input from whatever was captured: log lines, database records, a saved request or message, an event sequence. You rarely have a full capture; rebuilding the relevant state and events from logs or DB rows is usually enough. Feed it through the code path in isolation.
4. **Throwaway harness.** A minimal subset of the system (one service, mocked or stubbed dependencies) that exercises the bug path with a single call.
5. **Property / fuzz loop.** If the bug is "sometimes wrong output", generate many random inputs and check an invariant (e.g. `proptest`/`quickcheck` in Rust, `hypothesis` in Python).
6. **Bisection harness.** If the bug appeared between two known states (commits, dependency versions, datasets), automate the check so `git bisect run <script>` can drive it.
7. **Differential loop.** Run the same input through two versions or two configs and diff the outputs.
8. **UI-driven loop.** For frontend bugs, a headless browser script (Playwright/Puppeteer) asserting on DOM, console or network.
10. **Human-in-the-loop script.** Last resort. If a human must click, drive _them_ with `scripts/hitl-loop.template.sh` so the loop is still structured. Captured output feeds back to you.

### Tighten the loop

Once you have *a* loop, improve it:

- **Faster:** cache setup, skip unrelated initialisation, narrow the test scope.
- **Sharper:** assert on the specific symptom, not "didn't crash".
- **More deterministic:** fake the clock, seed RNGs, stub network and filesystem, control scheduling where possible.

A 30-second flaky loop is barely better than none; a 2-second deterministic one makes the rest of the work fast.

### Non-deterministic bugs

The goal is not a clean repro but a **higher reproduction rate**. Loop the trigger 100×, parallelise, add stress, narrow timing windows, inject sleeps. A 50%-flake bug is debuggable; 1% is not — keep raising the rate until it's debuggable.

### When you genuinely cannot build a loop

Stop and say so. List what you tried. Ask the user for one of:

- access to the environment that reproduces it,
- redacted evidence (relevant log excerpts, DB records, a core dump, timestamps of occurrences),
- permission to add temporary instrumentation where it occurs.

Do **not** proceed to hypothesise without a loop; hypotheses you can't test just become guesses.

### Completion criterion — a tight loop that goes red

Phase 1 is done when the loop is **tight** and **red-capable**: you can name **one command** (a test invocation, script path or request) that you have **already run at least once** (show the invocation and its output, redacted), and that is:

- **Red-capable**: it drives the actual bug code path and asserts the **user's exact symptom**, so it can go red on this bug and green once fixed. Not "runs without erroring", it must be able to _catch this specific bug_.
- **Deterministic**: same verdict every run, or for flaky bugs a known, high enough reproduction rate.
- **Fast**: seconds, not minutes.
- **Agent-runnable**: you can run it unattended; a human in the loop only via `scripts/hitl-loop.template.sh`.

If you catch yourself reading code to build a theory before this command exists, **stop — jumping straight to a hypothesis is the exact failure this skill prevents.** No red-capable command, no Phase 2.

## Phase 2 — Reproduce + minimise

Run the loop and watch it go red. Confirm:

- It shows the failure the **user** described, not a different failure nearby. Wrong bug = wrong fix.
- The failure is reproducible across multiple runs (or, for non-deterministic bugs, reproducible at a high enough rate to debug against).
- You have captured the exact symptom (error message, wrong output, slow timing) so later phases can verify the fix actually addresses it.

### Minimise

Once it's red, shrink the repro by cutting inputs, data, callers, config and steps, re-running after each cut. This narrows the hypothesis space and gives you a clean regression test later.

Minimise until the remaining scenario is small enough that the plausible causes are few. You don't need a perfectly minimal repro if the cause is already narrowing, and if each loop run is slow, cut in large chunks (halve the input) rather than one element at a time.

## Phase 3 — Hypothesise

Generate **3–5 ranked hypotheses** before testing any of them. Generating only one anchors you on the first plausible idea. (If the minimised repro makes one cause overwhelmingly likely, fewer is fine; say why.)

Each hypothesis must make a testable prediction:

> "If <X> is the cause, then <changing Y> will make the bug disappear / <changing Z> will make it worse."

If you can't state the prediction, sharpen the hypothesis or drop it.

Post the ranked list to the user, then continue with the top hypothesis without waiting. The user may re-rank it ("we changed #3 yesterday") or rule items out, and you should adjust if they reply.

## Phase 4 — Instrument

Each probe must map to a specific prediction from Phase 3. **Change one variable at a time.**

Tool preference:

1. **Debugger or REPL inspection** where the environment supports it.
2. **Targeted logs** at the boundaries that distinguish your hypotheses.
3. Avoid logging everything and grepping.

Tag every temporary debug log with a unique prefix, e.g. `[DEBUG-a4f2]`, so cleanup is a single grep.

## Performance regressions

Perf bugs follow the same phases with different tools:

- **The loop is a benchmark,** and red/green is a threshold on a distribution, not a boolean. Run enough iterations with warmup to see past noise, and compare against a baseline with a statistical tool rather than single timings (e.g. `criterion` or `hyperfine` in Rust/CLI land, `pytest-benchmark` or `timeit` in Python). Note the variance; a change smaller than the noise isn't a regression yet.
- **Locate before hypothesising:** a profiler or flamegraph (`perf`, `cargo flamegraph`, `py-spy`, query plans for DB-bound paths) usually narrows the cause faster than logs, which can themselves distort timing.
- **Bisect when there's a known-good version:** wrap the benchmark and its threshold in a script and `git bisect run` it.

## Phase 5 — Fix and regression test

Write the regression test **before** the fix, but only if there is a **correct seam** for it.

A correct seam is one where the test exercises the **real bug pattern** as it occurs at the call site. If the only available seam is too shallow (single-caller test when the bug needs multiple callers, unit test that can't replicate the chain that triggered the bug), a regression test there gives false confidence.

**If no correct seam exists, that itself is the finding.** Note it. The codebase architecture is preventing the bug from being locked down. Carry it to Phase 6.

If a correct seam exists:

1. Turn the minimised repro into a failing test at that seam.
2. Watch it fail.
3. Apply the fix.
4. Watch it pass.
5. Re-run the Phase 1 feedback loop against the original, un-minimised scenario.

## Phase 6 — Cleanup and post-mortem

Required before declaring done:

- [ ] The original repro no longer reproduces (re-run the Phase 1 loop).
- [ ] The regression test passes, or the lack of a seam is documented.
- [ ] All `[DEBUG-...]` instrumentation is removed (grep the prefix)
- [ ] Throwaway harnesses are deleted, or moved to a clearly marked debug location.
- [ ] The commit or PR message states the hypothesis that proved correct.

**Then ask: what would have prevented this bug?** If the answer involves architectural change (no good test seam, tangled callers, hidden coupling), make that recommendation now, after the fix, with the specifics. If an `improve-codebase-architecture` skill is available, hand off to it.