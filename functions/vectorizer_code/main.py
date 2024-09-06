from azure.core.credentials import AzureKeyCredential
from shared_code.config import AzureOpenAIConfig, AISearchConfig, DbConfig
from shared_code.agent import ConnectionAgent
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndexerDataContainer,
    SearchIndexerDataSourceConnection
)
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    HnswParameters,
    VectorSearchAlgorithmMetric,
    ExhaustiveKnnAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    VectorSearchProfile,
    AzureOpenAIVectorizer,
    AzureOpenAIParameters,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
    SearchIndex
)
from azure.search.documents.indexes.models import (
    SplitSkill,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    AzureOpenAIEmbeddingSkill,
    SearchIndexerIndexProjections,
    SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjectionsParameters,
    IndexProjectionMode,
    SearchIndexerSkillset
)
from azure.search.documents.indexes.models import (
    SearchIndexer,
    FieldMapping
)

import logging


def create_datasource_connector(endpoint: str,
                                credential: AzureKeyCredential,
                                sql_table_name: str,
                                index_name: str,
                                sql_connection_string: str) -> SearchIndexerDataSourceConnection:

    """Create a datasource connector in the search service.

    Args:
        endpoint (str): ai search endpoint
        credential (AzureKeyCredential): ai search admin api key
        sql table name (str): table name
        index_name (str): desired index name
        sql_connection_string (str): sql connection string in the format
        'Server=<>,1433;Database=<>;Uid=<>;Pwd=<>;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    Returns:
        SearchIndexerDataSourceConnection: the data source.
    """
    try:
        indexer_client = SearchIndexerClient(endpoint,
                                             credential)
        container = SearchIndexerDataContainer(name=sql_table_name)
        data_source_connection = SearchIndexerDataSourceConnection(
            name=f'{index_name}',
            type='azuresql',
            connection_string=sql_connection_string,
            container=container

        )
        data_source = indexer_client.create_or_update_data_source_connection(data_source_connection)
        logging.info(f"Data source '{data_source.name}' created or updated.")
        return data_source
    except Exception as e:
        logging.error(f'Error creating data source: {e}.')


def create_search_index(endpoint: str,
                        credential: AzureKeyCredential,
                        azure_openai_endpoint: str,
                        azure_openai_embedding_deployment: str,
                        azure_openai_key: str,
                        index_name: str) -> SearchIndex:
    """Create a search index.

    Args:
        endpoint (str): ai search endpoint
        credential (AzureKeyCredential): ai search admin api key
        azure_openai_endpoint (str): aoai endpoint
        azure_openai_embedding_deployment (str): name of the embedding deployment
        azure_openai_key (AzureKeyCredential): aoai api key
        index_name (str): index name

    Returns:
        SearchIndex: the search index.
    """
    try:
        index_client = SearchIndexClient(endpoint=endpoint,
                                         credential=credential)
        fields = [
            SearchField(name='parent_id', type=SearchFieldDataType.String, sortable=True, filterable=True,
                        facetable=True),
            SearchField(name='title', type=SearchFieldDataType.String),
            SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True, sortable=True, filterable=True,
                        facetable=True, analyzer_name='keyword'),
            SearchField(name='process_info_chunk', type=SearchFieldDataType.String, sortable=False, filterable=False,
                        facetable=False),
            SearchField(name='vector', type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                        vector_search_dimensions=1536, vector_search_profile_name="myHnswProfile"),
        ]

        # Configure the vector search configuration
        vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name='myHnsw',
                    parameters=HnswParameters(
                        m=4,
                        ef_construction=400,
                        ef_search=500,
                        metric=VectorSearchAlgorithmMetric.COSINE,
                    ),
                ),
                ExhaustiveKnnAlgorithmConfiguration(
                    name='myExhaustiveKnn',
                    parameters=ExhaustiveKnnParameters(
                        metric=VectorSearchAlgorithmMetric.COSINE,
                    ),
                ),
            ],
            profiles=[
                VectorSearchProfile(
                    name='myHnswProfile',
                    algorithm_configuration_name='myHnsw',
                    vectorizer='myOpenAI',
                ),
                VectorSearchProfile(
                    name='myExhaustiveKnnProfile',
                    algorithm_configuration_name='myExhaustiveKnn',
                    vectorizer='myOpenAI',
                ),
            ],
            vectorizers=[
                AzureOpenAIVectorizer(
                    name='myOpenAI',
                    kind='azureOpenAI',
                    azure_open_ai_parameters=AzureOpenAIParameters(
                        resource_uri=azure_openai_endpoint,
                        deployment_id=azure_openai_embedding_deployment,
                        api_key=azure_openai_key,
                    ),
                ),
            ],
        )

        semantic_config = SemanticConfiguration(
            name='my-semantic-config',
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name='title'),
                content_fields=[
                    SemanticField(field_name='process_info_chunk'),
                    SemanticField(field_name='title'),
                    ],
            ),
        )

        # Create the semantic search with the configuration
        semantic_search = SemanticSearch(configurations=[semantic_config])

        # Create the search index
        index = SearchIndex(name=index_name,
                            fields=fields,
                            vector_search=vector_search,
                            semantic_search=semantic_search)

        result = index_client.create_or_update_index(index)
        logging.info(f'{result.name} created.')

        return index
    except Exception as e:
        logging.error(f'Error creating {index_name}: {e}.')


def create_skillset(index_name: str,
                    azure_openai_endpoint: str,
                    azure_openai_embedding_deployment: str,
                    azure_openai_key: str,
                    endpoint: str,
                    credential: AzureKeyCredential) -> SearchIndexerSkillset:
    """_summary_

    Args:
        index_name (str): index name
        azure_openai_endpoint (str): aoai endpoint
        azure_openai_embedding_deployment (str): name of the embedding deployment
        azure_openai_key (AzureKeyCredential): aoai api key
        endpoint (str): ai search endpoint
        credential (AzureKeyCredential): ai search admin api key

    Returns:
        SearchIndexerSkillset: the skillset to be used when indexing documents.
        In this case we use two skills: the split and embedding skills.
    """
    try:
        skillset_name = f'{index_name}-skillset'

        split_skill = SplitSkill(
            description='Split skill to chunk documents',
            text_split_mode="pages",
            context='/document',
            maximum_page_length=2000,
            page_overlap_length=200,
            inputs=[
                InputFieldMappingEntry(name='text',
                                       source='/document/ProcessInformation'),
            ],
            outputs=[
                OutputFieldMappingEntry(name='textItems',
                                        target_name='pages')
            ],
        )

        embedding_skill = AzureOpenAIEmbeddingSkill(
            description='Skill to generate embeddings via Azure OpenAI',
            context='/document/pages/*',
            resource_uri=azure_openai_endpoint,
            deployment_id=azure_openai_embedding_deployment,
            api_key=azure_openai_key,
            inputs=[
                InputFieldMappingEntry(name='text',
                                       source='/document/pages/*'),
            ],
            outputs=[
                OutputFieldMappingEntry(name='embedding',
                                        target_name='vector')
            ],
        )

        index_projections = SearchIndexerIndexProjections(
            selectors=[
                SearchIndexerIndexProjectionSelector(
                    target_index_name=index_name,
                    parent_key_field_name='parent_id',
                    source_context='/document/pages/*',
                    mappings=[
                            InputFieldMappingEntry(name='process_info_chunk', source='/document/pages/*'),
                            InputFieldMappingEntry(name='vector', source='/document/pages/*/vector'),
                            InputFieldMappingEntry(name='title', source='/document/Process'),
                        ],
                ),
            ],
            parameters=SearchIndexerIndexProjectionsParameters(
                projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS
            ),
        )

        skillset = SearchIndexerSkillset(
            name=skillset_name,
            description='Skillset to chunk documents and generating embeddings',
            skills=[split_skill, embedding_skill],
            index_projections=index_projections,
        )

        client = SearchIndexerClient(endpoint, credential)
        skillset_result = client.create_or_update_skillset(skillset)
        logging.info(f'{skillset.name} created.')

        return skillset_result

    except Exception as e:
        logging.error(f'Error creating {skillset.name}: {e}.')


def create_indexer(index_name: str,
                   skillset_name: str,
                   data_source: SearchIndexerDataSourceConnection,
                   endpoint: str,
                   credential: AzureKeyCredential
                   ) -> SearchIndexer:
    """Creates the indexer which will populate the index.

    Args:
        index_name (str): index name
        skillset_name (str): skillset name
        data_source (SearchIndexerDataSourceConnection): data source
        endpoint (str): ai search endpoint
        credential (AzureKeyCredential): ai search admin api key

    Returns:
        SearchIndexer: the search indexer.
    """
    try:
        indexer_name = f'{index_name}-indexer'

        indexer = SearchIndexer(
            name=indexer_name,
            description='Indexer to index documents and generate embeddings',
            skillset_name=skillset_name,
            target_index_name=index_name,
            data_source_name=data_source.name,
            field_mappings=[FieldMapping(source_field_name='id', target_field_name='chunk_id'),
                            FieldMapping(source_field_name='Process', target_field_name='title'),
                            FieldMapping(source_field_name='ProcessInformation', target_field_name='process_info_chunk')
                            ]
        )

        indexer_client = SearchIndexerClient(endpoint,
                                             credential)
        indexer_result = indexer_client.create_or_update_indexer(indexer)

        # Run the indexer
        indexer_client.run_indexer(indexer_name)
        logging.info(f'{indexer_name} is created and running. \
                     If queries return no results, please wait a bit and try again.')

        return indexer_result

    except Exception as e:
        logging.error(f'Error creating {indexer_name}: {e}.')


def main() -> None:
    aoai_cfg = AzureOpenAIConfig()
    ais_cfg = AISearchConfig()
    db_cfg = DbConfig()
    db_agent = ConnectionAgent(db_cfg.MSSQL_USERNAME,
                               db_cfg.MSSQL_PASSWORD,
                               db_cfg.MSSQL_HOST,
                               db_cfg.MSSQL_PORT,
                               db_cfg.MSSQL_DATABASE,
                               db_cfg.MSSQL_DRIVER)

    endpoint = ais_cfg.AZURE_SEARCH_SERVICE_ENDPOINT
    credential = AzureKeyCredential(ais_cfg.AZURE_SEARCH_ADMIN_KEY)
    sql_connection_string = db_agent.create_connection_str

    index_name = ais_cfg.AZURE_SEARCH_INDEX

    aoai_endpoint = aoai_cfg.AOAI_ENDPOINT
    aoai_api_key = aoai_cfg.AOAI_API_KEY
    aoai_embedding_deployment = aoai_cfg.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    try:
        ds = create_datasource_connector(endpoint,
                                         credential,
                                         'Content.AI_RagQnA',  # schema name must be explicitly set
                                         index_name,
                                         sql_connection_string)
    except Exception as e:
        logging.error(f'Error creating data source: {e}')

    try:
        create_search_index(endpoint,
                            credential,
                            aoai_endpoint,
                            aoai_embedding_deployment,
                            aoai_api_key,
                            index_name)
    except Exception as e:
        logging.error(f'Error creating search index: {e}')

    try:
        ss = create_skillset(index_name,
                             aoai_endpoint,
                             aoai_embedding_deployment,
                             aoai_api_key,
                             endpoint,
                             credential)
    except Exception as e:
        logging.error(f'Error creating skillset: {e}')

    try:
        create_indexer(index_name,
                       ss.name,
                       ds,
                       endpoint,
                       credential)
    except Exception as e:
        logging.error(f'Error creating indexer: {e}')
