Scrapy是一个流行的网络爬虫框架，它拥有狠毒简化网站爬取的高级函数．在这篇文章中，我们将学习使用Srapy抓取示例网站．

### 1. 安装

```
pip install Scrapy
```
由于Scrapy依赖一些外部库，因此如果在安装过程中遇到困难的话，可以从官方网站上获取更多信息(https://docs.scrapy.org/en/latest/intro/install.html)

如果Scrapy安装成功，那么就可以在终端执行`Scrapy`命令：
```
xiaosi@yoona:~$ scrapy -h
Scrapy 1.0.5.post4+g4b324a8 - no active project

Usage:
  scrapy <command> [options] [args]

Available commands:
  bench         Run quick benchmark test
  commands      
  fetch         Fetch a URL using the Scrapy downloader
  runspider     Run a self-contained spider (without creating a project)
  settings      Get settings values
  shell         Interactive scraping console
  startproject  Create new project
  version       Print Scrapy version
  view          Open URL in browser, as seen by Scrapy

  [ more ]      More commands available when run from project directory

Use "scrapy <command> -h" to see more info about a command

```

### 2. 启动安装

安装好Scrapy以后，我们可以运行`startproject`命令生成该项目的默认结构．具体步骤为：打开终端进入想要存储Scrapy项目的目录(在这我们使用Scrapy_demo作为项目名称)，然后运行如下命令：
```
xiaosi@yoona:~/code/scrapy_demo$ scrapy startproject scrapy_demo
New Scrapy project 'scrapy_demo' created in:
    /home/xiaosi/code/scrapy_demo/scrapy_demo

You can start your first spider with:
    cd scrapy_demo
    scrapy genspider example example.com
```
进入爬虫项目目录下，我们可以查看生成的文件结构：
```
xiaosi@yoona:~/code/scrapy_demo/scrapy_demo$ tree 
.
├── scrapy.cfg
└── scrapy_demo
    ├── __init__.py
    ├── items.py
    ├── pipelines.py
    ├── settings.py
    └── spiders
        └── __init__.py
```
其中，比较重要的几个文件如下：

文件名 | 说明
---|---
items.py | 定义了待抓取域的模型
settings.py | 定义了一些设置，如用户代理，爬取延迟等
spiders/: | 该目录ｕｃ拿出实际的爬虫代码
scrapy.cfg | 设置项目配置
pipelines.py | 处理要抓取的域

#### 2.1 定义模型

默认情况下，scrapy_demo/items.py文件下包含如下代码：
```
# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapyDemoItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

```
ScrapyDemoItem类是一个模板，需要将其中的内容替换为爬虫运行时想要存储的待抓取的信息，我们以抓取马蜂窝()目的地为例：
```

```
