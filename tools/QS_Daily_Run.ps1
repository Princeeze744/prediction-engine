<#
QuantSport DAILY RUN - one command that publishes the day's 10 tickets.
  1. Collects yesterday's results (so yesterday's tickets get settled)
  2. Collects today's pre-match prices for every market the models use
  3. Rebuilds the website data: today's 10 tickets (3 x 3 odds, 3 x 5 odds, 3 x 10 odds, 1 x 20 odds) + all records

Run from anywhere:   & "<v22 folder>\tools\QS_Daily_Run.ps1"
Schedule it Monday-Saturday in the morning (see the command Claude gave you).
The day's tickets are saved the first time this runs and are never changed afterwards.
#>
$ErrorActionPreference = 'Continue'
$tools = $PSScriptRoot
$v22 = Split-Path $tools -Parent
$log = Join-Path $HOME 'Documents\QuantSport_Data\daily_run.log'
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
"`n===== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') daily run =====" | Tee-Object -FilePath $log -Append
if (-not $env:APIFOOTBALL_KEY) { $env:APIFOOTBALL_KEY = [Environment]::GetEnvironmentVariable('APIFOOTBALL_KEY', 'User') }
if (-not $env:APIFOOTBALL_KEY) { "No API key found. Run:  setx APIFOOTBALL_KEY <your key>" | Tee-Object -FilePath $log -Append; exit 1 }

"[1/3] Results for the last 2 days" | Tee-Object -FilePath $log -Append
& (Join-Path $tools 'collectors\QS_Collect_APIFootball.ps1') -DaysBack 2 *>&1 | Out-String -Stream | Select-Object -Last 6 | Tee-Object -FilePath $log -Append

"[2/3] Today's pre-match prices" | Tee-Object -FilePath $log -Append
& (Join-Path $tools 'collectors\QS_Today_AllMarkets.ps1') *>&1 | Out-String -Stream | Select-Object -Last 3 | Tee-Object -FilePath $log -Append

"[3/3] Building today's 10 tickets" | Tee-Object -FilePath $log -Append
$py = Join-Path $v22 '.venv\Scripts\python.exe'; if (-not (Test-Path $py)) { $py = 'python' }
Push-Location $v22
& $py 'tools\build_models.py' *>&1 | Out-String -Stream | Select-Object -First 3 | Tee-Object -FilePath $log -Append
Pop-Location
"Done. Open the website page /tickets" | Tee-Object -FilePath $log -Append
