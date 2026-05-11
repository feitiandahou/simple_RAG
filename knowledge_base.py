from datetime import datetime
import hashlib
import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import config_data as config

load_dotenv()

def check_md5(md5_str: str):
    '''
    检查给定的字符串是否是有效的MD5哈希值。
    返回:bool: 如果字符串是有效的MD5哈希值，则返回True，否则返回False。
    '''
    if not os.path.exists(config.md5_path):
        open(config.md5_path, 'w', encoding='utf-8').close()
        return False
    else:
        for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip() #处理字符串前后的空格和回车
            if line == md5_str:
                return True
        
        return False
def save_md5(md5_str: str):
    with open(config.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str + '\n')

def get_string_md5(input_str: str, encoding='utf-8'):
    str_bytes = input_str.encode(encoding=encoding)

    md5_obj = hashlib.md5()
    md5_obj.update(str_bytes)
    md5_hex = md5_obj.hexdigest()
    return md5_hex

class KnowledgeBaseService(object):
    def __init__(self):
        os.makedirs(config.persist_directory, exist_ok=True)

        self.chroma = Chroma(
            collection_name=config.collection_name, #数据库的表名
            embedding_function=DashScopeEmbeddings(model="text-embedding-v4"),
            persist_directory=config.persist_directory, #数据库的存储路径
        ) #向量存储的实例 Chroma向量库对象

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size, #分割后的文本段最大长度
            chunk_overlap=config.chunk_overlap, #分割后的文本段之间的重叠长度
            separators=config.separators, #分割文本的分隔符列表
            length_function=len, #计算文本长度的函数
        ) #文本分割器对象

    def upload_by_str(self, data: str, filename):
        #将传入的字符串向量化，存入向量数据库中
        md5_hex = get_string_md5(data)

        if check_md5(md5_hex):
            return f"文件 {filename} 已经存在于知识库中，无需重复上传。"
        if len(data) > config.max_split_char_number:
            knowledge_chunks: list[str] = self.spliter.split_text(data)
        else:
            knowledge_chunks = [data]
        
        metadata = {
            "source": filename,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "user_001",
        }

        self.chroma.add_texts(
            knowledge_chunks,
            metadatas=[metadata for _ in knowledge_chunks],
        )
        save_md5(md5_hex)
        return f"文件 {filename} 已成功上传到知识库中，共分割成 {len(knowledge_chunks)} 个文本块。"
    
if __name__ == '__main__':
    service = KnowledgeBaseService()
    r = service.upload_by_str("这是一个测试文本。", "test.txt")
    print(r)