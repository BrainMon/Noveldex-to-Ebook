from seleniumbase import SB
from bs4 import BeautifulSoup
import re
import sys
sys.stdout.reconfigure(encoding="utf-8")
from ebooklib import epub
import time
import json
import argparse

from novel_updater import update_all

## Old use of variables
# name = "Murim Psychopath"
# page_url = "https://noveldex.io/series/novel/murim-psychopath/chapter/"
# total_pages = 216
# author = "Unknown"
# image = "WebNovel_Images/Murim Psychopath.jpg"

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--novel", type=str, help="Name of the novel in quotes")
group.add_argument("-U", "--update", action="store_true", help="Updates all novels")

args = parser.parse_args()

with open("noveldex_novels.json", encoding="utf-8") as f:
    novels = json.load(f)

if args.update:
    for novel in novels:
        print(f"Updating {novel["name"]}")
        update_all(novel)
    sys.exit()

print("not in update?")

novel = next(
    (n for n in novels if n["name"] == args.novel),
    None
)

if novel is None:
    raise ValueError(f'Novel "{args.novel}" not found.')

name = novel["name"]
author = novel["author"]
page_url = novel["url"]
total_pages = novel["pages"]
image = novel["image"]
latest_page = novel['latest']

# Flag if we are adding new pages
add_new = False
book = ''
toc_list = ''
i = 0

if  total_pages == latest_page:
    # Create a new EPUB book
    book = epub.EpubBook()

    # Metadata
    book.set_identifier('id9kIJH28iuY3')
    book.set_title(name)
    book.set_language('en')
    book.add_author(author)
elif (latest_page > total_pages):
    # sets where the new chapter should start
    print(f"On Chapter {total_pages+1} out of Lates page {latest_page}")
    i = total_pages
    total_pages = latest_page
    add_new = True
    book = epub.read_epub(f"WebNovels/{name}.epub")
    toc_list = list(book.toc)


urls = [
    # put your chapter URLs here
    # "https://novelfire.net/book/sss-class-suicide-hunter/chapter-1",
    # "https://novelfire.net/book/sss-class-suicide-hunter/chapter-2",
]

# Collect chapters
chapters = []

if (add_new):
    # Add Previous Chapters from book
    chapters = [
    item for item in book.get_items()
    if isinstance(item, epub.EpubHtml)
    and item.file_name.startswith("chap_")
    ]

    chapters.sort(
        key=lambda c: int(c.file_name.split("_")[1].split(".")[0])
    )

for n in range(total_pages):
     urls.append(f"{page_url}{n+1}")

retries = 0

print(f"Total Number of pages: {total_pages}")

while i < total_pages:
    if (i%20 == 0): 
        print(f"On {i+1}: Progress: {(i+1)/total_pages*100:.2f}")
    chapter_title = ''
    with SB(uc=True, headless=True) as sb:
        sb.open(urls[i])

        # wait for Cloudflare + JS to finish
        sb.sleep(3)
        sb. solve_captcha()
        sb.sleep(3)

        # now grab rendered HTML
        try:
            html = sb.get_page_source()
        except:
            print(f"Broke on chapter {i+1}")
            retries += 1
            if (retries == 6): break
            continue

        soup = BeautifulSoup(html, "lxml")
        try:
            title_div = soup.find("h1", {"class": "text-lg sm:text-xl md:text-2xl font-bold mb-4 sm:mb-6 md:mb-8 text-center opacity-70"})
            small_title = title_div.get_text(" ", strip=True)
            chapter_title = small_title
        except:
            print() # No title Found
        content_div = soup.find("div",  {"data-chapter-id": True})

        try:
            blocks = content_div.find_all("div", attrs={"data-paragraph-index": True})
        except:
            print(f"Retry: {i+1}")
            retries += 1
            if (retries == 5): 
                time.sleep(60)
            if (retries == 6): break
            continue
        retries = 0

        paragraphs = []
        
        # if blocks[0].find(["h1"]).replace("<h1>", "").replace("</h1>", "") == chapter_title: 
        #     print("the same")
        # The site has all paragraphs in the wrong order this will correct them
        for b in blocks:
            idx = int(b["data-paragraph-index"])
            text = b.get_text(" ", strip=True)

            if (text == chapter_title):
                continue
            if b.find(["h1"]) and chapter_title == "":
                chapter_title = text
                continue
            if b.find("span"):
                text = text[:-1]
            paragraphs.append((idx, text))

        paragraphs.sort(key=lambda x: x[0])

        # html_content = "".join(f"{t}\n" for _, t in paragraphs)
        # print(html_content)

        if (chapter_title == ''): 
            # chapter_title = paragraphs[0][1] #if chapter title is in first <p>
            chapter_title = f"Chapter {i+1}"

        content = "<h1>{}</h1>".format(chapter_title) 
        for p in paragraphs:
            # print(p)
            content += "<p>{}</p>".format(p[1])

        # Make EPUB chapter
        chapter = epub.EpubHtml(
            title=chapter_title, # f"Chapter {i+1}: " +  # if need to have chapter alongside chapter name
            file_name=f"chap_{i+1}.xhtml", 
            lang="en"
        )

        chapter.id = f"chapter_{i+1}"
        chapter.content = content
        book.add_item(chapter)
        if add_new == True:
            new_link = epub.Link(chapter.file_name, chapter.title, chapter.id)
            toc_list.append(new_link)

        chapters.append(chapter)
        i += 1

# Define table of contents
book.toc = tuple(chapters)

if (add_new == True): 
    book.toc = tuple(toc_list)

# Add default NCX and Nav files
if (add_new):
    # Spine (reading order)
    book.spine += chapters

    # Save book
    epub.write_epub(f"{name}_2.epub", book, {})

    print("Done!")
    sys.exit()

book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# Add default CSS (optional)
style = 'BODY { font-family: Times, serif; }'
nav_css = epub.EpubItem(
    uid="style_nav",
    file_name="style/nav.css",
    media_type="text/css",
    content=style
)
book.add_item(nav_css)

# cover_page = book.get_item_with_id('cover')

with open(image, 'rb') as f:
    cover_data = f.read()

# Create a custom cover page
cover_page = epub.EpubHtml(title='Cover', file_name='cover.xhtml', lang='en')
cover_page.content = f'<html><body><img src="cover.png" alt="Cover"/></body></html>'
book.add_item(cover_page)

# Add the cover image as a separate item
cover_image = epub.EpubItem(uid="cover_image", file_name="cover.png", media_type="image/png", content=cover_data)
book.add_item(cover_image)

# Spine (reading order)
book.spine = [cover_page, 'nav'] + chapters

# Save book
epub.write_epub(f"{name}.epub", book, {})

print("Done!")