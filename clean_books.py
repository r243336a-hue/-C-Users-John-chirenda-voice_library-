import os
import re


def clean_gutenberg(text):
    """Remove Project Gutenberg header and footer, collapse multiple blank lines."""
    # Remove Project Gutenberg header and footer
    start = re.search(r'\*\*\* START OF .* PROJECT GUTENBERG EBOOK .* \*\*\*', text)
    end = re.search(r'\*\*\* END OF .* PROJECT GUTENBERG EBOOK .* \*\*\*', text)
    if start and end:
        text = text[start.end():end.start()]
    # Collapse multiple blank lines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def main():
    """Main execution function."""
    input_dir = 'data/raw'
    output_dir = 'data/cleaned'
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as f:
                content = f.read()
            cleaned = clean_gutenberg(content)
            out_name = filename.replace('.txt', '_cleaned.txt')
            with open(os.path.join(output_dir, out_name), 'w', encoding='utf-8') as f:
                f.write(cleaned)
            print(f"Cleaned {filename}")


if __name__ == '__main__':
    main()
