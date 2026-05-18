# -*- coding: utf-8 -*-
"""
快速检查和初始化向量数据
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsServer.settings')

# 确保日志目录存在（必须在 django.setup() 之前）
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)
    print(f"[OK] 创建日志目录: {log_dir}")

import django
django.setup()
import django
django.setup()
from news_api.models import newsdetail
from news_api.qa_models import NewsVector
from Recommend.NewsQAAgent import initNewsVectors


def check_and_init():
    """检查并初始化向量数据"""

    print("=" * 60)
    print("向量数据检查与初始化")
    print("=" * 60)

    # 检查新闻总数
    total_news = newsdetail.objects.count()
    print(f"\n数据库新闻总数: {total_news}")

    if total_news == 0:
        print("\n[警告] 数据库中没有新闻数据！")
        print("请先运行新闻爬虫添加新闻数据。")
        return False

    # 检查已向量化的数量
    vectorized_count = NewsVector.objects.count()
    print(f"已向量化的新闻: {vectorized_count}")
    print(f"待处理的新闻: {total_news - vectorized_count}")

    if vectorized_count == 0:
        print("\n需要初始化向量数据...")
        print("\n开始初始化（这可能需要几分钟）...\n")

        try:
            success_count = initNewsVectors(batch_size=100)

            print("\n" + "=" * 60)
            print("[完成] 初始化完成！")
            print("=" * 60)
            print(f"成功处理: {success_count} 篇新闻")

            # 验证结果
            new_vectorized_count = NewsVector.objects.count()
            print(f"当前已向量化: {new_vectorized_count} 篇新闻")

            return True

        except Exception as e:
            print(f"\n[错误] 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("\n[OK] 向量数据已存在，无需初始化")

        # 询问是否重新初始化
        if vectorized_count < total_news:
            print(f"\n注意: 还有 {total_news - vectorized_count} 篇新闻未向量化")
            print("正在处理剩余的未向量化新闻...\n")

            try:
                additional_count = initNewsVectors(batch_size=100)

                print("\n" + "=" * 60)
                print("[完成] 补充初始化完成！")
                print("=" * 60)
                print(f"本次处理: {additional_count} 篇新闻")

                # 验证结果
                final_vectorized_count = NewsVector.objects.count()
                print(f"当前已向量化: {final_vectorized_count} 篇新闻")
                print(f"数据库总数: {total_news} 篇新闻")

                if final_vectorized_count >= total_news:
                    print("\n✓ 所有新闻已完成向量化！")
                else:
                    print(f"\n注意: 仍有 {total_news - final_vectorized_count} 篇新闻未处理")
                    print("可能是因为这些新闻不在最近的1000条范围内。")

                return True

            except Exception as e:
                print(f"\n[错误] 补充初始化失败: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("\n✓ 所有新闻均已完成向量化")

        return True


if __name__ == '__main__':
    check_and_init()

