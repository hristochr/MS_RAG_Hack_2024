RESOURCE_GROUP="myResourceGroup"
LOCATION="eastus"
WEB_APP_NAME="manufacturing-bot-app"
PLAN_NAME="${WEB_APP_NAME}Plan"
DEPLOYMENT_SOURCE_PATH="/path/to/your/webapp/code"  # Replace with the path to your app's code

az group create --name $RESOURCE_GROUP --location $LOCATION

az appservice plan create --name $PLAN_NAME --resource-group $RESOURCE_GROUP --sku B1 --is-linux

az webapp create --resource-group $RESOURCE_GROUP --plan $PLAN_NAME --name $WEB_APP_NAME --runtime "PYTHON|3.11"

az webapp up --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP --location $LOCATION --plan $PLAN_NAME --runtime "PYTHON:3.11" --src-path $DEPLOYMENT_SOURCE_PATH