# Plan:
#
# (1) Have a main program that runs each table of content, calls upon
# (2) Page-Crawler to return the context of a page as a
# (3) Page object, which contains the text (appropriately encoded) as well as
# any footnotes, section headings, etc.

import re
import sys
import urllib.request
from bs4 import BeautifulSoup
import pdb
from helper import *
from sectionparser import Section, SectionCrawler

BASE_URL = """http://korpora.zim.uni-duisburg-essen.de/kant/aa"""




class Book:

    def __init__(self, book_no):
        self.book_number = book_no
        self.crawl()

    parts = []

    def traverse(self):
        for part in self.parts:
            part.traverse()

    def crawl(self):
        toc_crawler = TOCCrawler(self)
        toc_crawler.crawl()
        self.crawl_sections()

    def crawl_sections(self):
        for part in self.parts:
            part.crawl()


class TOCCrawler:

    def __init__(self, book):
        self.book = book
        book_string = "%02d" % self.book.book_number
        self.url = BASE_URL + book_string + "/"
        self.crawl_queue = []

    def get_table_of_contents(self):
        toc_data = urllib.request.urlopen(self.url)
        toc_soup = BeautifulSoup(toc_data)
        return toc_soup

    def crawl(self):
        # Get ToC
        soup = self.get_table_of_contents()
        # Run through table contents
        for cell in soup("td"):
            # Check if it has contents
            if is_valign_top(cell) and has_words(cell):
                # Get the link if there is one
                is_link, link = next_cell_is_pagelink(cell)
                # If there is a link, we've found a section
                indent = int(cell.attrs['colspan'])
                if is_link:
                    if indent >= 4:
                        start_page = int(link[0:3])
                        title = re.sub('\s+', ' ', cell.text)
                        cur_sec = Section(self.book, title, indent, start_page)
                        self.crawl_queue.append(cur_sec)
                else:
                    is_empty, next_header = is_empty_section_header(cell)
                    if not is_empty:
                        continue
                    is_link, link = next_cell_is_pagelink(next_header)
                    if is_empty and is_link:
                        start_page = int(link[0:3])
                        title = re.sub('(?: +|\n)', ' ', cell.text)
                        cur_sec = Section(self.book, title, indent, start_page)
                        self.crawl_queue.append(cur_sec)

        for section in self.crawl_queue:
            # If we have a root:
            if section.indent == 9:
                self.book.parts.append(section)
                level = 9
                last_section = section
            # If we found a child of the previous section
            elif section.indent < level:
                last_section.add_child(section)
                section.set_parent(last_section)
                level = section.indent
                last_section = section
            # If we found a sibling of the previous section
            elif section.indent == level:
                last_section.parent.add_child(section)
                section.set_parent(last_section.parent)
                last_section = section
            # If we found a higher level:
            elif section.indent > level:
                while section.indent > level:
                    last_section = last_section.parent
                    level = last_section.indent
                last_section.parent.add_child(section)
                section.set_parent(last_section.parent)
                last_section = section



def main():
    test_book = 15
    the_book = Book(test_book)
    the_book.traverse()




# Start the program
if __name__ == '__main__':
    main()
