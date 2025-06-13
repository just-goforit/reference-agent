import re
from typing import Optional
from utils import extract_arxiv_id

# 测试用例
test_cases = [
    # 正常情况
    "arXiv:1810.04805",
    "arXiv 1810.04805",
    "https://arxiv.org/abs/1810.04805",
    # 带句点的情况
    "arXiv:1810.04805.",
    "arXiv 1810.04805.",
    "https://arxiv.org/abs/1810.04805.",
    # 完整引用格式
    "Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2018). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. arXiv:1810.04805.",
    "Strubell, E., Ganesh, A., & McCallum, A. (2019). Energy and Policy Considerations for Deep Learning in NLP. arXiv:1906.02243."
]

# 将结果写入文件
with open('extract_arxiv_id_test_results.txt', 'w', encoding='utf-8') as f:
    f.write("测试 extract_arxiv_id 函数：\n")
    f.write("-" * 50 + "\n")
    
    for i, test_case in enumerate(test_cases, 1):
        arxiv_id = extract_arxiv_id(test_case)
        f.write(f"测试 {i}:\n")
        f.write(f"输入: {test_case}\n")
        f.write(f"提取的 arXiv ID: {arxiv_id}\n")
        f.write("-" * 50 + "\n")