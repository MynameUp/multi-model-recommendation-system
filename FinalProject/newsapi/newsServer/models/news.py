import datetime
import time
import json
from django.db.models import F, Q, Count # 💡 引入 F 对象处理原子操作
from django.http import JsonResponse
# 💡 已经彻底移除了 serializers，全部改用 .values() 或字典构造，保证前端直接读取
from news_api.models import newsdetail, recommend, newshot, newssimilar, history, user, givelike, comments


def safe_userid(raw_value, default=100000):
    """防御性 userid 解析: 非数字/None → 默认游客ID 100000"""
    if raw_value is None or raw_value == '':
        return default
    try:
        return int(raw_value)
    except (ValueError, TypeError):
        return default


def all_news(request):
    '''
        @Description：获取所有新闻
        @:param None
    '''
    if request.method == "GET":
        newslist = list(newsdetail.objects.all().order_by('-news_id').values(
            'news_id', 'title', 'date', 'pic_url', 'category', 'readnum', 'comments', 'mainpage', 'origin', 'url'
        ))
        response = JsonResponse({"status": 100, "newslist": newslist})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Methods"] = "GET,POST"
        response["Access-Control-Allow-Headers"] = "Origin,Content-Type,Cookie,Accept,Token"
        response["Cache-Control"] = "no-cache"
        return response

def del_news(request):
    '''
        @Description：删除指定新闻
        @:param url---指定新闻url
    '''
    if request.method == "GET":
        url = request.GET.get('url')
        if newsdetail.objects.filter(url=url).delete()[0] == 0:
            return JsonResponse({"status": "100", "message": "Fail."})
        else:
            return JsonResponse({"status": "100", "message": "Success."})


def reconewsbytags(request):
    '''
        @Description：推送用户推荐新闻集（融合了你的单次批量查询优化版）
        @:param userid---用户id
    '''
    if request.method == "GET":
        userid = safe_userid(request.GET.get('userid'))
        # 💡 优化：提取 ID 列表，不再循环中查询数据库
        news_ids = recommend.objects.filter(userid=userid, headread=0).values_list('newsid', flat=True)
        
        # 💡 优化：单次批量获取所有新闻详情，并转为纯净字典列表
        news_list = list(newsdetail.objects.filter(news_id__in=news_ids).values())
        
        return JsonResponse({"status": 100, "newsidlist": news_list})


def reconewsbysimilar(request):
    '''
        @Description：推送相似新闻集（保持相关度排序优化）
    '''
    if request.method == "GET":
        newsid = request.GET.get('newsid')
        # 获取相关 ID 及其排序
        sim_records = newssimilar.objects.filter(new_id_base=newsid).order_by('-new_correlation')[:5]
        sim_ids = [rec.new_id_sim for rec in sim_records]

        # 批量获取详情，并转换为字典以供快速映射
        details = newsdetail.objects.filter(news_id__in=sim_ids)
        detail_map = {d.news_id: d for d in details}

        # 💡 按原始相似度顺序重新构建列表，已经是纯净的 dict 列表，无需修改
        newsdetaillist = []
        for sid in sim_ids:
            if sid in detail_map:
                d = detail_map[sid]
                newsdetaillist.append({
                    'newsid': d.news_id,
                    'title': d.title,
                    'pic_url': d.pic_url,
                    'mainpage': d.mainpage,
                })
        
        return JsonResponse({"status": 100, "newslist": newsdetaillist})


def typenews(request):
    '''
        @Description：推送各类别新闻集
        @:param typeid---类别id
    '''
    if request.method == "GET":
        typeid = request.GET.get('type')
        # 💡 核心修复：跳过 newshot，直接从 newsdetail 查最新分类数据，防止热度未更新导致空白
        queryset = newsdetail.objects.filter(category=typeid).order_by('-date', '-news_id')[:50]
        
        # 使用 values 只取前端需要的字段，极大减轻网络传输负担
        news_list = list(queryset.values(
            'news_id', 'title', 'date', 'pic_url', 'mainpage', 'category', 'origin', 'readnum'
        ))
        
        return JsonResponse({"status": 100, "newslist": news_list})


import re  # 💡 确保文件开头有这一行！

def getpicture(request):
    '''
        @Description：获取热度较高的图片（引入正则提取，无视脏数据格式）
    '''
    if request.method == "GET":
        try:
            # 选秀范围扩大到 100
            hot_ids = list(newshot.objects.all().order_by('-news_hot').values_list('news_id', flat=True)[:100])
            # 过滤空图
            hot_news = newsdetail.objects.filter(news_id__in=hot_ids).exclude(pic_url='[]').exclude(pic_url='').exclude(pic_url__isnull=True)
            
            pictlist = list()
            for news in hot_news:
                if len(pictlist) >= 5: # 凑够 5 张就收工
                    break
                    
                # 💡 终极杀招：使用正则表达式直接提取所有 HTTP 链接，无视任何列表、引号的报错！
                urls = re.findall(r'https?://[^\s\'"\]]+', str(news.pic_url))
                
                if urls: # 如果成功提取到了有效链接
                    pictlist.append({
                        'newsid': news.news_id, 
                        'pic_url': urls[0],  # 取第一张图
                        'title': news.title
                    })
                    
            return JsonResponse({"status": "100", "message": pictlist})
        except Exception as e:
            print(f"❌ 轮播图获取失败: {e}")
            return JsonResponse({"status": "500", "message": str(e)})


def getNewsDetailByNewsid(request):
    '''
        @Description：通过newsid获取新闻详情
        @:param newsid ----> 新闻id
    '''
    if request.method == "GET":
        newsid = request.GET.get('newsid')
        userid = safe_userid(request.GET.get('userid'))
        
        # 💡 使用 F() 对象实现原子性自增
        newsdetail.objects.filter(news_id=newsid).update(readnum=F('readnum') + 1)
        news = newsdetail.objects.filter(news_id=newsid).first()
        if not news:
            return JsonResponse({"status": "404", "message": "News not found"})
            
        if int(userid) != 100000:
            user_qs = user.objects.filter(userid=userid)
            if user_qs.exists():
                users = user_qs[0]
                usertags = users.tags
                usertags = set(usertags.split(','))
                if news.keywords != None:
                    newskeywords = set(news.keywords.split(','))
                else:
                    newskeywords = set()
                weight = eval(users.tagsweight)
                for keyword in newskeywords:
                    if keyword in weight:
                        weight[keyword] = float(format(weight[keyword] + 0.01, ".3f"))
                        if weight[keyword] >= 0.1:
                            usertags.add(keyword)
                            user.objects.filter(userid=userid).update(tags=str(",".join(usertags)))
                    else:
                        weight[keyword] = 0.01
                user.objects.filter(userid=userid).update(tagsweight=str(weight).replace("\'", "\""))

        temp = givelike.objects.filter(newsid=newsid, userid=userid)
        if len(temp) == 0:
            liking = 0
        else:
            liking = temp[0].givelikeornot
            
        newsdetails = {
            "newsid": news.news_id,
            "title": news.title,
            "date": news.date,
            "pic_url": news.pic_url,
            "videourl": news.videourl,
            "category": news.category,
            "readnum": int(news.readnum),
            "comments": news.comments,
            "origin": news.origin,
            "mainpage": news.mainpage, # 新增正文返回，防止详情页空白
            "givelike": liking,
        }
        return JsonResponse({"status": "100", "message": newsdetails})


def all_news_to_page(request):
    '''
        @Description：获取所有新闻
        @:param None
    '''
    if request.method == "GET":
        # 💡 补全 mainpage 和 origin 和 comments 字段
        newslist = list(newsdetail.objects.all().order_by('-date', '-news_id')[0:100].values(
            'news_id', 'title', 'date', 'pic_url', 'category', 'readnum', 'comments', 'mainpage', 'origin'
        ))
        response = JsonResponse({"status": 100, "newslist": newslist})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Methods"] = "GET,POST"
        response["Access-Control-Allow-Headers"] = "Origin,Content-Type,Cookie,Accept,Token"
        response["Cache-Control"] = "no-cache"
        return response


def newsHistory(request):
    '''
        @Description：更新用户阅读记录
        @:param userid ---> 用户id
        @:param newsid ---> 新闻id
    '''
    if request.method == "GET":
        userid = safe_userid(request.GET.get('userid'))
        newsid = request.GET.get('newsid')
        daytime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        history.objects.create(userid=userid, history_newsid=newsid, time=daytime)
        return JsonResponse({"status": "200"})


def newsHotRec(request):
    '''
        @Description：获取热点新闻推荐
    '''
    if request.method == "GET":
        hotnewsidlist = newshot.objects.all().order_by('-news_hot')[:5]
        newsdetaillist = list()
        for hotnews in hotnewsidlist:
            detail = newsdetail.objects.filter(news_id=hotnews.news_id).first()
            if detail:
                data = {
                    'newsid': detail.news_id,
                    'mainpage': detail.mainpage,
                    'title': detail.title,
                    'pic_url': detail.pic_url,
                }
                newsdetaillist.append(data)
        return JsonResponse({"status": "200", 'newslist': newsdetaillist})


def getComments(request):
    '''
        @Description：获取新闻评论列表
    '''
    if request.method == "GET":
        newsid = request.GET.get('newsid')
        commentlistdata = comments.objects.filter(newsid=newsid, status="正常")
        commentlist = list()
        for comment in commentlistdata:
            User = user.objects.filter(userid=comment.userid).first()
            if not User:
                continue
            userheadPortrait = User.headPortrait
            userName = User.username
            
            touser = user.objects.filter(userid=comment.touserid).first()
            if touser:
                toUserHeadPortrait = touser.headPortrait
                toUserName = touser.username
            else:
                toUserHeadPortrait = None
                toUserName = None

            data = {
                'userid': comment.userid,
                'touserid': comment.touserid,
                'comments': comment.comments,
                'time': comment.time,
                'username': userName,
                'userheadPortrait': userheadPortrait,
                'tousername': toUserName,
                'toUserHeadPortrait': toUserHeadPortrait,
            }
            commentlist.append(data)
        return JsonResponse({"status": "200", 'commentlist': commentlist})


def gethotnews(request):
    '''
        @Description：获取热点新闻排行
    '''
    if request.method == "GET":
        newsidlist = newshot.objects.all().order_by('-news_hot')[:50]
        newslist = list()
        for news in newsidlist:
            detail = newsdetail.objects.filter(news_id=news.news_id).first()
            if detail:
                data = {
                    "newsid": detail.news_id,
                    "title": detail.title,
                    "date": detail.date,
                    "pic_url": detail.pic_url,
                    "mainpage": detail.mainpage,
                    "category": detail.category,
                    "readnum": detail.readnum,
                    "comments": detail.comments,
                    "hotvalue": news.news_hot,
                }
                newslist.append(data)
        return JsonResponse({"status": "200", 'newslist': newslist})


def updateGiveLike(request):
    '''
        @Description：更新点赞/点踩状态
    '''
    if request.method == "GET":
        newsid = request.GET.get('newsid')
        userid = safe_userid(request.GET.get('userid'))
        like = request.GET.get('like')
        
        if int(like) == 1:
            if int(userid) != 100000:
                try:
                    user_qs = user.objects.filter(userid=userid)
                    news_qs = newsdetail.objects.filter(news_id=newsid)
                    if not user_qs.exists() or not news_qs.exists():
                        pass  # 用户或新闻不存在，跳过标签更新
                    else:
                        users = user_qs[0]
                        usertags = users.tags
                        news = news_qs[0]
                        usertags = set(usertags.split(','))
                        if news.keywords != None:
                            newskeywords = set(news.keywords.split(','))
                        else:
                            newskeywords = set()
                        key = usertags & newskeywords
                        key = list(key)
                        if len(key) > 0:
                            weight = eval(users.tagsweight)
                            weight[key[0]] = weight.get(key[0], 0.0) + 0.01
                            user.objects.filter(userid=userid).update(tagsweight=str(weight).replace("\'", "\""))
                except Exception:
                    pass  # 标签更新失败不影响核心功能

        if int(like) == 2:
            if int(userid) != 100000:
                try:
                    user_qs = user.objects.filter(userid=userid)
                    news_qs = newsdetail.objects.filter(news_id=newsid)
                    if not user_qs.exists() or not news_qs.exists():
                        pass
                    else:
                        users = user_qs[0]
                        usertags = users.tags
                        news = news_qs[0]
                        usertags = set(usertags.split(','))
                        if news.keywords != None:
                            newskeywords = set(news.keywords.split(','))
                        else:
                            newskeywords = set()
                        for k in newskeywords:
                            weight = eval(users.tagsweight)
                            if k in weight:
                                if weight[k] >= 0.1:
                                    weight[k] = float(format(weight.get(k) - 0.1, ".3f"))
                                    if weight.get(k) > 0:
                                        user.objects.filter(userid=userid).update(tagsweight=str(weight).replace("\'", "\""))
                                    else:
                                        weight.pop(k)
                                        user.objects.filter(userid=userid).update(tagsweight=str(weight).replace("\'", "\""))
                                        usertags.remove(k)
                                        newusertags = ','.join(usertags)
                                        user.objects.filter(userid=userid).update(tags=newusertags)
                except Exception:
                    pass
                                
        selectres = givelike.objects.filter(userid=userid, newsid=newsid)
        if len(selectres) == 0:
            givelike(userid=userid, newsid=newsid, givelikeornot=like).save()
        else:
            selectres.update(userid=userid, newsid=newsid, givelikeornot=like)
        return JsonResponse({"status": "200", 'message': 'Success.'})
    else:
        return JsonResponse({"status": "200", 'message': 'Fail.'})


def submitComments(request):
    """
        @Description: 提交新闻评论 (防御性版本)
    """
    if request.method == "POST":
        req = json.loads(request.body)
        userid = req['userid']
        newsid = req['newsid']
        comment = req['comment']

        # 非游客: 尝试更新兴趣标签 (用户/新闻缺失时静默跳过)
        if int(userid) != 100000:
            try:
                users = user.objects.filter(userid=userid).first()
                news = newsdetail.objects.filter(news_id=newsid).first()
                if users is not None and news is not None:
                    usertags = set(users.tags.split(','))
                    if news.keywords is not None:
                        newskeywords = set(news.keywords.split(','))
                    else:
                        newskeywords = set()
                    key = list(usertags & newskeywords)
                    if len(key) > 0:
                        weight = eval(users.tagsweight)
                        weight[key[0]] = weight.get(key[0], 0.0) + 0.01
                        user.objects.filter(userid=userid).update(
                            tagsweight=str(weight).replace("'", '"'))
            except Exception:
                pass

        time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        comments(userid=userid, newsid=newsid, comments=comment, time=time_str, status="正常").save()
        nqs = newsdetail.objects.filter(news_id=newsid)
        if nqs.exists():
            newsdetail.objects.filter(news_id=newsid).update(
                comments=int(nqs[0].comments) + 1)
        return JsonResponse({"status": "200", 'message': 'Success.'})


def submitCommenttoUser(request):
    """
        @Description: 对用户评论进行回复 (防御性版本)
    """
    if request.method == "POST":
        req = json.loads(request.body)
        userid = req['userid']
        newsid = req['newsid']
        comment = req['comment']
        touserid = req['touserid']

        # 非游客: 尝试更新兴趣标签
        if int(userid) != 100000:
            try:
                users = user.objects.filter(userid=userid).first()
                news = newsdetail.objects.filter(news_id=newsid).first()
                if users is not None and news is not None:
                    usertags = set(users.tags.split(','))
                    if news.keywords is not None:
                        newskeywords = set(news.keywords.split(','))
                    else:
                        newskeywords = set()
                    key = list(usertags & newskeywords)
                    if len(key) > 0:
                        weight = eval(users.tagsweight)
                        weight[key[0]] = weight.get(key[0], 0.0) + 0.01
                        user.objects.filter(userid=userid).update(
                            tagsweight=str(weight).replace("'", '"'))
            except Exception:
                pass

        time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sendMessage = "新的回复了！！请速速查看！！"
        comments(userid=userid, newsid=newsid, comments=comment, time=time_str, touserid=touserid, status="正常").save()
        message(userid=touserid, message=sendMessage, time=time_str, newsid=newsid, title="收到回复", hadread=0).save()
        return JsonResponse({"status": "200", 'message': 'Success.'})


def getManageHomeData(request):
    '''
        @Description：高效获取管理端主页统计数据
    '''
    if request.method == "GET":
        try:
            readnum = history.objects.count()
            usernum = user.objects.count()
            newsnum = newsdetail.objects.count()
            recnum = recommend.objects.count()
            comnum = comments.objects.count()
            likenum = givelike.objects.filter(givelikeornot=1).count()

            region_query = user.objects.values('region').annotate(count=Count('region'))
            regionlist = {item['region']: item['count'] for item in region_query if item['region']}

            stat_query = recommend.objects.filter(hadread=1).values('time').annotate(count=Count('time'))
            statistical = {item['time']: item['count'] for item in stat_query if item['time']}

            data = {
                'usernum': usernum,
                'readnum': readnum,
                'newsnum': newsnum,
                'recnum': recnum,
                'comnum': comnum,
                'statistical': statistical,
                'likenum': likenum,
                'regionlist': regionlist,
            }
            return JsonResponse({"status": "200", 'message': data})

        except Exception as e:
            print(f"统计数据获取失败: {e}")
            return JsonResponse({"status": "500", "message": "Internal Server Error"})


def updateRecHis(request):
    '''
        @Description：更新推荐列表阅读历史/更改推荐新闻已读状态
    '''
    if request.method == "GET":
        userid = safe_userid(request.GET.get('userid'))
        newsid = request.GET.get('newsid')
        recommend.objects.filter(newsid=newsid, userid=userid).update(hadread=1)
        return JsonResponse({"status": "200", 'message': 'Success.'})
    return JsonResponse({"status": "200", 'message': 'Fail.'})


def searchNews(request):
    '''
        @Description：管理端搜索新闻（模糊搜索）
    '''
    if request.method == "GET":
        keyword = request.GET.get('keyword')
        if not keyword:
            return JsonResponse({"status": 100, "newslist": []})
            
        # 💡 优化：移除 serializers，直接输出字典列表
        news_objs = newsdetail.objects.filter(Q(title__contains=keyword) | Q(mainpage__contains=keyword))
        newslist = list(news_objs.values(
            'news_id', 'title', 'date', 'pic_url', 'category', 'mainpage'
        ))
        
        response = JsonResponse({"status": 100, "newslist": newslist})
        return response