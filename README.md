# UTC Clan Seeder

UTC Clan Seeder is a Hell Let Loose auto-seeding helper adapted from the `hll_advanced_seeder` concept for use with the UTC clan environment.

This updated repository replaces the legacy `.bat` workflow with a single PowerShell entry point that can install dependencies, create or remove the scheduled task, run the seeder immediately, validate configuration, and open the live YAML configuration used by the Python runtime.

## What changed

- Replaced `setup.bat`, `runGame.bat`, `requirements_pip_install.bat`, `verify.bat`, and `uninstall.bat` with one script: `Manage-HLLSeeder.ps1`.
- Removed the XML placeholder replacement flow based on `repl.bat`; scheduled tasks are now created natively in PowerShell.
- Added command-line switches to `seeding.py` so the launcher can validate configuration, run with an explicit config path, or print the effective settings without editing source code.
- Preserved `seeding.yaml` as the authoritative game-server configuration file.

## Requirements

- Windows with PowerShell 5.1 or newer.
- Python 3 installed and available as `py`, `python`, or `python3`.
- Hell Let Loose installed on the local machine.
- A valid `seeding.yaml` at the repository root unless `-ConfigPath` is used.

## Quick start

1. Open PowerShell in the repository folder.
2. Run `./Manage-HLLSeeder.ps1`.
3. Choose `Install` to install requirements and create the daily scheduled task.
4. Use `RunNow` to test the seeder immediately.

## Common commands

- `./Manage-HLLSeeder.ps1 -Action Install -StartupTime 10:00:00`
- `./Manage-HLLSeeder.ps1 -Action RunNow`
- `./Manage-HLLSeeder.ps1 -Action Verify`
- `./Manage-HLLSeeder.ps1 -Action EditConfig`
- `./Manage-HLLSeeder.ps1 -Action ValidateConfig`
- `./Manage-HLLSeeder.ps1 -Action Uninstall`

## PowerShell manager actions

- `Install`: Install Python dependencies and create or replace the `HLLAdvSeeder` scheduled task.
- `Uninstall`: Remove the scheduled task only; keep repository files and `seeding.yaml`.
- `RunNow`: Launch `seeding.py` in a new console window.
- `Verify`: Show scheduled task status and next run time.
- `EditConfig`: Open `seeding.yaml` in Notepad.
- `ValidateConfig`: Ask Python to parse and validate the YAML without starting the seeder loop.
- `ShowConfig`: Print the effective configuration summary from Python.
- `InstallDeps`: Run `pip install -r requirements.txt`.
- `CreateTask`: Create or replace the scheduled task without reinstalling dependencies.
- `RemoveTask`: Remove the scheduled task only.

## seeding.yaml

`seeding.yaml` is still required by default. The seeder reads it at runtime for debug controls, seeding windows, priority monitoring, player thresholds, query timing, perpetual mode behavior, and player identity settings.

Do not delete this file during install or uninstall. If you want to test an alternate configuration, run Python with `--config path\\to\\other.yaml` or pass `-ConfigPath` through the PowerShell manager.

## Notes

- The scheduler launches the script from the repository root so relative imports and `seeding.yaml` resolution continue to work.
- `TaskSchedulerTemplate.xml` is retained only as a reference from the original project and is no longer required by the new workflow.
