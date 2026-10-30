# Issues Found — gym_membership_system.py

Line numbers refer to the ORIGINAL file. Ordered by severity (High → Low).
Tool results: Pylint 4.81/10, Bandit 6 issues (2 High, 1 Medium, 3 Low), Flake8 9 issues.

| # | Issue | Type | Line(s) | Description | Fix Approach |
|---|-------|------|---------|-------------|--------------|
| 1 | Shell command injection (Bandit B605, High) | Security | 58 | `os.system("echo ... " + filename)` builds a shell command from a variable, so a filename like `x; rm -rf ~` would execute. The shell isn't needed at all. | Removed `os.system`; replaced with `print(...)`. |
| 2 | Weak hash MD5 (Bandit B324, High) | Security | 47 | `hashlib.md5` is cryptographically broken (collisions). Unsafe if the hash is ever used for identity/integrity. | Switched to `hashlib.sha256`. |
| 3 | Use of `eval` (Bandit B307 / Pylint W0123, Medium) | Security | 42 | `eval(discount_expr)` runs arbitrary code from the caller (remote code execution if the string is user-supplied). | Removed `eval`. Function now takes a numeric `discount` (0.15 = 15% off), validates 0–1, returns `fee * (1 - discount)`. |
| 4 | Hard-coded secret (Bandit B105, Low) | Security | 70 | API secret stored in source code, so it lives in git history for everyone with repo access. | Read from env var `GYM_API_SECRET` via `os.environ.get`. |
| 5 | Secret printed to console | Security (not tool-flagged) | 79 | Program prints the portal secret to stdout/logs. | Print only whether it is configured (`True/False`). |
| 6 | Insecure random for PIN (Bandit B311, Low) | Security | 51 | `random` is predictable (Mersenne Twister); not suitable for PINs/credentials. | Used `secrets.randbelow(9000) + 1000`; removed unused `random` import. |
| 7 | try / except / pass (Bandit B110, Low) | Security/Bug | 26-27 | Silently swallows every error; caller can't tell if cancellation worked. | Catch only `KeyError`; function returns `True/False`. |
| 8 | Bare except (Pylint W0702, Flake8 E722) | Bug | 26 | Catches `KeyboardInterrupt`/`SystemExit` and hides real bugs. | `except KeyError:` (same change as #7). |
| 9 | Mutable default argument (Pylint W0102) | Bug | 15 | `member_log=[]` is created once and shared across all calls. | Default `None`; fall back to a clearly named module-level `activity_log`. |
| 10 | File opened without `with` / encoding (Pylint R1732, W1514) | Bug/Quality | 55-57 | File leaks if `write` raises; encoding depends on OS. | `with open(..., encoding="utf-8")`; also write valid JSON instead of `str(dict)`. |
| 11 | `== None` comparison (Pylint C0121, Flake8 E711) | Style/Bug | 32 | Equality can be overridden; `None` is a singleton. | Use `is None` (simplified to `member is not None and ...`). |
| 12 | Redundant if/else returning booleans (R1703, R1705) | Quality | 34-37 | Four lines to return a boolean expression. | `return member is not None and member["months_left"] > 0`. |
| 13 | Unused variables (W0612, Flake8 F841) | Quality | 31, 41, 63 | `locker_deposit`, `base_fee` (inside eval), loop var `m` never used. | Removed `locker_deposit`; `base_fee` now genuinely used; loop rewritten with `sum(...)` over `.values()`. |
| 14 | Shadowing global `members` (W0621) | Bug-prone | 61 | Parameter name hides the module-level dict. | Renamed parameter to `roster`. |
| 15 | Non-snake_case names (C0103) | Style | 15, 23, 30, 40 | `registerMember`, `cancelMembership`, `checkMembershipStatus`, `calculateRenewalRate`. | Renamed to `register_member`, `cancel_membership`, `check_membership_status`, `calculate_renewal_rate`; callers updated. |
| 16 | Missing docstrings (C0116) | Style | 15,23,30,40,46,50,54,61,69 | 9 functions undocumented. | Added one-line docstrings. |
| 17 | Old-style `%` formatting (C0209) | Style | 19 | `%` string formatting. | f-string. |
| 18 | Unused import `math` (Pylint W0611, Flake8 F401) | Style | 6 | Dead import. | Removed. |
| 19 | Lines > 79 chars (Flake8 E501) | Style | 10, 11, 18 | Three long lines (80, 83, 93 chars). | Wrapped dicts across lines. |
| 20 | No newline at EOF (Pylint C0304, Flake8 W292) | Style | 82 | File ends without newline. | Added final newline. |
| 21 | `main()` runs on import (not tool-flagged) | Design | 82 | Importing the module executes the demo. | Wrapped in `if __name__ == "__main__":`. |

## Observed but deliberately NOT changed (logic/business questions)
- **Fee ignores plan:** `register_member` charges `50.0 * months` for every plan, but seed data implies Gold = 100/month, Silver = 350 for 1 month, Platinum ≈ 83/month. Diana (Gold, 3 months) pays 150 vs 300 under Alex's rate. The correct pricing rule is unknown, so I flagged it rather than guess.
- **Unknown IDs:** `calculate_renewal_rate` raises `KeyError` if the member doesn't exist.
