RESOURCE_GROUP="myResourceGroup"
LOCATION="eastus"
FUNCTION_APP_NAME="vectorizerFunctionApp"
STORAGE_ACCOUNT_NAME="vectorizerstorage$(date +%s)"  

az group create --name $RESOURCE_GROUP --location $LOCATION

az storage account create --name $STORAGE_ACCOUNT_NAME --location $LOCATION --resource-group $RESOURCE_GROUP --sku Standard_LRS

az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name $FUNCTION_APP_NAME \
  --storage-account $STORAGE_ACCOUNT_NAME

echo 'Creating a default Timer Trigger function...'
func init $FUNCTION_APP_NAME --python
cd $FUNCTION_APP_NAME
func new --template "Timer trigger" --name TimerTriggerFunction
func azure functionapp publish $FUNCTION_APP_NAME
