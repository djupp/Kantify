__author__ = 'djupp'

from helper import *
from main import Page

INDENT = {9: "Part", 8: "Chapter", 7: "Section",
          6: "Subsection", 5: "Subsubsection",
          4: "Paragraph"}

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
            if len(siblings) > siblings.index(self) + 1:
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
        print((9 - self.indent) * ' ' + self.title)
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
