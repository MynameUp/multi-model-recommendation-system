import pymysql
import logging

# 配置日志，方便控制输出
logger = logging.getLogger("OperationMysql")

class OperationMysql:
    def __init__(self):
        try:
            self.conn = pymysql.connect(
                host='127.0.0.1',
                port=3306,
                user='root',
                password='123456',
                db='news',
                charset='utf8mb4', # 支持 Emoji 等特殊字符
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False    # 建议手动控制 commit 保证原子性
            )
            self.cur = self.conn.cursor()
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            self.conn = None

    # 实现上下文管理器，支持 with 语句自动释放连接
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def search_all(self, sql, args=None):
        """通用查询"""
        if not self.conn: return []
        try:
            self.cur.execute(sql, args)
            return self.cur.fetchall()
        except Exception as e:
            logger.error(f"查询出错: {e}")
            return []

    # 💡 终极优化：执行增删改，并智能判断是否真正插入了数据
    def execute(self, sql, args=None, silent_duplicate=True):
        if not self.conn: return False
        try:
            # cur.execute 会返回受影响的行数
            affected_rows = self.cur.execute(sql, args)
            self.conn.commit()
            
            # 如果是 INSERT IGNORE 且遇到了重复数据，受影响行数为 0，则返回 False
            return affected_rows > 0
            
        except pymysql.err.IntegrityError as e:
            self.conn.rollback()
            if silent_duplicate and e.args[0] == 1062:
                # 静默处理主键冲突，不打印 Error 日志
                return False 
            logger.error(f"数据完整性错误: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"执行 SQL 出错: {e}")
            return False

    def close(self):
        """释放资源"""
        try:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()
        except Exception:
            pass