---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Follow the project's existing implementation and testing conventions.
Use the `tdd` skill only when explicitly requested or required by project instructions.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use the `code-review` skill to review the work.

Stage the completed work with `git add`, excluding unrelated changes, then suggest a commit message using the `commit-message` skill. Do not create the commit; leave the final review and commit to the user.
