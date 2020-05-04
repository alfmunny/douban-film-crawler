# Douban Film Top 250 Crawler

The script pulls the Top 250 films from [douban](https://movie.douban.com/top250).

## Requirements

- python3
- pip

Install `BeautifulSoup` for parsing html.

```shell
pip install beautifulsoup4
```

## Usage

```shell
python ./run.py
```
The films will be written to `films.json` under current folder.

You can also import crawler and run it yourself

```python
from crawler import DouBanFilm250Crawler

film_crawler = DouBanFilm250Crawler()
# only fetch the two pages
film_crawler.start(page_limit=2)
```



