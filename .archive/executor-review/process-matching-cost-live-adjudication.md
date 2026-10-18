# Process matching cost live adjudication

The retained after-filter evidence is at `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/identity-latency-after-filter-binding-20261018`. Its manifest, report, and three response files were read offline. The source and plan inputs were not changed.

The restored source binding is `fe439243afdb7e2fd0ba8244819eac2fa9086761`, with the restored `driver.py` hash `ca0ca123d0fa09d8361c8632d9cc1c2c501d87adf99cb3cc268688dd4291a166`. The other six named source hashes are also recorded in [identity-latency-after-filter-20261018-summary.json](/home/dev/repos/pegasus/.archive/executor-review/identity-latency-after-filter-20261018-summary.json). The named configuration’s raw hash, semantic hash, and pinned producer hash matched the retained manifest without exposing configuration contents. A fresh rollback manifest was written at `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/identity-latency-rollback-binding-20261018/manifest.json`; its directory is `0700`, file is `0600`, and its SHA-256 is `5a3e3311bbc5f4f601a906b637857a9de88160f357183512027006e5b929c67a`.

The before evidence contains three requests, four reached barriers per request, and twelve `proc_match` spans. The owner-thread CPU/wall medians by process-match barrier were:

| Barrier | Count | CPU median (ms) | Wall median (ms) |
| --- | ---: | ---: | ---: |
| `daemon_pre` | 3 | 105.277835 | 105.547809 |
| `backend_pre` | 3 | 105.033735 | 105.789960 |
| `backend_post` | 3 | 102.839772 | 103.143155 |
| `daemon_post` | 3 | 102.949214 | 103.064664 |

The after-filter evidence also has three requests, but all three responses are unsuccessful at `region_capture`. Each artifact is partial and binding-consistent. Only `daemon_pre` and `backend_pre` were reached in each request; `backend_post` and `daemon_post` were not reached. The six available process-match spans have these medians:

| Barrier | Count | CPU median (ms) | Wall median (ms) |
| --- | ---: | ---: | ---: |
| `daemon_pre` | 3 | 34.100135 | 35.375467 |
| `backend_pre` | 3 | 33.187342 | 40.059847 |
| `backend_post` | 0 | unavailable | unavailable |
| `daemon_post` | 0 | unavailable | unavailable |

The pooled CPU median is descriptively lower in the observed spans (`103.158364 ms` across 12 before spans versus `33.6437385 ms` across 6 after spans), but the counts and reached barrier sets are unequal. This does not establish a four-barrier performance comparison, and no four-median acceptance assertion is made.

Adjudication: **FAIL — incomplete comparison**. The required live acceptance needs all four fresh barriers in every after-filter request, all four new medians decreasing, a pooled reduction threshold, no changed phase/error, and unchanged matched identity. The retained after-filter run ended earlier in `region_capture` with only two barriers reached per request, so the acceptance cannot pass. This record makes no causal regression claim and no Rust-trigger claim. No new samples were run or authorized.

The machine-readable proof record is [identity-latency-after-filter-20261018-summary.json](/home/dev/repos/pegasus/.archive/executor-review/identity-latency-after-filter-20261018-summary.json).
