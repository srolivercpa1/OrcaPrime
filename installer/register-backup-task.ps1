param(
    [Parameter(Mandatory=$true)][ValidateSet('register','unregister')][string]$Action,
    [string]$ExePath
)
$ErrorActionPreference = 'Stop'
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$taskName = 'OrcaPrime-Backup-' + $sid
if ($Action -eq 'unregister') {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    exit 0
}
if (-not $ExePath -or -not (Test-Path -LiteralPath $ExePath -PathType Leaf)) {
    throw 'OrcaPrime.exe não encontrado para agendar o backup.'
}
$taskAction = New-ScheduledTaskAction -Execute $ExePath -Argument '--backup-only'
$triggers = @()
$triggers += New-ScheduledTaskTrigger -Daily -At '18:00'
$triggers += New-ScheduledTaskTrigger -AtLogOn -User $sid
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$principal = New-ScheduledTaskPrincipal -UserId $sid -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $triggers -Settings $settings -Principal $principal -Force | Out-Null
