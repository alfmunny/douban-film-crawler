import requests
import os
import json
from collections import OrderedDict
from bs4 import BeautifulSoup
import datetime
from pymongo import MongoClient
import hashlib

MONGODB = MongoClient()

class Crawler:
  def __init__(self, url):
    self.headers = { 
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36' 
    }
    self.url = url

  def get_base_data(self):
    data = self.request(self.url).text
    return data

  def request(self, url):
      response = requests.get(url, headers=self.headers)
      return response

  def soupify(self, data):
    return BeautifulSoup(data, "html.parser")

  def get_soup(self, page):
    response = self.request(page)
    data = response.text
    soup = self.soupify(data)
    return soup

class DouBanFilm250Crawler(Crawler):
  def __init__(self):
    self.url = 'https://movie.douban.com/top250'
    Crawler.__init__(self, self.url)
    self.output_file = "films.json"
    self.raw_text = ""
    self.pages = []
    self.films = []

    # set raw_text and pages
    self.__get_raw_text()
    self.__get_pages()

  def __get_raw_text(self):
    self.raw_text = self.get_base_data()

  def __get_pages(self):
    soup = self.soupify(self.raw_text)
    paginator = soup.find_all("div", class_="paginator")
    hrefs = [a.get("href") for a in paginator[0].find_all('a')]
    self.pages = [ self.url ] + [ self.url + h for h in hrefs ]

  def __get_tags(self, node):
    tags = [ n.string for n in node ]
    return ' / '.join(tags)

  def __remove_file(self):
    try:
      os.remove(self.output_file)
    except OSError:
      pass

  def __write_to_json(self, film):
    with open(self.output_file, 'a', encoding='utf8') as output:
      json.dump(film.data, output, ensure_ascii=False, indent=2)

  def get_film_list(self, page):
    soup = self.get_soup(page)
    pics = soup.find_all("div", class_="pic")
    return [ pic.a.get("href") for pic in pics ]
    
  def get_film(self, film_page):
    soup = self.get_soup(film_page)
    film = DoubanFilm()

    info = soup.find_all('div', id='info')[0].find_all('span')

    film.data['rank'] = soup.find_all('span', class_='top250-no')[0].string
    film.data['name'] = soup.find_all('span', property='v:itemreviewed')[0].string
    film.data['directors'] = self.__get_tags(info[0].find_all('a'))
    film.data['writers'] = self.__get_tags(info[3].find_all('a'))
    film.data['actors'] = self.__get_tags(soup.find_all('span', class_="actor")[0].find_all('a'))
    film.data['type'] = self.__get_tags(soup.find_all('span', property='v:genre'))
    film.data['country'] = soup.find(text='制片国家/地区:').next_element.lstrip().rstrip()
    film.data['release_date'] = self.__get_tags(soup.find_all('span', property='v:initialReleaseDate'))
    film.data['rating'] = soup.find_all('strong', property='v:average')[0].string

    return film

  def start(self, page_limit=100):
    print("Start fetching films from douban top 250, exporting to " + str(self.output_file))
    print("===============================================")

    self.__remove_file() if os.path.exists(self.output_file) else None

    for page in self.pages[:page_limit]: 
      film_list = self.get_film_list(page)
      for film_page in film_list:
        print("Processing page: " + film_page + "...")
        film = self.get_film(film_page)
        print("Film processed: " + film.data['name'])
        #self._write_to_json(film)
        film.save_to_db()

class DoubanFilm:
  def __init__(self):
    self.data = OrderedDict()

  def __str__(self):
    return str(self.data)

  def save_to_db(self):
    # compute the id using sha1 hashing
    id = hashlib.sha1(self.data['name'].encode('utf-8')).hexdigest()
    # update the datetime
    self.data['update_time'] = datetime.datetime.now()
    self.data['_id'] = id
    MONGODB['douban']['films'].update_one(
        filter={'_id': id }, # make sure we don't insert an exsiting document
        update={'$set': self.data },
        upsert=True
        )

if __name__ == "__main__":
  crawler = DouBanFilm250Crawler()
  crawler.start()

