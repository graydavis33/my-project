# Install Windows Task Scheduler task for CRM weekly reminder (Mondays 9am)
# Run as Administrator

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = (Get-Command python).Source
$taskName = "Client CRM - Weekly Reminder"

$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "main.py remind" `
    -WorkingDirectory $scriptPath

$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday `
    -At 9am

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Force

Write-Host "Task '$taskName' registered. Runs every Monday at 9:00 AM."
