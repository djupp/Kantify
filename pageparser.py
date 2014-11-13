__author__ = 'djupp'


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

