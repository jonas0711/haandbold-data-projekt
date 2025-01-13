import requests
from bs4 import BeautifulSoup
import os
import logging
from urllib.parse import urljoin
import time
from datetime import datetime

# Opsætning af logging
def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(f'logs/scraper_{timestamp}.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def create_download_folder():
    """Opret Downloads mappe hvis den ikke eksisterer"""
    download_folder = "Downloads"
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        logging.info(f"Oprettet {download_folder} mappe")
    return download_folder

def get_session():
    """Opret en session med standard headers"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'da,en-US;q=0.9,en;q=0.8'
    })
    return session

def scrape_match_links(session):
    """Hent alle relevante PDF-links fra kampprogrammet"""
    base_url = "https://tophaandbold.dk"
    program_url = f"{base_url}/kampprogram/herreligaen"
    
    logging.info(f"Henter kampprogram fra {program_url}")
    
    try:
        response = session.get(program_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find alle dropdown-items (links)
        pdf_links = []
        for link in soup.find_all('a', class_='dropdown-item'):
            if "Alle hændelser" in link.text.strip():
                href = link.get('href')
                if href and href.startswith('/intranet/pdfs/game/'):
                    full_url = urljoin(base_url, href)
                    pdf_links.append(full_url)
                    logging.debug(f"Fundet PDF link: {full_url}")
        
        logging.info(f"Fundet {len(pdf_links)} unikke PDF-links")
        return pdf_links
    
    except requests.RequestException as e:
        logging.error(f"Fejl ved hentning af kampprogram: {str(e)}")
        return []

def download_pdf(session, url, download_folder):
    """Download en enkelt PDF-fil"""
    try:
        # Generer filnavn fra URL
        filename = url.split('/')[-2] + '_' + url.split('/')[-1].split('?')[0] + '.pdf'
        filepath = os.path.join(download_folder, filename)
        
        # Skip hvis filen allerede eksisterer
        if os.path.exists(filepath):
            logging.info(f"Fil eksisterer allerede: {filename}")
            return True
        
        logging.info(f"Downloader: {filename}")
        response = session.get(url, stream=True)
        response.raise_for_status()
        
        # Gem filen
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logging.info(f"Gemt fil: {filename}")
        return True
    
    except requests.RequestException as e:
        logging.error(f"Fejl ved download af {url}: {str(e)}")
        return False

def main():
    setup_logging()
    logging.info("Starter scraping af kampprogrammer")
    
    download_folder = create_download_folder()
    session = get_session()
    
    # Hent alle PDF links
    pdf_links = scrape_match_links(session)
    
    if not pdf_links:
        logging.error("Ingen PDF-links fundet")
        return
    
    # Download hver PDF
    successful_downloads = 0
    for i, url in enumerate(pdf_links, 1):
        logging.info(f"Behandler fil {i}/{len(pdf_links)}")
        if download_pdf(session, url, download_folder):
            successful_downloads += 1
        time.sleep(1)  # Ventetid mellem downloads
    
    logging.info(f"Færdig! Downloadet {successful_downloads} af {len(pdf_links)} filer")

if __name__ == "__main__":
    main() 