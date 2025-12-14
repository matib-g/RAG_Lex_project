import pytest
from src.data_ingestion.preprocessor import DataPreprocessor

@pytest.fixture
def preprocessor():
    return DataPreprocessor()

def test_html_to_text(preprocessor):
    html = """
    <html>
        <head><title>Test</title></head>
        <body>
            <style>body { color: red; }</style>
            <h1>   Header   </h1>
            <p>Paragraph with   spaces.</p>
        </body>
    </html>
    """
    text = preprocessor.html_to_text(html)
    assert "Header" in text
    assert "Paragraph with spaces." in text
    assert "Test" not in text # Title removed
    assert "color: red" not in text # Style removed
    assert "   " not in text # Spaces normalized

def test_chunk_text(preprocessor):
    text = "0123456789" * 10 # 100 chars
    # Chunk size 20, overlap 5
    chunks = preprocessor.chunk_text(text, max_chars=20, overlap=5)
    
    assert len(chunks) > 0
    assert len(chunks[0]) <= 20
    
    # Check overlap
    # First chunk: 0...9012345678 (indices 0-20)
    # Second chunk start should be 20 - 5 = 15
    # text[15] is '5'
    assert chunks[1].startswith("56789")

def test_chunk_text_small(preprocessor):
    text = "Small text"
    chunks = preprocessor.chunk_text(text, max_chars=100)
    assert len(chunks) == 1
    assert chunks[0] == "Small text"
