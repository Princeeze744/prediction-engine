<#
QuantSport - TODAY's pre-match odds for the 30 candidate models.
Saves today's fixtures and prices (only the markets the models use) BEFORE kick-off, then the
website builder turns them into today's picks.

Output: Documents\QuantSport_Data\prematch\oddsall_<date>.csv  and  fixtures_<date>.csv
Usage:  .\QS_Today_AllMarkets.ps1              # today
        .\QS_Today_AllMarkets.ps1 -DayOffset 1 # tomorrow
Requests: about 15-60.  Time: 1-3 minutes.
#>
param(
  [int]$DayOffset = 0,
  [string]$OutDir = "$HOME\Documents\QuantSport_Data\prematch",
  [string[]]$Bookmakers = @('1xBet','Bet365','Marathonbet','Pinnacle'),
  [string]$Timezone = 'Africa/Lagos'
)
$Markets = @('Match Winner','Goals Over/Under','To Win Either Half','Away Team Total Goals(2nd Half)','First Half Winner',
             'Goals Over/Under First Half','Home Team Total Goals(1st Half)','Asian Handicap First Half','Away Odd/Even',
             'Away Team Total Goals(1st Half)','To Score In Both Halves By Teams','Double Chance','Both Teams Score',
             'Handicap Result','Total - Home','Total - Away','Win to Nil - Home','Goals Over/Under - Second Half','Both Teams To Score in Both Halves',
             'Clean Sheet - Home','Clean Sheet - Away','Away team will score in both halves','Both Teams Score - First Half','Asian Handicap',
             'Handicap Result - First Half','Home win both halves','HT/FT Double','Exact Goals Number','Results/Both Teams Score','Win To Nil')
$ErrorActionPreference = 'Stop'
if (-not $env:APIFOOTBALL_KEY) { $env:APIFOOTBALL_KEY = Read-Host 'API-Football key' }
$Headers = @{ 'x-apisports-key' = ("$env:APIFOOTBALL_KEY" -replace '\s', '') }   # strips any hidden spaces or line breaks from a pasted key
$Base = 'https://v3.football.api-sports.io'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$day = (Get-Date).AddDays($DayOffset).ToString('yyyy-MM-dd'); $stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
$mk = @{}; foreach ($m in $Markets) { $mk[$m] = $true }
$bk = @{}; foreach ($b in $Bookmakers) { $bk[$b] = $true }
function Invoke-Api([string]$Path) {
  for ($try = 1; $try -le 6; $try++) {
    try {
      $r = Invoke-RestMethod -Uri "$Base$Path" -Headers $Headers -TimeoutSec 90; Start-Sleep -Milliseconds 250
      $hasErr = $false
      if ($null -ne $r.errors) { if ($r.errors -is [array]) { $hasErr = $r.errors.Count -gt 0 } else { $hasErr = @($r.errors.PSObject.Properties).Count -gt 0 } }
      if ($hasErr) { Write-Host "  API busy - waiting 30s" -ForegroundColor Yellow; Start-Sleep 30; continue }
      return $r
    } catch { Start-Sleep -Seconds (5 * $try) }
  }
  return $null
}
Write-Host "Today's pre-match prices for $day (taken $stamp)" -ForegroundColor Cyan
$fx = Invoke-Api "/fixtures?date=$day&timezone=$Timezone"
$rows = @(foreach ($m in $fx.response) {
  [pscustomobject]@{ snapshot=$stamp; fixture_id=$m.fixture.id; date=$day; kickoff=$m.fixture.date; status=$m.fixture.status.short
    league_id=$m.league.id; league=$m.league.name; country=$m.league.country; home=$m.teams.home.name; away=$m.teams.away.name
    home_id=$m.teams.home.id; away_id=$m.teams.away.id } })
$rows | Export-Csv (Join-Path $OutDir "fixtures_$day.csv") -NoTypeInformation -Encoding utf8
Write-Host "  fixtures: $($rows.Count)  (not started: $(@($rows | Where-Object { $_.status -eq 'NS' }).Count))"

$Out = Join-Path $OutDir "oddsall_$day.csv"
$sw = New-Object System.IO.StreamWriter($Out, $false, (New-Object System.Text.UTF8Encoding($false)))
$sw.WriteLine('fixture_id,date,bookmaker,market,selection,odd'); $n = 0; $page = 1; $pages = 1
try {
  do {
    $od = Invoke-Api "/odds?date=$day&timezone=$Timezone&page=$page"
    if ($null -eq $od) { break }
    $pages = [int]$od.paging.total
    foreach ($f in $od.response) { foreach ($b in $f.bookmakers) { if (-not $bk.ContainsKey($b.name)) { continue }
      foreach ($bet in $b.bets) { if (-not $mk.ContainsKey($bet.name)) { continue }
        foreach ($v in $bet.values) { $sel = "$($v.value)".Replace('"', "'"); $sw.WriteLine("$($f.fixture.id),$day,$($b.name),`"$($bet.name)`",`"$sel`",$($v.odd)"); $n++ } } } }
    Write-Host "  odds page $page/$pages"
    $page++
  } while ($page -le $pages)
} finally { $sw.Close() }
Write-Host "Saved $n prices to $Out" -ForegroundColor Green
Write-Host "Next (in the v22 folder with .venv active):  python tools\build_models.py"
