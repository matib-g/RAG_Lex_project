import requests
import time
import json
import os
from pathlib import Path
from typing import List, Dict, Union, Optional
from src.utils.config import SEJM_API_URL, RAW_DATA_DIR
from src.utils.logger import setup_logger

logger = setup_logger("downloader")

class SejmDownloader:
    """
    Class responsible for downloading acts from Sejm API.
    """
    def __init__(self, save_dir: Union[str, Path] = RAW_DATA_DIR, base_url: str = SEJM_API_URL):
        self.save_dir = Path(save_dir)
        self.base_url = base_url
        self._ensure_dir()

    def _ensure_dir(self):
        if not self.save_dir.exists():
            self.save_dir.mkdir(parents=True, exist_ok=True)

    def fetch_acts_for_year(self, publisher: str, year: int, limit: int = 100, offset: int = 0) -> Dict:
        """
        Retrieves a list of acts for a given publisher and year.
        """
        url = f"{self.base_url}/{publisher}/{year}"
        params = {
            "limit": limit,
            "offset": offset
        }
        try:
            resp = requests.get(url, params=params, headers={"Accept": "application/json"})
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch acts list for {publisher}/{year}: {e}")
            raise

    def fetch_act_text(self, publisher: str, year: int, num: int, as_pdf: bool = False) -> Union[str, bytes]:
        """
        Retrieves the text/content of the document.
        """
        ext = "pdf" if as_pdf else "html"
        url = f"{self.base_url}/{publisher}/{year}/{num}/text.{ext}"
        headers = {"Accept": "application/octet-stream" if as_pdf else "text/html"}
        
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            return resp.content if as_pdf else resp.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch content for {publisher}/{year}/{num}: {e}")
            raise

    def download_acts(self, publisher: str, year: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Main method to download files and save them locally. Returns a manifest of downloaded files.
        """
        logger.info(f"Starting download for {publisher}/{year} (Limit: {limit}, Offset: {offset})")
        
        acts_data = self.fetch_acts_for_year(publisher, year, limit, offset)
        items = acts_data.get("items", [])
        
        manifest = []
        
        for act in items:
            pos = act.get("pos")
            eli = act.get("ELI")
            title = act.get("title")
            has_html = act.get("textHTML", False)
            has_pdf = act.get("textPDF", False)

            content = None
            fname = None
            mode = "w"
            encoding = "utf-8"

            try:
                if has_html:
                    content = self.fetch_act_text(publisher, year, pos, as_pdf=False)
                    fname = f"{publisher}_{year}_{pos}.html"
                    mode = "w"
                    encoding = "utf-8"
                elif has_pdf:
                    content = self.fetch_act_text(publisher, year, pos, as_pdf=True)
                    fname = f"{publisher}_{year}_{pos}.pdf"
                    mode = "wb"
                    encoding = None
                else:
                    logger.warning(f"No text content for act {publisher} {year} {pos}")
                    continue
                
                output_path = self.save_dir / fname
                
                if encoding:
                    with open(output_path, mode, encoding=encoding) as f:
                        f.write(content)
                else:
                    with open(output_path, mode) as f:
                        f.write(content)
                        
                manifest.append({
                    "publisher": publisher,
                    "year": year,
                    "pos": pos,
                    "ELI": eli,
                    "title": title,
                    "filename": fname,
                    "path": str(output_path),
                    "has_html": has_html,
                    "has_pdf": has_pdf
                })
                
                # Polite delay
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error processing act {publisher} {year} {pos}: {e}")

        # Save manifest
        manifest_path = self.save_dir / f"{publisher}_{year}_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(manifest, mf, ensure_ascii=False, indent=2)
            
        logger.info(f"download_acts completed. Downloaded {len(manifest)} items.")
        return manifest

if __name__ == "__main__":
    # Test execution
    downloader = SejmDownloader()
    downloader.download_acts("DU", 2020, limit=10)
