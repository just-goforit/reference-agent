# test_simple.py
from utils import find_citation_context

text = "本文简要讨论了基于Transformer架构的自然语言处理模型的最新进展。我们重点关注BERT和GPT等预训练语言模型在各种NLP任务中的应用。研究表明，这些模型在文本分类、问答系统和机器翻译等任务上取得了显著的性能提升[1]。"
citation = "[1]"
result = find_citation_context(text, citation)
print(f'原始文本: {text}')
print(f'提取的引用句子: {result}')

# 测试更多案例
text2 = "引用可能出现在句子的开头[2]，中间或结尾。"
citation2 = "[2]"
result2 = find_citation_context(text2, citation2)
print(f'\n原始文本2: {text2}')
print(f'提取的引用句子2: {result2}')