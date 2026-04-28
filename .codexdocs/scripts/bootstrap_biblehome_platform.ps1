$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path -LiteralPath ".").Path
$parentDir = Split-Path -Path $repoRoot -Parent
$targetRoot = Join-Path -Path $parentDir -ChildPath "biblehome-platform"

$folders = @(
    "docs",
    "migrations",
    "ingestion",
    "static-data",
    "api",
    "rag"
)

if (-not (Test-Path -LiteralPath $targetRoot)) {
    New-Item -ItemType Directory -Path $targetRoot | Out-Null
    Write-Output "Created workspace: $targetRoot"
} else {
    Write-Output "Workspace exists: $targetRoot"
}

foreach ($folder in $folders) {
    $path = Join-Path -Path $targetRoot -ChildPath $folder
    if (-not (Test-Path -LiteralPath $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
        Write-Output "Created folder: $path"
    } else {
        Write-Output "Folder exists: $path"
    }
}

$readmePath = Join-Path -Path $targetRoot -ChildPath "README.md"
if (-not (Test-Path -LiteralPath $readmePath)) {
    @'
# biblehome-platform

This workspace is dedicated to BibleHome platform implementation.

## Scope

- API and application code
- PostgreSQL migration scripts
- Ingestion and normalization pipelines
- Static chapter JSON generation for CDN
- RAG and embedding workflows

## Boundary

The sibling `bible_databases` repository remains the upstream Bible source-data repository.
'@ | Set-Content -LiteralPath $readmePath -Encoding UTF8
    Write-Output "Created file: $readmePath"
} else {
    Write-Output "File exists: $readmePath"
}

$gitignorePath = Join-Path -Path $targetRoot -ChildPath ".gitignore"
if (-not (Test-Path -LiteralPath $gitignorePath)) {
    @'
.env
.env.*
*.log
*.tmp
node_modules/
dist/
build/
.venv/
__pycache__/
'@ | Set-Content -LiteralPath $gitignorePath -Encoding UTF8
    Write-Output "Created file: $gitignorePath"
} else {
    Write-Output "File exists: $gitignorePath"
}
