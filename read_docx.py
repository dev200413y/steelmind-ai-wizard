import zipfile
import xml.etree.ElementTree as ET
import sys

def read_docx(path):
    try:
        with zipfile.ZipFile(path) as docx:
            xml_content = docx.read('word/document.xml')
        tree = ET.XML(xml_content)
        namespace = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        text = []
        for paragraph in tree.iterfind('.//w:p', namespace):
            texts = [node.text for node in paragraph.iterfind('.//w:t', namespace) if node.text]
            if texts:
                text.append(''.join(texts))
        return '\n'.join(text)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    content = read_docx(sys.argv[1])
    with open("docx_output.txt", "w", encoding="utf-8") as f:
        f.write(content)
