# Add Blog Scheduler shortcut to Windows Startup folder
# No admin rights needed!

$StartupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
$ShortcutPath  = "$StartupFolder\BlogAutoScheduler.lnk"
$BatFile       = "C:\Users\hamza\OneDrive\Desktop\QuizBot\start_blog_scheduler.bat"
$WorkingDir    = "C:\Users\hamza\OneDrive\Desktop\QuizBot"

Write-Host ""
Write-Host "Startup folder: $StartupFolder"
Write-Host "Shortcut path:  $ShortcutPath"
Write-Host ""

# Shortcut create karo
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath      = $BatFile
$Shortcut.WorkingDirectory = $WorkingDir
$Shortcut.WindowStyle     = 7   # 7 = Minimized
$Shortcut.Description     = "Blog Auto Scheduler - 3 blogs/day"
$Shortcut.Save()

if (Test-Path $ShortcutPath) {
    Write-Host "[SUCCESS] Shortcut successfully created in Startup folder!"
    Write-Host ""
    Write-Host "Ab har baar Windows login hone par blog scheduler"
    Write-Host "automatically minimized window mein start ho jayega."
    Write-Host ""
    Write-Host "Verify karo: Win+R > shell:startup"
} else {
    Write-Host "[ERROR] Shortcut create nahi hua."
}
