# Sol plan review: recipe foundation R3

The two prior blockers are closed.

- The installed artifact is self-contained: it embeds the normalized v2 manifest, binds its canonical digest, and validates claim-to-locator permissions without reading `.archive` (`PLAN-recipe-foundation.md:6,24,157-159,176,180`). The raw snapshots and archive-only paths are consumed only by the separately named review helper in `tests/test_recipes.py`. This is feasible within the three-file implementation fence and the installed loader no longer depends on files omitted from the production image. The specified normalized digest, `7da0a957d6d04a5e351a9cba7c54ef622d816fa519c0682501c481a114187378`, matches canonical JSON for the frozen manifest with only `snapshot_path` removed.
- The pilot now uses only the four displayed thresholds, records output quantities as unknown, retains the known reagent quantities, and includes the forge/cooking-fire conditions (`:36-56,163-176,184,194-212`). Known factual paths have exact locator IDs and machine-checkable allowed field paths; derived and unknown/null fields are explicitly distinguished from source claims. The manifest provides all 34 bounded locators across the unchanged six snapshots, and the Mining example covers each retained known source fact. Cooking is required to use the same contract with its own listed locators and values.

No remaining issue in the bounded R3 closure requires another planning round.

STATUS: READY
