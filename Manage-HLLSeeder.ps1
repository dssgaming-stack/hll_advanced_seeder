#requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateSet('Install','Uninstall','RunNow','Verify','EditConfig','ValidateConfig','ShowConfig','InstallDeps','CreateTask','RemoveTask')]
    [string]$Action,
    [string]$TaskName = 'HLLAdvSeeder',
    [string]$StartupTime,
    [string]$RepoRoot = $PSScriptRoot,
    [string]$PythonExe,
    [string]$ConfigPath,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

function Write-Info($Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Ok($Message) { Write-Host "[ OK ] $Message" -ForegroundColor Green }
function Write-Warn($Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }

function Get-RepoFile([string]$Name) {
    Join-Path $RepoRoot $Name
}

function Test-RepoFiles {
    foreach ($file in @('seeding.py','requirements.txt')) {
        $path = Get-RepoFile $file
        if (-not (Test-Path $path)) {
            throw "Required repository file missing: $path"
        }
    }
}

function Get-ConfigPath {
    if ($ConfigPath) {
        $resolved = Resolve-Path -Path $ConfigPath -ErrorAction Stop
        return $resolved.Path
    }
    return (Get-RepoFile 'seeding.yaml')
}

function Get-PythonCommand {
    if ($PythonExe) {
        if (Test-Path $PythonExe) { return $PythonExe }
        throw "Specified Python executable not found: $PythonExe"
    }

    foreach ($candidate in @('py','python','python3')) {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) { return $candidate }
    }

    throw 'Python was not found in PATH. Install Python 3 and rerun.'
}

function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)

    $python = Get-PythonCommand
    Push-Location $RepoRoot
    try {
        if ($python -eq 'py') {
            & py @Args
        } else {
            & $python @Args
        }
        if ($LASTEXITCODE -ne 0) {
            throw "Python command failed: $($Args -join ' ')"
        }
    } finally {
        Pop-Location
    }
}

function Test-SeedConfig {
    $cfg = Get-ConfigPath
    if (-not (Test-Path $cfg)) {
        throw "Configuration not found: $cfg"
    }
    Invoke-Python 'seeding.py' '--validate-config' '--config' $cfg
    Write-Ok "Validated config: $cfg"
}

function Show-SeedConfig {
    $cfg = Get-ConfigPath
    Invoke-Python 'seeding.py' '--print-config' '--config' $cfg
}

function Install-Dependencies {
    Test-RepoFiles
    $python = Get-PythonCommand
    $req = Get-RepoFile 'requirements.txt'
    Write-Info "Installing Python requirements from $req"
    if ($python -eq 'py') {
        & py -m pip install -r $req
    } else {
        & $python -m pip install -r $req
    }
    if ($LASTEXITCODE -ne 0) {
        throw 'Dependency installation failed.'
    }
    Write-Ok 'Dependencies installed.'
}

function Get-TaskArguments {
    $scriptPath = Get-RepoFile 'seeding.py'
    $cfg = Get-ConfigPath
    $python = Get-PythonCommand
    if ($python -eq 'py') {
        return "/c title hll_seeding_script && py `"$scriptPath`" --config `"$cfg`""
    }
    return "/c title hll_seeding_script && `"$python`" `"$scriptPath`" --config `"$cfg`""
}

function Remove-Task {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Ok "Scheduled task removed: $TaskName"
    } else {
        Write-Warn "No scheduled task found with name $TaskName"
    }
}

function New-Task {
    Test-RepoFiles
    Test-SeedConfig

    if (-not $StartupTime) {
        $StartupTime = Read-Host 'Enter daily start time (example 10:00:00 or 07:00:00)'
    }

    try {
        $triggerTime = [datetime]::Parse($StartupTime)
    } catch {
        throw 'Invalid StartupTime format. Use a Windows-parseable time like 10:00:00.'
    }

    $action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument (Get-TaskArguments) -WorkingDirectory $RepoRoot
    $trigger = New-ScheduledTaskTrigger -Daily -At $triggerTime.TimeOfDay
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Info "Replaced existing scheduled task: $TaskName"
    }

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null
    Write-Ok "Scheduled task created: $TaskName at $($triggerTime.ToString('HH:mm:ss'))"
}

function Run-Now {
    Test-RepoFiles
    Test-SeedConfig
    Start-Process -FilePath 'cmd.exe' -ArgumentList (Get-TaskArguments) -WorkingDirectory $RepoRoot
    Write-Ok 'Seeder launched in a new console window.'
}

function Verify-Task {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Warn 'There is no scheduled task present. Run Install or CreateTask.'
        return
    }
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    [pscustomobject]@{
        TaskName = $TaskName
        State = $task.State
        LastRunTime = $info.LastRunTime
        NextRunTime = $info.NextRunTime
        LastTaskResult = $info.LastTaskResult
        ConfigPath = Get-ConfigPath
    } | Format-List
}

function Edit-Config {
    $cfg = Get-ConfigPath
    if (-not (Test-Path $cfg)) {
        throw "Configuration not found: $cfg"
    }
    Start-Process notepad.exe $cfg
}

function Install-All {
    Install-Dependencies
    New-Task
}

function Show-Menu {
    Write-Host ''
    Write-Host 'HLL Advanced Seeder PowerShell Manager' -ForegroundColor Magenta
    Write-Host '1) Install (dependencies + scheduled task)'
    Write-Host '2) Uninstall (scheduled task only; keep seeding.yaml)'
    Write-Host '3) Run now'
    Write-Host '4) Verify task'
    Write-Host '5) Edit config'
    Write-Host '6) Validate config'
    Write-Host '7) Show effective config summary'
    Write-Host '8) Install dependencies only'
    Write-Host '9) Create/update task only'
    Write-Host '10) Remove task only'
    switch (Read-Host 'Choose an option') {
        '1' { $script:Action = 'Install' }
        '2' { $script:Action = 'Uninstall' }
        '3' { $script:Action = 'RunNow' }
        '4' { $script:Action = 'Verify' }
        '5' { $script:Action = 'EditConfig' }
        '6' { $script:Action = 'ValidateConfig' }
        '7' { $script:Action = 'ShowConfig' }
        '8' { $script:Action = 'InstallDeps' }
        '9' { $script:Action = 'CreateTask' }
        '10' { $script:Action = 'RemoveTask' }
        default { throw 'Invalid selection.' }
    }
}

if (-not $Action) {
    Show-Menu
}

switch ($Action) {
    'Install'        { Install-All }
    'Uninstall'      {
        if (-not $Force) {
            $answer = Read-Host 'Type REMOVE to delete the scheduled task and keep repository files including seeding.yaml'
            if ($answer -ne 'REMOVE') { Write-Warn 'Uninstall cancelled.'; exit 0 }
        }
        Remove-Task
        Write-Ok 'Uninstall completed. Repository files and seeding.yaml were left in place.'
    }
    'RunNow'         { Run-Now }
    'Verify'         { Verify-Task }
    'EditConfig'     { Edit-Config }
    'ValidateConfig' { Test-SeedConfig }
    'ShowConfig'     { Show-SeedConfig }
    'InstallDeps'    { Install-Dependencies }
    'CreateTask'     { New-Task }
    'RemoveTask'     { Remove-Task }
}
