<#
.SYNOPSIS
    Automated Infrastructure Provisioning and Deployment Script for Research2Build on Microsoft Azure.
.DESCRIPTION
    Provisions all required Azure native services (Azure Blob Storage, Azure AI Search, Azure OpenAI/Foundry,
    Azure App Service Linux, and Azure Static Web Apps) and deploys both backend and frontend.
#>

param(
    [string]$ResourceGroupName = "moksh",
    [string]$PrimaryLocation = "centralindia",
    [string]$SecondaryLocation = "eastasia",
    [string]$StorageAccountName = "stgr2bmoksh",
    [string]$SearchServiceName = "search-r2b-moksh",
    [string]$CognitiveServiceName = "research2build-resource",
    [string]$AppServicePlanName = "asp-r2b-moksh",
    [string]$WebAppName = "api-r2b-moksh",
    [string]$StaticWebAppName = "swa-r2b-moksh"
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  Research2Build — Azure Deployment Automation Pipeline  " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 1. Verify Azure CLI Login
Write-Host "`n[1/7] Verifying Azure CLI Authentication..." -ForegroundColor Yellow
$sub = az account show --query "{name:name, id:id, state:state}" -o json | ConvertFrom-Json
if (-not $sub) {
    throw "Not logged into Azure CLI. Please run 'az login' first."
}
Write-Host "Connected to Azure Subscription: $($sub.name) ($($sub.id))" -ForegroundColor Green

# 2. Resource Group
Write-Host "`n[2/7] Ensuring Resource Group: $ResourceGroupName in $PrimaryLocation..." -ForegroundColor Yellow
az group create --name $ResourceGroupName --location $PrimaryLocation -o none
Write-Host "Resource Group '$ResourceGroupName' ready." -ForegroundColor Green

# 3. Azure Storage Account & Container
Write-Host "`n[3/7] Provisioning Azure Blob Storage: $StorageAccountName..." -ForegroundColor Yellow
az storage account create --name $StorageAccountName --resource-group $ResourceGroupName --location $PrimaryLocation --sku Standard_LRS --kind StorageV2 -o none
$storageConnString = az storage account show-connection-string --name $StorageAccountName --resource-group $ResourceGroupName --query connectionString -o tsv
az storage container create --name "papers" --connection-string $storageConnString --public-access off -o none
Write-Host "Blob Storage & 'papers' container configured." -ForegroundColor Green

# 4. Azure AI Search Service
Write-Host "`n[4/7] Ensuring Azure AI Search: $SearchServiceName..." -ForegroundColor Yellow
$searchExists = az search service show --name $SearchServiceName --resource-group $ResourceGroupName --query name -o tsv 2>$null
if (-not $searchExists) {
    az search service create --name $SearchServiceName --resource-group $ResourceGroupName --location $PrimaryLocation --sku free -o none
}
$searchEndpoint = "https://$SearchServiceName.search.windows.net"
$searchKey = az search admin-key show --service-name $SearchServiceName --resource-group $ResourceGroupName --query primaryKey -o tsv
Write-Host "Azure AI Search endpoint: $searchEndpoint" -ForegroundColor Green

# 5. Azure OpenAI / Cognitive Services
Write-Host "`n[5/7] Ensuring Azure Cognitive Services: $CognitiveServiceName..." -ForegroundColor Yellow
$cogExists = az cognitiveservices account show --name $CognitiveServiceName --resource-group $ResourceGroupName --query name -o tsv 2>$null
if (-not $cogExists) {
    az cognitiveservices account create --name $CognitiveServiceName --resource-group $ResourceGroupName --location $SecondaryLocation --kind OpenAI --sku S0 --yes -o none
}
$cogEndpoint = az cognitiveservices account show --name $CognitiveServiceName --resource-group $ResourceGroupName --query properties.endpoint -o tsv
$cogKey = az cognitiveservices account keys list --name $CognitiveServiceName --resource-group $ResourceGroupName --query key1 -o tsv
Write-Host "Azure OpenAI/Foundry endpoint: $cogEndpoint" -ForegroundColor Green

# 6. Backend Deployment (App Service Plan & Linux Web App)
Write-Host "`n[6/7] Deploying Backend to Azure App Service: $WebAppName..." -ForegroundColor Yellow
$planExists = az appservice plan show --name $AppServicePlanName --resource-group $ResourceGroupName --query name -o tsv 2>$null
if (-not $planExists) {
    az appservice plan create --name $AppServicePlanName --resource-group $ResourceGroupName --location $PrimaryLocation --is-linux --sku B1 -o none
}
$appExists = az webapp show --name $WebAppName --resource-group $ResourceGroupName --query name -o tsv 2>$null
if (-not $appExists) {
    az webapp create --name $WebAppName --plan $AppServicePlanName --resource-group $ResourceGroupName --runtime "PYTHON:3.12" -o none
}

# Set App Settings
az webapp config appsettings set --name $WebAppName --resource-group $ResourceGroupName --settings `
    AZURE_STORAGE_CONNECTION_STRING="$storageConnString" `
    AZURE_STORAGE_CONTAINER="papers" `
    AZURE_SEARCH_ENDPOINT="$searchEndpoint" `
    AZURE_SEARCH_KEY="$searchKey" `
    AZURE_SEARCH_INDEX="research2build-evidence" `
    AZURE_OPENAI_ENDPOINT="$cogEndpoint" `
    AZURE_OPENAI_API_KEY="$cogKey" `
    AZURE_OPENAI_DEPLOYMENT="gpt-4o" `
    AZURE_OPENAI_API_VERSION="2024-02-15-preview" `
    OPENAI_API_KEY="$cogKey" `
    OPENAI_API_BASE="$cogEndpoint" `
    PYTHONPATH="/home/site/wwwroot" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
    PORT="8000" `
    FRONTEND_ORIGINS="*" -o none

az webapp config set --name $WebAppName --resource-group $ResourceGroupName --startup-file "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000" -o none

# Package and deploy backend
& "$ScriptRoot\package_backend.ps1"
az webapp deploy --src-path "$ProjectRoot\backend-deploy.zip" -g $ResourceGroupName -n $WebAppName --type zip -o none
Write-Host "Backend API deployed at: https://$WebAppName.azurewebsites.net" -ForegroundColor Green

# 7. Frontend Deployment (Azure Static Web Apps)
Write-Host "`n[7/7] Deploying Frontend to Azure Static Web Apps: $StaticWebAppName..." -ForegroundColor Yellow
$swaExists = az staticwebapp show --name $StaticWebAppName --resource-group $ResourceGroupName --query name -o tsv 2>$null
if (-not $swaExists) {
    az staticwebapp create --name $StaticWebAppName --resource-group $ResourceGroupName --location $SecondaryLocation --sku Free -o none
}
$swaToken = az staticwebapp secrets list --name $StaticWebAppName --resource-group $ResourceGroupName --query properties.apiKey -o tsv
$swaHost = az staticwebapp show --name $StaticWebAppName --resource-group $ResourceGroupName --query defaultHostname -o tsv

# Build frontend with production API URL
Set-Content -Path "$ProjectRoot\frontend\.env.production" -Value "VITE_API_BASE_URL=https://$WebAppName.azurewebsites.net"
Push-Location "$ProjectRoot\frontend"
try {
    npm run build
    Copy-Item "$ProjectRoot\frontend\staticwebapp.config.json" -Destination "$ProjectRoot\frontend\dist\staticwebapp.config.json" -Force -ErrorAction SilentlyContinue
    npx -y @azure/static-web-apps-cli deploy ./dist --deployment-token $swaToken --env production
} finally {
    Pop-Location
}

Write-Host "`n=========================================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETE!                                   " -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green
Write-Host "Frontend URL:  https://$swaHost" -ForegroundColor Cyan
Write-Host "Backend API:   https://$WebAppName.azurewebsites.net" -ForegroundColor Cyan
Write-Host "API Health:    https://$WebAppName.azurewebsites.net/health" -ForegroundColor Cyan
Write-Host "API Docs:      https://$WebAppName.azurewebsites.net/docs" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Green
