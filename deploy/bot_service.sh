BOT_SERVICE_NAME="manufacturing-Support-Bot"
BOT_APP_PASSWORD="Password"  # Change this to a secure password

# register a bot service and an app registration
az bot create --resource-group $RESOURCE_GROUP --name $BOT_SERVICE_NAME --kind webapp --location $LOCATION \
  --sku F0 --appid $(az ad app create --display-name "${BOT_SERVICE_NAME}App" --password $BOT_APP_PASSWORD --query appId -o tsv) \
  --password $BOT_APP_PASSWORD --echo
