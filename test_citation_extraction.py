# test_citation_extraction.py
import re
from utils import find_citation_context
from document_parser import DocumentParser

def test_find_citation_context():
    # 测试文本
    text = "本文简要讨论了基于Transformer架构的自然语言处理模型的最新进展。我们重点关注BERT和GPT等预训练语言模型在各种NLP任务中的应用。研究表明，这些模型在文本分类、问答系统和机器翻译等任务上取得了显著的性能提升[1]。"

    # 测试引用
    citation = "[1]"

    # 测试修改后的函数
    result = find_citation_context(text, citation)
    print(f"原始文本: {text}")
    print(f"提取的引用句子: {result}")

    # 测试更复杂的情况
    text2 = "第一句话。第二句话包含引用[2]。第三句话也有内容。"
    citation2 = "[2]"
    result2 = find_citation_context(text2, citation2)
    print(f"\n原始文本2: {text2}")
    print(f"提取的引用句子2: {result2}")

    # 测试句子中间的引用
    text3 = "这是一个长句子，中间包含了[3]引用标记，然后继续。"
    citation3 = "[3]"
    result3 = find_citation_context(text3, citation3)
    print(f"\n原始文本3: {text3}")
    print(f"提取的引用句子3: {result3}")

    # 测试文本开头的引用
    text4 = "[4]这是一个以引用开头的句子。"
    citation4 = "[4]"
    result4 = find_citation_context(text4, citation4)
    print(f"\n原始文本4: {text4}")
    print(f"提取的引用句子4: {result4}")

    # 测试文本结尾的引用
    text5 = "这是一个以引用结尾的句子[5]"
    citation5 = "[5]"
    result5 = find_citation_context(text5, citation5)
    print(f"\n原始文本5: {text5}")
    print(f"提取的引用句子5: {result5}")

def test_document_parser_get_citation_contexts():
    # 创建一个简单的测试文本
    test_text = """这是第一段，不包含引用。
    
    这是第二段，包含一个引用[1]。这是第二段的第二句话。
    
    这是第三段，包含另一个引用[2]，位于句子中间。
    
    [3]这是第四段，引用在句子开头。
    
    这是最后一段，引用在句子结尾[4]"""
    
    # 由于我们不能直接创建DocumentParser实例（需要文件），
    # 我们将模拟其行为
    class MockDocumentParser(DocumentParser):
        def __init__(self, text):
            self.text_content = text
            self.citations = set(["[1]", "[2]", "[3]", "[4]"])
    
    # 创建模拟解析器
    parser = MockDocumentParser(test_text)
    
    # 测试获取引用上下文
    for citation in ["[1]", "[2]", "[3]", "[4]"]:
        contexts = parser.get_citation_contexts(citation)
        print(f"\n引用 {citation} 的上下文:")
        for i, context in enumerate(contexts):
            print(f"  {i+1}. {context}")

if __name__ == "__main__":
    print("测试 find_citation_context 函数:")
    print("-" * 50)
    test_find_citation_context()
    
    print("\n\n测试 DocumentParser.get_citation_contexts 方法:")
    print("-" * 50)
    try:
        test_document_parser_get_citation_contexts()
    except Exception as e:
        print(f"测试 DocumentParser.get_citation_contexts 失败: {e}")