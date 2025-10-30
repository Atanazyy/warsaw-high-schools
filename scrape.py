import re
import pandas as pd
import requests
import pdfplumber

# Official PDF with admission thresholds for Warsaw high schools (2024)
OFFICIAL_PDF_URL = "https://edukacja.um.warszawa.pl/documents/66399/83605261/Minimalna%2Bliczba%2Bpunkt%C3%B3w%2B2024%2Br..pdf/dc6ed342-55c7-8aaf-518e-58cbb4640ea7?t=1721916124051"
OFFICIAL_PDF = "warsaw_highschools_2024.pdf"

RANKINGS_PDF = "ranking-licea-warszawskie-2025.pdf"

def download_pdf():
    """Download the official PDF file if it is not already saved locally."""
    print("Downloading the official PDF from the Warsaw Education Office...")
    r = requests.get(OFFICIAL_PDF_URL)
    with open(OFFICIAL_PDF, "wb") as f:
        f.write(r.content)
    print("File downloaded:", OFFICIAL_PDF)

def parse_official_pdf():
    print("Parsing the official PDF...")
    data = []
    with pdfplumber.open(OFFICIAL_PDF) as pdf:
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
    return df

def add_rankings(df):
    print("Adding rankings from the rankings PDF...")
    with pdfplumber.open(RANKINGS_PDF) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                for row_idx, row in enumerate(table):
                    if not row[0] or not row[0].isdigit():
                        continue
                    if row[0] == '2025':
                        continue
                    ranking25 = row[0] if row[0] else ""
                    nazwa_szkoly = row[1] + row[2] if row[1] or row[2] else ""
                    if nazwa_szkoly[0:2] != "LO":
                        continue
                    nazwa_szkoly = nazwa_szkoly.split("LO")[-1].strip()
                    rankingi = [float(x) for x in row[4:7] if x != "-"] # places in 2024, 2023, 2022
                    srednia22do24 = round(sum(rankingi) / len(rankingi), 2) if rankingi else None
                    mask = df['nazwa_szkoly'].str.startswith(nazwa_szkoly)
                    df.loc[mask, 'ranking25'] = ranking25
                    df.loc[mask, 'srednia22do24'] = srednia22do24
    return df

if __name__ == "__main__":
    download_pdf()
    df = parse_official_pdf()
    df = add_rankings(df)
    df.to_csv("./app/data/warsaw_highschools_2024.csv", index=False, encoding="utf-8-sig")
