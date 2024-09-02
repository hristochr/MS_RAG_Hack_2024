import json
from openai import AsyncAzureOpenAI
from cfg.config import OpenAIServiceConfig

CONFIG = OpenAIServiceConfig()


class OpenAIServiceResponder():

    @staticmethod
    async def get_completion(usr_msg: list[dict[str:str]]) -> tuple[str, list[tuple[int, str, str]]]:

        rag_client = AsyncAzureOpenAI(
            azure_endpoint=CONFIG.AZURE_OPENAI_ENDPOINT,
            api_key=CONFIG.API_KEY,
            api_version=CONFIG.API_V
        )

        completion = await rag_client.chat.completions.create(
            model=CONFIG.DEPLOYMENT_ID,
            messages=usr_msg,
            extra_body={
                'data_sources': [
                    {
                        'type': 'azure_search',
                        'parameters': {
                            'endpoint': CONFIG.SEARCH_ENDPOINT,
                            'authentication': {
                                'type': 'api_key',
                                'key': CONFIG.SEARCH_KEY
                                 },
                            'embedding_dependency': {
                                'type': 'deployment_name',
                                'deployment_name': 'embeddings'
                            },  # required when using vector search to vectorize the user query
                            'index_name': CONFIG.SEARCH_INDEX_NAME,
                            # name of the semantic config # name of the semantic config
                            'semantic_configuration': 'my-semantic-config',
                            'query_type': 'vector_semantic_hybrid',
                            # If you're using your own index, you will be prompted in the Azure OpenAI Studio to define
                            # which fields you want to map for answering questions
                            'fields_mapping': {},
                            'role_information':
                                "You are a manufacturing process expert. Your task is to help junior operators resolve \
                                 CNC machining process problems by providing accurate answers based on the data you \
                                 have. If the  answer is not available in the retrieved data, reply with \
                                'I do not know. Maybe the answer you are looking for is not part of the source data.'",
                            'filter': None,  # https://learn.microsoft.com/en-us/azure/search/search-filters
                            # Determines the system's aggressiveness in filtering search documents based on their
                            # similarity scores.
                            'strictness': 3,
                            # how many documents to show
                            'top_n_documents': 2,
                            # limit responses from the model to the grounding data content
                            'in_scope': True
                        }
                    }
                ]
            },
            temperature=0.25,
            top_p=1,
            max_tokens=2048,
            stop=None
        )

        doc_data = None
        answer = json.loads(completion.model_dump_json(indent=2))['choices'][0]['message']['content']
        if 'The requested information is not available in the retrieved data. Please try another query ' not in answer:
            document_refs = json.loads(completion.model_dump_json(indent=2))['choices'][0]['message']['context']
            doc_data = [(nr+1, citation['title'], citation['content'])
                        for nr, citation
                        in enumerate(document_refs['citations'])]

        return (answer, doc_data)
