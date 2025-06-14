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


def find_citation_context(text: str, citation: str) -> List[str]:
    """查找引用上下文，返回包含引用的所有句子
    
    Args:
        text: 要搜索的文本
        citation: 引用标记
        
    Returns:
        包含引用的所有句子列表
    """
    # 转义特殊字符
    escaped_citation = re.escape(citation)
    
    # 初始化结果列表
    context_sentences = []
    
    # 将文本分割成句子
    # 使用正则表达式匹配句子，考虑中英文句号、问号和感叹号
    sentences = re.split(r'(?<=[.。!！?？])\s*', text)
    
    # 查找所有包含引用的完整句子
    for sentence in sentences:
        if citation in sentence:
            # 确保句子是完整的，包含标点符号
            clean_sentence = clean_text(sentence)
            if clean_sentence:
                # 如果句子不以标点结束，添加句号
                if clean_sentence[-1] not in '.。!！?？':
                    clean_sentence += '。'
                context_sentences.append(clean_sentence)
    
    # 如果通过句子分割没有找到任何引用上下文，使用回退方法
    if not context_sentences:
        # 查找所有引用位置
        for match in re.finditer(escaped_citation, text):
            # 向前找到句子开始（查找最近的句号、问号或感叹号）
            start_pos = max(
                text.rfind('.', 0, match.start()),
                text.rfind('。', 0, match.start()),
                text.rfind('!', 0, match.start()),
                text.rfind('！', 0, match.start()),
                text.rfind('?', 0, match.start()),
                text.rfind('？', 0, match.start())
            )
            
            if start_pos == -1:  # 如果找不到句子开始标点，从文本开始
                sentence_start = 0
            else:
                sentence_start = start_pos + 1  # 跳过句号
            
            # 向后找到句子结束（查找最近的句号、问号或感叹号）
            end_markers = ['.', '。', '!', '！', '?', '？']
            sentence_end = -1
            
            for marker in end_markers:
                pos = text.find(marker, match.end())
                if pos != -1 and (sentence_end == -1 or pos < sentence_end):
                    sentence_end = pos
            
            if sentence_end == -1:  # 如果找不到句子结束标点，到文本结束
                sentence_end = len(text)
            else:
                sentence_end += 1  # 包含句号
            
            # 提取包含引用的句子
            citation_sentence = text[sentence_start:sentence_end]
            clean_sentence = clean_text(citation_sentence)
            if clean_sentence:
                # 如果句子不以标点结束，添加句号
                if clean_sentence[-1] not in '.。!！?？':
                    clean_sentence += '。'
                context_sentences.append(clean_sentence)
    
    # 去重并返回结果
    return list(set(context_sentences)) if context_sentences else []


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