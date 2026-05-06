"""
rename_books.py
Renames all .txt files in data/cleaned to a standard format:
    title_author_cleaned.txt
Also rewrites books_metadata.csv so everything stays linked.
"""

import os
import re
import csv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BOOK_FOLDER = os.path.join(PROJECT_ROOT, "data", "cleaned")
CSV_PATH = os.path.join(PROJECT_ROOT, "books_metadata.csv")

# User-provided authoritative mapping: old filename -> (title, author, new filename)
EXPLICIT_MAPPING = {
    "title_ A.S.Boyd_cleaned.txt": (
        "Glasgow Men and Women",
        "A. S. Boyd",
        "glasgow_men_and_women_boyd_cleaned.txt",
    ),
    "title_ SaxonHomelandProtectionAssociation_cleaned.txt": (
        "Mitteilungen des Landesvereins Saechsischer Heimatschutz",
        "Landesverein Saechsischer Heimatschutz",
        "landesverein_saechsischer_heimatschutz_cleaned.txt",
    ),
    "title_AntoniFerreriCodina_cleaned.txt": (
        "Africa",
        "Antoni Ferrer i Codina",
        "africa_ferrer_i_codina_cleaned.txt",
    ),
    "title_ArthurConanDoyle_cleaned.txt": (
        "Spaete Rache",
        "Arthur Conan Doyle",
        "spaete_rache_doyle_cleaned.txt",
    ),
    "title_ArthurDoyle_cleaned.txt": (
        "Its Time Something Happened",
        "Arthur Doyle",
        "its_time_something_happened_doyle_cleaned.txt",
    ),
    "title_AylmerMaude_cleaned.txt": (
        "The Authorized Life of Marie C Stopes",
        "Aylmer Maude",
        "authorized_life_of_marie_c_stopes_maude_cleaned.txt",
    ),
    "title_ConstanceStewartRichardson_cleaned.txt": (
        "Dancing Beauty and Games",
        "Lady Constance Stewart Richardson",
        "dancing_beauty_and_games_richardson_cleaned.txt",
    ),
    "title_ErnestNathanielBennett_cleaned.txt": (
        "The Mordant",
        "Merab Eberle",
        "the_mordant_eberle_cleaned.txt",
    ),
    "title_HaroldD.Lasswell_cleaned.txt": (
        "Psychopathology and Politics",
        "Harold D Lasswell",
        "psychopathology_and_politics_lasswell_cleaned.txt",
    ),
    "title_HonorédeBalzac_cleaned.txt": (
        "Another Study of Woman",
        "Honore de Balzac",
        "another_study_of_woman_balzac_cleaned.txt",
    ),
    "title_JamesBranchCabell_cleaned.txt": (
        "From the Hidden Way",
        "James Branch Cabell",
        "from_the_hidden_way_cabell_cleaned.txt",
    ),
}


def slugify(text):
    """Convert text to lowercase, replace spaces with underscores, remove punctuation."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text


def build_fallback_name(file_name):
    base = file_name.replace("title_", "").replace("_cleaned", "").replace(".txt", "")
    base = re.sub(r"[_\s]+", " ", base).strip()
    title = base if base else "unknown_title"
    author = "unknown_author"
    new_name = f"{slugify(title)}_{slugify(author)}_cleaned.txt"
    return title, author, new_name


def rename_books_in_folder(folder_path, metadata_csv_path, dry_run=True):
    if not os.path.exists(folder_path):
        print(f"Books folder not found: {folder_path}")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(".txt")]
    rename_map = {}
    metadata_rows = []

    for file_name in files:
        if file_name in EXPLICIT_MAPPING:
            title, author, new_name = EXPLICIT_MAPPING[file_name]
        else:
            title, author, new_name = build_fallback_name(file_name)

        rename_map[file_name] = (new_name, title, author)

    new_names = [v[0] for v in rename_map.values()]
    if len(new_names) != len(set(new_names)):
        print("Error: duplicate target filenames detected. Resolve before renaming.")
        return

    for old_basename, (new_basename, title, author) in rename_map.items():
        old_full = os.path.join(folder_path, old_basename)
        new_full = os.path.join(folder_path, new_basename)
        if not os.path.exists(old_full):
            print(f"Warning: {old_full} not found, skipping.")
            continue
        if dry_run:
            print(f"[DRY RUN] Would rename: {old_basename} -> {new_basename}")
        else:
            os.rename(old_full, new_full)
            print(f"Renamed: {old_basename} -> {new_basename}")

        wordcount = 0
        filesize = 0
        target_path = new_full if not dry_run else old_full
        if os.path.exists(target_path):
            filesize = os.path.getsize(target_path)
            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                wordcount = len(re.findall(r"\b\w+\b", text))

        metadata_rows.append(
            {
                "title": title,
                "author": author,
                "subject_tags": "English",
                "category": "English",
                "language": "en",
                "file_path": os.path.join("data", "cleaned", new_basename),
                "wordcount": wordcount,
                "filesize_bytes": filesize,
            }
        )

    if not dry_run:
        with open(metadata_csv_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "title",
                "author",
                "subject_tags",
                "category",
                "language",
                "file_path",
                "wordcount",
                "filesize_bytes",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(metadata_rows)
        print(f"Updated {metadata_csv_path} with new file paths and metadata.")


if __name__ == "__main__":
    rename_books_in_folder(BOOK_FOLDER, CSV_PATH, dry_run=False)
