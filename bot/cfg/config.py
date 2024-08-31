import os
from dotenv import load_dotenv

load_dotenv()


class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")


class OpenAIServiceConfig:
    """ Open AI Service Configuration """

    API_KEY = os.environ.get('OPENAI_API_KEY')
    SEARCH_KEY = os.environ.get('SEARCH_KEY')
    SEARCH_ENDPOINT = os.environ.get('SEARCH_ENDPOINT')
    SEARCH_INDEX_NAME = os.environ.get('SEARCH_INDEX_NAME')
    AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
    DEPLOYMENT_ID = os.environ.get('DEPLOYMENT_ID')
    API_V = os.environ.get('API_V')


class DbConfig:

    """Azure SQL account"""
    MSSQL_USERNAME = os.environ.get('MSSQL_USERNAME')
    MSSQL_PASSWORD = os.environ.get('MSSQL_PASSWORD')
    MSSQL_HOST = os.environ.get('MSSQL_HOST')
    MSSQL_PORT = os.environ.get('MSSQL_PORT')
    MSSQL_DATABASE = os.environ.get('MSSQL_DATABASE')
    MSSQL_DRIVER = os.environ.get('MSSQL_DRIVER')

# if __name__ == "__main__":
#     # c = DefaultConfig()
#     d = DbConfig()
#     print(d.MSSQL_DATABASE)
