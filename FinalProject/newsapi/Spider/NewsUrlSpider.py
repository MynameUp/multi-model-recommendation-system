# -*- coding: utf-8 -*-
import datetime
import logging
import os
from logging.handlers import TimedRotatingFileHandler

import requests, re, pymysql
from apscheduler.schedulers.blocking import BlockingScheduler

from Spider.OperationMysql import OperationMysql

# --- 日志系统优化 ---
logger = logging.getLogger("UrlSpider")
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)-7s - %(message)s')

log_file_handler = TimedRotatingFileHandler(
    filename="Spider/Urllogs/log.log",
    when="D",           # 按天滚动
    interval=1,         # 间隔1天
    backupCount=30,     # 保留30个文件
    encoding='utf-8'    # 防止中文乱码
)
log_file_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(log_file_handler)

def urlcollect(lid):
    """
    使用新浪新闻 API 进行 URL 采集，自动去重入库
    """
    # 自动管理数据库连接的生命周期
    with OperationMysql() as op_mysql:
        url = f'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid={lid}&num=50' 
        
        try:
            result = requests.get(url, timeout=10) 
            result.encoding = 'utf-8' 
            urls = re.findall(r'"url":"(.*?)"', result.text)    
            
            changedict = {
                "2518": 0, "2510": 1, "2511": 2, "2669": 3, "2512": 4, 
                "2513": 5, "2514": 6, "2515": 7, "2516": 8, "2517": 9
            }
            news_type = changedict.get(str(lid))
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # 💡 核心修改点：加入 IGNORE 关键字，让 MySQL 在引擎层直接抛弃重复数据！
            sql_i = "INSERT IGNORE INTO news_api_urlcollect(url, type, time) values (%s, %s, %s)"
            
            for u in urls:
                clean_url = u.replace('\\', '')
                
                # 如果插入成功（即不是重复数据），is_new 才会是 True
                is_new = op_mysql.execute(sql_i, (clean_url, news_type, current_date))
                
                if is_new:
                    logger.info(f"🆕 新闻入库成功: {clean_url}")
                    
        except Exception as e:
            logger.error(f"获取 URL 列表异常, lid: {lid}, 错误: {e}")

sched = BlockingScheduler()
def begincollect(time):
    time = int(time)
    try:
        sched.add_job(urlcollect, 'interval', max_instances=1, seconds=time, id='urlcollect1', kwargs={"lid": "2510"})
        sched.add_job(urlcollect, 'interval', max_instances=1, seconds=time, id='urlcollect2', kwargs={"lid": "2511"})
        sched.add_job(urlcollect, 'interval', max_instances=1, seconds=time, id='urlcollect3', kwargs={"lid": "2669"})
        sched.add_job(urlcollect, 'interval', max_instances=1, seconds=time, id='urlcollect4', kwargs={"lid": "2512"})
        sched.add_job(urlcollect, 'interval', max_instances=1, seconds=time, id='urlcollect5', kwargs={"lid": "2513"})
        sched.add_job(urlcollect, 'interval', max_instances=1, seconds=time, id='urlcollect6', kwargs={"lid": "2514"})
        sched.add_job(urlcollect, 'interval', max_instances=1, seconds=time, id='urlcollect7', kwargs={"lid": "2515"})
        sched.add_job(urlcollect, 'interval', max_instances=1, seconds=time, id='urlcollect8', kwargs={"lid": "2516"})
        sched.add_job(urlcollect, 'interval', max_instances=1, seconds=time, id='urlcollect9', kwargs={"lid": "2517"})
        sched.add_job(urlcollect, 'interval', max_instances=1, seconds=time, id='urlcollect10', kwargs={"lid": "2518"})
        
        pid = os.getpid()
        with open(file='urlSpider.txt', mode='w') as f1:
            f1.write(str(pid))
            
        sched.start()
    except Exception as e:
        logger.error('调度器启动错误:' + str(e))

def endsched():
    try:
        sched.shutdown()
    except Exception as e:
        logger.info("Url爬虫调度器原本未运行或已关闭，忽略此操作。")
        pass