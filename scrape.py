import re
import pandas as pd
import requests
import pdfplumber

# Official PDF with admission thresholds for Warsaw high schools (2024)
PDF_URL = "https://edukacja.um.warszawa.pl/documents/66399/83605261/Minimalna%2Bliczba%2Bpunkt%C3%B3w%2B2024%2Br..pdf/dc6ed342-55c7-8aaf-518e-58cbb4640ea7?t=1721916124051"
PDF_FILE = "warsaw_highschools_2024.pdf"

def download_pdf():
    """Download the official PDF file if it is not already saved locally."""
    print("Downloading the official PDF from the Warsaw Education Office...")
    r = requests.get(PDF_URL)
    with open(PDF_FILE, "wb") as f:
        f.write(r.content)
    print("File downloaded:", PDF_FILE)

def parse_pdf():
    data = []

    with pdfplumber.open(PDF_FILE) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                for row_idx, row in enumerate(table):
                    # skip incomplete rows
                    if len(row) < 5:
                        continue
                    # skip first row on the first page (column headers)
                    if page_num == 1 and row_idx == 0:
                        continue

                    dzielnica = row[0] if row[0] else ""
                    typ_szkoly = row[1] if row[1] else ""
                    nazwa_szkoly = row[2] if row[2] else ""
                    nazwa_oddzialu = row[4] if row[4] else ""
                    prog_min = row[5] if row[5] else ""

                    match = re.search(r".*\]\s*(.*?)\s*\(", nazwa_oddzialu)
                    if match:
                        rozszerzenia = match.group(1)
                        rozszerzenia = "-".join(sorted(rozszerzenia.split("-")))
                    else:
                        rozszerzenia = ""

                    match = re.search(r"\]\s*[^\(]*\((.*?)\)", nazwa_oddzialu)
                    if match:
                        jezyki = match.group(1)
                        jezyki = "-".join(sorted(filter(None, re.split(r"[,*-]", jezyki))))
                    else:
                        jezyki = ""

                    data.append({
                        "dzielnica": dzielnica.strip() if dzielnica else "",
                        "typ_szkoly": typ_szkoly.strip() if typ_szkoly else "",
                        "nazwa_szkoly": nazwa_szkoly.strip() if nazwa_szkoly else "",
                        "nazwa_oddzialu": nazwa_oddzialu.strip() if nazwa_oddzialu else "",
                        "rozszerzenia": rozszerzenia.strip() if rozszerzenia else "brak rozszerzeń",
                        "jezyki": jezyki.strip() if jezyki else "",
                        "prog_min": prog_min.strip() if prog_min else ""
                    })

    df = pd.DataFrame(data)
    df.to_csv("warsaw_highschools_2024.csv", index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    download_pdf()
    parse_pdf()