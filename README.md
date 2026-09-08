## Noveldex-to-Ebook
This code downloads the webnovel/text from the Noveldex website and creates a ebook from that. Used to archive webnovels from the website.

### Dependencies
pip install before running code.
Seleniumbase
ebooklib
BeautifulSoup

## How to run
The old version used the variables in the code. This new one the reads the json for the variables. In noveldex_novels.json, add or modify novels to download. 

**!Important!** Pages and latest are for updating. **pages** is what you currently or want to have in your ebook, change **latest** to add more pages to it. If pages and latest are the same it creates a new ebook, if **latest** is higher than pages it will try to find the ebook in your webnovel directory and create a new ebook with the added pages.

Commands to run code:
python Noveldex_webscraper.py --novel "Murim Psychopath"
python Noveldex_webscraper.py --update

## Errors that might Occur
Because it is running selenium base it sometimes fails to download the text for the page, it was made so it completes the ebook with the last page it could get. Just update the json to reflect this and run the novel again.
