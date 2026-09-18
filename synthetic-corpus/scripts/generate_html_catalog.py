#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generate_html_catalog.py
Generates a style-rich, interactive HTML catalog of the 55 textbook PDFs.
Uses premium aesthetics, glassmorphism, and responsive CSS grids.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKS_JSON_PATH = os.path.join(BASE_DIR, "textbook_links.json")
OUTPUT_HTML_PATH = os.path.join(BASE_DIR, "textbook_catalog.html")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WBBSE Bengali-Medium Textbook Catalog</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Playfair+Display:ital,wght@0,600;1,400&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(255, 255, 255, 0.03);
            --border-color: rgba(255, 255, 255, 0.08);
            --accent-color: #4f46e5;
            --accent-hover: #6366f1;
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --gradient: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            padding: 3rem 1.5rem;
            overflow-x: hidden;
        }}

        .background-glow {{
            position: absolute;
            top: -10%;
            left: 50%;
            transform: translateX(-50%);
            width: 80vw;
            height: 50vh;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, rgba(99, 102, 241, 0) 70%);
            z-index: -1;
            pointer-events: none;
        }}

        header {{
            max-width: 1200px;
            margin: 0 auto 3rem auto;
            text-align: center;
        }}

        h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 3.5rem;
            font-weight: 800;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            letter-spacing: -0.02em;
        }}

        p.subtitle {{
            color: var(--text-secondary);
            font-size: 1.2rem;
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.6;
        }}

        .search-container {{
            max-width: 500px;
            margin: 2rem auto 0 auto;
            position: relative;
        }}

        .search-container input {{
            width: 100%;
            padding: 1rem 1.5rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 50px;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 1rem;
            transition: all 0.3s ease;
            outline: none;
            backdrop-filter: blur(10px);
        }}

        .search-container input:focus {{
            border-color: var(--accent-hover);
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);
            background: rgba(255, 255, 255, 0.08);
        }}

        main {{
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 2rem;
        }}

        .class-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 2rem;
            backdrop-filter: blur(20px);
            transition: transform 0.3s ease, border-color 0.3s ease;
        }}

        .class-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(99, 102, 241, 0.3);
        }}

        .class-header {{
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 0.8rem;
            background: linear-gradient(90deg, #f3f4f6, #9ca3af);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .book-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .book-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.8rem 1rem;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            transition: all 0.2s ease;
        }}

        .book-item:hover {{
            background: rgba(99, 102, 241, 0.05);
            border-color: rgba(99, 102, 241, 0.2);
        }}

        .book-title {{
            font-weight: 400;
            color: var(--text-primary);
            font-size: 0.95rem;
            max-width: 70%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .btn-link {{
            background: var(--accent-color);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            transition: background 0.2s ease;
        }}

        .btn-link:hover {{
            background: var(--accent-hover);
        }}

        footer {{
            text-align: center;
            margin-top: 5rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}

        /* Responsive adjustments */
        @media (max-width: 768px) {{
            h1 {{
                font-size: 2.5rem;
            }}
            main {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="background-glow"></div>
    
    <header>
        <h1>WBBSE Textbook Catalog</h1>
        <p class="subtitle">A curated database of WBBSE Bengali-Medium textbooks across Class 1-10. Open each textbook directly in Google Drive to preview, download, or copy to your target folder.</p>
        <div class="search-container">
            <input type="text" id="searchInput" placeholder="Search by book name..." onkeyup="filterBooks()">
        </div>
    </header>

    <main id="catalogGrid">
        {cards_html}
    </main>

    <footer>
        <p>SahayakAI Teacher Model Ingestion Project · 2026</p>
    </footer>

    <script>
        function filterBooks() {{
            let input = document.getElementById('searchInput').value.toLowerCase();
            let cards = document.getElementsByClassName('class-card');
            
            for (let card of cards) {{
                let bookItems = card.getElementsByClassName('book-item');
                let cardHasVisibleBook = false;
                
                for (let item of bookItems) {{
                    let title = item.getElementsByClassName('book-title')[0].textContent.toLowerCase();
                    if (title.includes(input)) {{
                        item.style.display = 'flex';
                        cardHasVisibleBook = true;
                    }} else {{
                        item.style.display = 'none';
                    }}
                }}
                
                if (cardHasVisibleBook || input === "") {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }}
        }}
    </script>
</body>
</html>
"""

def generate_catalog():
    if not os.path.exists(LINKS_JSON_PATH):
        print(f"Error: {LINKS_JSON_PATH} not found. Please run scrape_textbook_links.py first.")
        return
        
    with open(LINKS_JSON_PATH, "r", encoding="utf-8") as f:
        database = json.load(f)
        
    cards_html = []
    
    # Sort classes chronologically
    sorted_classes = sorted(database.keys(), key=lambda x: int(x.split("_")[1]) if x.split("_")[1].isdigit() else 99)
    
    for class_key in sorted_classes:
        books = database[class_key]
        class_label = class_key.replace("_", " ").title()
        
        books_html = []
        for book in books:
            book_title = book["title"]
            drive_url = book["url"]
            
            book_li = f"""
            <li class="book-item">
                <span class="book-title" title="{book_title}">{book_title}</span>
                <a href="{drive_url}" target="_blank" class="btn-link">Open PDF</a>
            </li>"""
            books_html.append(book_li)
            
        card = f"""
        <div class="class-card">
            <h2 class="class-header">{class_label}</h2>
            <ul class="book-list">
                {"".join(books_html)}
            </ul>
        </div>"""
        cards_html.append(card)
        
    full_html = HTML_TEMPLATE.format(cards_html="".join(cards_html))
    
    with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print(f"HTML Catalog successfully generated at {OUTPUT_HTML_PATH}")

if __name__ == "__main__":
    generate_catalog()
