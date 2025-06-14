# reference_checker.py
import re
import logging
from typing import List, Dict, Set, Tuple, Optional

from document_parser import DocumentParser
from utils import normalize_citation, logger


class ReferenceChecker:
    """引文核查器，用于检查文档中的引用和参考文献的对应关系"""
    
    def __init__(self, document_parser: DocumentParser):
        """初始化引文核查器
        
        Args:
            document_parser: 文档解析器实例
        """
        self.parser = document_parser
        self.references = []
        self.citations = set()
        self.reference_map = {}  # 参考文献映射表
        self.citation_map = {}  # 引用映射表
        self.unused_references = []  # 未被引用的参考文献
        self.missing_references = []  # 引用但未在参考文献中的引用
        
        # 加载参考文献和引用
        self._load_data()
    
    def _load_data(self) -> None:
        """加载参考文献和引用数据"""
        # 获取参考文献
        self.references = self.parser.parse_references()
        
        # 获取引用
        self.citations = self.parser.extract_citations()
        
        logger.info(f"加载了 {len(self.references)} 条参考文献和 {len(self.citations)} 个引用")
    
    def _build_reference_map(self) -> Dict[str, int]:
        """构建参考文献映射表
        
        Returns:
            参考文献映射表，键为标准化的参考文献，值为参考文献索引
        """
        reference_map = {}
        
        for i, ref in enumerate(self.references):
            # 提取可能的引用标识符
            # 例如：[1] Author et al. -> 1
            # 或者：1. Author et al. -> 1
            ref_id_match = re.match(r'^\[?(\d+)\]?\.?\s+', ref)
            if ref_id_match:
                ref_id = ref_id_match.group(1)
                reference_map[ref_id] = i
            
            # 提取作者和年份
            # 例如：Smith et al., 2020
            author_year_match = re.search(r'([A-Za-z]+)\s+et\s+al\.?\s*,\s*(\d{4})', ref)
            if author_year_match:
                author = author_year_match.group(1)
                year = author_year_match.group(2)
                reference_map[f"{author.lower()}{year}"] = i
                reference_map[f"{author.lower()} et al {year}"] = i
                reference_map[f"{author.lower()} et al., {year}"] = i
            
            # 提取单个作者和年份
            # 例如：Smith, 2020
            single_author_match = re.search(r'([A-Za-z]+)\s*,\s*(\d{4})', ref)
            if single_author_match:
                author = single_author_match.group(1)
                year = single_author_match.group(2)
                reference_map[f"{author.lower()}{year}"] = i
                reference_map[f"{author.lower()}, {year}"] = i
            
            # 提取两个作者和年份
            # 例如：Smith and Jones, 2020
            two_authors_match = re.search(r'([A-Za-z]+)\s+and\s+([A-Za-z]+)\s*,\s*(\d{4})', ref)
            if two_authors_match:
                author1 = two_authors_match.group(1)
                author2 = two_authors_match.group(2)
                year = two_authors_match.group(3)
                reference_map[f"{author1.lower()}{author2.lower()}{year}"] = i
                reference_map[f"{author1.lower()} and {author2.lower()}, {year}"] = i
        
        self.reference_map = reference_map
        return reference_map
    
    def _build_citation_map(self) -> Dict[str, Set[str]]:
        """构建引用映射表
        
        Returns:
            引用映射表，键为标准化的引用，值为原始引用集合
        """
        citation_map = {}
        
        for citation in self.citations:
            normalized = normalize_citation(citation)
            if normalized not in citation_map:
                citation_map[normalized] = set()
            citation_map[normalized].add(citation)
        
        self.citation_map = citation_map
        return citation_map
    
    def check_references(self) -> Tuple[List[str], List[str]]:
        """检查参考文献和引用的对应关系
        
        Returns:
            未被引用的参考文献列表和引用但未在参考文献中的引用列表
        """
        # 构建映射表
        self._build_reference_map()
        self._build_citation_map()
        
        # 检查未被引用的参考文献
        referenced_indices = set()
        for citation in self.citations:
            normalized = normalize_citation(citation)
            
            # 检查是否在参考文献映射表中
            if normalized in self.reference_map:
                referenced_indices.add(self.reference_map[normalized])
            else:
                # 尝试其他可能的格式
                found = False
                for key, index in self.reference_map.items():
                    if normalized in key or key in normalized:
                        referenced_indices.add(index)
                        found = True
                        break
                
                if not found:
                    self.missing_references.append(citation)
        
        # 找出未被引用的参考文献
        for i, ref in enumerate(self.references):
            if i not in referenced_indices:
                self.unused_references.append(ref)
        
        logger.info(f"发现 {len(self.unused_references)} 条未被引用的参考文献")
        logger.info(f"发现 {len(self.missing_references)} 个引用但未在参考文献中的引用")
        
        return self.unused_references, self.missing_references
    
    def get_citation_statistics(self) -> Dict[str, int]:
        """获取引用统计信息
        
        Returns:
            引用统计信息，键为参考文献，值为被引用次数
        """
        citation_counts = {ref: 0 for ref in self.references}
        
        # 构建映射表（如果尚未构建）
        if not self.reference_map:
            self._build_reference_map()
        
        if not self.citation_map:
            self._build_citation_map()
        
        # 统计每个参考文献被引用的次数
        for citation in self.citations:
            normalized = normalize_citation(citation)
            
            # 检查是否在参考文献映射表中
            if normalized in self.reference_map:
                index = self.reference_map[normalized]
                if index < len(self.references):
                    citation_counts[self.references[index]] += 1
            else:
                # 尝试其他可能的格式
                for key, index in self.reference_map.items():
                    if normalized in key or key in normalized:
                        if index < len(self.references):
                            citation_counts[self.references[index]] += 1
                        break
        
        return citation_counts
    
    
    def generate_report(self) -> Dict[str, any]:
        """生成引文核查报告
        
        Returns:
            包含核查结果的字典
        """
        # 确保已经进行了核查
        if not self.unused_references and not self.missing_references:
            self.check_references()
        
        # 获取引用统计信息
        citation_stats = self.get_citation_statistics()
        
        # 生成报告
        report = {
            "total_references": len(self.references),
            "total_citations": len(self.citations),
            "unused_references": self.unused_references,
            "missing_references": self.missing_references,
            "citation_statistics": citation_stats,
            "document_metadata": self.parser.get_document_metadata()
        }
        
        return report