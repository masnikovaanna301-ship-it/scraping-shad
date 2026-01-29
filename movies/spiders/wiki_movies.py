import scrapy
import re

class MoviesSpider(scrapy.Spider):
    name = 'movies'

    def start_requests(self):
        url = 'https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту'
        yield scrapy.Request(url=url, callback=self.response_parser)

    def response_parser(self, response):
        film_links = response.css('div.mw-category a::attr(href)').getall()

        for link in film_links:
            if link.startswith('/wiki/'):
                yield response.follow(link, callback=self.parse_movie)

        next_page = response.css('a:contains("Следующая страница")::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.response_parser)

    def parse_movie(self, response):

        infobox = response.css('table.infobox')
        if not infobox:
            return

        def clean(text):
            return ' '.join(t.strip() for t in text if t.strip())

        title = response.css('#firstHeading span::text').get()

        genre_selectors = [
            "//table[contains(@class,'infobox')]//tr[.//th[contains(text(),'Жанр')]]/td//text()",
            "//table[contains(@class,'infobox')]//tr[.//th[contains(text(),'жанр')]]/td//text()",
            "//table[contains(@class,'infobox')]//tr[.//th[contains(text(),'Жанры')]]/td//text()",
            "//table[contains(@class,'infobox')]//tr[.//th[contains(text(),'жанры')]]/td//text()",
            # Для английской версии страниц
            "//table[contains(@class,'infobox')]//tr[.//th[contains(text(),'Genre')]]/td//text()",
            "//table[contains(@class,'infobox')]//tr[.//th[contains(text(),'genre')]]/td//text()",
            "//table[contains(@class,'infobox')]//tr[.//th[contains(text(),'Genres')]]/td//text()"
        ]

        genre = ''
        for selector in genre_selectors:
            genre_data = clean(response.xpath(selector).getall())
            if genre_data:
                genre = genre_data
                break

        # Альтернативный вариант с более гибким поиском
        if not genre:
            # Ищем любую строку с "жанр" в таблице
            all_rows = response.xpath("//table[contains(@class,'infobox')]//tr")
            for row in all_rows:
                header = row.xpath(".//th//text()").get()
                if header and any(word in header.lower() for word in ['жанр', 'genre']):
                    genre = clean(row.xpath(".//td//text()").getall())
                    break

        director = clean(response.xpath(
            "//table[contains(@class,'infobox')]"
            "//tr[th[contains(text(),'Режиссёр')]]/td//text()"
        ).getall())

        country = clean(response.xpath(
            "//table[contains(@class,'infobox')]"
            "//tr[th[contains(text(),'Страна')]]/td//text()"
        ).getall())

        year = clean(response.xpath(
            "//table[contains(@class,'infobox')]"
            "//tr[th[contains(text(),'Год')]]/td//text()"
        ).getall())

        yield {
            'title': title,
            'genre': genre,
            'director': director,
            'country': country,
            'year': year
        }

