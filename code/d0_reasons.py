"""TASK-0042 dispatch D0 withheld-category reasons.

Single source of truth for both the staging decision (d0_stage.py) and the
published explanations (MANIFEST.md and PUBLISH-STATUS.md via d0_report.py), so
a category cannot be withheld in one file and explained differently in another.
"""

HOLD_REASONS = {
    "shipped-starcraft-data":
        "Copy of shipped StarCraft map data. `base-map.scx` is Blizzard's stock Brood War map, "
        "`maps/rc.scm` is the shipped map `(2)River Crossing.scm`, and `live-seed.scm` is byte-identical "
        "to `maps/rc.scm` by `sha256sum`, so it is a copy of a shipped map rather than this team's "
        "authorship.",
    "harvested-reference-chks":
        "Reference CHK sections harvested from Blizzard-published maps under `ts-harvest/`. Extracts of "
        "a Blizzard map, not this team's authorship.",
    "chk-or-scx-intermediate":
        "CHK and SCX intermediates. Every `.scm` that landed is the MPQ container holding the same map "
        "data, and each `.chk` here is either an extract of a shipped Blizzard map or a decompressed copy "
        "of a `.scm` that landed.",
    "probe-map":
        "Throwaway calibration, tileset-probe and save-path-probe maps. Superseded by the calibration "
        "renders and gate reports that landed, and several of them are seeded from a shipped StarCraft "
        "map.",
    "upstream-library":
        "StormLib checkout, an upstream third-party library (MIT). Not this team's authorship and not in "
        "this dispatch's include list; its licence is ruled by `R4` and `R5`, and the build command that "
        "produces the tool this task used is recorded in `DEMO-LOG.md`.",
    "upstream-dataset":
        "Natural Earth GeoJSON downloaded from `nvkelso/natural-earth-vector` at tag `v5.1.2`. Upstream "
        "data declared public domain upstream. Re-publishing 17 MB of it verbatim is outside this "
        "dispatch's include list; the landed record names the repo, tag, commit `f1890d9f`, and the git "
        "blob SHA-1 of each file, which is enough to fetch and verify the same bytes.",
    "upstream-code":
        "`starcraft_mpq_io.py` and the `richchk` fragments, imported from upstream projects. Not this "
        "team's authorship, licence not yet ruled by `Charmy` and `Flicky`.",
    "compiled-binary":
        "ELF binaries the team built on the controller from the C sources that landed, `chkdump`, "
        "`mkmpq`, `rdp-input`, `rdp-shot`. Build artifacts, machine-specific, reproducible from the "
        "sources in `code/`.",
    "build-artifact":
        "`__pycache__` bytecode caches.",
    "build-log-or-probe":
        "Build, launch and error logs, and the bulk per-row tileset probe captures from the calibration "
        "stage, superseded by the calibration renders that landed.",
    "credential":
        "A scratch argument file for the team's own RDP input injector holding a live target credential "
        "in plaintext. Never published. Reported to the operator for rotation. Its value appears in no "
        "commit, no landed file, and no document in either repository.",
    "transient-note":
        "One-off scratch notes and partial hash lists superseded by `DEMO-LOG.md` and `MANIFEST.md`.",
    "undocumented-binary":
        "`colorbase.bin`, an opaque intermediate whose generating script no longer exists on the "
        "controller, so its provenance cannot be stated honestly.",
    "raw-desktop-capture":
        "Uncompressed PPM desktop sanity captures from the earliest control stage, superseded by the PNG "
        "capture sets that landed.",
}
