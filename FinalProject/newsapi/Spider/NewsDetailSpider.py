# -- coding: utf-8 --
import logging
import os
import time

from logging.handlers import TimedRotatingFileHandler

import requests, re
from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions # 💡 明确指定 Edge 的 Options
from selenium.webdriver.edge.service import Service

from Spider.OperationMysql import OperationMysql

# --- 日志系统优化 ---
logger = logging.getLogger("DetailSpider")
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)-7s - %(message)s')

# 💡 修改这里：同步改为按天归档
log_file_handler = TimedRotatingFileHandler(
    filename="Spider/Detaillogs/log.log",
    when="D", 
    interval=1, 
    backupCount=30,
    encoding='utf-8'
)
log_file_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(log_file_handler)

# 3. 向logger对象中添加handler
logger.addHandler(log_file_handler)


def has_class_but_no_id(tag):
    return not tag.has_attr('class') and not tag.has_attr('id')


def getnewsdetail(url):
    try:
        result = requests.get(url, timeout=10)
        result.encoding = 'utf-8'
        soup = BeautifulSoup(result.content, features="html.parser")
        
        title = getnewstitle(soup)
        if not title: return None
        
        date = getnewsdate(soup)
        mainpage, orimainpage = getmainpage(soup)
        if not mainpage: return None
        
        pic_url = getnewspic_url(soup)
        
        # 💡 核心改动：把视频爬取放在子 try 里，防止它拖累全文
        videourl = []
        try:
            if 'playsinline' in result.text or 'video' in result.text.lower():
                videourl = getvideourl(url)
        except Exception as video_err:
            logger.warning(f"视频解析跳过: {video_err}")

        return {
            'mainpage': mainpage,
            'pic_url': pic_url,
            'title': title,
            'date': date,
            'videourl': videourl,
            'origin': str(orimainpage),
        }
    except Exception as e:
        logger.error(f"正文抓取致命失败: {url}, 错误: {e}")
        return None


def getmainpage(soup):
    '''
    @Description：获取正文部分的p标签内容
    @:param soup: BeautifulSoup对象
    @:return: (清洗后的全文, 原始标签列表)
    '''
    # 💡 1. 兼容多种容器 ID
    container = soup.find('div', id='article') or soup.find('div', id='artibody')
    
    if container is None:
        return None, None

    # 💡 2. 提取所有段落并清洗内容
    p_tags = container.find_all('p')
    cleaned_paragraphs = [
        p.get_text(strip=True).replace("\u3000", "").replace("\xa0", "").replace("新浪", "新闻")
        for p in p_tags
    ]

    # 💡 3. 使用 join 提升拼接效率
    text_all = "".join(cleaned_paragraphs)

    # 💡 4. 修复日志 Bug：确保你能看到正文内容
    if text_all:
        # 使用 f-string 彻底告别 mainpage:{} 的报错
        logger.info(f"成功提取正文 (长度: {len(text_all)}): {text_all[:50]}...") 
    
    return text_all, p_tags


def getnewspic_url(soup):
    '''
        @Description：获取正文部分的pic内容，网易对正文部分的图片内容通过div中class属性为“img_wrapper”
        @:param None
    '''
    pic = soup.find_all('div', class_='img_wrapper')
    pic_url = re.findall('src="(.*?)"', str(pic))
    for numbers in range(len(pic_url)):
        pic_url[numbers] = pic_url[numbers].replace("//", 'https://')
    logging.info("pic_url:{}".format(pic_url))
    return pic_url


def getnewsdate(soup):
    '''
        @Description：获取新闻的发布时间，网易对新闻的发布时间使用span的class属性为“date”
        @:param None
    '''
    if soup.find('span', class_='date') != None:
        date = str(soup.find('span', class_='date').text)
    else:
        date = str(soup.find('span', id="pub_date").text)
    logger.info("date:{}".format(date))
    return date


def getnewstitle(soup):
    '''
        @Description：获取新闻的标题，网易对新闻的标题使用h1的class属性为“main-title”
        @:param None
    '''
    if soup.find('h1', class_='main-title') != None:
        title = soup.find('h1', class_='main-title').text
    elif soup.find('h1', id='artibodyTitle') != None:
        title = soup.find('h1', id='artibodyTitle').text
    else:
        return None
    logger.info("title:{}".format(title))
    return title


def getvideourl(url):
    driver = None
    video_url = []
    try:
        edge_options = EdgeOptions() 
        edge_options.add_argument('--headless')
        edge_options.add_argument('--disable-gpu')
        edge_options.add_argument('--mute-audio')
        edge_options.add_argument('blink-settings=imagesEnabled=false')
        
        service = Service(executable_path='msedgedriver.exe')
        driver = webdriver.Edge(service=service, options=edge_options)
        
        driver.get(url)
        regex1 = re.compile('playsinline="playsinline" src="(.*?)"')
        video_url = regex1.findall(driver.page_source)
        video_url = [v.replace("amp;", "") for v in video_url]
        
    except Exception as e:
        # 💡 这里只记录错误，不抛出异常，让主程序继续
        logger.error(f"WebDriver 解析视频失败 (非致命): {e}")
        return [] # 返回空列表
    finally:
        if driver:
            driver.quit()
    return video_url


def getdatabaseurl():
    op_mysql = OperationMysql()
    try:
        searchresult = op_mysql.search_all('select url, type from news_api_urlcollect where handle=0')
        if len(searchresult) == 0:
            logger.warning(" No such url to get detail")
            return None
        else:
            logger.info("Got All Url")
            return searchresult
    finally:
        # 无论成功还是失败，最后强制关闭连接！
        op_mysql.conn.close()


# def insertdatabase(news, geturl, Type):
#     op_mysql = OperationMysql()
#     url = geturl['url']
#     try:
#         # 💡 核心优化：使用元组传参，PyMySQL 会自动处理 mainpage 里的引号问题！[cite: 1]
#         insert_sql = """
#             INSERT INTO news_api_newsdetail
#             (url, title, date, pic_url, videourl, mainpage, category, readnum, comments, origin) 
#             VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 0, %s)
#         """
#         args = (url, news['title'], news['date'], str(news['pic_url']), 
#                 str(news['videourl']), news['mainpage'], Type, news['origin'])
        
#         op_mysql.insert_one(insert_sql, args)
        
#         # 状态更新
#         op_mysql.update_one("UPDATE news_api_urlcollect SET handle=1 WHERE url=%s", (url,))
#         logger.info(f"新闻入库成功: {news['title']}")
        
#     except Exception as e:
#         logger.error(f"数据库操作失败: {url}, 错误: {e}")
#     finally:
#         op_mysql.close() # 💡 确保连接释放，防止连接数爆掉[cite: 1]


# def deleteurl(url_dict):
#     """💡 优化：删除无效URL，也使用参数化查询"""
#     op_mysql = OperationMysql()
#     try:
#         sql = "DELETE FROM news_api_urlcollect WHERE url=%s"
#         op_mysql.delete_one(sql, (url_dict['url'],))
#     finally:
#         op_mysql.close()


# Spider/NewsDetailSpider.py

def insertalldetial():
    with OperationMysql() as db:
        # 1. 查找所有未处理的 URL
        sql_s = "SELECT * FROM news_api_urlcollect WHERE handle=0"
        results = db.search_all(sql_s)
        
        if not results:
            logger.info("当前无待处理 URL")
            return

        for row in results:
            url = row['url']
            # 注意：采集表里存的是 type，对应详情表里的 category
            news_category = row['type'] 
            
            detail_data = getnewsdetail(url)
            
            if detail_data:
                # 💡 核心修改：严格对应 DESC 出来的字段名和数量
                # 我们按照表结构顺序排列：url, title, date, pic_url, videourl, mainpage, category, readnum, comments, origin
                sql_insert = """
                    INSERT INTO news_api_newsdetail (
                        url, title, date, pic_url, videourl, 
                        mainpage, category, readnum, comments, origin
                    ) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # 💡 对应参数：确保 readnum 和 comments 初始为 0
                args = (
                    url,                                # url
                    detail_data['title'],               # title
                    detail_data['date'],                # date
                    str(detail_data['pic_url']),        # pic_url
                    str(detail_data['videourl'])[:255], # videourl (强制截断，防止超出 255 长度)
                    detail_data['mainpage'],            # mainpage
                    news_category,                      # category (对应数据库列名)
                    0,                                  # readnum (必填)
                    0,                                  # comments (必填)
                    detail_data['origin']               # origin
                )
                
                # 执行插入
                if db.execute(sql_insert, args):
                    # 5. 更新采集表状态
                    db.execute("UPDATE news_api_urlcollect SET handle=1 WHERE url=%s", (url,))
                    logger.info(f"新闻入库成功: {detail_data['title']}")
            else:
                # 彻底解析失败的链接，清理掉
                db.execute("DELETE FROM news_api_urlcollect WHERE url=%s", (url,))
                logger.warning(f"无效URL已从任务中删除: {url}")


# --- 调度系统 ---
sched = BlockingScheduler()

def begindetailcollect(time):  # 💡 统一参数名为 time
    """启动详情爬虫调度器"""
    try:
        # 将传入的 time 转换为整数并设置给调度任务
        sched.add_job(insertalldetial, 'interval', max_instances=1, seconds=int(time), id='detailcollect1')
        
        # 记录PID供关闭使用
        pid = os.getpid()
        with open('detailSpider.txt', 'w') as f:
            f.write(str(pid))
            
        # 💡 这里也使用参数 time
        logger.info(f"详情爬虫已启动，间隔: {time}s，PID: {pid}")
        sched.start()
    except Exception as e:
        logger.error(f"启动详情爬虫失败: {e}")


def endsched():
    """停止调度器"""
    try:
        sched.shutdown()
        logger.info("调度器已成功关闭")
    except Exception:
        logger.info("调度器未运行，无需关闭")
