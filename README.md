# Reference Agent

Reference Agent 是一个用于学术论文引用核查与文献下载的智能工具。它能够自动分析 Word 文档中的参考文献引用情况，自动从 arXiv 检索并下载文献，并结合大模型自动核查引文与文献内容的对应关系。

## 主要功能

1. **引文核查**：自动统计文档中参考文献的引用情况，检测未被引用的文献。

2. **文献下载**：根据文档参考文献列表，自动从 arXiv 检索并下载对应的 PDF 文献。

3. **引文内容核查**：利用大模型自动比对文档中的引文内容与实际文献内容，判断引用是否准确。

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python main.py --input your_paper.docx --all
```

## 项目结构

- `main.py`: 主程序入口
- `document_parser.py`: Word文档解析模块
- `reference_checker.py`: 引文核查模块
- `arxiv_downloader.py`: arXiv文献下载模块
- `content_verifier.py`: 引文内容核查模块
- `utils.py`: 工具函数
- `config.py`: 配置文件

## 依赖

本项目使用DeepSeek V3 API进行内容分析。
