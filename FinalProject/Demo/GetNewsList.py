import logging
import pymysql

# 假设你的配置正常导入
from newsapi.Spider.settings import DB_HOST, DB_USER, DB_PASSWD, DB_NAME, DB_PORT

class GetNewsList:
    def __init__(self, _type):
        self._type = _type
        # 优化3：不在初始化时建立连接，避免连接长时间闲置和泄露

    def get_connection(self):
        # 每次调用时生成一个新的短连接
        return pymysql.Connect(
            host=DB_HOST, 
            user=DB_USER, 
            password=DB_PASSWD, 
            database=DB_NAME, 
            port=DB_PORT,
            charset='utf8',
            # 强烈建议加上这行：让查询结果变成字典（带有字段名），而不是纯元组，更方便后续算法读取
            cursorclass=pymysql.cursors.DictCursor 
        )

    def getDataList(self):
        # 优化2：将初始值设为空列表 []，保证失败时外部调用也不会报 TypeError
        newslist = [] 
        # 修复SQL注入风险：使用参数化查询占位符
        sql = 'select * from news_api_newsdetail where category=%s'
        
        db = None
        cursor = None
        
        try:
            db = self.get_connection()
            cursor = db.cursor()
            # 修复SQL注入风险：将参数作为元组传递给 execute
            cursor.execute(sql, (self._type,))
            newslist = cursor.fetchall()
            
        except Exception as e:
            # 打印具体的报错信息，方便排查问题，而不是笼统的 "Demo Error"
            logging.error(f"Database Query Error: {e}")
            
        finally:
            # 优化3：无论 try 中的代码是否报错，finally 都会严格执行关闭操作
            if cursor:
                cursor.close()
            if db:
                db.close()
                
        return newslist


if __name__ == '__main__':
    newslist_helper = GetNewsList(_type=1)
    results = newslist_helper.getDataList()
    print(f"共获取到 {len(results)} 条数据。")