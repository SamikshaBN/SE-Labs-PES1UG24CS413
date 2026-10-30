# Reflection

> NOTE: confirm these are the exact four questions in your handout/instructor sheet (the PDF text I was given did not list them). Adjust headings if they differ.

**1. Which issues were the easiest to fix and which were the hardest?**
Easiest: the style/mechanical ones: unused import, `== None`, missing newline, snake_case renames, f-strings. Pylint and Flake8 tell you exactly what to change. Hardest: `eval` (B307). You can't just "fix" it, because the function's design (taking an expression string) was the problem. I had to change the function's interface to take a numeric discount and update the caller. The hard-coded secret also needed a design change (env var) rather than a one-line edit.

**2. Did the tools report any false positives, or miss anything?**
Mostly accurate. The MD5 finding (B324) is arguably a false positive in spirit, since a member-ID fingerprint isn't a security control, but switching to SHA-256 costs nothing, so I treated it as real. The `random` PIN finding is Low severity but correct for a PIN. The tools missed logic problems: fee ignores the plan, `main()` runs on import, and the secret was printed to the console. Only running the program and reading the code found those.

**3. How would you integrate static analysis into a real workflow?**
Run Flake8 and Pylint as a pre-commit hook so style problems never reach the repo, and run all three tools in CI (e.g. GitHub Actions) on every pull request, failing the build on any Bandit High/Medium finding or a Pylint score below a threshold (e.g. 9.5). Bandit especially belongs in CI as a security gate.

**4. What tangible improvements did you see in the code?**
Pylint rose from 4.81/10 to 10.00/10, Bandit went from 6 issues (2 High, 1 Medium) to 0, and Flake8 from 9 issues to 0. Beyond the numbers: no code-injection paths (`eval`, `os.system`), no secret in source, a mutable-default bug removed, resources closed safely, and functions documented. The code is easier to read, review and import without side effects.
