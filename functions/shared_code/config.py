import os
from attrs import define, field


@define
class DbConfig:
    MSSQL_USERNAME: str = field(default=os.getenv('MSSQL_USERNAME'))
    MSSQL_PASSWORD: str = field(default=os.getenv('MSSQL_PASSWORD'))
    MSSQL_HOST: str = field(default=os.getenv('MSSQL_HOST'))
    MSSQL_PORT: int = field(default=os.getenv('MSSQL_PORT'))
    MSSQL_DATABASE: str = field(default=os.getenv('MSSQL_DATABASE'))
    MSSQL_DRIVER: str = field(default=os.getenv('MSSQL_DRIVER'))


@define
class AzureOpenAIConfig:
    AOAI_ENDPOINT: str = field(default=os.getenv('AOAI_ENDPOINT'))
    AOAI_API_KEY: str = field(default=os.getenv('AOAI_API_KEY'))
    AOAI_API_V: str = field(default=os.getenv('AOAI_API_V'))
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: int = field(default=os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT'))


@define
class AISearchConfig:
    AZURE_SEARCH_SERVICE_ENDPOINT: str = field(default=os.getenv('AZURE_SEARCH_SERVICE_ENDPOINT'))
    AZURE_SEARCH_ADMIN_KEY: str = field(default=os.getenv('AZURE_SEARCH_ADMIN_KEY'))
    AZURE_SEARCH_INDEX: str = field(default=os.getenv('AZURE_SEARCH_INDEX'))
