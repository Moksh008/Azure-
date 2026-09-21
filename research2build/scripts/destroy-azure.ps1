<#
.SYNOPSIS
    Clean teardown script for all Research2Build Azure resources.
.DESCRIPTION
    Deletes the resource group containing all provisioned resources to prevent any lingering cost.
#>

param(
    [string]$ResourceGroupName = "moksh",
    [switch]$Force
)

Write-Host "=========================================================" -ForegroundColor Yellow
Write-Host "  Research2Build — Azure Teardown Script                 " -ForegroundColor Yellow
Write-Host "=========================================================" -ForegroundColor Yellow

if (-not $Force) {
    $confirm = Read-Host "Are you sure you want to delete Resource Group '$ResourceGroupName' and all its resources? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Host "Teardown cancelled." -ForegroundColor Cyan
        exit 0
    }
}

Write-Host "Deleting Resource Group '$ResourceGroupName' asynchronously..." -ForegroundColor Yellow
az group delete --name $ResourceGroupName --yes --no-wait

Write-Host "Resource Group '$ResourceGroupName' deletion initiated. All resources are being deprovisioned." -ForegroundColor Green
