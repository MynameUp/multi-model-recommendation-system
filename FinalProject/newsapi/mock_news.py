#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mock 新闻数据生成器
生成 10 条多类别假新闻，用于前端页面调试。

用法: python mock_news.py
"""
import os, sys, django, random, json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsServer.settings')
django.setup()

from news_api.models import newsdetail, newshot, newssimilar, user

print("=" * 60)
print("Mock 新闻数据生成")
print("=" * 60)

# 确保游客账号存在
if not user.objects.filter(userid=100000).exists():
    user.objects.create(
        userid=100000, username="游客", password="tourist_guest",
        gender=1, ip="127.0.0.1", tags="综合,科技,财经",
        tagsweight='{"综合":0.5,"科技":0.5,"财经":0.5}',
        headPortrait="default.jpg"
    )
    print("[OK] 游客账号已创建 (userid=100000)")

# 如果已有新闻数据，跳过
existing = newsdetail.objects.count()
if existing >= 10:
    print(f"[跳过] 已有 {existing} 条新闻，无需生成")
    sys.exit(0)

# 10 条假新闻模板
mock_news = [
    {
        "title": "OpenAI 发布 GPT-5：多模态推理能力全面超越人类专家",
        "mainpage": (
            "<p>北京时间 2026 年 7 月 5 日，OpenAI 在旧金山发布会上正式推出 GPT-5 系列模型。"
            "新模型在 MMLU、HumanEval 等基准测试中全面超越人类专家水平，支持文本、图像、视频、音频四模态联合推理。"
            "GPT-5 采用全新的 MoE（混合专家）架构，总参数量达到 10 万亿，但推理成本仅为 GPT-4 的 40%。</p>"
            "<p>OpenAI CEO Sam Altman 表示：'这标志着 AGI 时代的真正开端。'</p>"
        ),
        "origin": "TechCrunch",
        "category": 7,
        "keywords": "人工智能,GPT-5,OpenAI,多模态,MoE,大模型",
        "pic_url": "['https://picsum.photos/seed/gpt5/800/400']",
    },
    {
        "title": "SpaceX 星舰第八次试飞成功：首次实现轨道级全回收",
        "mainpage": (
            "<p>当地时间 2026 年 7 月 4 日，SpaceX 在德克萨斯州博卡奇卡发射场成功完成星舰（Starship）第八次轨道级试飞。"
            "本次试飞实现了超重型助推器和星舰飞船的同时回收——助推器精准降落在发射塔的'筷子'机械臂上，"
            "星舰飞船则首次完成了轨道再入后的垂直着陆。</p>"
            "<p>Elon Musk 称这标志着'人类成为多行星物种的最后一道技术障碍已被移除'。</p>"
        ),
        "origin": "CNN",
        "category": 7,
        "keywords": "SpaceX,星舰,火箭回收,航天,火星,Elon Musk",
        "pic_url": "['https://picsum.photos/seed/starship/800/400']",
    },
    {
        "title": "中国央行宣布数字人民币 3.0 正式上线：支持离线双离线支付",
        "mainpage": (
            "<p>中国人民银行今日宣布数字人民币（e-CNY）3.0 版本正式在全国范围内上线。"
            "新版本最大的亮点是支持 NFC 双离线支付——即使交易双方均无网络连接，也可以通过碰一碰完成交易。"
            "目前数字人民币累计交易额已突破 15 万亿元。</p>"
        ),
        "origin": "新华社",
        "category": 8,
        "keywords": "数字人民币,央行,移动支付,金融科技,区块链",
        "pic_url": "['https://picsum.photos/seed/ecny/800/400']",
    },
    {
        "title": "2026 世界杯：中国队 2-1 逆转巴西，历史性闯入八强",
        "mainpage": (
            "<p>在 2026 年美加墨世界杯 1/8 决赛中，中国队在下半场补时阶段连入两球，以 2-1 逆转战胜五星巴西，"
            "历史性地闯入世界杯八强。武磊在第 89 分钟打入绝杀球，全国沸腾。</p>"
            "<p>国足主教练表示：'这是中国足球几代人共同努力的结果。'</p>"
        ),
        "origin": "央视体育",
        "category": 4,
        "keywords": "世界杯,中国足球,巴西,武磊,逆转",
        "pic_url": "['https://picsum.photos/seed/worldcup/800/400']",
    },
    {
        "title": "苹果发布 Vision Pro 3：重量仅 120 克，续航达 8 小时",
        "mainpage": (
            "<p>苹果公司在 WWDC 2026 大会上发布了第三代混合现实头显 Vision Pro 3。"
            "新设备重量仅 120 克（比上一代减轻 60%），采用全新的 microLED + 光波导方案，"
            "续航时间达到 8 小时。售价降至 1999 美元起。</p>"
        ),
        "origin": "The Verge",
        "category": 7,
        "keywords": "苹果,Vision Pro,AR,VR,混合现实,可穿戴",
        "pic_url": "['https://picsum.photos/seed/visionpro/800/400']",
    },
    {
        "title": "全球股市掀起 AI 算力投资热潮：英伟达市值突破 10 万亿美元",
        "mainpage": (
            "<p>受 GPT-5 发布及 AI 应用爆发推动，英伟达（NVIDIA）股价本周飙升 15%，"
            "市值历史上首次突破 10 万亿美元大关，成为全球市值最高的公司。"
            "分析师预计全球 AI 算力市场规模将在 2027 年达到 2 万亿美元。</p>"
        ),
        "origin": "Bloomberg",
        "category": 9,
        "keywords": "英伟达,AI算力,市值,GPU,投资,股市",
        "pic_url": "['https://picsum.photos/seed/nvidia/800/400']",
    },
    {
        "title": "我国首条超级高铁试验线建成：设计时速 1000 公里",
        "mainpage": (
            "<p>中国首条超级高铁（Hyperloop）试验线今日在成都正式建成并完成首次载人测试。"
            "该线路全长 50 公里，采用磁悬浮 + 低真空管道技术，设计时速达 1000 公里/小时。"
            "从成都到重庆的旅行时间将压缩至 20 分钟。</p>"
        ),
        "origin": "人民日报",
        "category": 1,
        "keywords": "超级高铁,磁悬浮,交通,中国制造,科技创新",
        "pic_url": "['https://picsum.photos/seed/hyperloop/800/400']",
    },
    {
        "title": "《黑神话：悟空 2》首周销量突破 3000 万份，国游再创纪录",
        "mainpage": (
            "<p>游戏科学工作室今日宣布，《黑神话：悟空 2》全球首周销量突破 3000 万份，"
            "超越前作同期成绩 50%，成为中国游戏史上最成功的作品。"
            "游戏凭借虚幻引擎 6 打造的极致画面和深度战斗系统，获得全球媒体一致好评。</p>"
        ),
        "origin": "IGN中国",
        "category": 5,
        "keywords": "黑神话悟空,国产游戏,3A大作,销量纪录,文化输出",
        "pic_url": "['https://picsum.photos/seed/wukong2/800/400']",
    },
    {
        "title": "中美达成气候合作协议：共同承诺 2035 年碳中和目标",
        "mainpage": (
            "<p>中美两国元首在 G20 峰会期间签署了历史性的《中美气候合作联合声明》，"
            "双方承诺在 2035 年前实现碳中和，并在清洁能源技术、碳捕获等领域开展深度合作。"
            "协议还包括建立联合绿色基金，总规模达 2000 亿美元。</p>"
        ),
        "origin": "路透社",
        "category": 2,
        "keywords": "中美关系,气候变化,碳中和,清洁能源,国际合作",
        "pic_url": "['https://picsum.photos/seed/climate/800/400']",
    },
    {
        "title": "2026 暑期档票房破百亿：《流浪地球 3》贡献超三成",
        "mainpage": (
            "<p>据国家电影局统计，2026 年暑期档（6 月 1 日至今）全国电影票房已突破 100 亿元人民币。"
            "其中《流浪地球 3》以 35 亿元的票房成绩领跑，"
            "影片通过先进的 AI 辅助特效技术和宏大的叙事架构，被誉为'中国科幻电影的新里程碑'。</p>"
        ),
        "origin": "新浪娱乐",
        "category": 5,
        "keywords": "电影票房,流浪地球3,暑期档,科幻,国产电影",
        "pic_url": "['https://picsum.photos/seed/movie/800/400']",
    },
]

created = 0
now = datetime.now()

for i, data in enumerate(mock_news):
    days_ago = len(mock_news) - i
    pub_date = (now - timedelta(days=days_ago, hours=random.randint(0, 23))).strftime('%Y{y}%m{m}%d{d} %H:%M').format(y='年', m='月', d='日')

    ns = newsdetail.objects.create(
        title=data["title"],
        date=pub_date,
        pic_url=data["pic_url"],
        mainpage=data["mainpage"],
        origin=data["origin"],
        category=data["category"],
        readnum=random.randint(500, 50000),
        comments=random.randint(10, 500),
        keywords=data["keywords"],
        url=f"https://example.com/news/mock_{i+1}",
        videourl="",
    )

    # 生成热度值
    hot_val = round(ns.readnum * 0.4 + ns.comments * 0.5 - days_ago * 0.1, 2)
    newshot.objects.create(news_id=ns.news_id, news_hot=hot_val, category=ns.category)

    created += 1
    print(f"[{created}] {data['title'][:40]}... | 分类={ns.category} | 热度={hot_val}")

# 生成新闻相似度（模拟：同类新闻之间高相似度）
news_ids = list(newsdetail.objects.all().order_by('-news_id')[:10].values_list('news_id', flat=True))
sim_count = 0
for i in range(len(news_ids)):
    for j in range(i + 1, len(news_ids)):
        ni = newsdetail.objects.get(news_id=news_ids[i])
        nj = newsdetail.objects.get(news_id=news_ids[j])
        # 同类别相似度 0.6-0.95，不同类别 0.1-0.4
        if ni.category == nj.category:
            cor = round(random.uniform(0.6, 0.95), 2)
        else:
            cor = round(random.uniform(0.1, 0.4), 2)
        newssimilar.objects.update_or_create(
            new_id_base=news_ids[i],
            new_id_sim=news_ids[j],
            defaults={'new_correlation': cor}
        )
        sim_count += 1

print(f"\n[Done] 生成 {created} 条新闻 + {sim_count} 条相似度关系")
print("现在可以刷新前端页面查看效果！")
