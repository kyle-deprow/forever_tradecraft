# Private GNOME Screenshot no-flash experiment

Objective: remove a confirmed500ms flash wait from the exact GNOME capture path
without changing desktop settings, installed packages, screenshot pixels, native
schema, capture freshness or strict100one-Hz acceptance. This is a private build
and bounded benchmark proposal, not production acceptance. AGENTS.md revoked.

Evidence: live transparent timings show screenshotCLI1.021–1.038s, all21identity
queries264–268ms, totalidentity→decode1.629–1.641s. Installed Screenshot41.0-3,
Shell48.0-1ubuntu1.3, settings delay0/pointerfalse. Matching Screenshot Shell
backend hardcodes flashTRUE. Official Shell48.0 waits for capture and500msflash.
Remaining~0.52s CLI time is not yet decomposed. Existing user setting is not the
cause; do not change it or guess that removing flash alone meets1Hz.

## Stages and fences

1. Read-only feasibility: inspect exact installed/build dependencies and obtain
   authoritative source/provenance for the matching screenshot implementation.
   No package installs, service/process changes, captures, GUI/input or source
   edits yet. Record exact dependency availability and proposed build command.
2. After Sol plan acceptance, build in private `~/.cache/crowley/` from verified
   official source, with exactly the Shell backend flashTRUE→FALSE change.
   No system package/config/desktop changes, appID spoofing or fallback backend.
   Preserve source archives/checksums, patch, build logs, native binary SHA and
   dependency versions. No misleading version wrapper; no production profile
   or source changes. If development dependencies are missing, report exact
   blockers and legitimate private-build options before expanding scope.
3. Parent inspect provenance and one-line patch, actual version/help and build
   result. Sol and actual Opus review the bounded experiment and caller-identity
   behavior before any live execution. This does not reopen accepted captures.
4. Stage the actual benchmark proposal first. Account for GApplication's shared
   `org.gnome.Screenshot` service: invoking a private binary can forward to an
   already-running original. Prove which genuine implementation owns the bus
   name. No allowed-caller impersonation, forged ownership, compositor changes
   or reading another process's temporary screenshot. Any normal service
   transition must be explicitly scoped to the actual screenshot application,
   retain original state and restore normally. Do not silently change the appID
   to evade Shell's legitimate caller checks.
5. Once parent releases a concrete reviewed benchmark, sole operator measures
   bounded ordinary stationary captures through the same production identity,
   locking, completion, crop and decoder checks with the genuine private build.
   No formalnative/inputcalibration/movement/camera/AH/trades. Record absolute
   source/artifact paths, actual caller PID/exe/hash, command/PNG/wholepath times,
   complete images and fresh frames. Stop on identity/parse/permission failure;
   never count a failed/late frame as passing. Compare with prior observed timings.

If timing is still infeasible, retain the result and diagnose remaining cost.
Only after measured feasibility may a separate reviewed production binding be
implemented. The exact100freshordinals and all existing bounds remain required.

Workers own only new private build directories and
`/home/dev/repos/pegasus/.archive/executor-review/gnome-no-flash-*` artifacts.
Use absolute live-repo paths; long-lived workers can retain an old worktree cwd.
No git commits/reset/stash/revert, helper edits, host/profile/server/database
mutation, actual screenshot or input until the applicable stage is released.

## Authorized private dependency environment

Stage1 proved hostdevelopmentheaders/Meson/Ninja absent; Docker29.2.1 is already
available. Parent authorizes an isolated temporary Docker build container using
official Debian Bookworm (record resolved image digest), matching verified GNOME
source and signed distro development dependencies inside the container only.
Mount only a new private build directory, retain source/patch/logs/versioned
package list, and write artifacts owned by the host user. No privileged container,
Docker socket mount, host root/repository mount, host packages or host config.
The container may install its own build dependencies; this does not authorize
host installation or runtime screenshot/service execution. Compile/install under
a private prefix, then read-only host version/help/ldd checks of the genuine
binary. Record any ABI incompatibility instead of replacing host libraries.

IMPORTANT: there are three hardcoded flash booleans in the original source, but
only change the full-screen `Screenshot` call used by `-f`. Keep window and area
branches byte-identical. This is exactly ONE boolean modification; do not broaden
to all three just because the shared file contains them.

Use the upstream supported `-Dx11=disabled` build option for this private
experiment, and record it explicitly. This prevents the existing optional legacy
X11 screenshot fallback from silently satisfying the benchmark if the Shell API
fails. It does not change GNOME Shell capture or add another backend. Failure of
the Shell request must remain a failed capture. Source edits still total one
full-screen flash boolean; build configuration is separately disclosed.
