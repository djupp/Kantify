__author__ = 'djupp'

import re

BASE_URL = """http://korpora.zim.uni-duisburg-essen.de/kant/aa"""

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