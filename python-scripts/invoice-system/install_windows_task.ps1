# install_windows_task.ps1
# Registers the invoice daily scan as a Windows Task Scheduler task.
# Run once from an admin PowerShell prompt:
#   powershell -File install_windows_task.ps1

$taskName = "GrayInvoiceDailyScan"
$batPath  = "$PSScriptRoot\run_daily.bat"
$workDir  = $PSScriptRoot

# Remove old task if it exists (safe to re-run)
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$batPath`"" `
    -WorkingDirectory $workDir

$trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At "08:00"

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit 0 `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -Hidden

Register-ScheduledTask `
    -TaskName  $taskName `
    -Action    $action `
    -Trigger   $trigger `
    -Settings  $settings `
    -RunLevel  Limited `
    -Force | Out-Null

Write-Host ""
Write-Host "Task '$taskName' registered - runs daily at 8:00 AM." -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  Start now:   Start-ScheduledTask -TaskName '$taskName'"
Write-Host "  Stop:        Stop-ScheduledTask  -TaskName '$taskName'"
Write-Host "  Remove:      Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
Write-Host "  View logs:   notepad '$workDir\invoice_scan.log'"
Write-Host ""
