# GTK certificate review

Reviewer: gpt-5.6-sol, xhigh. Read-only; no tests or GUI operations.
Status: NEEDS WORK.

Accepted Must-Fix: geometry parsing collapses duplicate fields and accepts
trailing junk. Require exactly one complete field line and positive dimensions;
add missing, duplicate, conflicting, suffix and nonpositive regressions.

Accepted Should-Fix: replace invented GTK tree rows with retained native-format
rows, distinguishing deliberate mutations from captured data. Add compact
negative cases for mismatched frame-for, missing/duplicate/conflicting property
types and nonpositive user time.

The remaining scoped logic correctly pins measured Mutter identity, exact
children, advertised InputOnly helper and positive user time, excluding the
helper/root/foreign windows from input targets. Live acceptance remains pending.
The same Luna source worker owns these narrow repairs; other ownership stays
unchanged. Fresh review follows source freeze.
