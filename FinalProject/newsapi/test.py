# -*- coding: utf-8 -*-
"""
数据库访问演示 Demo
基于 multi-model-recommendation-system 项目
功能：展示如何访问和操作新闻推荐系统的数据库
"""

import pymysql
from Spider.settings import DB_HOST, DB_USER, DB_PASSWD, DB_NAME, DB_PORT
from Spider.OperationMysql import OperationMysql


class DatabaseDemo:
    """数据库操作演示类"""

    def __init__(self):
        """初始化数据库连接"""
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        """
        连接到 MySQL 数据库
        :return: 连接对象
        """
        try:
            self.conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWD,
                database=DB_NAME,
                charset='utf8',
                cursorclass=pymysql.cursors.DictCursor  # 返回字典格式结果
            )
            self.cursor = self.conn.cursor()
            print("✓ 数据库连接成功")
        except Exception as e:
            print(f"✗ 数据库连接失败：{e}")
            raise

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✓ 数据库连接已关闭")

    # ==================== 查询操作 ====================

    def get_all_users(self):
        """获取所有用户信息"""
        sql = "SELECT userid, username, gender, ip, tags FROM news_api_user"
        self.cursor.execute(sql)
        users = self.cursor.fetchall()
        print(f"\n【所有用户】共 {len(users)} 条记录")
        for user in users[:5]:  # 只显示前 5 条
            gender = '男' if user['gender'] == 1 else '女'
            print(f"  - ID: {user['userid']}, 姓名：{user['username']}, 性别：{gender}")
        return users

    def get_user_by_id(self, userid):
        """
        根据用户 ID 查询用户详情
        :param userid: 用户 ID
        """
        sql = "SELECT * FROM news_api_user WHERE userid = %s"
        self.cursor.execute(sql, (userid,))
        user = self.cursor.fetchone()
        if user:
            print(f"\n【用户详情】ID: {userid}")
            print(f"  用户名：{user['username']}")
            print(f"  性别：{'男' if user['gender'] == 1 else '女'}")
            print(f"  IP 地址：{user['ip']}")
            print(f"  标签：{user['tags']}")
            print(f"  标签权重：{user['tagsweight']}")
        else:
            print(f"\n✗ 未找到用户 ID: {userid}")
        return user

    def get_news_by_category(self, category_id, limit=10):
        """
        按类别获取新闻
        :param category_id: 类别 ID (0-9)
        :param limit: 返回数量限制
        """
        category_names = {
            0: "美股", 1: "国内", 2: "国际", 3: "国际",
            4: "体育", 5: "娱乐", 6: "军事", 7: "科技",
            8: "财经", 9: "股市"
        }

        sql = """
            SELECT news_id, title, date, category, readnum, comments 
            FROM news_api_newsdetail 
            WHERE category = %s 
            ORDER BY news_id DESC 
            LIMIT %s
        """
        self.cursor.execute(sql, (category_id, limit))
        news_list = self.cursor.fetchall()

        print(f"\n【{category_names.get(category_id, '未知')} 类新闻】共 {len(news_list)} 条")
        for news in news_list:
            print(f"  - ID:{news['news_id']} 《{news['title']}》")
            print(f"    阅读：{news['readnum']}, 评论：{news['comments']}, 日期：{news['date']}")
        return news_list

    def get_hot_news(self, limit=10):
        """
        获取热门新闻（按热度排序）
        :param limit: 返回数量限制
        """
        sql = """
            SELECT n.news_id, n.title, n.readnum, n.comments, h.news_hot
            FROM news_api_newsdetail n
            INNER JOIN news_api_newshot h ON n.news_id = h.news_id
            ORDER BY h.news_hot DESC
            LIMIT %s
        """
        self.cursor.execute(sql, (limit,))
        hot_news = self.cursor.fetchall()

        print(f"\n【热门新闻 TOP{limit}】")
        for idx, news in enumerate(hot_news, 1):
            print(f"  {idx}. 《{news['title']}》")
            print(f"     热度值：{news['news_hot']}, 阅读：{news['readnum']}, 评论：{news['comments']}")
        return hot_news

    def get_user_recommendations(self, userid):
        """
        获取用户的推荐新闻
        :param userid: 用户 ID
        """
        sql = """
            SELECT r.newsid, r.cor, r.species, n.title, n.date
            FROM news_api_recommend r
            INNER JOIN news_api_newsdetail n ON r.newsid = n.news_id
            WHERE r.userid = %s AND r.hadread = 0
            ORDER BY r.cor DESC, r.time DESC
        """
        self.cursor.execute(sql, (userid,))
        recommendations = self.cursor.fetchall()

        print(f"\n【用户 {userid} 的推荐新闻】共 {len(recommendations)} 条")
        for rec in recommendations[:10]:
            species_map = {0: '标签推荐', 1: '热度推荐', 2: '城市推荐'}
            print(f"  - 《{rec['title']}》")
            print(f"    相关度：{rec['cor']}, 类型：{species_map.get(rec['species'], '未知')}")
        return recommendations

    def get_news_comments(self, newsid):
        """
        获取新闻的评论列表
        :param newsid: 新闻 ID
        """
        sql = """
            SELECT c.id, c.comments, c.time, c.status, u.username
            FROM news_api_comments c
            LEFT JOIN news_api_user u ON c.userid = u.userid
            WHERE c.newsid = %s AND c.status = '正常'
            ORDER BY c.time DESC
        """
        self.cursor.execute(sql, (newsid,))
        comments = self.cursor.fetchall()

        print(f"\n【新闻评论】共 {len(comments)} 条评论")
        for comment in comments[:5]:
            print(f"  - {comment['username']}: {comment['comments']}")
            print(f"    时间：{comment['time']}")
        return comments

    def get_user_history(self, userid):
        """
        获取用户浏览历史
        :param userid: 用户 ID
        """
        sql = """
            SELECT h.time, n.title, n.news_id
            FROM news_api_history h
            INNER JOIN news_api_newsdetail n ON h.history_newsid = n.news_id
            WHERE h.userid = %s
            ORDER BY h.time DESC
            LIMIT 20
        """
        self.cursor.execute(sql, (userid,))
        history = self.cursor.fetchall()

        print(f"\n【用户 {userid} 的浏览历史】共 {len(history)} 条")
        for record in history[:10]:
            print(f"  - 《{record['title']}》")
            print(f"    浏览时间：{record['time']}")
        return history

    # ==================== 统计查询 ====================

    def get_statistics(self):
        """获取系统统计数据"""
        stats = {}

        # 用户总数
        self.cursor.execute("SELECT COUNT(*) as count FROM news_api_user")
        stats['user_count'] = self.cursor.fetchone()['count']

        # 新闻总数
        self.cursor.execute("SELECT COUNT(*) as count FROM news_api_newsdetail")
        stats['news_count'] = self.cursor.fetchone()['count']

        # 评论总数
        self.cursor.execute("SELECT COUNT(*) as count FROM news_api_comments WHERE status = '正常'")
        stats['comment_count'] = self.cursor.fetchone()['count']

        # 推荐记录总数
        self.cursor.execute("SELECT COUNT(*) as count FROM news_api_recommend")
        stats['recommend_count'] = self.cursor.fetchone()['count']

        # 浏览历史总数
        self.cursor.execute("SELECT COUNT(*) as count FROM news_api_history")
        stats['history_count'] = self.cursor.fetchone()['count']

        print("\n【系统统计】")
        print(f"  用户总数：{stats['user_count']}")
        print(f"  新闻总数：{stats['news_count']}")
        print(f"  评论总数：{stats['comment_count']}")
        print(f"  推荐记录：{stats['recommend_count']}")
        print(f"  浏览历史：{stats['history_count']}")

        return stats

    def get_category_distribution(self):
        """获取新闻类别分布统计"""
        category_names = {
            0: "美股", 1: "国内", 2: "国际", 3: "国际",
            4: "体育", 5: "娱乐", 6: "军事", 7: "科技",
            8: "财经", 9: "股市"
        }

        sql = """
            SELECT category, COUNT(*) as count
            FROM news_api_newsdetail
            GROUP BY category
            ORDER BY category
        """
        self.cursor.execute(sql)
        result = self.cursor.fetchall()

        print("\n【新闻类别分布】")
        for row in result:
            cat_name = category_names.get(row['category'], '未知')
            print(f"  {cat_name} (ID:{row['category']}): {row['count']} 篇")

        return result

    # ==================== 增删改操作 ====================

    def add_test_user(self, userid, username, password, tags):
        """
        添加测试用户
        :param userid: 用户 ID
        :param username: 用户名
        :param password: 密码
        :param tags: 标签（逗号分隔）
        """
        try:
            # 检查用户是否已存在
            check_sql = "SELECT userid FROM news_api_user WHERE userid = %s"
            self.cursor.execute(check_sql, (userid,))
            if self.cursor.fetchone():
                print(f"✗ 用户 {userid} 已存在")
                return False

            # 插入新用户
            insert_sql = """
                INSERT INTO news_api_user 
                (userid, username, password, gender, ip, tags, tagsweight, region, headPortrait)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            tag_list = tags.split(',')
            tagsweight = {tag: 0.5 for tag in tag_list}

            self.cursor.execute(insert_sql, (
                userid, username, password, 1, '127.0.0.1',
                tags, str(tagsweight).replace("'", '"'), '北京',
                'https://example.com/default.jpg'
            ))
            self.conn.commit()
            print(f"✓ 成功添加用户：{username} (ID: {userid})")
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"✗ 添加用户失败：{e}")
            return False

    def update_user_tags(self, userid, new_tags):
        """
        更新用户标签
        :param userid: 用户 ID
        :param new_tags: 新标签（逗号分隔）
        """
        try:
            sql = "UPDATE news_api_user SET tags = %s WHERE userid = %s"
            self.cursor.execute(sql, (new_tags, userid))
            self.conn.commit()
            print(f"✓ 成功更新用户 {userid} 的标签")
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"✗ 更新标签失败：{e}")
            return False

    def delete_user(self, userid):
        """
        删除用户
        :param userid: 用户 ID
        """
        try:
            # 先删除相关记录
            self.cursor.execute("DELETE FROM news_api_history WHERE userid = %s", (userid,))
            self.cursor.execute("DELETE FROM news_api_recommend WHERE userid = %s", (userid,))
            self.cursor.execute("DELETE FROM news_api_comments WHERE userid = %s", (userid,))
            self.cursor.execute("DELETE FROM news_api_givelike WHERE userid = %s", (userid,))
            self.cursor.execute("DELETE FROM news_api_message WHERE userid = %s", (userid,))

            # 删除用户
            self.cursor.execute("DELETE FROM news_api_user WHERE userid = %s", (userid,))
            self.conn.commit()
            print(f"✓ 成功删除用户 {userid} 及其相关数据")
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"✗ 删除用户失败：{e}")
            return False

    # ==================== 高级查询 ====================

    def search_news(self, keyword):
        """
        模糊搜索新闻
        :param keyword: 搜索关键词
        """
        sql = """
            SELECT news_id, title, date, category, readnum
            FROM news_api_newsdetail
            WHERE title LIKE %s OR mainpage LIKE %s
            ORDER BY news_id DESC
            LIMIT 20
        """
        search_pattern = f"%{keyword}%"
        self.cursor.execute(sql, (search_pattern, search_pattern))
        results = self.cursor.fetchall()

        print(f"\n【搜索 '{keyword}'】找到 {len(results)} 条结果")
        for news in results[:10]:
            print(f"  - 《{news['title']}》")
            print(f"    阅读：{news['readnum']}, 日期：{news['date']}")
        return results

    def get_active_users(self, min_comments=5):
        """
        获取活跃用户（评论数超过指定值）
        :param min_comments: 最小评论数
        """
        sql = """
            SELECT u.userid, u.username, COUNT(c.id) as comment_count
            FROM news_api_user u
            LEFT JOIN news_api_comments c ON u.userid = c.userid
            GROUP BY u.userid, u.username
            HAVING comment_count >= %s
            ORDER BY comment_count DESC
        """
        self.cursor.execute(sql, (min_comments,))
        users = self.cursor.fetchall()

        print(f"\n【活跃用户 TOP10】（评论数 ≥ {min_comments}）")
        for idx, user in enumerate(users[:10], 1):
            print(f"  {idx}. {user['username']} (ID:{user['userid']}) - {user['comment_count']} 条评论")
        return users

    def get_daily_news_count(self, days=7):
        """
        获取最近 N 天的新闻发布统计
        :param days: 天数
        """
        sql = """
            SELECT DATE(time) as date, COUNT(*) as count
            FROM news_api_urlcollect
            WHERE time >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY DATE(time)
            ORDER BY date DESC
        """
        self.cursor.execute(sql, (days,))
        result = self.cursor.fetchall()

        print(f"\n【最近 {days} 天新闻采集统计】")
        for row in result:
            print(f"  {row['date']}: {row['count']} 篇")
        return result


def main():
    """主函数 - 演示各种数据库操作"""
    print("=" * 60)
    print("新闻推荐系统 - 数据库访问演示".center(60))
    print("=" * 60)

    # 创建 demo 实例
    demo = DatabaseDemo()

    try:
        # 1. 基础查询
        demo.get_all_users()
        demo.get_user_by_id('100000')  # 游客用户

        # 2. 新闻查询
        demo.get_news_by_category(category_id=7, limit=5)  # 科技类新闻
        demo.get_hot_news(limit=5)

        # 3. 推荐和历史记录
        demo.get_user_recommendations(userid='100000')
        demo.get_user_history(userid='100000')

        # 4. 评论查询
        demo.get_news_comments(newsid=1)

        # 5. 统计信息
        demo.get_statistics()
        demo.get_category_distribution()

        # 6. 搜索功能
        demo.search_news(keyword='科技')

        # 7. 活跃用户
        demo.get_active_users(min_comments=1)

        # 8. 数据统计
        demo.get_daily_news_count(days=7)

        # 9. 增删改操作演示（可选）
        # demo.add_test_user('test123', '测试用户', '123456', '科技，AI, 互联网')
        # demo.update_user_tags('test123', '科技，AI, 5G')
        # demo.delete_user('test123')

    except Exception as e:
        print(f"\n✗ 演示过程中发生错误：{e}")
    finally:
        # 关闭连接
        demo.close()
        print("\n" + "=" * 60)
        print("演示结束".center(60))
        print("=" * 60)


if __name__ == '__main__':
    main()
