# arxiv_downloader.py
import os
import re
import time
import logging
from typing import List, Dict, Tuple, Optional, Any

import requests
import arxiv
from tqdm import tqdm

from config import ARXIV_QUERY_DELAY, MAX_RESULTS_PER_QUERY, DOWNLOAD_DIR
from utils import extract_arxiv_id, generate_filename, get_file_path, logger


class ArxivDownloader:
    """arXiv文献下载器，用于检索和下载arXiv论文"""
    
    def __init__(self):
        """初始化arXiv下载器"""
        self.client = arxiv.Client()
        self.download_dir = DOWNLOAD_DIR
        
        # 确保下载目录存在
        os.makedirs(self.download_dir, exist_ok=True)
    
    def search_paper(self, query: str, max_results: int = MAX_RESULTS_PER_QUERY) -> List[Dict[str, Any]]:
        """搜索arXiv论文
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            搜索结果列表
        """
        logger.info(f"搜索arXiv论文: {query}")
        
        try:
            # 构建搜索查询
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            # 执行搜索
            results = []
            for result in self.client.results(search):
                paper_info = {
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "summary": result.summary,
                    "published": result.published,
                    "updated": result.updated,
                    "arxiv_id": result.entry_id.split('/')[-1],
                    "pdf_url": result.pdf_url,
                    "primary_category": result.primary_category,
                    "categories": result.categories,
                    "links": [link.href for link in result.links]
                }
                results.append(paper_info)
            
            logger.info(f"找到 {len(results)} 篇论文")
            return results
            
        except Exception as e:
            logger.error(f"搜索arXiv论文失败: {str(e)}")
            return []
    
    def download_paper(self, arxiv_id: str, output_path: Optional[str] = None) -> Optional[str]:
        """下载arXiv论文
        
        Args:
            arxiv_id: arXiv ID
            output_path: 输出路径，如果为None则使用默认路径
            
        Returns:
            下载的PDF文件路径，如果下载失败则返回None
        """
        logger.info(f"下载arXiv论文: {arxiv_id}")
        
        try:
            # 构建搜索查询
            search = arxiv.Search(
                id_list=[arxiv_id],
                max_results=1
            )
            
            # 获取论文信息
            result = next(self.client.results(search), None)
            if not result:
                logger.warning(f"未找到arXiv ID为 {arxiv_id} 的论文")
                return None
            
            # 确定输出路径
            if not output_path:
                # 从论文信息生成文件名
                first_author = result.authors[0].name if result.authors else "Unknown"
                year = result.published.year if result.published else "Unknown"
                filename = generate_filename(result.title, first_author, str(year))
                output_path = get_file_path(filename)
            
            # 下载PDF
            result.download_pdf(dirpath=self.download_dir, filename=os.path.basename(output_path))
            
            logger.info(f"成功下载论文到: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"下载arXiv论文失败: {str(e)}")
            return None
    
    def download_paper_by_url(self, pdf_url: str, output_path: str) -> Optional[str]:
        """通过URL下载论文
        
        Args:
            pdf_url: PDF URL
            output_path: 输出路径
            
        Returns:
            下载的PDF文件路径，如果下载失败则返回None
        """
        logger.info(f"通过URL下载论文: {pdf_url}")
        
        try:
            # 发送请求
            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()
            
            # 获取文件大小
            file_size = int(response.headers.get('content-length', 0))
            
            # 下载文件
            with open(output_path, 'wb') as f, tqdm(
                desc=os.path.basename(output_path),
                total=file_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
            
            logger.info(f"成功下载论文到: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"通过URL下载论文失败: {str(e)}")
            return None
    
    def find_and_download_papers(self, references: List[str]) -> Dict[str, str]:
        """查找并下载参考文献中的论文
        
        Args:
            references: 参考文献列表
            
        Returns:
            下载结果字典，键为参考文献，值为下载的PDF文件路径
        """
        download_results = {}
        
        for i, reference in enumerate(references):
            logger.info(f"处理参考文献 {i+1}/{len(references)}: {reference[:50]}...")
            
            # 提取arXiv ID
            arxiv_id = extract_arxiv_id(reference)
            if arxiv_id:
                # 直接下载
                output_path = self.download_paper(arxiv_id)
                if output_path:
                    download_results[reference] = output_path
                    continue
            
            # 如果没有arXiv ID或下载失败，尝试搜索
            # 构建搜索查询
            # 移除引用编号和特殊字符
            clean_ref = re.sub(r'^\[?\d+\]?\.?\s+', '', reference)
            clean_ref = re.sub(r'[\[\]\(\)\{\}]', '', clean_ref)
            
            # 提取可能的标题和作者
            title_match = re.search(r'"([^"]+)"', clean_ref)
            if title_match:
                query = title_match.group(1)
            else:
                # 使用前30个单词作为查询
                words = clean_ref.split()[:30]
                query = ' '.join(words)
            
            # 搜索论文
            results = self.search_paper(query)
            
            if results:
                # 下载第一个结果
                paper_info = results[0]
                arxiv_id = paper_info["arxiv_id"]
                
                # 生成输出路径
                first_author = paper_info["authors"][0] if paper_info["authors"] else "Unknown"
                year = paper_info["published"].year if hasattr(paper_info["published"], "year") else "Unknown"
                filename = generate_filename(paper_info["title"], first_author, str(year))
                output_path = get_file_path(filename)
                
                # 下载论文
                downloaded_path = self.download_paper(arxiv_id, output_path)
                if downloaded_path:
                    download_results[reference] = downloaded_path
            
            # 避免过于频繁的请求
            time.sleep(ARXIV_QUERY_DELAY)
        
        logger.info(f"成功下载 {len(download_results)}/{len(references)} 篇论文")
        return download_results