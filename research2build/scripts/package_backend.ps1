$ErrorActionPreference = "Stop"
$root = "d:\Azure-\research2build"
$staging = "$root\deploy_staging"
$zipPath = "$root\backend-deploy.zip"

if (Test-Path $staging) {
    Remove-Item -Recurse -Force $staging
}
New-Item -ItemType Directory -Path $staging | Out-Null

New-Item -ItemType Directory -Path "$staging\backend" | Out-Null
Copy-Item "$root\backend\requirements.txt" -Destination "$staging\requirements.txt"
Copy-Item "$root\main.py" -Destination "$staging\main.py"
Copy-Item "$root\startup.sh" -Destination "$staging\startup.sh"
Copy-Item "$root\backend\__init__.py" -Destination "$staging\backend\__init__.py"
Copy-Item "$root\backend\app" -Destination "$staging\backend\app" -Recurse
Copy-Item "$root\shared" -Destination "$staging\shared" -Recurse

Get-ChildItem -Path $staging -Recurse -Include "__pycache__", ".pytest_cache", "*.pyc" | Remove-Item -Recurse -Force

if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

Compress-Archive -Path "$staging\*" -DestinationPath $zipPath
Remove-Item -Recurse -Force $staging

Write-Host "Backend deploy zip packaged successfully at $zipPath"
