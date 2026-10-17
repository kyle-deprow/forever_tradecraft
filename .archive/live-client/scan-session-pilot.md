# Three-sweep session pilot

Authorized window: 2026-10-15 06:54:52–07:54:52 UTC. The initial state was an account-conflict dialog (`BLZ51900060`), documented below. Under the plan's explicit one-reconnect exception, I performed one recovery through the already-authenticated Battle.net client and its game reconnect control, without credentials or another client. It succeeded: the client reached character select and entered Arthur. No repeated conflict or credential prompt occurred.

At 06:56:23 UTC, one local `WowB.exe` process and one WoW window were present. Battle.net was foreground with an account-conflict warning; the existing game's login screen showed the same conflict. At approximately 07:04 UTC I dismissed the game's notice, used the existing launcher's single Reconnect control, then the existing game's Reconnect control once. The launcher began logging in; the game then reached character selection. I selected Arthur Aguafuerte (Ironforge) and entered the world. No duplicate client was started.

At approximately 07:14 UTC Arthur loaded in Ironforge at the established AH location (24.0,72.0), beside Auctioneer Buckler. `/crowley status` showed house `beta-normal-alliance (auto)`, plan `0712de248d42`, 428 IDs, cadence ready, cursor 159, previous run 293/428 attempted with 136 failed, and zero stored sweeps. I opened Buckler's AH at approximately 07:15 UTC; a scan was due and the AH-open scheduler should start it. The prepared `/crowley status` command after AH open was submitted, but its result was obscured behind the AH panel. The status result was obscured, but the saved native record later established the exact start time.

A helper issue was corrected in `/tmp/crowley-game-control.py`: it previously stripped the slash from a prepared command. I verified the command buffer visually after correction, and submitted only the exact `/crowley status` command. No chat message was sent publicly.

## Initial read-only baseline

SavedVariables inspection at 07:02:37 UTC found zero pending scans and last-sweep counters 293/428 attempted. No pilot UID/upload/acknowledgement existed at that point. Companion remained active; no services or configuration were changed.

## Sweep 1

- UID `beta-normal-alliance-1792048509-Arthur-7339`; house `beta-normal-alliance`; plan `0712de248d42`.
- Native start `2026-10-15 07:15:09 UTC`; native finish `07:23:17 UTC`; duration 488s. It was saved by `/reload` at approximately 07:27 UTC.
- Native record: 428 observations, 2,725 rows, 0 failures; parent DB verification reports 308 full + 21 bounded commodities and 99 full items, with zero incomplete or unqueried IDs.
- Server DB received it at `07:28:28.607172 UTC`; the companion logged HTTP 200 at `07:28:29.506 UTC`, sweep row 7, 428 observations and 2,725 rows. The companion journal proves `Crowley_Data/Data.lua` was written with one acknowledgement at `07:28:29.522 UTC`, immediately after the upload. The operator observed the UID by `07:33:29 UTC`, a later refresh; that observation time is not acknowledgement publication latency.
- Native finish to accepted upload took about 5m12s. The AH closed on reload. The next native start was `07:36:05 UTC`; the target `07:30:09` had already passed. The operator's save/check/reopen procedure missed the cadence; companion acknowledgement publication did not require a five-minute refresh wait.

## Sweep 2 and closeout

- UID `beta-normal-alliance-1792049765-Arthur-6163`; house `beta-normal-alliance`; same plan `0712de248d42`.
- Native start `2026-10-15 07:36:05 UTC`; native finish `07:44:05 UTC`; duration 480s. Saved on the normal `/reload` at approximately 07:46 UTC.
- Native record: 428 observations, 2,688 rows, 0 failures. Parent DB verification reports 307 full + 22 bounded commodities and 99 full items, with zero incomplete or unqueried IDs.
- Server accepted it (HTTP 200) at `07:47:42 UTC`; DB has 428 observations and 2,688 rows. `Crowley_Data/Data.lua` contained this UID at that time. A normal `/reload` was then issued to load the posted acknowledgement. The subsequent normal `/logout` returned to character select; the on-disk `Crowley.lua` parse after logout showed zero pending scans. I did not capture a separate in-game acknowledgement chat line.
- The two native starts were 1,256 seconds apart, 356 seconds later than the 900-second target. Sweep 1 ended at 07:23:17 and sweep 2 began at 07:36:05, a 768-second finish-to-start interval. Sweep 1 was not recognized until the operator waited past the 600-second cap and reloaded around 07:27. Upload and acknowledgement publication both completed at 07:28:29, but the operator observed the later 07:33:29 refresh before reopening the AH. This unnecessary wait contributed to missing the 07:30:09 slot. Sweep 2 finish-to-upload was 217s; sweep 1 finish-to-upload was 312s.

## Pilot result

Two consecutive useful sweeps completed, were accepted by the correct beta house, and had acknowledgements posted; the final acknowledgement was followed by a normal reload and normal logout, and the disk queue was verified empty. Combined new rows: 5,413. There was no third sweep: its earliest 900-second slot after sweep 2 was 07:51:05, and a full run at the observed 480-second duration plus closeout could not fit before the 07:54:52 collection cutoff. No late scan was started. Therefore the three-sweep acceptance target was not met, and the starts were not 900 seconds apart. After cutoff, only the already-authorized final acknowledgement/flush/logout cleanup was completed. Final screen showed Arthur selected at character select; AH closed. No credentials were entered, no public chat was sent, no trade actions occurred, and no recurring schedule was configured.
