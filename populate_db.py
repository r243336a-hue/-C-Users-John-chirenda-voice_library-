import sqlite3
import os


def populate_database(db_path, cleaned_dir):
    """Populate database with cleaned book data."""
    if not os.path.exists(cleaned_dir):
        print(f"Cleaned data directory not found: {cleaned_dir}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    added_count = 0
    for filename in os.listdir(cleaned_dir):
        if filename.endswith('_cleaned.txt'):
            file_path = os.path.join(cleaned_dir, filename)
            
            # Extract title and author from filename (e.g., pride_and_prejudice_austen_cleaned.txt)
            name_part = filename.replace('_cleaned.txt', '')
            parts = name_part.split('_')
            
            # Simple heuristic: last part is author, rest is title
            if len(parts) >= 2:
                author = parts[-1].title()
                title = ' '.join(parts[:-1]).title()
            else:
                title = name_part.title()
                author = 'Unknown'
            
            # Compute word count and file size
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            word_count = len(text.split())
            file_size = os.path.getsize(file_path)
            
            try:
                cursor.execute('''
                INSERT INTO books (title, author, file_path, word_count, file_size_bytes)
                VALUES (?, ?, ?, ?, ?)
                ''', (title, author, file_path, word_count, file_size))
                
                added_count += 1
                print(f"  ✓ Added: {filename} -> Title: '{title}', Author: '{author}'")
            except sqlite3.IntegrityError as e:
                print(f"  ✗ Skipped {filename}: {e}")
    
    conn.commit()
    conn.close()
    print(f"\nTotal books added: {added_count}")


def main():
    """Main execution function."""
    db_path = 'data/database/library.db'
    cleaned_dir = 'data/cleaned'
    
    print(f"Database path: {db_path}")
    print(f"Cleaned data directory: {cleaned_dir}\n")
    
    print("Populating database with cleaned books...")
    populate_database(db_path, cleaned_dir)
    print("Database populated.")


if __name__ == '__main__':
    main()