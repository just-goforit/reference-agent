# utils.py
import os
import re
import logging
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from config import LOG_LEVEL, DOWNLOAD_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 直接使用logging.INFO而不是从环境变量获取
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('reference_agent.log')
    ]
)

logger = logging.getLogger('reference_agent')


def clean_text(text: str) -> str:
    """清理文本，移除多余的空白字符"""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_arxiv_id(reference: str) -> Optional[str]:
    """从参考文献中提取arXiv ID"""
    # 匹配arXiv ID的模式
    patterns = [
        r'arXiv:(\d+\.\d+)',  # arXiv:2101.12345
        r'arXiv\s+(\d+\.\d+)',  # arXiv 2101.12345
        r'https?://arxiv.org/abs/(\d+\.\d+)',  # https://arxiv.org/abs/2101.12345
    ]
    
    for pattern in patterns:
        match = re.search(pattern, reference, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def extract_doi(reference: str) -> Optional[str]:
    """从参考文献中提取DOI"""
    # 匹配DOI的模式
    patterns = [
        r'doi:\s*([\d\.]+/[^\s]+)',  # doi: 10.1234/abcd
        r'https?://doi.org/([\d\.]+/[^\s]+)',  # https://doi.org/10.1234/abcd
    ]
    
    for pattern in patterns:
        match = re.search(pattern, reference, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def generate_filename(title: str, authors: str, year: str) -> str:
    """根据论文信息生成文件名"""
    # 清理标题，只保留字母、数字和空格
    clean_title = re.sub(r'[^\w\s]', '', title)
    clean_title = re.sub(r'\s+', '_', clean_title)
    
    # 获取第一作者姓氏
    first_author = authors.split(',')[0].strip() if authors else 'Unknown'
    first_author_surname = first_author.split()[-1] if ' ' in first_author else first_author
    
    # 生成文件名：作者_年份_标题前30个字符
    filename = f"{first_author_surname}_{year}_{clean_title[:30]}"
    
    return filename


def get_file_path(filename: str, extension: str = 'pdf') -> str:
    """获取文件的完整路径"""
    # 确保文件名不包含非法字符
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 如果文件名太长，使用哈希值
    if len(safe_filename) > 100:
        hash_obj = hashlib.md5(safe_filename.encode())
        safe_filename = hash_obj.hexdigest()
    
    return os.path.join(DOWNLOAD_DIR, f"{safe_filename}.{extension}")


def normalize_citation(citation: str) -> str:
    """标准化引用格式，便于比较"""
    # 移除空白字符和标点符号
    normalized = re.sub(r'[\s.,;:\-\[\](){}]', '', citation.lower())
    return normalized


def find_citation_context(text: str, citation: str, window_size: int = 200) -> str:
    """查找引用上下文"""
    # 转义特殊字符
    escaped_citation = re.escape(citation)
    
    # 查找引用位置
    match = re.search(escaped_citation, text)
    if not match:
        return ""
    
    start_pos = max(0, match.start() - window_size)
    end_pos = min(len(text), match.end() + window_size)
    
    # 提取上下文
    context = text[start_pos:end_pos]
    
    # 尝试扩展到完整句子
    if start_pos > 0:
        # 向前找到句子开始
        sentence_start = text.rfind('.', 0, start_pos)
        if sentence_start != -1:
            context = text[sentence_start+1:end_pos]
    
    if end_pos < len(text):
        # 向后找到句子结束
        sentence_end = text.find('.', end_pos)
        if sentence_end != -1:
            context = text[start_pos:sentence_end+1]
    
    return clean_text(context)


def chunk_text(text: str, chunk_size: int = 4000) -> List[str]:
    """将长文本分割成小块，以适应API限制"""
    # 按段落分割
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # 如果当前段落加上当前块超过了块大小，保存当前块并开始新块
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n" + paragraph
            else:
                current_chunk = paragraph
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks