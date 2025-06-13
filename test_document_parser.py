# test_document_parser.py
from document_parser import DocumentParser
import os

# 查找一个docx文件进行测试
docx_files = [f for f in os.listdir('.') if f.endswith('.docx')]
if docx_files:
    test_file = docx_files[0]
    print(f'测试文件: {test_file}')
    
    try:
        parser = DocumentParser(test_file)
        citations = parser.extract_citations()
        print(f'提取到的引用: {citations}')
        
        if citations:
            # 测试第一个引用
            first_citation = list(citations)[0]
            contexts = parser.get_citation_contexts(first_citation)
            print(f'\n引用 {first_citation} 的上下文:')
            for i, context in enumerate(contexts):
                print(f'  {i+1}. {context}')
    except Exception as e:
        print(f'测试失败: {e}')
else:
    print('未找到docx文件进行测试')