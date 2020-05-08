# Douban Film Top 250 Crawler

The script pulls the Top 250 films from [douban](https://movie.douban.com/top250).

## Requirements

- python3
- pip

Install `BeautifulSoup` for parsing html.

```shell
$ pip install beautifulsoup4
```

## Usage

```shell
$ git clone https://github.com/alfmunny/douban-film-crawler.git
$ cd douban-film-crawler
$ python run.py
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
- [x] 三：[抓取图片](#抓取图片)
- [x] 四：[搞个Docker部署呗](#Docker部署)
- [ ] 五：反爬机制和如何应对

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
$ brew tap mongodb/brew
$ brew install mongodb-community@4.2
$ brew services start mongodb-community@4.2
```

如何在Windows上安装，请看https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/

安装 python的mongodb API：pymongo

```
$ pip install pymongo
```

我们先试试看登陆mongodb，学习简单操作一下数据库。

登陆

```shell
$ mongo
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
    title: 'Unforgiven',
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

接下来我门来补全 `DoubanFilm`类中的`save_to_db`函数。

先在开头加载库。

```python
from pymongo import MongoClient # mongodb API
import datetime # 用于加入update时间戳
import hashlib # hash函数库
```

这里需要注意的是我们最好给每个记录计算一个独一无二的_id，防止我们在多次运行爬虫后，反复插入同一个电影。我们利用`update_one`的`filter`来找到已有的电影。如果存在，就更新。如果不存在，就创建。

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
  # self._write_to_json(film)
  film.save_to_db()
```

运行

```
$ python run.py
```

结束后，登陆mongodb，查询数据。

```
> db.films.find({name: '肖申克的救赎 The Shawshank Redemption'})
{ "_id" : "767b93c5a76d091a3a28a7fa88000ca28120fe06", "actors" : "蒂姆·罗宾斯 / 摩根·弗里曼 / 鲍勃·冈顿 / 威廉姆·赛德勒 / 克兰西·布朗 / 吉尔·贝罗斯 / 马克·罗斯顿 / 詹姆斯·惠特摩 / 杰弗里·德曼 / 拉里·布兰登伯格 / 尼尔·吉恩托利 / 布赖恩·利比 / 大卫·普罗瓦尔 / 约瑟夫·劳格诺 / 祖德·塞克利拉 / 保罗·麦克兰尼 / 芮妮·布莱恩 / 阿方索·弗里曼 / V·J·福斯特 / 弗兰克·梅德拉诺 / 马克·迈尔斯 / 尼尔·萨默斯 / 耐德·巴拉米 / 布赖恩·戴拉特 / 唐·麦克马纳斯", "country" : "美国", "directors" : "弗兰克·德拉邦特", "name" : "肖申克的救赎 The Shawshank Redemption", "rank" : "No.1", "rating" : "9.7", "release_date" : "1994-09-10(多伦多电影节) / 1994-10-14(美国)", "type" : "剧情 / 犯罪", "update_time" : ISODate("2020-05-06T15:39:25.524Z"), "writers" : "弗兰克·德拉邦特 / 斯蒂芬·金" }
```

### 抓取图片

每一部电影都有一幅海报，我们同样可以抓取下来。

import urllib。无需安装，官方包。用来下载图片。

```python
import urllib.request as urllib
```

添加图片信息

```python
def get_film(self, film_page):
    ...
    ...
    film.data['img'] = soup.find_all('div', id='mainpic')[0].find_all('img')[0]['src']
```
在初始化时创建储存图片的文件夹`images/`

```python
def __creat_image_dir(self):
    if not os.path.exists(self.image_dir):
      os.mkdir(self.image_dir)
      print("Directory", self.image_dir, " created")
```

```python
class DouBanFilm250Crawler(Crawler):
    def __init__(self):
        ...
        self.__creat_image_dir()
```

在DoubanFilm类中实现图片储存的方法`save_img()`

```python
def save_img(self, directory):
    print("Poster saved int to {0}/".format(directory))
    urllib.urlretrieve(self.data['img'], "./{0}/{1}.jpg".format(directory, self.data['name']))
```

最后把`save_img()`添加到主抓取循环中

```python
def start(self, page_limit=100):
    ...
    film.save_img(self.image_dir)
```

运行程序，现在可以看到电影海报都被抓取到了当前的images文件夹。

###  Docker部署

目标：把爬虫和数据库分别部署在两个容器内。并让他们互相通信，存储信息。

#### 第一步 部署数据库mongodb

指定我们要使用的镜像`mongo`，run起来。如果本地没用mongo镜像，docker会自动从Docker Hub上下载。

```shell
$ docker run -p 4001:27017 --name crawler-mongo -d mongo
```

解释一下参数

`-p`: 指定端口。因为mongodb是默认跑在容器内部的端口27017上的，我们把它和映射到我们主机的端口4001。这样我也可以从外部通过访问4001访问mongodb了。可以试一下`mongo --port 4001`。你应该可以成功登陆容器内的mongodb了

`--name`: 给你的容器取个名字

`-d`: 以daemon形式启动容器。这样容器就是一个跑在后台的service了。

查看下你的容器

```bash
$ docker ps
```

```
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                     NAMES
f78ffdc9793b        mongo               "docker-entrypoint.s…"   About an hour ago   Up About an hour    0.0.0.0:4001->27017/tcp   crawler-mongo

```

#### 第二部 部署爬虫

我们先来准备一下如何python的requirements.txt文件。待会容器内可以使用它来自动下载你需要的python包。

我们一共就需要4个包

```
beautifulsoup4==4.6.0
requests==2.22.0
pymongo==3.10.1
urllib3==1.24.2
```

我们需要通过Dockerfile来配置容器。docker会自动读取本目录下的Dockerfile来制作镜像。

```dockerfile
FROM python:3 		# 使用什么镜像，从Docker Hub上下载

WORKDIR /usr/src/app  # 在容器中的工作目录，指定后，后面的操作都会在此目录下
COPY requirements.txt ./ # 复制requirements文件
RUN pip install --no-cache-dir -r requirements.txt # 通过requirements文件下载所需的python包
COPY crawler.py run.py ./ # 复制python程序到工作目录

CMD [ "python", "./run.py" ] # 在容器内运行
```

保存在`Dockerfile`。开始制作镜像。

```bash
$ docker build -t douban-crawler .
```

最后那个点别忽略，是说在本目录制作。`-t` 是tag的意思，我们给容器打上`douban-crawler `的名字标签，待会就可以用这个名字来启动它。docker会根据你的Dockerfile下载并配置好镜像。

在启动镜像之前，我们最好配置一下网络。因为我们必须保证他和mongodb跑在同一个网络，才可以通过IP地址来连接它。我们先创建一个网络。

```bash
$ docker create network crawler
```

查看一下，可以看到新建的网络。

```bash
$ docker network ls
NETWORK ID          NAME                         DRIVER              SCOPE
92a8f572284b        bridge                       bridge              local
aaf658a2ca2e        crawler                      bridge              local
1f40716b60ad        host                         host                local
```

将我们刚才跑起来的数据库连上这个网络。

```bash
$ docker network connect crawler crawler-mongo
```

查看一下网络情况

```bash
$ docker inspect network crawler
[
    {
        "Name": "crawler",
        "Id": "aaf658a2ca2e5710a8cd8843d26053578dc2449710892ed6d9d361f5d7c4f379",
        "Created": "2020-05-08T18:36:50.5939359Z",
        "Scope": "local",
        "Driver": "bridge",
					....
					....
        "Containers": {
            "f78ffdc9793b80d2b77aef9f0a2e4b5a80e0ec1df85041405140fb160e2ee5ff": {
                "Name": "crawler-mongo",
                "EndpointID": "c3a6ad16a1be645586784e7418c54e1971b5aa3dcb73478ea9293aadd7e0129f",
                "MacAddress": "02:42:ac:14:00:02",
                "IPv4Address": "172.20.0.2/16",
                "IPv6Address": ""
            }
        },
    }
]
```

可以看见Containers里面已经包括了我们的数据库容器`crawler-mongo`。

修改crawler.py里的数据库连接地址。我们不需要知道数据库容器的IP地址(虽然我们刚才已经通过inspect查看到)，docker可以解析在同一个网络下的容器的IP，通过他们的名字。所以只需要改成如下。

```python
MONGODB = MongoClient(host="mongodb://crawler-mongo", port=27017) # mongodb的容器名字和它在容器内部的端口
```

好，万事俱备，我们启动爬虫的容器，使用刚才通过Dockerfile制作的镜像。

```
$ docker run -it --rm -v ${PWD}:/usr/src/app --network crawler --name crawler-app douban-crawler
```

`-it`: 是 interactive terminal的意思，启动后我们将会进入容器的交互终端

`--rm`: 退出容器是自动删除容器

`-v`: volumes选项，可以把本机上的文件位置挂载到容器内部的位置。这里这样的目的是我们的爬虫有下载图片到images文件夹。但是当爬虫跑在容器内部，images文件夹也在容器里。我们从外面看不见。你需要进入到容器内部查看。而且如果指定了`--rm`会在运行后删除容器。我们通过挂载本地的文件系统到容器内部的app的工作目录，那么images就会直接写入我们本地的文件夹，实现了同步的效果。这算是一种让保存数据的常用方法。

其实这里还有一个作用，我们刚才在crawler.py里修改了端口。本应该重新docker build这个镜像。但是通过挂载，容器内部也使用了最新的crawler.py文件。所以省去了从新build的步骤。

`--network`: 指定网络，别忘了我们需要app和数据库在同一个网络才能通信。

现在可以看到容器在运行，以及他的输出.

```
Start fetching films from douban top 250
===============================================
Processing page: https://movie.douban.com/subject/1292052/...
Film processed: 肖申克的救赎 The Shawshank Redemption
Data saved with id 767b93c5a76d091a3a28a7fa88000ca28120fe06
Poster saved int to images/
Processing page: https://movie.douban.com/subject/1291546/...
Film processed: 霸王别姬
Data saved with id c8ef1e21bbf697c997957ec09a27524aaf059edf
Poster saved int to images/
```

你也可以通过-d来启动容器，那么容器就会在后台。可以通过docker ps查看

```bash
$ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                     NAMES
5df1741310a2        douban-crawler      "python ./run.py"        2 seconds ago       Up 1 second                                   crawler-app
f78ffdc9793b        mongo               "docker-entrypoint.s…"   2 hours ago         Up 2 hours          0.0.0.0:4001->27017/tcp   crawler-mongo
```

爬一会，我们结束容器。

```bash
$ docker kill crawler-app
```

#### 成果

来查看下成果

1. 你可以在本地看到images文件夹被建立，里面是爬下来的文件
2. 通过登陆暴露在4001的端口，我们也可连接mongodb。查看电影信息。

```
$ mongo --port 4001
> use douban
> db.films.find()
{ "_id" : "767b93c5a76d091a3a28a7fa88000ca28120fe06", "actors" : "蒂姆·罗宾斯 / 摩根·弗里曼 / 鲍勃·冈顿 / 威廉姆·赛德勒 / 克兰西·布朗 / 吉尔·贝罗斯 / 马克·罗斯顿 / 詹姆斯·惠特摩 / 杰弗里·德曼 / 拉里·布兰登伯格 / 尼尔·吉恩托利 / 布赖恩·利比 / 大卫·普罗瓦尔 / 约瑟夫·劳格诺 / 祖德·塞克利拉 / 保罗·麦克兰尼 / 芮妮·布莱恩 / 阿方索·弗里曼 / V·J·福斯特 / 弗兰克·梅德拉诺 / 马克·迈尔斯 / 尼尔·萨默斯 / 耐德·巴拉米 / 布赖恩·戴拉特 / 唐·麦克马纳斯", "country" : "美国", "directors" : "弗兰克·德拉邦特", "img" : "https://img9.doubanio.com/view/photo/s_ratio_poster/public/p480747492.jpg", "name" : "肖申克的救赎 The Shawshank Redemption", "rank" : "No.1", "rating" : "9.7", "release_date" : "1994-09-10(多伦多电影节) / 1994-10-14(美国)", "type" : "剧情 / 犯罪", "update_time" : ISODate("2020-05-08T20:13:10.916Z"), "writers" : "弗兰克·德拉邦特 / 斯蒂芬·金" }
{ "_id" : "c8ef1e21bbf697c997957ec09a27524aaf059edf", "actors" : "张国荣 / 张丰毅 / 巩俐 / 葛优 / 英达 / 蒋雯丽 / 吴大维 / 吕齐 / 雷汉 / 尹治 / 马明威 / 费振翔 / 智一桐 / 李春 / 赵海龙 / 李丹 / 童弟 / 沈慧芬 / 黄斐 / 徐杰", "country" : "中国大陆 / 中国香港", "directors" : "陈凯歌", "img" : "https://img9.doubanio.com/view/photo/s_ratio_poster/public/p2561716440.jpg", "name" : "霸王别姬", "rank" : "No.2", "rating" : "9.6", "release_date" : "1993-01-01(中国香港) / 1993-07-26(中国大陆)", "type" : "剧情 / 爱情 / 同性", "update_time" : ISODate("2020-05-08T20:13:12.717Z"), "writers" : "芦苇 / 李碧华" }
```

#### 整合

我们可以看到之前为了制作，配置网络，启动，是一个颇为繁琐的过程。

我们可以通过`docker-compose`工具来全自动地完成这些动作，大大地简化部署。

先kill掉之前的容器，防止ip被占用等一些其他的情况，安全起见。如果后台还在跑crawler-app也关掉。

```
$ docker kill crwaler-mongo
$ docker kill crawler-app 
```

通过配置`docker-compose.yaml`来实现自动化部署。

```docker-compose.yml
services:
	crawler-mongo:
		image: mongo     	# 镜像名字
		ports:							
			- "4002:27017" 	# 这里使用4002，是因为如果没有kill之前的mongodb容器，那么4001已经被占用，会报错。
	crawler-app:     
		build: .					 # 使用Dockerfile制作镜像
		volumes:	
			- .:/usr/src/app	
		depends_on:
			- crawler-mongo	#	依赖数据库。crawler-app会在mongo启动后运行。
```

你可能注意到这里并没有指定他们的网络。那是因为docker-compose会自动创建一个以当前项目文件夹的名字加上`_default`为名的网络，然后有所的services都加入都同一个网络下面，不需要手动配置。

现在只需要执行

```bash
$ docker-compose up -d
```

两个容器都已经在后台运行了。完成了上一章的所有动作。

查看一下网络。 顺便删除之前手工创建的网络。

```bash
$ docker network ls
NETWORK ID          NAME                         DRIVER              SCOPE
92a8f572284b        bridge                       bridge              local
aaf658a2ca2e        crawler                      bridge              local
494fbe3674c4        douban-crawler_default       bridge              local
1f40716b60ad        host                         host                local
$ docker network rm crawler
```

查看一下容器

```bash
$ docker ps
CONTAINER ID        IMAGE                        COMMAND                  CREATED             STATUS              PORTS                     NAMES
c3fb64f1e357        douban-crawler_crawler-app   "python ./run.py"        27 minutes ago      Up 2 seconds                                  douban-crawler_crawler-app_1
816eadab6a57        mongo                        "docker-entrypoint.s…"   27 minutes ago      Up 3 seconds        0.0.0.0:4001->27017/tcp   douban-crawler_crawler-mongo_1
```

两个容器的名字都是docker-compose根据配置自动取的，特别长。我们也可以使用他们的ID来查看。是一样的。比如使用python程序运行容器的ID：`c3fb64f1e357`。

通过查看日志来了解程序运行情况。

 ```bash
$ docker logs c3fb64f1e357
Poster saved int to images/Start fetching films from douban top 250
===============================================
Processing page: https://movie.douban.com/subject/1292052/...
Film processed: 肖申克的救赎 The Shawshank Redemption
Data saved with id 767b93c5a76d091a3a28a7fa88000ca28120fe06
... ...
 ```

只差看近三十分钟

```bash
$ docker logs --since 30m c3fb64f1e357
```

实时查看

```bash
$ docker logs -f c3fb64f1e357
```

关闭容器，但不删除容器。

```bash
$ docker-compose stop
```

如果想要停止并且删除容器。

```bash
$ docker-compose down	
```



### 反爬虫机制的应对

