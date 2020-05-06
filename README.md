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
git clone https://github.com/alfmunny/douban-film-crawler.git
cd douban-film-crawler
python run.py
```
The films will be written to `films.json` under current folder.

You can also import crawler and run it yourself

```python
from crawler import DouBanFilm250Crawler

film_crawler = DouBanFilm250Crawler()
# only fetch the two pages
film_crawler.start(page_limit=2)
```

## 实现过程

- [x] 一：[简单的爬虫](#简单的爬虫)
- [x] 二：[加入数据库](#加入数据库)
- [ ] 三：反爬机制和如何应对
- [ ] 四：顺便搞个Docker部署呗

### 简单的爬虫

目标

1. 爬取豆瓣Top250电影
2. 将信息存入json文件

我们主要用到`requests` and `beautifulsoup4`

`requests` 用来发送请求

`beautifulsoup4` 用来解析返回的html内容，抽取信息

访问根网站，取回html内容。headers是为了让你的访问看起来像是来自浏览器。

```python
class Crawler:
  def __init__(self):
		self.headers = {
  		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'
		}
		self.url = 'https://movie.douban.com/top250'

 	def request(self, url):
    response = requests.get(url, headers=self.headers)
    
	def get_base_data(self):
    data = self.request(self.url).text
    return data

```

首先我们需要取得所有需要访问的页面链接。一共有十页，找到页面底部翻页，打开浏览器的Developer Tools。

![Screenshot 2020-05-05 at 19.44.28](README/1.png)

我们可以看到剩下9页的链接。通过BeautifulSoap抓取出来，放在self.pages里。

```python
def get_pages(self):
  soup = (self.raw_text)
  paginator = soup.find_all("div", class_="paginator") # 通过class的名字找到对应区域
  hrefs = [a.get("href") for a in paginator[0].find_all('a')] # 抽取出所有链接
  self.pages = [ self.url ] + [ self.url + h for h in hrefs ] # 别忘了把第一页也放进去
```

接下来就是遍历self.pages里每个页面，每个页面有25个电影。

主要程序就是一个循环，很简单。

```python
for page in self.pages: # 遍历所有页面 
  film_list = self.get_film_list(page) # 提取单个页面上的25个电影链接 
  for film_page in film_list: # 遍历这些电影
    film = self.get_film(film_page) # 提取电影数据
    self.write_to_json(film) # 保存到文件
```

接下来我们我们来实现其中的 `get_film_list()`， `get_film()`和 `write_to_json()`

首先抓取25个电影链接 `get_film_list()`。

![Screenshot 2020-05-05 at 19.53.40](README/2.png)

```python
def get_film_list(self, page):
  soup = self._get_soup(page)
  pics = soup.find_all("div", class_="pic")
  return [ pic.a.get("href") for pic in pics ]
```

然后对25个电影链接进行访问，解析数据`get_film()`。点进单个电影的页面，inspect他的元素，比如导演。

![Screenshot 2020-05-05 at 19.57.27](README/3.png)

我们为每个电影创建一个电影对象，记录下以下数据。

```python
class DoubanFilm:
  def __init__(self):
    self.data = OrderedDict()
```
```python
def get_film(self, film_page):
  soup = self._get_soup(film_page)
  film = DoubanFilm()

  info = soup.find_all('div', id='info')[0].find_all('span')
  
  film.data['rank'] = soup.find_all('span', class_='top250-no')[0].string
  film.data['name'] = soup.find_all('span', property='v:itemreviewed')[0].string
  film.data['directors'] = self._get_tags(info[0].find_all('a'))
  film.data['writers'] = self._get_tags(info[3].find_all('a'))
  film.data['actors'] = self._get_tags(soup.find_all('span', class_="actor")[0].find_all('a'))
  film.data['type'] = self._get_tags(soup.find_all('span', property='v:genre'))
```

最后保存数据到json。`write_to_json()`。

```python
def write_to_json(self, film):
  with open(self.output_file, 'a', encoding='utf8') as output:
    json.dump(film.data, output, ensure_ascii=False, indent=2)
```

### 加入数据库

我们将实用[mongodb](mongodb.com)

安装 mongodb（macOs）

```
brew tap mongodb/brew
brew install mongodb-community@4.2
brew services start mongodb-community@4.2
```

如何在Windows上安装，请看https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/

安装 python的mongodb API：pymongo

```
pip install pymongo
```

我们下试试看登陆mongodb，操作一下数据库。

登陆

```shell
mongo
```

看下帮助

```
> help
```

显示所有databases

```
> show dbs
```

我们将使用一个新的test db。在mongodb上无需事先创建，直接use。

```
> use test_db
> db # 查看当前db
test_db
```

创建一个新的Collection

```
> db.createCollection('film')
```

插入一个新的Document，比如说一部电影。

```
> db.film.insert(
  {
    name: 'Unforgiven',
    director: 'Clint Eastwood',
    actors: ['Client Eastwood', 'Gene Hackman', 'Morgan Freeman'],
    country: 'USA',
  }
)
```
找出电影查看下。

```
> db.film.find({title: 'Unforgiven'})
{ "_id" : ObjectId("5eb2b6be0d590d69c0e06386"), "title" : "Unforgiven", "director" : "Clint Eastwood", "actors" : [ "Clint Eastwood", "Gene Hackman", "Morgan Freeman" ], "country" : "USA" }
```

数据库熟悉到此结束。更多尽在[官方文档](https://docs.mongodb.com/)。大致看下这篇简介也有帮助：[MongoDB 极简实践入门](https://github.com/StevenSLXie/Tutorials-for-Web-Developers/blob/master/MongoDB%20极简实践入门.md)

接下来我门来不全 `DoubanFilm`类中的`save_to_db`函数。

先在开头加载库。

```python
from pymongo import MongoClient # mongodb API
import datetime # 用于加入update时间戳
import hashlib # hash函数库
```

这里需要注意的是我们最好给每天记录计算一个独一无二的_id，防止我们在多次运行爬虫后，反复插入同一个电影。我们利用`update_one`的`filter`来找到已有的电影。如果存在，就更新。如果不存在，就创建。

```python
MONGODB = MongoClient() # # connnet to the default mongodb
def save_to_db(self):
  id = hashlib.sha1(self.data['name'].encode('utf-8')).hexdigest() # compute the unique id using sha1 hashing
  self.data['update_time'] = datetime.datetime.now() # update the update time
  self.data['_id'] = id # insert id into data
  mongodb['douban']['films'].update_one(
      filter={'_id': id }, # find the film with the id
      update={'$set': self.data }, # pass the data
      upsert=True # create if the document does not exist
      )
```

然后将之前的write_to_json注释了，使用我们新的write_to_db

```python
def start(self):
  ...
  for ...
  	for ...
      ...
			# self._write_to_json(film)
			film.save_to_db()
```

运行

```
python run.py
```

结束后，登陆mongodb，查询数据。

```
> db.films.find({name: '肖申克的救赎 The Shawshank Redemption'})
{ "_id" : "767b93c5a76d091a3a28a7fa88000ca28120fe06", "actors" : "蒂姆·罗宾斯 / 摩根·弗里曼 / 鲍勃·冈顿 / 威廉姆·赛德勒 / 克兰西·布朗 / 吉尔·贝罗斯 / 马克·罗斯顿 / 詹姆斯·惠特摩 / 杰弗里·德曼 / 拉里·布兰登伯格 / 尼尔·吉恩托利 / 布赖恩·利比 / 大卫·普罗瓦尔 / 约瑟夫·劳格诺 / 祖德·塞克利拉 / 保罗·麦克兰尼 / 芮妮·布莱恩 / 阿方索·弗里曼 / V·J·福斯特 / 弗兰克·梅德拉诺 / 马克·迈尔斯 / 尼尔·萨默斯 / 耐德·巴拉米 / 布赖恩·戴拉特 / 唐·麦克马纳斯", "country" : "美国", "directors" : "弗兰克·德拉邦特", "name" : "肖申克的救赎 The Shawshank Redemption", "rank" : "No.1", "rating" : "9.7", "release_date" : "1994-09-10(多伦多电影节) / 1994-10-14(美国)", "type" : "剧情 / 犯罪", "update_time" : ISODate("2020-05-06T15:39:25.524Z"), "writers" : "弗兰克·德拉邦特 / 斯蒂芬·金" }
```

### 反爬虫机制的应对

###  Docker部署

