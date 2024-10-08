# Microsoft RAGHack 2024

## About

This is my entry to the [2024 Microsoft RAGHack](https://techcommunity.microsoft.com/t5/educator-developer-blog/raghack-free-global-hackathon-sept-3rd-13th-2024/ba-p/4217191https://techcommunity.microsoft.com/t5/educator-developer-blog/raghack-free-global-hackathon-sept-3rd-13th-2024/ba-p/4217191). My OpenAI RAG-powered chatbot is driven by the need to provide guidance, troubleshooting and problem resolution during various CNC machining processes.

## Solution Components

The solution consists of the following components:

- **Azure SQL**: storing the source data for the RAG, storing the user prompts, the bot's responses and the feedback to bot responses. 
- **Azure AI Search**: indexing (vectorizing) and storing vectorized data.
- **Azure OpenAI**: hosting AI models and inference.
- **Azure function** with timer trigger: automating the data vectorization process on a recurring basis (e.g. daily).
- **Azure AI Bot Service**: bot application.
- **Azure Web App**: hosting the  Azure AI Bot Service.

### Azure SQL

- Tier: Basic, 5 DTUs

I use one simple table for storing the source data subject to vectorization. To avoid disclosing company data I have used ChatGPT to generate dummy data on five manufacturing processes. In a production scenario, an upstream process would populate this table. 

| table name | purpose | DDL statement |
|------------|----------|---------------|
| Content.AI_RagQnA| stores the source data | `CREATE TABLE [Content].[AI_RagQnA]`(<br> `[ID] [int] IDENTITY(1,1) PRIMARY KEY,`<br />`[Process] nvarchar(1024) NOT NULL`,<br />`[ProcessInformation] nvarchar(max) NOT NULL)`| 
| Content.AIBotChatHistory | stores conversation history | `CREATE TABLE [Content].[AIBotChatHistory](`<br>`[Id] [int] IDENTITY(1,1) PRIMARY KEY',`<br>`[Rating] [tinyint] NULL`,<br>`[UserName] [nvarchar](128) NULL`,<br>`[Response] [nvarchar](max) NOT NULL`,<br>`[Channel] [nvarchar](128) NULL`,<br>`[InteractionType] [nvarchar](8) NOT NULL`,<br>`[CreatedOn] [datetime] NOT NULL`,<br>`[Prompt] [nvarchar](max) NULL)`

### Azure AI Search

- Tier: Standard 
- Semantic configuration: yes. 

The setup of the data source, index, skillset and indexer are done entirely programmatically via the Python SDK using the Azure Function. 

### Azure OpenAI

- Tier: Standard
- Models:
    - **gpt-4o** for the RAG
    - **text-embedding-ada-002** for vectorizing the content. 

### Vectorizer function

- Type: timer-triggered Azure function
- folder: `functions`
- to run the function, type in the VS Code terminal: 
    - `cd functions`
    - `func start`
    - make an HTTP request:
        - type: POST
        - URI: `http://localhost:7071/admin/functions/Vectorizer`
        - Body: `{ "input": "" }`
- to run the function you must set the following environment variables in the `local.settings.json` file:

| variable | explanation |
|---|---|
| `MSSQL_USERNAME`| sql login user name |
| `MSSQL_PASSWORD`| sql login password |
| `MSSQL_HOST`| ***.database.windows.net |
| `MSSQL_PORT` | 1433 |
| `MSSQL_DATABASE` | database name |
| `MSSQL_DRIVER` | ODBC Driver 17 for SQL Server|
| `AOAI_ENDPOINT` | https://***.openai.azure.com/ |
| `AOAI_API_KEY`| api key for the AOAI service |,
| `AOAI_API_V` | 2024-05-01-preview |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | name of the deployment of the embeddings model |
| `AZURE_SEARCH_SERVICE_ENDPOINT` | https://***.search.windows.net" |
| `AZURE_SEARCH_ADMIN_KEY` | admin key for connecting to the search service |
| `AZURE_SEARCH_INDEX` | the desired search index name | 

### Web app 

- folder: `bot`
- to run the app: 
    - [download the Bot Framework Emulator](https://learn.microsoft.com/en-us/azure/bot-service/bot-service-debug-emulator?view=azure-bot-service-4.0&tabs=python) then type in the VS Code terminal
        - `cd bot`
        - `python app.py`
    - using the Bot Framework Emulator open the bot URL `http://localhost:3978/api/messages`
- to run the app you must set the following environment variables in the `cfg\.env` file:

| variable | explanation |
|---|---|
| `AZURE_OPENAI_ENDPOINT`| AZURE_OPENAI_ENDPOINT|
| `OPENAI_API_KEY`| api key for the AOAI service |
| `DEPLOYMENT_ID` | name of the deployment to use for generating answers |
| `API_V` | 2024-05-01-preview |
| `SEARCH_KEY` | admin key for connecting to the search service |
| `SEARCH_ENDPOINT` | https://***.search.windows.net" |
| `SEARCH_INDEX_NAME` | the search index name to use for generating answers | 
| `MicrosoftAppId` | leave blank for local development unless you plan to deploy to Azure |
| `MicrosoftAppPassword` | leave blank for local development unless you plan to deploy to Azure |
| `MSSQL_USERNAME`| sql login user name |
| `MSSQL_PASSWORD`| sql login password |
| `MSSQL_HOST`| ****.database.windows.net |
| `MSSQL_PORT` | 1433 |
| `MSSQL_DATABASE` | database name to use for storing conversation data|
| `MSSQL_DRIVER` | ODBC Driver 17 for SQL Server|

## Deployment 

Examine the bash scrirpts in `/deploy`. Adjust the variables and run from a Bash terminal. 
Once the services are deployed:
- Set your environment variables in Azure.
- configure the web app startup command: `python3.11 -m aiohttp.web -H 0.0.0.0 -P 8000 app:init_func`
- configure the messaging endpoint in your bot service `{webappname}/api/messages`

## Sample questions:

- Which CNC machining processes do you know and can answer questions about?
- What are the maximum allowed vibration values during machining aluminum?
- What is the average spindle speed across all processes?
- What are the acceptable vibration levels for steel component milling?
    1. Help me troubleshoot high coolant temperature during boring of aluminum.
    2. I cannot boost the flow or use a chiller. What is the next best thing to do?

## Others

- [project submission](https://github.com/microsoft/RAG_Hack/issues/58)
- [video](https://www.youtube.com/watch?v=GN0SccxbpjI)