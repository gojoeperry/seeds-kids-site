param(
  [string]$ApiKey = $env:CLAUDE_API_KEY,             # optional; if provided, pass as env var
  [string[]]$Csvs = @(".\keyword_clusters.csv", ".\keyword_clusters_expanded.csv"),
  [string]$SongsJson = ".\assets\seeds_songs.json",
  [string]$StyleGuide = ".\seeds_style_guide.txt",
  [string]$OutDir = ".\site\content\guides",
  [int]$TopK = 5,
  [double]$MinScore = 0.18,
  [int]$BatchSize = 15,
  [string]$StatePath = ".\tmp\generate_state.json",
  [string]$Order = "keyword",                        # keyword | random
  [switch]$Overwrite,                                # if set, include --overwrite
  [int]$CommitEvery = 10,                            # commit every N batches
  [int]$SleepSeconds = 12,                           # delay between batches
  [switch]$DryRun,                                   # if set, include --dry-run (no writes, no state)
  [string]$LogPath = ".\tmp\generate_guides_loop.log"
)

# Setup
New-Item -ItemType Directory -Force -Path (Split-Path $LogPath) | Out-Null
$ErrorActionPreference = "Stop"

function Write-Log([string]$msg) {
  $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  $logMsg = "$ts `t $msg"
  Write-Host $logMsg
  $logMsg | Out-File -FilePath $LogPath -Append -Encoding UTF8
}

# Helper to count total keywords (best effort; tolerate different CSV shapes)
function Get-TotalKeywords {
  $c = 0
  foreach ($csv in $Csvs) {
    if (Test-Path $csv) {
      try {
        $c += (Import-Csv $csv).Count
      } catch {
        # fallback: line count minus header
        $c += [math]::Max((Get-Content $csv | Measure-Object -Line).Lines - 1, 0)
      }
    }
  }
  return $c
}

# Helper to get completed count from state file
function Get-CompletedCount {
  if (Test-Path $StatePath) {
    try {
      $state = Get-Content $StatePath | ConvertFrom-Json
      return $state.completed.Count
    } catch {
      return 0
    }
  }
  return 0
}

# Helper to check if git repo and commit changes
function Commit-Changes([int]$batchNum) {
  if (-not (Test-Path ".git")) {
    Write-Log "No git repository found, skipping commit"
    return
  }
  
  try {
    # Check if there are any changes
    $status = git status --porcelain
    if (-not $status) {
      Write-Log "No changes to commit"
      return
    }
    
    # Add all changes in the output directory
    git add $OutDir
    git add $StatePath
    git add $LogPath
    
    # Commit with descriptive message
    $completed = Get-CompletedCount
    $commitMsg = "Generate guides batch #${batchNum} - $completed articles completed"
    git commit -m $commitMsg
    
    Write-Log "Committed batch #${batchNum}: $commitMsg"
  } catch {
    Write-Log "WARNING: Git commit failed: $($_.Exception.Message)"
  }
}

# Build base command
$base = @(
  "python", ".\tools\generate_seeds_pages.py"
)

# CSV args
foreach ($csv in $Csvs) { $base += @("--csv", $csv) }

# Required args
$base += @(
  "--songs-json", $SongsJson,
  "--style-guide", $StyleGuide,
  "--out-dir", $OutDir,
  "--top-k", $TopK,
  "--min-score", $MinScore,
  "--batch-size", $BatchSize,
  "--state-path", $StatePath,
  "--resume",
  "--order", $Order
)

# Optional flags
if ($Overwrite.IsPresent) { $base += @("--overwrite") }
if ($DryRun.IsPresent)    { $base += @("--dry-run") }

# Pre-flight info
$tot = Get-TotalKeywords
$completed = Get-CompletedCount
$remaining = $tot - $completed

Write-Log "=== STARTING GENERATOR LOOP ==="
Write-Log "Target batch-size: $BatchSize"
Write-Log "Total keywords (approx): $tot"
Write-Log "Already completed: $completed"
Write-Log "Remaining: $remaining"
Write-Log "Estimated batches: $([math]::Ceiling($remaining / $BatchSize))"
Write-Log "OutDir: $OutDir"
Write-Log "StatePath: $StatePath"
Write-Log "Order: $Order"
Write-Log "Overwrite: $($Overwrite.IsPresent)"
Write-Log "DryRun: $($DryRun.IsPresent)"
Write-Log "Commit every: $CommitEvery batches"
Write-Log "Sleep between batches: $SleepSeconds seconds"
Write-Log "API Key: $($ApiKey -ne $null -and $ApiKey -ne '')"

if ($remaining -le 0) {
  Write-Log "No remaining keywords to process. Exiting."
  exit 0
}

# Loop
$batches = 0
$consecutiveErrors = 0
$maxConsecutiveErrors = 3

do {
  $batches++
  
  Write-Log ""
  Write-Log "--- BATCH #${batches} ---"
  
  # Set environment variable for API key
  if ($ApiKey) {
    $env:CLAUDE_API_KEY = $ApiKey
  }
  
  $cmd = ($base -join " ")
  Write-Log "Command: $cmd"
  
  try {
    # Run the generation script and capture exit code properly
    $process = Start-Process -FilePath $base[0] -ArgumentList ($base[1..$($base.Length-1)]) -NoNewWindow -Wait -PassThru -RedirectStandardOutput "tmp\batch_output.txt" -RedirectStandardError "tmp\batch_error.txt"
    $exitCode = $process.ExitCode
    
    # Read and log output
    if (Test-Path "tmp\batch_output.txt") {
      $output = Get-Content "tmp\batch_output.txt"
      foreach ($line in $output) {
        Write-Log "  STDOUT: $line"
      }
    }
    
    if (Test-Path "tmp\batch_error.txt") {
      $errorOutput = Get-Content "tmp\batch_error.txt"
      if ($errorOutput) {
        foreach ($line in $errorOutput) {
          Write-Log "  STDERR: $line"
        }
      }
    }
    
    if ($exitCode -eq 0) {
      Write-Log "Batch #${batches} completed successfully"
      $consecutiveErrors = 0
      
      # Check if we should commit
      if (($batches % $CommitEvery) -eq 0) {
        Write-Log "Committing after $batches batches..."
        Commit-Changes $batches
      }
      
      # Update progress
      $newCompleted = Get-CompletedCount
      $newRemaining = $tot - $newCompleted
      Write-Log "Progress: $newCompleted completed, $newRemaining remaining"
      
      # Check if we're done
      if ($newRemaining -le 0) {
        Write-Log "All keywords processed! Final commit..."
        Commit-Changes $batches
        Write-Log "=== GENERATION COMPLETE ==="
        break
      }
      
      # Sleep between batches (except for dry run)
      if (-not $DryRun.IsPresent -and $SleepSeconds -gt 0) {
        Write-Log "Sleeping $SleepSeconds seconds before next batch..."
        Start-Sleep -Seconds $SleepSeconds
      }
      
    } else {
      $consecutiveErrors++
      Write-Log "ERROR: Batch #${batches} failed with exit code $exitCode"
      Write-Log "Consecutive errors: $consecutiveErrors"
      
      if ($consecutiveErrors -ge $maxConsecutiveErrors) {
        Write-Log "FATAL: Too many consecutive errors ($maxConsecutiveErrors). Stopping."
        exit 1
      }
      
      # Wait longer after errors
      $errorSleep = $SleepSeconds * 2
      Write-Log "Waiting $errorSleep seconds before retry..."
      Start-Sleep -Seconds $errorSleep
    }
    
  } catch {
    $consecutiveErrors++
    Write-Log "EXCEPTION in batch #${batches}: $($_.Exception.Message)"
    Write-Log "Consecutive errors: $consecutiveErrors"
    
    if ($consecutiveErrors -ge $maxConsecutiveErrors) {
      Write-Log "FATAL: Too many consecutive errors ($maxConsecutiveErrors). Stopping."
      exit 1
    }
    
    $errorSleep = $SleepSeconds * 2
    Write-Log "Waiting $errorSleep seconds before retry..."
    Start-Sleep -Seconds $errorSleep
  }
  
} while ($true)

Write-Log "Generator loop completed at $(Get-Date)"
Write-Log "Total batches processed: $batches"
Write-Log "Log file: $LogPath"