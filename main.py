# main.py
import os
import sys
import json
import argparse
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from document_parser import DocumentParser
from reference_checker import ReferenceChecker
from arxiv_downloader import ArxivDownloader
from content_verifier import ContentVerifier
from config import OUTPUT_DIR
from utils import logger


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Reference Agent - 学术论文引用核查与文献下载工具")
    
    parser.add_argument(
        "--input", "-i", 
        type=str, 
        required=True,
        help="输入Word文档路径"
    )
    
    parser.add_argument(
        "--output", "-o", 
        type=str, 
        default=None,
        help="输出报告路径，默认为output目录下的时间戳命名文件"
    )
    
    parser.add_argument(
        "--download", "-d", 
        action="store_true", 
        help="是否下载参考文献"
    )
    
    parser.add_argument(
        "--verify", "-v", 
        action="store_true", 
        help="是否验证引用内容"
    )
    
    parser.add_argument(
        "--all", "-a", 
        action="store_true", 
        help="执行所有功能（引文核查、文献下载、内容验证）"
    )
    
    return parser.parse_args()


def check_references(input_file: str) -> Dict[str, Any]:
    """检查文档中的引用和参考文献
    
    Args:
        input_file: 输入文档路径
        
    Returns:
        引文核查报告
    """
    logger.info(f"开始引文核查: {input_file}")
    
    # 解析文档
    parser = DocumentParser(input_file)
    
    # 检查引用
    checker = ReferenceChecker(parser)
    checker.check_references()
    
    # 生成报告
    report = checker.generate_report()
    
    logger.info(f"引文核查完成，共 {report['total_references']} 条参考文献，{report['total_citations']} 个引用")
    return report


def download_references(references: List[str]) -> Dict[str, str]:
    """下载参考文献
    
    Args:
        references: 参考文献列表
        
    Returns:
        下载结果字典，键为参考文献，值为下载的PDF文件路径
    """
    logger.info(f"开始下载参考文献，共 {len(references)} 条")
    
    # 下载参考文献
    downloader = ArxivDownloader()
    download_results = downloader.find_and_download_papers(references)
    
    logger.info(f"参考文献下载完成，成功下载 {len(download_results)}/{len(references)} 篇")
    return download_results


def verify_citations(parser: DocumentParser, reference_checker: ReferenceChecker, pdf_map: Dict[str, str]) -> Dict[str, Any]:
    """验证引用内容
    
    Args:
        parser: 文档解析器
        reference_checker: 引文核查器
        pdf_map: PDF映射，键为参考文献，值为PDF路径
        
    Returns:
        验证报告
    """
    logger.info("开始验证引用内容")
    
    # 构建引用上下文映射
    citation_map = {}
    for i, reference in enumerate(reference_checker.references):
        if reference in pdf_map:
            contexts = reference_checker.get_reference_contexts(i)
            if contexts:
                citation_map[reference] = contexts
    
    # 验证引用内容
    verifier = ContentVerifier()
    verification_results = verifier.batch_verify_citations(citation_map, pdf_map)
    
    # 生成验证报告
    report = verifier.generate_verification_report(verification_results)
    
    logger.info(f"引用内容验证完成，共验证 {report['total_citations']} 个引用")
    return report


def save_report(report_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """保存报告
    
    Args:
        report_data: 报告数据
        output_path: 输出路径
        
    Returns:
        报告保存路径
    """
    
    # 确定输出路径
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(OUTPUT_DIR, f"reference_report_{timestamp}.json")
    
    # 保存报告
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"报告已保存到: {output_path}")
    
    # 生成HTML报告
    html_path = output_path.replace(".json", ".html")
    generate_html_report(report_data, html_path)
    
    return output_path


def generate_html_report(report_data: Dict[str, Any], output_path: str) -> None:
    """生成HTML报告
    
    Args:
        report_data: 报告数据
        output_path: 输出路径
    """
    # HTML模板
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reference Agent 报告</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1, h2, h3 {
                color: #2c3e50;
            }
            .card {
                background: #fff;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                padding: 20px;
                margin-bottom: 20px;
            }
            .stat {
                display: inline-block;
                background: #f8f9fa;
                border-radius: 4px;
                padding: 10px 15px;
                margin-right: 10px;
                margin-bottom: 10px;
            }
            .stat strong {
                display: block;
                font-size: 20px;
                color: #3498db;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            th, td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #e1e1e1;
            }
            th {
                background-color: #f8f9fa;
            }
            .accurate {
                color: #27ae60;
            }
            .inaccurate {
                color: #e74c3c;
            }
            .partial {
                color: #f39c12;
            }
            .error {
                color: #7f8c8d;
            }
            .reference-item {
                margin-bottom: 10px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
            .citation-context {
                margin: 10px 0;
                padding: 10px;
                background-color: #ecf0f1;
                border-left: 4px solid #3498db;
                border-radius: 0 4px 4px 0;
            }
            .analysis {
                margin: 10px 0;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Reference Agent 报告</h1>
            <p>生成时间: {{timestamp}}</p>
            
            <div class="card">
                <h2>引文核查摘要</h2>
                <div class="stat">
                    <strong>{{total_references}}</strong>
                    参考文献总数
                </div>
                <div class="stat">
                    <strong>{{total_citations}}</strong>
                    引用总数
                </div>
                <div class="stat">
                    <strong>{{unused_references}}</strong>
                    未被引用的参考文献
                </div>
                <div class="stat">
                    <strong>{{missing_references}}</strong>
                    引用但未在参考文献中的引用
                </div>
            </div>
            
            {{#has_download_results}}
            <div class="card">
                <h2>文献下载摘要</h2>
                <div class="stat">
                    <strong>{{downloaded_count}}</strong>
                    成功下载的文献数
                </div>
                <div class="stat">
                    <strong>{{download_percentage}}%</strong>
                    下载成功率
                </div>
            </div>
            {{/has_download_results}}
            
            {{#has_verification_results}}
            <div class="card">
                <h2>引用内容核查摘要</h2>
                <div class="stat">
                    <strong>{{verified_citations}}</strong>
                    已验证的引用总数
                </div>
                <div class="stat">
                    <strong class="accurate">{{accurate_citations}}</strong>
                    准确的引用
                </div>
                <div class="stat">
                    <strong class="partial">{{partially_accurate_citations}}</strong>
                    部分准确的引用
                </div>
                <div class="stat">
                    <strong class="inaccurate">{{inaccurate_citations}}</strong>
                    不准确的引用
                </div>
                <div class="stat">
                    <strong class="error">{{error_citations}}</strong>
                    验证出错的引用
                </div>
            </div>
            {{/has_verification_results}}
            
            <div class="card">
                <h2>未被引用的参考文献</h2>
                {{#unused_reference_list}}
                <div class="reference-item">{{.}}</div>
                {{/unused_reference_list}}
                {{^unused_reference_list}}
                <p>没有未被引用的参考文献。</p>
                {{/unused_reference_list}}
            </div>
            
            <div class="card">
                <h2>引用但未在参考文献中的引用</h2>
                {{#missing_reference_list}}
                <div class="reference-item">{{.}}</div>
                {{/missing_reference_list}}
                {{^missing_reference_list}}
                <p>没有引用但未在参考文献中的引用。</p>
                {{/missing_reference_list}}
            </div>
            
            {{#has_verification_results}}
            <div class="card">
                <h2>引用内容核查详情</h2>
                {{#verification_details}}
                <h3>参考文献</h3>
                <div class="reference-item">{{reference}}</div>
                
                {{#citations}}
                <div class="citation-context">
                    <strong class="{{result_class}}">{{result}}</strong>
                    <p>{{citation_text}}</p>
                    <div class="analysis">
                        <strong>分析:</strong>
                        <p>{{analysis}}</p>
                    </div>
                </div>
                {{/citations}}
                {{/verification_details}}
            </div>
            {{/has_verification_results}}
        </div>
    </body>
    </html>
    """
    
    # 准备模板数据
    template_data = {
        "timestamp": report_data["timestamp"],
        "total_references": report_data["reference_check"]["total_references"],
        "total_citations": report_data["reference_check"]["total_citations"],
        "unused_references": len(report_data["reference_check"]["unused_references"]),
        "missing_references": len(report_data["reference_check"]["missing_references"]),
        "unused_reference_list": report_data["reference_check"]["unused_references"],
        "missing_reference_list": report_data["reference_check"]["missing_references"],
        "has_download_results": "download_results" in report_data,
        "has_verification_results": "verification_report" in report_data
    }
    
    # 添加下载结果
    if "download_results" in report_data:
        template_data["downloaded_count"] = report_data["download_results"]["downloaded_references"]
        # 避免除以零错误
        total_refs = report_data["download_results"]["total_references"]
        if total_refs > 0:
            template_data["download_percentage"] = round(
                report_data["download_results"]["downloaded_references"] / total_refs * 100
            )
        else:
            template_data["download_percentage"] = 0
    
    # 添加验证结果
    if "verification_report" in report_data:
        verification_report = report_data["verification_report"]
        template_data["verified_citations"] = verification_report["total_citations"]
        template_data["accurate_citations"] = verification_report["accurate_citations"]
        template_data["partially_accurate_citations"] = verification_report["partially_accurate_citations"]
        template_data["inaccurate_citations"] = verification_report["inaccurate_citations"]
        template_data["error_citations"] = verification_report["error_citations"]
        
        # 添加详细验证结果
        verification_details = []
        for reference, results in verification_report["detailed_results"].items():
            citations = []
            for result in results:
                result_class = "accurate" if result["result"] == "准确" else \
                              "inaccurate" if result["result"] == "不准确" else \
                              "partial" if result["result"] == "部分准确" else "error"
                
                citations.append({
                    "result": result["result"],
                    "result_class": result_class,
                    "citation_text": result["citation_text"],
                    "analysis": result["analysis"]
                })
            
            verification_details.append({
                "reference": reference,
                "citations": citations
            })
        
        template_data["verification_details"] = verification_details
    
    # 简单的模板渲染
    html_content = html_template
    
    # 替换变量
    for key, value in template_data.items():
        if isinstance(value, (int, float)):
            html_content = html_content.replace("{{" + key + "}}", str(value))
        elif isinstance(value, bool):
            if value:
                html_content = html_content.replace("{{#" + key + "}}", "")
                html_content = html_content.replace("{{/" + key + "}}", "")
            else:
                # 移除条件块
                start_tag = "{{#" + key + "}}"
                end_tag = "{{/" + key + "}}"
                start_pos = html_content.find(start_tag)
                end_pos = html_content.find(end_tag) + len(end_tag)
                if start_pos != -1 and end_pos != -1:
                    html_content = html_content[:start_pos] + html_content[end_pos:]
        elif isinstance(value, str):
            html_content = html_content.replace("{{" + key + "}}", value)
    
    # 处理列表
    for key in ["unused_reference_list", "missing_reference_list"]:
        if key in template_data and template_data[key]:
            list_items = ""
            for item in template_data[key]:
                list_items += f'<div class="reference-item">{item}</div>\n'
            
            html_content = html_content.replace("{{#" + key + "}}", "")
            html_content = html_content.replace("{{/" + key + "}}", "")
            html_content = html_content.replace("{{.}}", "").replace(f'<div class="reference-item"></div>\n', list_items)
        else:
            # 移除条件块
            start_tag = "{{#" + key + "}}"
            end_tag = "{{/" + key + "}}"
            start_pos = html_content.find(start_tag)
            end_pos = html_content.find(end_tag) + len(end_tag)
            if start_pos != -1 and end_pos != -1:
                html_content = html_content[:start_pos] + html_content[end_pos:]
            
            # 显示空列表消息
            start_tag = "{{^" + key + "}}"
            end_tag = "{{/" + key + "}}"
            html_content = html_content.replace(start_tag, "")
            html_content = html_content.replace(end_tag, "")
    
    # 处理验证详情
    if "verification_details" in template_data:
        details_html = ""
        for detail in template_data["verification_details"]:
            detail_html = f'<h3>参考文献</h3>\n<div class="reference-item">{detail["reference"]}</div>\n'
            
            for citation in detail["citations"]:
                detail_html += f'''
                <div class="citation-context">
                    <strong class="{citation["result_class"]}">{citation["result"]}</strong>
                    <p>{citation["citation_text"]}</p>
                    <div class="analysis">
                        <strong>分析:</strong>
                        <p>{citation["analysis"]}</p>
                    </div>
                </div>
                '''
            
            details_html += detail_html
        
        html_content = html_content.replace("{{#verification_details}}", "")
        html_content = html_content.replace("{{/verification_details}}", "")
        html_content = html_content.replace('<h3>参考文献</h3>\n<div class="reference-item">{{reference}}</div>', "")
        html_content = html_content.replace('{{#citations}}\n                <div class="citation-context">\n                    <strong class="{{result_class}}">{{result}}</strong>\n                    <p>{{citation_text}}</p>\n                    <div class="analysis">\n                        <strong>分析:</strong>\n                        <p>{{analysis}}</p>\n                    </div>\n                </div>\n                {{/citations}}', details_html)
    
    # 保存HTML报告
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"HTML报告已保存到: {output_path}")


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 检查输入文件
    if not os.path.exists(args.input):
        logger.error(f"输入文件不存在: {args.input}")
        sys.exit(1)
    
    # 确定是否执行所有功能
    do_download = args.download or args.all
    do_verify = args.verify or args.all
    
    try:
        # 引文核查
        reference_report = check_references(args.input)
        
        # 文献下载
        download_results = None
        if do_download:
            # 从ReferenceChecker中获取参考文献列表
            references = reference_report.get("references", [])
            # 如果references键不存在，则尝试从document_parser中重新获取
            if not references:
                parser = DocumentParser(args.input)
                references = parser.parse_references()
            download_results = download_references(references)
        
        # 引文内容核查
        verification_report = None
        if do_verify and download_results:
            # 创建解析器和核查器
            parser = DocumentParser(args.input)
            checker = ReferenceChecker(parser)
            
            # 验证引用内容
            verification_report = verify_citations(parser, checker, download_results)
        
        # 保存报告
        # 构建报告数据结构
        report_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "reference_check": reference_report
        }
        
        # 添加下载结果
        if download_results:
            # 确保total_references至少为1，避免除以零错误
            total_refs = max(1, reference_report.get("total_references", 0))
            report_data["download_results"] = {
                "total_references": total_refs,
                "downloaded_references": len(download_results),
                "results": download_results
            }
        
        # 添加验证结果
        if verification_report:
            report_data["verification_report"] = verification_report
        
        save_report(report_data, args.output)
        
        logger.info("Reference Agent 任务完成")
        
    except Exception as e:
        logger.error(f"执行过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()