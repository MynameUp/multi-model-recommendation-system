# -*- coding: utf-8 -*-
import os
import threading
from django.http import JsonResponse
from Spider.NewsUrlSpider import begincollect
from Spider.NewsDetailSpider import begindetailcollect
from Spider import NewsUrlSpider, NewsDetailSpider
from news_api.models import spiderstate, urlcollect
from django.conf import settings # 💡 新增引入配置文件


def beginUrlSpider(request):
    '''
        @Description：启动新闻URL采集系统
        @:param time  --> 系统运行间隔时间
        @:param oritime  --> 系统运行间隔时间（原始记录用于前端读取显示）
    '''
    if request.method == "GET":
        time = request.GET.get('time')
        oritime = request.GET.get('oritime')
        t = threading.Thread(target=begincollect, kwargs={'time': time})
        t.setDaemon(True)
        t.start()
        spiderstate.objects.update_or_create(spiderid=1, defaults={"status": 1, "interval": oritime})
        return JsonResponse({"status": "200", 'message': 'Success.'})
    return JsonResponse({"status": "200", 'message': 'Fail.'})


def beginDetailSpider(request):
    '''
        @Description：启动新闻详情页内容采集系统
        @:param time  --> 系统运行间隔时间
        @:param oritime  --> 系统运行间隔时间（原始记录用于前端读取显示）
    '''
    if request.method == "GET":
        time = request.GET.get('time')
        oritime = request.GET.get('oritime')
        t = threading.Thread(target=begindetailcollect, kwargs={'time': time})
        t.setDaemon(True)
        t.start()
        # begindetailcollect(time)
        spiderstate.objects.update_or_create(spiderid=2, defaults={"status": 1, "interval": oritime})
        return JsonResponse({"status": "200", 'message': 'Success.'})
    return JsonResponse({"status": "200", 'message': 'Fail.'})


def closeSpiderThread(request):
    """
        @Description: 关闭爬虫系统 (防御性版本, 自动清理浏览器残留进程)
    """
    if request.method == "GET":
        servename = request.GET.get('servename', '')
        try:
            if servename == 'url':
                spiderstate.objects.update_or_create(spiderid=1, defaults={"status": 0, "interval": ""})
                NewsUrlSpider.endsched()
            elif servename == 'detail':
                spiderstate.objects.update_or_create(spiderid=2, defaults={"status": 0, "interval": ""})
                NewsDetailSpider.endsched()
        except Exception as e:
            import logging
            logging.getLogger("Spider").warning(f"关闭爬虫调度器异常: {e}")
        # 强制清理残留浏览器驱动进程 (解决弹窗问题)
        import os as _os
        if _os.name == 'nt':
            _os.system('taskkill /im chromedriver.exe /f /t 2>nul')
            _os.system('taskkill /im msedgedriver.exe /f /t 2>nul')
        return JsonResponse({"status": "200", 'message': '已关闭'})
    return JsonResponse({"status": "200", 'message': 'Fail.'})


def getSpiderPageData(request):
    '''
        @Description：获取爬虫系统管理页数据
        @:param None
    '''
    if request.method == "GET":
        statelist = spiderstate.objects.all()
        urllist = urlcollect.objects.all()
        urlloglist = dict()
        detaillist = dict()
        
        # 💡 优化 1：使用 BASE_DIR 动态获取当前项目根目录
        detail_log_dir = os.path.join(settings.BASE_DIR, "Spider", "Detaillogs")
        if os.path.exists(detail_log_dir):
            files = os.listdir(detail_log_dir)
            for file in files:
                if str(file) == 'log.log':
                    continue # 💡 优化 2：必须用 continue 跳过，千万别用 pass
                time = file[8:].replace("_", ' ')
                time = time[:13] + ':' + time[14:16] + ':' + time[17:]
                filepath = os.path.join(detail_log_dir, file) # 💡 动态拼接文件真实路径
                urlloglist[file] = {
                    'time': time,
                    'filepath': filepath
                }
                
        url_log_dir = os.path.join(settings.BASE_DIR, "Spider", "Urllogs")
        if os.path.exists(url_log_dir):
            files = os.listdir(url_log_dir)
            for file in files:
                if str(file) == 'log.log':
                    continue 
                time = file[8:].replace("_", ' ')
                time = time[:13] + ':' + time[14:16] + ':' + time[17:]
                filepath = os.path.join(url_log_dir, file)
                detaillist[file] = {
                    'time': time,
                    'filepath': filepath
                }
                
        statistical = dict()
        for url in urllist:
            if statistical.get(url.time) == None:
                statistical[url.time] = 1
            else:
                statistical[url.time] = statistical[url.time] + 1
                
        spiderstatelist = dict()
        for state in statelist:
            spiderstatelist[state.spiderid] = [state.status, state.interval]
            
        data = {
            'spiderstatelist': spiderstatelist,
            'statistical': statistical,
            'urlloglist': urlloglist,
            'detaillist': detaillist,
        }
        return JsonResponse({"status": "200", 'message': data})
