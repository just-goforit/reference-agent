# config.py
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# arXiv API配置
ARXIV_QUERY_DELAY = 3  # 查询间隔时间（秒）
MAX_RESULTS_PER_QUERY = 5  # 每次查询最大结果数

# 文件路径配置
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")  # PDF下载目录
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")  # 输出报告目录

# 创建必要的目录
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 引文核查配置
CITATION_PATTERNS = [
    r"\[\d+\]",  # [1], [2], etc.
    r"\(([A-Za-z]+\s*et\s*al\.?\s*,\s*\d{4}[a-z]?)\)",  # (Smith et al., 2020)
    r"([A-Za-z]+\s*et\s*al\.?\s*,\s*\d{4}[a-z]?)",  # Smith et al., 2020
    r"\(([A-Za-z]+\s*and\s*[A-Za-z]+\s*,\s*\d{4}[a-z]?)\)",  # (Smith and Jones, 2020)
    r"([A-Za-z]+\s*and\s*[A-Za-z]+\s*,\s*\d{4}[a-z]?)",  # Smith and Jones, 2020
    r"\(([A-Za-z]+\s*,\s*\d{4}[a-z]?)\)",  # (Smith, 2020)
    r"([A-Za-z]+\s*,\s*\d{4}[a-z]?)",  # Smith, 2020
]

# 内容核查配置
CONTENT_VERIFICATION_PROMPT = """
你是一个学术引用核查助手。请分析以下内容：

1. 原文引用：
{citation_text}

2. 参考文献内容：
{reference_text}

请判断原文引用是否准确反映了参考文献的内容。分析以下几点：
1. 引用的事实是否存在于参考文献中
2. 引用是否曲解或夸大了参考文献的结论
3. 引用的数据或统计信息是否与参考文献一致

请给出你的判断（准确/不准确/部分准确）并详细解释理由。
"""

NEW_CONTENT_VERIFICATION_PROMPT = """
你是一个学术引用核查助手。请严格按以下步骤和格式要求分析内容：

1. 基础信息：
   原文引用："{citation_text}"
   参考文献内容："{reference_text}"
   原文完整内容："{text_content}"

2. 上下文分析：
   - 判断是否需要更多上下文（是/否）
   - 若需要更多上下文：
     • 从原文完整内容中提取与引用相关的上下文段落
     • 上下文应包括：引用位置前后各1-2个完整句子

3. 核查分析：
   [判断结果]
   准确/不准确/部分准确  # 必须选择一项

   [上下文分析]
   <是否需要上下文的判断及理由>
   <提取的上下文段落（如需要）>

   [核查报告]
   1. 事实一致性：...
   2. 结论准确性：...
   3. 数据可靠性：...
   4. 语境完整性：...

   [最终结论]
   <综合判断的详细解释>
"""

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")