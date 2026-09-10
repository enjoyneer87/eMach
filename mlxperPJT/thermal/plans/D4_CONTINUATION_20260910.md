# D4 continuation from Claude Code

Gateway: `E:\Code_Rep\Thesis_emach`; simulation host: `ssh iso`
(`DESKTOP-513NQ4P`, repo `D:\KDH\NvidiaNemo\eMach`).

## Latest state recovered

Claude Code session `d1bde0b0-fac2-4682-9a46-6aa2789b0caa` last wrote at
2026-09-10 19:05 KST. Its D4 commits are `b7973e7` and `7509c45`.
No D4 solver was running when continuation began.

Two launch failures have direct evidence:

- `_mc_launch2.txt`: schtasks rejected the executable path at `Files\ANSYS`.
- `mc_start.cmd`: the `\v261` part was corrupted into a vertical-tab character.

These failures do not establish that interactive scheduled execution is impossible.
Using structured `New-ScheduledTaskAction` arguments and an interactive principal,
the Python driver successfully started Motor-CAD in session 2, loaded a work copy,
read back the requested operating point, and entered FEA calculation.

## Smoke run (not yet a validated result)

- Task: `Codex_D4_Smoke_20260910`
- Started: 2026-09-10 19:08 KST
- Motor-CAD PID: `33904` (PID is a snapshot, verify before any process operation)
- Point: 16000 rpm, 460 A RMS, 36 electrical degrees
- Directory: `C:\work\_thermal_kit_20260910\codex_smoke`
- Driver log: `run.log`; output: `point.json`
- Model and solver artifacts: `model\e10Turn6V261\`

Check task exit code, result completeness, operating-point readback and loss
outputs before launching the full grid. A running process alone is insufficient.
`run_d4_interactive.ps1` provides a reusable fresh-run launcher; it refuses an
existing task, output directory or Motor-CAD process. Remove its one-off task
after checking completion. It does not attach to a user's open model.

## Result interpretation

The 16 krpm zero continuous rating is conditional on the existing loss model.
Adding current dependence does not guarantee a nonzero continuous rating.
Flat magnet loss is a warning for investigation, not proof of ignored inputs.
Input readback, solver completion, loss extraction and model assumptions require
separate checks. The requested grid is recorded in JSON, and material databases
are copied alongside the work model when available.

## PC1 input transfer verified

Company NAS directory: `N:\_thermal_to_pc1_20260910` on the gateway.
Do not publish these input assets to the public GitHub repository.

| File | Bytes | SHA-256 |
|---|---:|---|
| ff_e10_mesh_v2.cdb | 260255850 | 85d28691cad6c202d4b6e633106893c3073ec14f227fca27fcd26c19001fb240 |
| e10Turn6V261.mot | 678053 | 45d91a7802749467cb607129a8decf1a37ba5cdef3a29bf6312afada681123bf |

Both hashes match the previous transfer record. `E10Material.mdb` and
`README_transfer.md` are also present. PC1 access to the NAS is not verified here.

## First smoke completed; extraction not accepted

The first driver finished in 290.6 seconds (FEA 254 seconds). All thermal
`Loss_[...]` and copper injection values were zero even though requested
speed/current/phase readbacks matched. Its reported PASS is invalid for D4;
do not promote that JSON or start the full grid from that verdict.
The solver also logged an operating-point voltage-limit warning.

The revised driver reads the separate Magnetics outputs
`StatorIronLoss_Total_Adj`, `RotorIronLoss_Total_Adj`, `MagnetLoss_Adj`, and
`ConductorLoss`, all verified in the parameter catalog. It retains unadjusted
magnetic values and thermal injection values independently, records DC voltage
and the magnet 2D/3D factor, and rejects zero copper loss at positive current.
`cu_mcad` is now explicitly a DC diagnostic, not total copper including AC.

Second smoke location: `C:\work\_thermal_kit_20260910\codex_smoke_magnetic`.
Task name: `Codex_D4_Magnetic_Smoke_20260910`. Check this newer run before
any full-grid execution. Its result filename is `points.json`.
