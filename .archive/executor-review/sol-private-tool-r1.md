# Private input tool review

Actual gpt-5.6-sol xhigh, read-only. STATUS MAJOR ISSUES. Parent accepted all
concrete findings for one focused correction before native input release.

Must: explicit positive admission token (EOF on owner death must not exec);
watchdog death/state publication failure must block admission; existing-artifact
builder paths require the same static-link/XTEST-call checks as fresh builds;
all constructor error paths close owned pinned FDs; actual revoke-after-disk-
replacement and pre-registration owner-death regressions are required.

Should accepted: hash the sealed image itself; typed native release spec instead
of magic command spelling; validate injected backend and driver display/auth
agreement before lease/image duplication; test publication drift through the
actual DesktopDriver to prove armed revocation, evidence/readiness clearing.

The source archive/hash, no committed compiled artifacts, convergence on the
pinned image and digest binding were confirmed by read-only inspection.

Parent additional observed protocol issue: the watchdog can read an earlier
P/R state, then notice owner death while a later H record remains queued; it
must consume final ownership before cleanup. Its parser also interprets an
incomplete non-newline chunk immediately. Require complete framing plus either
acknowledged latest ownership before physical admission or a proven final-state
drain before owner-death cleanup. Add actual no-input interleaving/fragmentation
tests. These follow directly from guardian.py's read4096/parse/death-check order.
