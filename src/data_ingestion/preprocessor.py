import os
import re
import json
from pathlib import Path
from typing import List, Dict, Union
from bs4 import BeautifulSoup
from src.utils.config import RAW_DATA_DIR, PREPARED_DATA_FILE
from src.utils.logger import setup_logger

logger = setup_logger("preprocessor")

class DataPreprocessor:
    """
    Class responsible for cleaning HTML legal acts and chunking them.
    """
    def __init__(self, input_dir: Union[str, Path] = RAW_DATA_DIR, output_file: Union[str, Path] = PREPARED_DATA_FILE):
        self.input_dir = Path(input_dir)
        self.output_file = Path(output_file)

    def html_to_text(self, html_content: str) -> str:
        """
        Parses HTML into plain text, removes unnecessary spaces and new lines.
        """
        soup = BeautifulSoup(html_content, "html.parser")

        for tag in soup(["style", "script", "head", "title", "meta"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        # Fix invalid escape sequence in re
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

    def chunk_text(self, text: str, max_chars: int = 1000, overlap: int = 100) -> List[str]:
        """
        Splits the text into blocks with a maximum length of `max_chars`, with overlap.
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        if text_len <= max_chars:
            return [text]

        while start < text_len:
            end = start + max_chars
            # Ensure we don't go out of bounds (python slicing handles this but being explicit is fine)
            chunk = text[start:end]
            chunks.append(chunk.strip())
            
            start = end - overlap
            if start >= text_len:
                break
                
        return chunks

    def process_files(self, max_chars: int = 1000, specific_files: List[str] = None) -> List[Dict]:
        """
        Converts HTML files (from directory or specific list) into a list of chunks with metadata.
        If specific_files is None, checks all *.html in input_dir and overwrites output_file.
        If specific_files is provided, processes only those files and DOES NOT overwrite main output_file (returns data).
        """
        dataset = []
        
        target_files = []
        if specific_files:
            # Assume specific_files contains filenames (not full paths)
            for fname in specific_files:
                target_files.append(self.input_dir / fname)
            logger.info(f"Processing {len(target_files)} specific files.")
        else:
            if not self.input_dir.exists():
                logger.error(f"Input directory does not exist: {self.input_dir}")
                return []
            target_files = list(self.input_dir.glob("*.html"))
            logger.info(f"Found {len(target_files)} HTML files to process in {self.input_dir}")

        for path in target_files:
            if not path.exists():
                logger.warning(f"File {path} does not exist, skipping.")
                continue
                
            fname = path.name
            try:
                with open(path, "r", encoding="utf-8") as f:
                    html = f.read()
                
                text = self.html_to_text(html)
                if not text:
                    logger.warning(f"File {fname} resulted in empty text.")
                    continue

                chunks = self.chunk_text(text, max_chars=max_chars)
                
                parts = fname.replace(".html", "").split("_")
                metadata = {}

                # Expected format: Publisher_Year_Pos.html
                if len(parts) >= 3:
                    metadata = {
                        "publisher": parts[0],
                        "year": parts[1],
                        "pos": parts[2],
                        "filename": fname
                    }
                else:
                    metadata = {"filename": fname}
                
                for i, chunk in enumerate(chunks):
                    dataset.append({
                        "text": chunk,
                        "metadata": {**metadata, "chunk_id": i}
                    })

            except Exception as e:
                logger.error(f"Error processing file {fname}: {e}")

        # If we are processing everything, we save to the main file
        if specific_files is None:
            # Ensure output dir exists
            if not self.output_file.parent.exists():
                self.output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(dataset)} chunks to {self.output_file}")
            
        return dataset

if __name__ == "__main__":
    prep = DataPreprocessor()
    prep.process_files()
