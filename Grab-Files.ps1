# Grab-Files.ps1
# This script recursively searches the current directory for files with specified extensions,
# excluding any directories that start with a dot (e.g., .venv).
# It concatenates their contents into a single output file, prefixed with a header for each file
# containing the file name and its original path.
# The output file is named after the current directory with a timestamp in YYYYMMDDHHMM format and .txt extension.

# Configuration: Edit the $extensions array to add or remove file types to grab.
# Example: To include C++ files, add '.h', '.cpp', 'makefile' etc.
$extensions = @('*.py', '*.json', '*.md')

# Get current directory name
$currentDir = (Get-Item -Path .).Name

# Generate timestamp
$timestamp = Get-Date -Format "yyyyMMddHHmm"

# Output file name
$outputFile = "$currentDir$timestamp.txt"

# Clear or create the output file
Out-File -FilePath $outputFile -Encoding utf8

# Find all matching files recursively, excluding paths with dot directories
$files = Get-ChildItem -Path . -Recurse -File -Include $extensions | Where-Object { $_.FullName -notmatch '(\\\.|/\.)' }

foreach ($file in $files) {
    # Header for the file
    $header = @"
===== File: $($file.Name) =====
Path: $($file.FullName)
=====

"@
    # Append header to output
    Add-Content -Path $outputFile -Value $header -Encoding utf8

    # Append file content
    Get-Content -Path $file.FullName | Add-Content -Path $outputFile -Encoding utf8

    # Optional: Add a blank line separator after content
    Add-Content -Path $outputFile -Value "`n" -Encoding utf8
}

Write-Host "Files concatenated into $outputFile"
