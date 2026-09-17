param(
    [string]$SubscriptionId = "b0da5a4e-7162-4bba-9bcf-94b325b93633",
    [string]$ResourceGroup = "rg-cs-ai-lab",
    [string]$AppName = "cs-ai-lab-web-jlavallet3",
    [string]$AppServicePlanName = "asp-cs-ai-lab",
    [string]$Location = "eastus2"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$packagePath = Join-Path $env:TEMP "cs-ai-lab.zip"

az account set --subscription $SubscriptionId
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

az deployment group create `
    --resource-group $ResourceGroup `
    --template-file "$PSScriptRoot/main.bicep" `
    --parameters `
        appName=$AppName `
        appServicePlanName=$AppServicePlanName `
        location=$Location `
        searchEndpoint=https://cs-ai-lab-search-jlavallet3.search.windows.net `
        openAiEndpoint=https://cs-ai-lab-project-resource.openai.azure.com/openai/v1
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if (Test-Path $packagePath) {
    Remove-Item $packagePath
}

$filesToDeploy = Get-ChildItem -Path $projectRoot -Recurse -File |
    Where-Object {
        $_.FullName -notmatch '\\.git\\|\\.venv\\|\\data\\|\\.env$|\\evaluation\\results'
    }
Compress-Archive -Path $filesToDeploy.FullName -DestinationPath $packagePath

az webapp deploy `
    --resource-group $ResourceGroup `
    --name $AppName `
    --src-path $packagePath `
    --type zip `
    --async false
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$principalId = az webapp identity show `
    --resource-group $ResourceGroup `
    --name $AppName `
    --query principalId `
    --output tsv
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Output "Web app: https://$AppName.azurewebsites.net"
Write-Output "Managed identity principal ID: $principalId"