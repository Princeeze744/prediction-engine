<#
QuantSport research data collector — API-Football (v3.football.api-sports.io)

Pulls, per day:
  - fixtures + results (league, country, kickoff, 90-min score, half-time, extra-time, penalties, status)
  - pre-match odds for the markets QuantSport publishes, from a short list of bookmakers

Writes two CSVs into $OutDir:
  fixtures.csv   one row per match
  odds.csv       one row per fixture / bookmaker / market / selection
plus markets_seen.txt (every market name the API returned, so we can add more later).

Safe to re-run: days already collected are skipped (see done_days.txt).
Usage examples (from the folder holding this script):
  .\QS_Collect_APIFootball.ps1                 # last 7 days
  .\QS_Collect_APIFootball.ps1 -DaysBack 1     # just yesterday (run daily)
#>
param(
  [int]$DaysBack = 7,
  [string]$OutDir = "$HOME\Documents\QuantSport_Data",
  [string[]]$Bookmakers = @('Bet365','Pinnacle','1xBet','Marathonbet','Unibet','Betfair','William Hill'),
  [string[]]$Markets = @('Match Winner','Double Chance','Goals Over/Under','Both Teams Score',
                         'Total - Home','Total - Away','Home Team Score a Goal','Away Team Score a Goal'),
  [string]$Timezone = 'Africa/Lagos'
)

$ErrorActionPreference = 'Stop'
if (-not $env:APIFOOTBALL_KEY) { $env:APIFOOTBALL_KEY = Read-Host 'API-Football key' }
$Headers = @{ 'x-apisports-key' = "$env:APIFOOTBALL_KEY".Trim() }   # Trim: a pasted key often carries a hidden line break
$Base = 'https://v3.football.api-sports.io'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$FixturesCsv = Join-Path $OutDir 'fixtures.csv'
$OddsCsv     = Join-Path $OutDir 'odds.csv'
$DoneFile    = Join-Path $OutDir 'done_days.txt'
$SeenFile    = Join-Path $OutDir 'markets_seen.txt'
$script:Calls = 0
$script:Seen = New-Object 'System.Collections.Generic.HashSet[string]'
if (Test-Path $SeenFile) { Get-Content $SeenFile | ForEach-Object { [void]$script:Seen.Add($_) } }

function Test-ApiErrors($r) {
  if ($null -eq $r.errors) { return $null }
  if ($r.errors -is [array]) { if ($r.errors.Count -gt 0) { return ($r.errors -join '; ') } else { return $null } }
  $props = @($r.errors.PSObject.Properties)
  if ($props.Count -gt 0) { return (($props | ForEach-Object { "$($_.Name): $($_.Value)" }) -join '; ') }
  return $null
}

function Invoke-Api([string]$Path) {
  for ($try = 1; $try -le 5; $try++) {
    try {
      $r = Invoke-RestMethod -Uri "$Base$Path" -Headers $Headers -TimeoutSec 60
      $script:Calls++
      Start-Sleep -Milliseconds 220
      $err = Test-ApiErrors $r
      if ($err) {
        if ($err -match 'rate|limit|too many') { Write-Host "  rate limit hit, waiting 60s ($err)" -ForegroundColor Yellow; Start-Sleep 60; continue }
        throw "API error on ${Path}: $err"
      }
      return $r
    } catch {
      if ($try -eq 5) { throw }
      Write-Host "  retry $try for $Path : $($_.Exception.Message)" -ForegroundColor Yellow
      Start-Sleep -Seconds (5 * $try)
    }
  }
}

$done = @{}
if (Test-Path $DoneFile) { Get-Content $DoneFile | ForEach-Object { $done[$_] = $true } }

$today = Get-Date
for ($i = $DaysBack; $i -ge 1; $i--) {
  $day = $today.AddDays(-$i).ToString('yyyy-MM-dd')
  if ($done.ContainsKey($day)) { Write-Host "$day already collected - skipping"; continue }
  Write-Host "`n=== $day ===" -ForegroundColor Cyan

  # ---------- fixtures & results ----------
  $fx = Invoke-Api "/fixtures?date=$day&timezone=$Timezone"
  $fxRows = foreach ($m in $fx.response) {
    [pscustomobject]@{
      fixture_id   = $m.fixture.id
      date         = $day
      kickoff      = $m.fixture.date
      status       = $m.fixture.status.short
      league_id    = $m.league.id
      league       = $m.league.name
      country      = $m.league.country
      season       = $m.league.season
      round        = $m.league.round
      home         = $m.teams.home.name
      away         = $m.teams.away.name
      home_id      = $m.teams.home.id
      away_id      = $m.teams.away.id
      ft_home      = $m.score.fulltime.home      # 90-minute score
      ft_away      = $m.score.fulltime.away
      ht_home      = $m.score.halftime.home
      ht_away      = $m.score.halftime.away
      et_home      = $m.score.extratime.home
      et_away      = $m.score.extratime.away
      pen_home     = $m.score.penalty.home
      pen_away     = $m.score.penalty.away
      goals_home   = $m.goals.home               # final incl. extra time
      goals_away   = $m.goals.away
    }
  }
  $fxRows = @($fxRows)
  if ($fxRows.Count) { $fxRows | Export-Csv $FixturesCsv -Append -NoTypeInformation -Encoding utf8 }
  Write-Host "  fixtures: $($fxRows.Count)"

  # ---------- odds (paginated) ----------
  $oddsRows = New-Object 'System.Collections.Generic.List[object]'
  $page = 1; $pages = 1
  do {
    $od = Invoke-Api "/odds?date=$day&timezone=$Timezone&page=$page"
    $pages = [int]$od.paging.total
    foreach ($f in $od.response) {
      foreach ($b in $f.bookmakers) {
        if ($Bookmakers -notcontains $b.name) { continue }
        foreach ($bet in $b.bets) {
          [void]$script:Seen.Add($bet.name)
          if ($Markets -notcontains $bet.name) { continue }
          foreach ($v in $bet.values) {
            $oddsRows.Add([pscustomobject]@{
              fixture_id = $f.fixture.id
              date       = $day
              updated    = $f.update
              bookmaker  = $b.name
              market     = $bet.name
              selection  = "$($v.value)"
              odd        = $v.odd
            })
          }
        }
      }
    }
    Write-Host ("  odds page {0}/{1}  rows so far {2}" -f $page, $pages, $oddsRows.Count)
    $page++
  } while ($page -le $pages)
  if ($oddsRows.Count) { $oddsRows | Export-Csv $OddsCsv -Append -NoTypeInformation -Encoding utf8 }

  Add-Content $DoneFile $day
  $script:Seen | Sort-Object | Set-Content $SeenFile
}

$st = Invoke-Api '/status'
Write-Host "`nDone. API calls this run: $script:Calls. Used today: $($st.response.requests.current) of $($st.response.requests.limit_day)." -ForegroundColor Green
Write-Host "Files in: $OutDir"
Get-ChildItem $OutDir | Select-Object Name, @{n='MB';e={[math]::Round($_.Length/1MB,2)}} | Format-Table -AutoSize
