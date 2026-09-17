@description('Unique name for the Linux App Service web app.')
param appName string

@description('Name for the App Service plan.')
param appServicePlanName string

@description('Azure region for App Service resources.')
param location string = resourceGroup().location

@description('Azure AI Search endpoint used by the application.')
param searchEndpoint string

@description('Azure AI Search index name used by the application.')
param searchIndexName string = 'cs-books'

@description('Azure OpenAI endpoint used by the application.')
param openAiEndpoint string

@description('Azure OpenAI chat deployment name.')
param chatDeployment string = 'gpt-4.1-mini'

@description('Azure OpenAI embedding deployment name.')
param embeddingDeployment string = 'text-embedding-3-small'

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  kind: 'linux'
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  properties: {
    reserved: true
  }
}

resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: appName
  location: location
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    httpsOnly: true
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.13'
      appCommandLine: 'python -m streamlit run apps/chat.py --server.port 8000 --server.address 0.0.0.0'
      appSettings: [
        {
          name: 'AZURE_SEARCH_ENDPOINT'
          value: searchEndpoint
        }
        {
          name: 'AZURE_SEARCH_INDEX_NAME'
          value: searchIndexName
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: openAiEndpoint
        }
        {
          name: 'AZURE_OPENAI_CHAT_DEPLOYMENT'
          value: chatDeployment
        }
        {
          name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
          value: embeddingDeployment
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
      ]
    }
  }
}

output webAppName string = webApp.name
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output principalId string = webApp.identity.principalId