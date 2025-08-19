# API key will be loaded from .env file automatically

$batchSize   = 20
$contentDir  = ".\content\songs"  # Songs directory
$songsJson   = ".\assets\seeds_songs.json"
$styleGuide  = ".\seeds_style_guide.txt"
$statePath   = ".\tmp\rewrite_songs_state.json"
$minScore    = 0.12
$topK        = 5

do {
    Write-Host "=== Running next batch of $batchSize files ===" -ForegroundColor Cyan
    
    python .\tools\rewrite_pages_with_seeds.py `
        --content-dir $contentDir `
        --songs-json $songsJson `
        --style-guide $styleGuide `
        --top-k $topK `
        --min-score $minScore `
        --batch-size $batchSize `
        --resume `
        --state-path $statePath `
        --order path

    Write-Host "=== Batch complete. Sleeping 15 seconds before next run... ===" -ForegroundColor Yellow
    Start-Sleep -Seconds 15

    # Count remaining files by checking the state file
    $state = @{ completed = @() }
    if (Test-Path $statePath) {
        $state = Get-Content $statePath | ConvertFrom-Json
    }

    # Get total files using the same logic as the Python script
    $allFiles = Get-ChildItem -Path $contentDir -Recurse -Filter *.md | Where-Object { $_.Name -ne "_index.md" }
    $totalFiles = ($allFiles | Measure-Object).Count
    $completed  = ($state.completed | Measure-Object).Count
    $remaining  = $totalFiles - $completed

    Write-Host "Completed: $completed / $totalFiles (Remaining: $remaining)" -ForegroundColor Green

    # Safety check to avoid infinite loop
    if ($remaining -le 0) {
        break
    }

} while ($remaining -gt 0)

Write-Host "=== All songs pages processed successfully! ===" -ForegroundColor Magenta