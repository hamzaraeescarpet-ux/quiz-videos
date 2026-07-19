# Blog Auto Scheduler - Windows Task Scheduler Registration

$TaskName    = "BlogAutoScheduler"
$BatFile     = "C:\Users\hamza\OneDrive\Desktop\QuizBot\start_blog_scheduler.bat"
$WorkingDir  = "C:\Users\hamza\OneDrive\Desktop\QuizBot"
$Description = "Runs blog auto-scheduler on PC login. Publishes 3 blogs/day with 2-hour gaps."

Write-Host ""
Write-Host "============================================================"
Write-Host "  Blog Auto Scheduler - Task Scheduler Registration"
Write-Host "============================================================"
Write-Host ""

# Purana task delete karo
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Write-Host "[1/4] Old task removed (if any)."

# Action: cmd.exe se bat file chalao
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$BatFile`"" `
    -WorkingDirectory $WorkingDir

Write-Host "[2/4] Action created."

# Trigger: User login par, 2 minute delay ke saath
$trigger = New-ScheduledTaskTrigger -AtLogOn
$trigger.Delay = "PT2M"
Write-Host "[3/4] Trigger created (At Logon + 2 min delay)."

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew

# Principal: LimitedAccess (no admin needed)
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -RunLevel Limited `
    -LogonType Interactive

# Task register karo
try {
    $task = Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description $Description `
        -Force
    
    Write-Host "[4/4] Task registered."
    Write-Host ""
    Write-Host "============================================================"
    Write-Host "  [SUCCESS] Task '$TaskName' successfully registered!"
    Write-Host "============================================================"
    Write-Host ""
    Write-Host "Ab har baar PC on + login karne k 2 minute baad"
    Write-Host "blog scheduler automatically start ho jayega."
    Write-Host ""
    Write-Host "Verify: Task Scheduler > Task Scheduler Library > '$TaskName'"
    Write-Host "Log:    $WorkingDir\blog_automation_worker.log"
    Write-Host ""
    $info = Get-ScheduledTask -TaskName $TaskName
    Write-Host "Task State: $($info.State)"
} catch {
    Write-Host "[ERROR] $($_.Exception.Message)"
    Write-Host ""
    Write-Host "Manual steps:"
    Write-Host "  1. Press Win+R, type: taskschd.msc, press Enter"
    Write-Host "  2. Right-click 'Task Scheduler Library' > 'Create Basic Task'"
    Write-Host "  3. Name: BlogAutoScheduler"
    Write-Host "  4. Trigger: When I log on"
    Write-Host "  5. Action: Start a program"
    Write-Host "  6. Program: cmd.exe"
    Write-Host "  7. Arguments: /c `"$BatFile`""
    Write-Host "  8. Finish"
}
