import logging
# 💡 优化 1：改为 BackgroundScheduler，不会阻塞 Django 的主线程
from apscheduler.schedulers.background import BackgroundScheduler

from Recommend.NewsRecommendByCity import beginrecommendbycity
from Recommend.NewsRecommendByHotValue import beginrecommendbyhotvalue
from Recommend.NewsRecommendByTags import beginNewsRecommendByTags
from Recommend.NewsKeyWordsSelect import beginSelectKeyWord
from Recommend.NewsHotValueCal import beginCalHotValue
from Recommend.NewsCorrelationCalculation import beginCorrelation
from Recommend.HotWordLibrary import beginHotWordLibrary

logger = logging.getLogger(__name__)

# 💡 优化 2：全局变量初始值设为 None，方便追踪存活状态
recommend_sched = None
analysis_sched = None


def beginRecommendSystem(time):
    '''
        @Description：推荐系统启动管理器（基于城市推荐、基于热度推荐、基于新闻标签推荐）
        @:param time --> 时间间隔
    '''
    global recommend_sched
    time = int(time)
    
    try:
        # 如果已有运行中的调度器，先安全关闭
        if recommend_sched is not None and recommend_sched.running:
            recommend_sched.shutdown(wait=False)
            
        # 💡 优化 3：每次启动都买一台“新发动机”，彻底绕开 shutdown 后的死亡状态
        recommend_sched = BackgroundScheduler()
        
        recommend_sched.add_job(func=beginrecommendbycity, trigger='interval', max_instances=1, seconds=time,
                                id='NewsRecommendByCity', kwargs={})
        recommend_sched.add_job(beginrecommendbyhotvalue, trigger='interval', max_instances=1, seconds=time,
                                id='NewsRecommendByHotValue', kwargs={})
        recommend_sched.add_job(beginNewsRecommendByTags, trigger='interval', max_instances=1, seconds=time, 
                                id='NewsRecommendByTags', kwargs={})
        
        recommend_sched.start()
        logger.info("✅ 推荐系统定时任务已全新启动！")
    except Exception as e:
        logger.error(f"❌ 推荐系统调度器启动错误: {e}")


def stopRecommendSystem():
    '''
        @Description：推荐系统关闭管理器
        @:param None
    '''
    global recommend_sched
    try:
        if recommend_sched is not None and recommend_sched.running:
            # 💡 优化 4：使用 wait=False 安全退出，并将变量置空释放内存
            recommend_sched.shutdown(wait=False)
            recommend_sched = None
            logger.info("🛑 推荐系统定时任务已安全关闭。")
    except Exception as e:
        logger.error(f"❌ 关闭推荐系统失败: {e}")


def beginAnalysisSystem(time):
    '''
        @Description：数据分析系统启动管理器（关键词分析、热词分析、新闻相似度分析、热词统计）
        @:param time --> 时间间隔
    '''
    global analysis_sched
    time = int(time)
    
    try:
        if analysis_sched is not None and analysis_sched.running:
            analysis_sched.shutdown(wait=False)

        analysis_sched = BackgroundScheduler()
        
        analysis_sched.add_job(beginSelectKeyWord, trigger='interval', max_instances=1, seconds=time,
                               id='beginSelectKeyWord', kwargs={"_type": 2})
        analysis_sched.add_job(beginCalHotValue, trigger='interval', max_instances=1, seconds=time,
                               id='beginCalHotValue', kwargs={})
        analysis_sched.add_job(beginCorrelation, trigger='interval', max_instances=1, seconds=time, 
                               id='beginCorrelation', kwargs={})
        analysis_sched.add_job(beginHotWordLibrary, trigger='interval', max_instances=1, seconds=time, 
                               id='beginHotWordLibrary', kwargs={})
        
        analysis_sched.start()
        logger.info("✅ 数据分析定时任务已全新启动！")
    except Exception as e:
        logger.error(f"❌ 数据分析调度器启动错误: {e}")


def stopAnalysisSystem():
    '''
        @Description：数据分析系统关闭管理器
        @:param None
    '''
    global analysis_sched
    try:
        if analysis_sched is not None and analysis_sched.running:
            analysis_sched.shutdown(wait=False)
            analysis_sched = None
            logger.info("🛑 数据分析定时任务已安全关闭。")
    except Exception as e:
        logger.error(f"❌ 关闭数据分析系统失败: {e}")