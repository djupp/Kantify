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

BASE_URL = """http://korpora.zim.uni-duisburg-essen.de/kant/aa"""
INDENT = {9: "Part", 8: "Chapter", 7: "Section",
          6: "Subsection", 5: "Subsubsection",
          4: "Paragraph"}


class Page:
    def __init__(self, page_no, book):
        self.page = page_no
        self.book = book
        self.url = to_url(self.page, self.book.book_number)
        self.soup = self.get_page()

    def get_page(self):
        page_data = urllib.request.urlopen(self.url)
        soup = BeautifulSoup(page_data)
        return soup

    def parse(self):
        pass

    def get_next_page(self):
        # Implement routine to find which page comes next
        page_nos = self.soup.findAll('a', text=re.compile('Seite \d{1,3}'))
        page_nos = [int(re.findall('\d{1,3}', i.text)[0]) for i in page_nos]
        if len(page_nos) == 2:
            return page_nos[1]
        elif page_nos[0] > self.page:
            return page_nos[0]
        else:
            return None


class Section:

    def __init__(self, book, title, indent, page_start):
        self.book = book
        self.indent = indent
        self.level = INDENT[indent]
        self.title = title
        self.start = page_start
        self.start_url = to_url(self.start, self.book.book_number)
        self.children = []
        self.pages = []
        self.parent = None
        self.end = -1
        self.length = -1

    def mark_section_end(self, page_end):
        self.end = page_end
        self.length = self.start - self.end

    def set_parent(self, section):
        self.parent = section

    def get_parent(self):
        return self.parent

    def add_sibling(self, section):
        self.siblings.append(section)

    def get_siblings(self):
        return self.parent.get_children()

    def get_next_section(self):
        # If there are children
        if len(self.children) > 0:
            return self.children[0]
        # Looking for siblings at highest indent
        elif self.indent == 9:
            if len(self.book.parts) > self.book.parts.index(self) + 1:
                return self.book.parts[self.book.parts.index(self) + 1]
            else:
                return None
        # Looking for siblings or parents
        else:
            siblings = self.parent.get_children()
            if len(siblings) > siblings.index(self)+1:
                return siblings[siblings.index(self) + 1]
            else:
                return self.parent.get_next_section()

    def add_child(self, section):
        self.children.append(section)

    def get_children(self):
        return self.children

    def is_parent(self, section):
        return section in self.children

    def traverse(self):
        print((9-self.indent) * ' ' + self.title)
        for child in self.children:
            child.traverse()

    def crawl(self):
        for child in self.children:
            child.crawl()
        crawler = SectionCrawler(self)


class SectionCrawler:

    def __init__(self, section):
        self.crawl(section)

    def crawl(self, section):
        cur_page = section.start
        next_section = section.get_next_section()
        if not next_section:
            end_page = -1
        else:
            end_page = next_section.start
        while not cur_page == end_page or not cur_page:
            print("Inserting page " + str(cur_page))
            page = Page(cur_page, section.book)
            section.pages.append(page)
            cur_page = page.get_next_page()


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


# Helper functions: is_valign_top
def is_valign_top(cell):
    if cell.has_attr('valign') and cell.attrs['valign'] == 'top':
        return True
    else:
        return False


def has_words(cell):
    if len(re.findall("[a-zA-Z]{5,}", cell.text)) > 0:
        return True
    else:
        return False


def next_cell_is_pagelink(cell):
    next_cell = cell.findNext('td')
    if len(next_cell.findChildren('a')) > 0:
        return True, next_cell.findChild('a').attrs['href']
    else:
        return False, ""


def is_empty_section_header(cell):
    cell2 = cell
    # Get the cells indent level:
    indent = int(cell.attrs['colspan'])

    # Find the next header cell:
    next_header = cell.findNext('td', attrs={'valign': 'top'})
    if not next_header:
        return False, None
    if int(next_header.attrs['colspan']) > indent:
        return False, None
    next_cell_with_text = cell2.findNext('td', attrs={'valign': 'top'})
    if not next_cell_with_text:
        return False, None
    if next_cell_with_text == next_header:
        return True, next_header
    else:
        return False, None


def to_url(page_no, book_no):
    return BASE_URL + str(book_no) + '/' + '%0.3d' % page_no + '.html'

# Start the program
if __name__ == '__main__':
    main()
