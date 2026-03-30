# install_windows_task.ps1
# Run this once to register the personal assistant as a Windows startup task.
# It will start automatically every time you log in, running silently in the background.
#
# Usage: Right-click -> "Run with PowerShell"  (or: powershell -File install_windows_task.ps1)

$taskName  = "GrayPersonalAssistant"
$batPath   = "$PSScriptRoot\run_agent.bat"
$workDir   = $PSScriptRoot

# Remove old task if it exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Run cmd /c <bat> hidden (no window) at every login
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$batPath`"" `
    -WorkingDirectory $workDir

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit 0 `
    -MultipleInstances IgnoreNew `
    -Hidden

$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName  $taskName `
    -Action    $action `
    -Trigger   $trigger `
    -Settings  $settings `
    -Principal $principal `
    -Force | Out-Null

Write-Host ""
Write-Host "✅  Task '$taskName' registered." -ForegroundColor Green
Write-Host "    The personal assistant will start automatically at every login."
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  Start now:  Start-ScheduledTask -TaskName '$taskName'"
Write-Host "  Stop:       Stop-ScheduledTask  -TaskName '$taskName'"
Write-Host "  Remove:     Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
Write-Host "  View logs:  notepad '$workDir\agent.log'"
Write-Host ""
