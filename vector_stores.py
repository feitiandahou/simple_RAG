import config_data as config
from dotenv import load_dotenv
from langchain_chroma import Chroma


load_dotenv()

class VectorStoreService(object):
    def __init__(self, embedding):
        '''
        :param embedding: 嵌入模型对象，负责将文本转换为向量表示
        '''
        self.embedding = embedding

        self.vector_store = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory
        )
    def get_retriever(self):
        '''返回向量检索器，用于从向量数据库中检索相关的文本段'''
        return self.vector_store.as_retriever()

if __name__ == '__main__':
    from langchain_community.embeddings import DashScopeEmbeddings
    retriever = VectorStoreService(DashScopeEmbeddings(model="text-embedding-v4")).get_retriever()
    res = retriever.invoke("什么是RAG？")
    print(res)