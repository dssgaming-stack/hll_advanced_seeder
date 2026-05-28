# UTC Clan Seeder

UTC Clan Seeder is a Hell Let Loose auto-seeding helper adapted from the `hll_advanced_seeder` concept for use with the UTC clan environment.

The tool is intended for members who want their PC to monitor the UTC game server during a chosen period and automatically join when seeding is needed. The seeding configuration is already built into the software, so users do not need to edit server settings or maintain custom config files.

## What it does

- Monitors the UTC game server within a user-selected time window.
- Automatically joins the server when the configured seeding conditions are met.
- Uses preloaded UTC-specific seeding settings.
- Installs required dependencies for installation automatically through PowerShell.

## Requirements

No manual dependency setup is required for normal use.

The installer automatically downloads and installs:

- Python (running the tool)
- Git (keeping the tool up to date)

Users only need:

- A Windows system with PowerShell available (standard installed on Windows).
- Hell Let Loose installed.
- Permission to run the setup and launcher scripts.
- A stable internet connection while monitoring is active.

## Installation

1. Retrieve PowerShell script from UTC-admin.
2. Open PowerShell in the project folder.
3. Select the timeframe in which the computer should monitor the UTC server.
5. Your PC will now monitor the UTC server during that period.

After installation, no additional configuration should be necessary for standard UTC clan use.
Done seeding? An uninstaller is provided with the software also.

## Usage

1. Start the tool.
2. Select the timeframe in which the computer should monitor the UTC server.
3. Set the desired dates and hours for monitoring.
4. Leave the tool running during that period.
5. When the UTC server matches the built-in seeding conditions, the tool will join automatically.

This workflow is designed to keep usage simple: choose when monitoring is allowed, then let the tool handle the rest.

## Configuration

The UTC seeding configuration is already included.

This means users do **not** need to:

- Enter server connection details manually.
- Tune seeding thresholds.
- Import separate config files.
- Install Python or Git by hand.

If a future version exposes additional options, they should be treated as optional overrides rather than required setup.

## Notes

- The PC must remain powered on and connected during the selected monitoring window. Check your Energy Settings!
- If your PC is in sleep-mode, it will wake to run Hell Let Loose (if possible).
- PowerShell may request permission during dependency installation, depending on local system policy.
- Closing the application stops monitoring immediately.
- Any game-specific launch requirements still need to be met on the local machine.

## Troubleshooting

### PowerShell blocks the script

Try starting PowerShell as Administrator and review the local execution policy.

### Python or Git installation fails

Check internet connectivity, rerun the installer, and confirm that security software is not blocking downloads.

### The tool does not join automatically

Confirm that:

- The selected date range is currently active.
- The chosen monitoring timeframe includes the current time.
- Hell Let Loose is installed correctly.
- The tool is still running in the background.

## Intended audience

This tool is meant for UTC clan members who want a low-maintenance way to help seed the UTC Hell Let Loose server during approved times.
