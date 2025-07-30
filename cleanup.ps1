# PowerShell Markdown Cleanup Script
param(
    [string]$ContentDir = "C:\Users\joepe\seeds-kids-seo\content",
    [int]$BatchSize = 50
)

$ErrorActionPreference = "Continue"

# Initialize counters
$totalFiles = 0
$processedFiles = 0
$frontmatterFixes = 0
$placeholderRemovals = 0
$formattingFixes = 0
$titleCapitalizations = 0
$spacingFixes = 0
$markdownSyntaxFixes = 0
$errorFiles = @()

# Get all markdown files
$allFiles = @()
$activitiesDir = Join-Path $ContentDir "activities"
$songsDir = Join-Path $ContentDir "songs"

if (Test-Path $activitiesDir) {
    $allFiles += Get-ChildItem -Path $activitiesDir -Filter "*.md" -File
}
if (Test-Path $songsDir) {
    $allFiles += Get-ChildItem -Path $songsDir -Filter "*.md" -File
}

$totalFiles = $allFiles.Count
Write-Host "Found $totalFiles Markdown files to process" -ForegroundColor Green
Write-Host "Processing in batches of $BatchSize files..." -ForegroundColor Yellow

function Clean-Frontmatter {
    param([string]$frontmatter)
    
    $changes = @()
    $lines = $frontmatter -split "`n"
    $cleanedLines = @()
    
    foreach ($line in $lines) {
        $line = $line.Trim()
        if ([string]::IsNullOrEmpty($line)) {
            $cleanedLines += ""
            continue
        }
        
        # Handle title
        if ($line.StartsWith("title:")) {
            $titlePart = $line.Substring(6).Trim()
            $titleClean = $titlePart.Trim('"', "'")
            
            # Capitalize first letter if needed
            if ($titleClean.Length -gt 0 -and [char]::IsLower($titleClean[0])) {
                $titleClean = [char]::ToUpper($titleClean[0]) + $titleClean.Substring(1)
                $changes += "Capitalized title"
            }
            
            # Ensure quoted
            if (-not $titlePart.StartsWith('"') -and -not $titlePart.StartsWith("'")) {
                $cleanedLines += "title: `"$titleClean`""
                $changes += "Added quotes to title"
            } else {
                $cleanedLines += "title: `"$titleClean`""
            }
        }
        # Handle description
        elseif ($line.StartsWith("description:")) {
            $descPart = $line.Substring(12).Trim()
            $descClean = $descPart.Trim('"', "'")
            if (-not $descPart.StartsWith('"') -and -not $descPart.StartsWith("'")) {
                $cleanedLines += "description: `"$descClean`""
                $changes += "Added quotes to description"
            } else {
                $cleanedLines += "description: `"$descClean`""
            }
        }
        # Handle slug
        elseif ($line.StartsWith("slug:")) {
            $slugPart = $line.Substring(5).Trim()
            $slugClean = $slugPart.Trim('"', "'")
            if (-not $slugPart.StartsWith('"') -and -not $slugPart.StartsWith("'")) {
                $cleanedLines += "slug: `"$slugClean`""
                $changes += "Added quotes to slug"
            } else {
                $cleanedLines += "slug: `"$slugClean`""
            }
        }
        # Handle tags
        elseif ($line.StartsWith("- ") -and -not $line.StartsWith('- "') -and -not $line.StartsWith("- '")) {
            $tagClean = $line.Substring(2).Trim().Trim('"', "'")
            $cleanedLines += "- `"$tagClean`""
            if ($changes -notcontains "Added quotes to tags") {
                $changes += "Added quotes to tags"
            }
        }
        else {
            $cleanedLines += $line
        }
    }
    
    return ($cleanedLines -join "`n"), $changes
}

function Remove-Placeholders {
    param([string]$content)
    
    $changes = @()
    $originalContent = $content
    
    $placeholderPatterns = @(
        '\[Insert content here\]',
        '\[Claude generating\.\.\.\]',
        '\[Content coming soon\]',
        'placeholder',
        '\[placeholder\]',
        '\[Placeholder text\]',
        '\[Add content here\]',
        '\[TODO:.*?\]',
        '\[Coming soon\]'
    )
    
    foreach ($pattern in $placeholderPatterns) {
        if ($content -match $pattern) {
            $content = $content -replace $pattern, ''
            $changes += "Removed placeholder content"
        }
    }
    
    return $content, $changes
}

function Fix-MarkdownFormatting {
    param([string]$content)
    
    $changes = @()
    $originalContent = $content
    
    # Fix malformed formatting
    $content = $content -replace '\*\*([^*]+)(?<!\*\*)$', '**$1**'
    $content = $content -replace '(?<!\*)\*([^*]+)(?<!\*)$', '*$1*'
    $content = $content -replace '__([^_]+)(?<!__)$', '__$1__'
    
    # Remove excessive blank lines
    $content = $content -replace '\n{3,}', "`n`n"
    
    if ($content -ne $originalContent) {
        $changes += "Fixed Markdown formatting"
    }
    
    return $content, $changes
}

function Process-File {
    param([System.IO.FileInfo]$file)
    
    try {
        $originalContent = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        $content = $originalContent
        $allChanges = @()
        
        # Split frontmatter and content
        if ($content.StartsWith("---")) {
            $parts = $content -split "---", 3
            if ($parts.Count -ge 3) {
                $frontmatter = $parts[1]
                $mainContent = $parts[2]
                
                # Clean frontmatter
                $cleanedFrontmatter, $fmChanges = Clean-Frontmatter $frontmatter
                $allChanges += $fmChanges
                
                # Clean main content
                $mainContent, $placeholderChanges = Remove-Placeholders $mainContent
                $allChanges += $placeholderChanges
                
                $mainContent, $formatChanges = Fix-MarkdownFormatting $mainContent
                $allChanges += $formatChanges
                
                # Reconstruct file
                $content = "---`n$cleanedFrontmatter`n---$mainContent"
            }
        }
        
        # Write back if changes were made
        if ($content -ne $originalContent) {
            Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
            
            # Update statistics
            $script:processedFiles++
            if ($allChanges -contains "Capitalized title" -or $allChanges -contains "Added quotes to title" -or $allChanges -contains "Added quotes to description" -or $allChanges -contains "Added quotes to slug" -or $allChanges -contains "Added quotes to tags") {
                $script:frontmatterFixes++
            }
            if (($allChanges | Where-Object { $_ -like "*placeholder*" }).Count -gt 0) {
                $script:placeholderRemovals++
            }
            if ($allChanges -contains "Fixed Markdown formatting") {
                $script:formattingFixes++
            }
            if ($allChanges -contains "Capitalized title") {
                $script:titleCapitalizations++
            }
        }
        
        return $true, $allChanges
    }
    catch {
        $script:errorFiles += $file.FullName
        Write-Warning "Error processing $($file.Name): $($_.Exception.Message)"
        return $false, @()
    }
}

# Process files in batches
$batchCount = 0
$startTime = Get-Date

for ($i = 0; $i -lt $totalFiles; $i += $BatchSize) {
    $batchCount++
    $endIndex = [Math]::Min($i + $BatchSize - 1, $totalFiles - 1)
    $batch = $allFiles[$i..$endIndex]
    
    Write-Host "Processing batch $batchCount (files $($i+1) to $($endIndex+1))..." -ForegroundColor Cyan
    
    foreach ($file in $batch) {
        $success, $changes = Process-File $file
        
        if ($success -and $changes.Count -gt 0) {
            Write-Host "  ✓ $($file.Name) - $($changes.Count) changes" -ForegroundColor Green
        }
    }
    
    # Progress update
    $progress = [math]::Round(($endIndex + 1) / $totalFiles * 100, 1)
    Write-Host "  Progress: $progress% ($($endIndex + 1)/$totalFiles)" -ForegroundColor Yellow
}

$endTime = Get-Date
$duration = $endTime - $startTime

# Generate report
Write-Host "`n" + "="*60 -ForegroundColor Green
Write-Host "CLEANUP COMPLETED!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green

Write-Host "`nSummary Statistics:" -ForegroundColor Yellow
Write-Host "Total files found: $totalFiles"
Write-Host "Files processed (with changes): $processedFiles"
Write-Host "Files with errors: $($errorFiles.Count)"
Write-Host "Success rate: $([math]::Round((($totalFiles - $errorFiles.Count) / $totalFiles * 100), 1))%"
Write-Host "Processing time: $($duration.ToString('mm\:ss'))"

Write-Host "`nIssues Found and Fixed:" -ForegroundColor Yellow
Write-Host "Frontmatter normalization fixes: $frontmatterFixes"
Write-Host "Placeholder content removed: $placeholderRemovals"
Write-Host "Markdown formatting corrections: $formattingFixes"
Write-Host "Title capitalization fixes: $titleCapitalizations"

if ($errorFiles.Count -gt 0) {
    Write-Host "`nFiles with Errors:" -ForegroundColor Red
    foreach ($errorFile in $errorFiles) {
        Write-Host "  - $errorFile" -ForegroundColor Red
    }
}

# Save report
$reportPath = Join-Path (Split-Path $ContentDir) "cleanup_report.txt"
@"
Markdown Cleanup Report
==================================================

Summary Statistics:
Total files found: $totalFiles
Files processed (with changes): $processedFiles
Files with errors: $($errorFiles.Count)
Success rate: $([math]::Round((($totalFiles - $errorFiles.Count) / $totalFiles * 100), 1))%
Processing time: $($duration.ToString('mm\:ss'))

Issues Found and Fixed:
Frontmatter normalization fixes: $frontmatterFixes
Placeholder content removed: $placeholderRemovals
Markdown formatting corrections: $formattingFixes
Title capitalization fixes: $titleCapitalizations

Files with Errors:
$($errorFiles | ForEach-Object { "- $_" } | Out-String)

Generated on: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@ | Set-Content -Path $reportPath -Encoding UTF8

Write-Host "`nDetailed report saved to: $reportPath" -ForegroundColor Green