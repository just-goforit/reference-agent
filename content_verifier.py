# content_verifier.py
import os
import re
import logging
from typing import List, Dict, Tuple, Optional, Any

import PyPDF2
import pdfplumber
import openai

from config import DEEPSEEK_API_KEY, DEEPSEEK_API_BASE, DEEPSEEK_MODEL, CONTENT_VERIFICATION_PROMPT, NEW_CONTENT_VERIFICATION_PROMPT
from utils import chunk_text, find_citation_context, logger


class ContentVerifier:
    """引文内容核查器，用于比对引文内容与实际文献内容"""
    
    def __init__(self):
        """初始化内容核查器"""
        # 配置OpenAI客户端（用于DeepSeek API）
        self.client = openai.OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_API_BASE if DEEPSEEK_API_BASE else None
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF中提取文本
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取的文本内容
        """
        logger.info(f"从PDF提取文本: {pdf_path}")
        
        try:
            # 首先尝试使用PyPDF2
            text = self._extract_with_pypdf2(pdf_path)
            
            # 如果提取的文本太少，尝试使用pdfplumber
            if len(text.strip().split()) < 100:
                logger.info("PyPDF2提取的文本太少，尝试使用pdfplumber")
                text = self._extract_with_pdfplumber(pdf_path)
            
            logger.info(f"成功提取文本，长度: {len(text)} 字符")
            return text
            
        except Exception as e:
            logger.error(f"从PDF提取文本失败: {str(e)}")
            return ""
    
    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """使用PyPDF2提取文本"""
        text = ""
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            
            for i in range(num_pages):
                page = reader.pages[i]
                text += page.extract_text() + "\n"
        
        return text
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """使用pdfplumber提取文本"""
        text = ""
        
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            
            for i in range(num_pages):
                page = pdf.pages[i]
                text += page.extract_text() + "\n"
        
        return text
    
    def verify_citation(self, citation_text: str, reference_text: str, content_without_references: str) -> Dict[str, Any]:
        """验证引用内容是否准确
        
        Args:
            citation_text: 引用上下文
            reference_text: 参考文献内容
            
        Returns:
            验证结果字典
        """
        logger.info(f"验证引用内容: {citation_text[:50]}...")
        logger.info(f"参考文献内容: {reference_text[:50]}...")
        
        try:
            prompt = NEW_CONTENT_VERIFICATION_PROMPT.format(
                citation_text=citation_text,
                reference_text=reference_text[:10000],
                text_content=content_without_references
            )
            
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "请严格按照要求的格式输出完整分析"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=8 * (2 ** 10)
            )
            
            analysis = response.choices[0].message.content
            logger.info(f"原始分析内容:\n{analysis}")  # 添加详细日志
            # 验证响应格式
            required_sections = ["[判断结果]", "[上下文分析]", "[核查报告]"]
            if not all(section in analysis for section in required_sections):
                logger.warning("响应格式不完整，尝试补充标记")
                analysis = f"{analysis}\n\n[注意]以上内容缺少必要分析部分"
            # 精确提取判断结果
            result = "未知"
            judgment_match = re.search(r'\[判断结果\]\s*([^\n]+)', analysis)
            if judgment_match:
                result_line = judgment_match.group(1).strip()
                if re.search(r'不准确', result_line):
                    result = "不准确"
                elif re.search(r'部分准确', result_line):
                    result = "部分准确"
                elif re.search(r'准确', result_line):
                    result = "准确"
            
            # 回退机制
            if result == "未知":
                if re.search(r'不准确', analysis, re.IGNORECASE):
                    result = "不准确"
                elif re.search(r'部分准确', analysis, re.IGNORECASE):
                    result = "部分准确"
                elif re.search(r'准确', analysis, re.IGNORECASE):
                    result = "准确"
            verification_result = {
                "result": result,
                "analysis": analysis,
                "citation_text": citation_text,
                "reference_text_sample": reference_text[:500] + "..."
            }
            
            logger.info(f"验证结果: {result}")
            return verification_result

        except Exception as e:
            logger.error(f"验证引用内容失败: {str(e)}")
            return {
                "result": "错误",
                "analysis": f"验证过程中发生错误: {str(e)}",
                "citation_text": citation_text,
                "reference_text_sample": reference_text[:500] + "..."
            }
    
    def verify_document_citations(self, citations: List[str], pdf_path: str, content_without_references: str) -> List[Dict[str, Any]]:
        """
        验证文档中的所有引用
        
        Args:
            citations: 引用列表
            pdf_path: 参考文献PDF路径
            
        Returns:
            验证结果列表
        """
        logger.info(f"验证文档引用，共 {len(citations)} 个引用")
        logger.info(f"引用内容: {citations}")
        
        # 提取PDF文本
        reference_text = self.extract_text_from_pdf(pdf_path)
        if not reference_text:
            logger.warning(f"无法从PDF提取文本: {pdf_path}")
            return [{
                "result": "错误",
                "analysis": "无法从PDF提取文本",
                "citation_text": citation,
                "reference_text_sample": ""
            } for citation in citations]
        
        # 验证每个引用
        verification_results = []
        for citation in citations:
            # 获取引用的所有上下文句子
            contexts = citation
            
            # 如果上下文是列表，则遍历每个上下文句子进行验证
            if isinstance(contexts, list):
                for context in contexts:
                    # 验证引用
                    result = self.verify_citation(context, reference_text, content_without_references)
                    verification_results.append(result)
            else:
                # 兼容旧版本，直接使用引用内容作为上下文
                result = self.verify_citation(contexts, reference_text, content_without_references)
                verification_results.append(result)
        
        return verification_results
    
    def batch_verify_citations(self, citation_map: Dict[str, List[str]], pdf_map: Dict[str, str], content_without_references: str) -> Dict[str, List[Dict[str, Any]]]:
        """批量验证引用
        
        Args:
            citation_map: 引用映射，键为参考文献，值为引用上下文列表
            pdf_map: PDF映射，键为参考文献，值为PDF路径
            
        Returns:
            验证结果映射，键为参考文献，值为验证结果列表
        """
        verification_results = {}
        
        for reference, contexts in citation_map.items():
            logger.info(f"处理参考文献: {reference[:50]}...")
            
            # 检查是否有对应的PDF
            if reference not in pdf_map:
                logger.warning(f"未找到参考文献的PDF: {reference[:50]}...")
                verification_results[reference] = [{
                    "result": "错误",
                    "analysis": "未找到参考文献的PDF",
                    "citation_text": context,
                    "reference_text_sample": ""
                } for context in contexts]
                continue
            
            # 验证引用
            pdf_path = pdf_map[reference]
            results = self.verify_document_citations(contexts, pdf_path, content_without_references)
            verification_results[reference] = results
        
        return verification_results
    
    def generate_verification_report(self, verification_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """生成验证报告
        
        Args:
            verification_results: 验证结果映射
            
        Returns:
            验证报告
        """
        report = {
            "total_references": len(verification_results),
            "total_citations": sum(len(results) for results in verification_results.values()),
            "accurate_citations": 0,
            "inaccurate_citations": 0,
            "partially_accurate_citations": 0,
            "error_citations": 0,
            "reference_summary": {},
            "detailed_results": verification_results
        }
        
        # 统计结果
        for reference, results in verification_results.items():
            reference_summary = {
                "total": len(results),
                "accurate": 0,
                "inaccurate": 0,
                "partially_accurate": 0,
                "error": 0
            }
            
            for result in results:
                if result["result"] == "准确":
                    report["accurate_citations"] += 1
                    reference_summary["accurate"] += 1
                elif result["result"] == "不准确":
                    report["inaccurate_citations"] += 1
                    reference_summary["inaccurate"] += 1
                elif result["result"] == "部分准确":
                    report["partially_accurate_citations"] += 1
                    reference_summary["partially_accurate"] += 1
                else:
                    report["error_citations"] += 1
                    reference_summary["error"] += 1
            
            # 添加到报告
            report["reference_summary"][reference] = reference_summary
        
        return report