import datetime
import json
from django.core import serializers
from django.db.models import Q
from django.http import JsonResponse
from news_api.models import user, history, newsdetail, recommend, hotword, message, comments
import os
from django.conf import settings
from django.conf.urls.static import static


def safe_userid(raw_value, default=100000):
    """防御性 userid 解析: 非数字/None → 默认游客ID 100000"""
    if raw_value is None or raw_value == '':
        return default
    try:
        return int(raw_value)
    except (ValueError, TypeError):
        return default

def add_user(request):
    '''
        @Description：管理员新增用户
        @:param userid---用户id
        @:param username---用户名
        @:param gender---性别
        @:param ip---IP地址
        @:param tags---用户标签
    '''
    if request.method == "POST":
        req = json.loads(request.body)
        if True:
            userid = req["userid"]
            username = req["username"]
            gender = req["gender"]
            ip = req["ip"]
            password = req["password"]
            tags = req["tags"]
            '''插入数据'''
            add_user = user(userid=userid, username=username, gender=gender, ip=ip, password=password, tags=tags)
            add_user.save()
            return JsonResponse({"status": "200", "msg": "add user sucess."})
        else:
            return JsonResponse({"status": "400", "message": "please check param."})


def all_user(request):
    '''
        @Description：管理员获取所有用户信息
    '''
    if request.method == "GET":
        userlist = serializers.serialize("json", user.objects.all())
        response = JsonResponse({"status": 100, "userlist": userlist})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Methods"] = "GET,POST"
        response["Access-Control-Allow-Headers"] = "Origin,Content-Type,Cookie,Accept,Token"
        response["Cache-Control"] = "no-cache"
        return response


def getall_comments(request):
    '''
        @Description：管理员获取所有评论信息
    '''
    if request.method == "GET":
        response = JsonResponse({"status": 100, "commentslist": serializers.serialize("json", comments.objects.all())})
        return response


def del_comments(request):
    '''
        @Description：管理员获取所有评论信息
    '''
    if request.method == "GET":
        commentsid = safe_userid(request.GET.get('commentsid'), default=0)
        newsid = request.GET.get('newsid')
        userid = safe_userid(request.GET.get('userid'))
        choose = int(request.GET.get('choose'))
        print(choose)
        if choose == 1:
            res = comments.objects.filter(id=commentsid).update(status="封禁")
            sendMessage = "尊敬的用户您好，您在标题《" + (newsdetail.objects.filter(news_id=newsid).first().title if newsdetail.objects.filter(news_id=newsid).exists() else '未知新闻') + "》的新闻评论，存在言论不当的问题，评论内容已被管理员封禁！"
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message(userid=userid, message=sendMessage, newsid=newsid, time=time, title="来自管理员的信息", hadread=0).save()
            if res == 0:
                return JsonResponse({"status": "100", "message": "Fail."})
            else:
                return JsonResponse({"status": "100", "message": "Success."})
        elif choose == 0:
            res = comments.objects.filter(id=commentsid).update(status="正常")
            sendMessage = "尊敬的用户您好，您在标题《" + (newsdetail.objects.filter(news_id=newsid).first().title if newsdetail.objects.filter(news_id=newsid).exists() else '未知新闻') + "》的新闻评论，已被管理员解除封禁，给您带来不便，十分抱歉！"
            time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message(userid=userid, message=sendMessage, newsid=newsid, time=time, title="来自管理员的信息", hadread=0).save()
            if res == 0:
                return JsonResponse({"status": "100", "message": "Fail."})
            else:
                return JsonResponse({"status": "100", "message": "Success."})


def del_user(request):
    '''
        @Description：管理员删除用户信息
        @:param userid---用户id
    '''
    if request.method == "GET":
        userid = safe_userid(request.GET.get('userid'))
        # print(user.objects.filter(userid=userid).delete()[0])
        if user.objects.filter(userid=userid).delete()[0] == 0:
            return JsonResponse({"status": "100", "message": "Fail."})
        else:
            return JsonResponse({"status": "100", "message": "Success."})


def up_user(request):
    '''
        @Description：管理员更新用户信息
        @:param userid---用户id
        @:param username---用户名
        @:param gender---性别
        @:param ip---IP地址
        @:param tags---用户标签
    '''
    if request.method == "POST":
        req = json.loads(request.body)
        userid = req['userid']
        username = req['username']
        gender = req['gender']
        ip = req['ip']
        tags = req['tags']
        res = user.objects.filter(userid=userid).update(username=username, gender=gender, ip=ip, tags=tags)
        # print(res)
        if res == 0:
            return JsonResponse({"status": "100", "message": "Fail."})
        else:
            return JsonResponse({"status": "100", "message": "Success."})


def user_login(request):
    """
        @Description: 用户登录 (防御性版本)
    """
    if request.method == "POST":
        try:
            req = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"status": "400", "message": "无效的请求格式"})

        userid_raw = str(req.get('userid', '')).strip()
        password = req.get('password', '')

        if not userid_raw or not password:
            return JsonResponse({"status": "400", "message": "账号和密码不能为空"})

        # 纯数字校验
        if not userid_raw.isdigit():
            return JsonResponse({"status": "400", "message": "账号必须为纯数字"})

        userid = int(userid_raw)
        res = user.objects.filter(userid=userid, password=password)
        if len(res) == 0:
            return JsonResponse({"status": "400", "message": "账号或密码错误"})

        u = res[0]
        data = {
            "userid": u.userid,
            "username": u.username,
            "gender": '男' if u.gender == 1 else '女',
            "headPortrait": u.headPortrait or "default.jpg",
        }

        # 更新登录 IP
        try:
            ip = get_ip(request)
            user.objects.filter(userid=userid).update(ip=str(ip))
        except Exception:
            pass

        # 非游客: 标签衰减
        if str(u.userid) != '100000':
            try:
                usertags = set(u.tags.split(',')) if u.tags else set()
                if u.tagsweight and len(u.tagsweight) > 0:
                    weight = eval(u.tagsweight) if isinstance(u.tagsweight, str) else u.tagsweight
                    for item in list(weight.keys()):
                        if weight[item] >= 0.05:
                            weight[item] = float(format(weight[item] - 0.15, ".3f"))
                            if weight[item] <= 0:
                                weight.pop(item, None)
                                usertags.discard(item)
                    new_tags = ','.join(usertags) if usertags else '综合'
                    new_weight = str(weight).replace("'", '"')
                    user.objects.filter(userid=userid).update(tags=new_tags, tagsweight=new_weight)
            except Exception:
                pass

        return JsonResponse({"status": "100", "message": "Success.", "data": data})
    return JsonResponse({"status": "400", "message": "仅支持POST请求"})


def tourists_login(request):
    if request.method == "GET":
        # 容错: 如果游客账号不存在则自动创建 (修复冷启动 500 崩溃)
        tourist_qs = user.objects.filter(userid=100000)
        if tourist_qs.exists():
            tourist = tourist_qs[0]
        else:
            tourist = user(
                userid=100000,
                username="游客",
                password="tourist_guest",
                gender=1,
                ip="127.0.0.1",
                tags="综合,社会,科技,财经",
                tagsweight='{"综合":0.5,"社会":0.5,"科技":0.5,"财经":0.5}',
                headPortrait="default.jpg"
            )
            tourist.save()
        data = {
            'userid': 100000,
            'username': "游客",
            "gender": '男',
            "headPortrait": tourist.headPortrait if tourist.headPortrait else "default.jpg",
        }
        return JsonResponse({"status": "100", "message": "Success.", "data": data})
    return JsonResponse({"status": "100", "message": "Fail."})


def user_register(request):
    """
        @Description: 用户注册 (防御性版本)
        - 强制校验 userid 为纯数字
        - 防止与游客账号 100000 主键冲突
        - 返回真实 userid 供前端存储
    """
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            userid_raw = str(req.get('userid', '')).strip()
            password = req.get('password', '')
            username = req.get('username', '')
            gender = req.get('gender', '男')
            tags = req.get('tags', '')

            # === 纯数字校验 (防止字符串污染) ===
            if not userid_raw.isdigit():
                return JsonResponse({"status": "400", "message": "账号必须为纯数字"})
            userid = int(userid_raw)

            # === 防止与游客账号冲突 ===
            if userid == 100000:
                return JsonResponse({"status": "400", "message": "该账号为系统保留账号，请使用其他账号"})

            # === 防止重复注册 ===
            if user.objects.filter(userid=userid).exists():
                return JsonResponse({"status": "400", "message": "账号已存在"})

            if not password:
                return JsonResponse({"status": "400", "message": "密码不能为空"})
            if not username:
                username = f"用户{userid}"  # 未填用户名时使用默认昵称

            # 将性别字符串转换为整数标识（1 代表男，0 代表女）
            if gender == '男':
                gender = 1
            elif gender == '女':
                gender = 0
            else:
                gender = 1

            # 获取用户注册时的 IP 地址
            ip = get_ip(request)

            # 初始化用户标签权重字典
            tagsweight = {}
            if tags:
                for t in str(tags).split(","):
                    t = t.strip()
                    if t:
                        tagsweight[t] = 0.5
            if not tagsweight:
                tags = "综合"
                tagsweight = {"综合": 0.5}
            tagsweight = json.dumps(tagsweight, ensure_ascii=False)

            # 创建新用户
            new_user = user(userid=userid, username=username, gender=gender, ip=ip,
                           password=password, tags=tags, tagsweight=tagsweight)
            new_user.save()

            # 返回 data 对象, 前端需要用 userid
            return JsonResponse({
                "status": 200,
                "message": "Success.",
                "data": {"userid": userid, "username": username}
            })
        except json.JSONDecodeError:
            return JsonResponse({"status": "400", "message": "无效的请求格式"})
        except Exception as e:
            return JsonResponse({"status": "500", "message": f"注册失败: {str(e)}"})
    return JsonResponse({"status": "400", "message": "仅支持POST请求"})


def get_ip(request):
    '''获取请求者的IP信息'''
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')  # 判断是否使用代理
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # 使用代理获取真实的ip
    else:
        ip = request.META.get('REMOTE_ADDR')  # 未使用代理获取IP
    return ip


def getHistory(request):
    '''
       @Description：获取用户浏览历史记录
       @:param userid---用户id
    '''
    if request.method == "GET":
        userid = safe_userid(request.GET.get('userid'))
        historylist = history.objects.filter(userid=userid).order_by('-id')
        newslist = dict()
        for historyitem in historylist:
            if len(newsdetail.objects.filter(news_id=historyitem.history_newsid)) > 0:
                news = newsdetail.objects.filter(news_id=historyitem.history_newsid)[0]
                # print(historyitem.history_newsid)
                data = {
                    'newsid': historyitem.history_newsid,
                    'time': historyitem.time,
                }
                newslist[news.title] = data
        # print(newslist)
        # return JsonResponse({"status": "200", 'newslist': serializers.serialize("json", newslist)})
        return JsonResponse({"status": "200", 'newslist': newslist})


def getRecNes(request):
    '''
       @Description：获取用户推荐新闻
       @:param userid---用户id
   '''
    if request.method == "GET":
        userid = safe_userid(request.GET.get('userid'))
        recnewsdetaillist = list()
        if userid != None:
            recnewslist = recommend.objects.filter(userid=userid, hadread=0).order_by('-time')
            for renews in recnewslist:
                recnewsdetailfromdata = newsdetail.objects.filter(news_id=renews.newsid)
                if recnewsdetailfromdata.exists():
                    data = {
                        'newsid': recnewsdetailfromdata[0].news_id,
                        'title': recnewsdetailfromdata[0].title,
                        'date': recnewsdetailfromdata[0].date,
                        'species': renews.species,
                        'pic_url': recnewsdetailfromdata[0].pic_url,
                        'mainpage': recnewsdetailfromdata[0].mainpage,
                        'readnum': recnewsdetailfromdata[0].readnum,
                        'comments': recnewsdetailfromdata[0].comments,
                    }
                    recnewsdetaillist.append(data)
        return JsonResponse({"status": "200", 'newslist': recnewsdetaillist})
    else:
        return JsonResponse({"status": "200", 'newslist': []})


def getUserMessage(request):
    '''
        @Description：获取用户信息
        @:param userid---用户id
    '''
    userid = safe_userid(request.GET.get('userid'))
    user_qs = user.objects.filter(userid=userid)
    if not user_qs.exists():
        return JsonResponse({"status": "404", "message": "用户不存在"})
    userdetail = user_qs[0]
    if userdetail.gender == 1:
        gender = '男'
    else:
        gender = '女'
    hotwordlist = hotword.objects.all().order_by('-num')[:60]
    wordlist = list()
    for hotwords in hotwordlist:
        wordlist.append(hotwords.hotword)
    tags = userdetail.tags
    if tags != None:
        tags = str(tags.split(','))
    else:
        tags = []
    data = {
        'userid': userdetail.userid,
        'username': userdetail.username,
        'gender': gender,
        'tags': tags,
        'headportrait': userdetail.headPortrait,
        'hotword': wordlist,
    }
    return JsonResponse({"status": "200", 'userdetail': data})


def up_user_by_user(request):
    """
        @Description: 用户更新个人信息 (防御性版本)
    """
    if request.method == "POST":
        try:
            req = json.loads(request.body)
            userid = safe_userid(req.get('userid'))
            username = req.get('username', '').strip()
            gender = req.get('gender', '男')

            if not user.objects.filter(userid=userid).exists():
                return JsonResponse({"status": "404", "message": "用户不存在"})

            if gender == '男':
                gender = 1
            else:
                gender = 0

            user.objects.filter(userid=userid).update(username=username, gender=gender)
            return JsonResponse({"status": "100", "message": "更新成功"})
        except json.JSONDecodeError:
            return JsonResponse({"status": "400", "message": "无效的请求格式"})
        except Exception as e:
            return JsonResponse({"status": "500", "message": f"更新失败: {str(e)}"})
    return JsonResponse({"status": "400", "message": "仅支持POST请求"})


def up_tags(request):
    '''
       @Description：更新用户标签
       @:param userid---用户id
       @:param tags---标签详情
    '''
    if request.method == "POST":
        req = json.loads(request.body)
        userid = req['userid']
        tags = req['tags']
        user_qs = user.objects.filter(userid=userid)
        if not user_qs.exists():
            return JsonResponse({"status": "404", "message": "用户不存在"})
        userdetail = user_qs[0]
        if userdetail.tagsweight != None:
            oringin_weight = json.loads(str(userdetail.tagsweight))
        else:
            oringin_weight = {}
        new_weight = {}
        for tag in tags:
            if tag in oringin_weight:
                new_weight[tag] = oringin_weight[tag]
            else:
                new_weight[tag] = 0.5
        tags = list(set(tags))
        new_tags = ",".join(tags)
        new_weight = json.dumps(new_weight, ensure_ascii=False)
        user.objects.filter(userid=userid).update(tags=new_tags)
        user.objects.filter(userid=userid).update(tagsweight=new_weight)
        return JsonResponse({"status": "100", "message": new_weight})


def getMessage(request):
    '''
        @Description：获取用户消息
        @:param userid --> 用户ID
    '''
    if request.method == "GET":
        userid = safe_userid(request.GET.get('userid'))
        print(userid)
        messagelist = message.objects.filter(userid=userid)
        mlist = list()
        for index in messagelist:
            data = {
                'id': index.id,
                'message': index.message,
                'time': index.time,
                'hadread': index.hadread,
                'newsid': index.newsid,
                'title': index.title,
            }
            mlist.append(data)
        return JsonResponse({"status": "100", "message": mlist})


def getTip(request):
    '''
        @Description：获取用户端是否有未读消息提示
        @:param userid --> 用户ID
    '''
    if request.method == "GET":
        userid = safe_userid(request.GET.get('userid'))
        if userid != None:
            if len(message.objects.filter(userid=userid, hadread=0)):
                return JsonResponse({"status": "100", "message": 1})
            else:
                return JsonResponse({"status": "100", "message": 0})


def setMessageHadRead(request):
    '''
        @Description：更新用户消息已读状态
        @:param id --> 消息ID
    '''
    if request.method == "GET":
        id = request.GET.get('id')
        message.objects.filter(id=id).update(hadread=1)
        return JsonResponse({"status": "100", "message": 'Success.'})


def getRegistrPageData(request):
    '''
        @Description：获取注册页数据
        @:param None
    '''
    if request.method == "GET":
        hotwordlist = hotword.objects.all().order_by('-num')[0:150]
        resultlist = list()
        for worditem in hotwordlist:
            resultlist.append(worditem.hotword)
        return JsonResponse({"status": "100", "message": resultlist})
    return JsonResponse({"status": "100", "message": "Fail.."})


def setUserHeadPic(request):
    '''设置用户头像（支持文件上传）'''
    if request.method == "POST":
        try:
            if 'avatar' in request.FILES:
                userid = request.POST.get('userid')
                avatar_file = request.FILES['avatar']

                # 生成唯一文件名 (如: user_123_168888.jpg)
                import time
                timestamp = int(time.time() * 1000)
                extension = avatar_file.name.split('.')[-1].lower()
                if extension not in ['jpg', 'jpeg', 'png', 'gif']:
                    extension = 'jpg'
                filename = f"user_{userid}_{timestamp}.{extension}"

                upload_dir = settings.MEDIA_ROOT
                filepath = os.path.join(upload_dir, filename)

                # 将文件流写入硬盘
                with open(filepath, 'wb+') as destination:
                    for chunk in avatar_file.chunks():
                        destination.write(chunk)

                # 更新数据库
                user_instance = user.objects.filter(userid=userid).first()
                if user_instance:
                    # 删除旧头像文件 (清理垃圾)
                    old_avatar = user_instance.headPortrait
                    if old_avatar and old_avatar != 'default.jpg':
                        old_path = os.path.join(settings.MEDIA_ROOT, old_avatar)
                        if os.path.exists(old_path):
                            os.remove(old_path)

                    user_instance.headPortrait = filename
                    user_instance.save()
                    return JsonResponse({"status": "100", "message": "Success.", "data": {"filename": filename}})
                else:
                    return JsonResponse({"status": "104", "message": "用户不存在"})
        except Exception as e:
            return JsonResponse({"status": "100", "message": f"Fail: {str(e)}"})
    return JsonResponse({"status": "101", "message": "Invalid request"})


def searchUser(request):
    '''
        @Description：管理端搜索用户（模糊搜索）
        @:param keyword --> 关键词
    '''
    if request.method == "GET":
        keyword = request.GET.get('keyword')
        userlist = user.objects.filter(
            Q(userid__contains=keyword) | Q(username__contains=keyword) | Q(tags__contains=keyword))
        response = JsonResponse({"status": 100, "userlist": serializers.serialize("json", userlist)})
        return response


def searchComments(request):
    '''
        @Description：管理端搜索评论
        @:param keyword --> 关键词
    '''
    if request.method == "GET":
        keyword = request.GET.get('keyword')
        commentslist = comments.objects.filter(
            Q(newsid__contains=keyword) | Q(comments__contains=keyword) | Q(userid__contains=keyword) | Q(
                touserid__contains=keyword))
        response = JsonResponse({"status": 100, "commentslist": serializers.serialize("json", commentslist)})
        return response
