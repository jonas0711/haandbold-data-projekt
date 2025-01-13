import PyPDF2
import os

def convert_pdf_to_text(pdf_path: str, output_path: str) -> bool:
    """
    Konverterer en PDF-fil til tekst.
    
    Args:
        pdf_path (str): Stien til PDF-filen
        output_path (str): Stien hvor tekstfilen skal gemmes
        
    Returns:
        bool: True hvis konverteringen lykkedes, ellers False
    """
    try:
        # Åbn PDF-filen
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ''
            
            # Læs hver side i PDF'en
            for page in pdf_reader.pages:
                text += page.extract_text() + '\n'

        # Gem teksten i en .txt fil
        with open(output_path, 'w', encoding='utf-8') as text_file:
            text_file.write(text)
            
        return True
    except Exception as e:
        print(f"Fejl ved konvertering af PDF: {str(e)}")
        return False

if __name__ == "__main__":
    # Test funktionen hvis filen køres direkte
    if os.path.exists('a.pdf'):
        convert_pdf_to_text('a.pdf', 'output.txt')