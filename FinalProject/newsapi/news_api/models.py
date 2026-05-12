from django.db import models


# Create your models here.
class user(models.Model):
    '''
        @Description: 用户模型类，用于定义数据库用户表的结构
        @Attributes:
            userid (CharField): 用户 ID，主键，最大长度 30 字符
            region (CharField): 用户所在地区，最大长度 30 字符
            username (CharField): 用户名，最大长度 50 字符
            gender (IntegerField): 用户性别（1 代表男，0 代表女）
            ip (GenericIPAddressField): 用户 IP 地址
            password (CharField): 用户密码，最大长度 20 字符
            tags (CharField): 用户标签集合（逗号分隔的字符串），最大长度 2000 字符
            tagsweight (CharField): 用户标签权重（JSON 格式字符串），最大长度 2000 字符
            headPortrait (CharField): 用户头像 URL，最大长度 255 字符
            objects (Manager): Django ORM 管理器，用于数据库查询操作
    '''
    userid = models.CharField(primary_key=True,max_length=30)
    region = models.CharField(max_length=30)
    username = models.CharField(max_length=50)
    gender = models.IntegerField()

    # active inactive
    ip = models.GenericIPAddressField()
    password = models.CharField(max_length=128)
    tags = models.CharField(max_length=2000)
    tagsweight = models.CharField(max_length=2000)
    headPortrait = models.CharField(max_length=255)
    objects = models.Manager()



class newsdetail(models.Model):
    news_id = models.AutoField(primary_key=True)
    # 💡 数据库是 255，代码必须同步，否则超过 100 的 URL 会导致崩溃
    url = models.CharField(max_length=255, unique=True) 
    # 💡 新闻标题通常较长，255 更稳妥
    title = models.TextField(null=True, blank=True) 
    date = models.CharField(max_length=30)
    # 💡 关键修改：数据库已经是 LONGTEXT，代码里必须用 TextField()
    pic_url = models.TextField(null=True, blank=True) 
    # 💡 数据库是 255，保持一致
    videourl = models.CharField(max_length=255, null=True, blank=True) 
    # 💡 关键修改：正文必须是 TextField() 对应数据库的 LONGTEXT
    mainpage = models.TextField(null=True, blank=True) 
    origin = models.TextField(null=True, blank=True)
    
    category = models.IntegerField() 
    # 💡 增加 default=0，防止入库时因为没传值而报错
    readnum = models.PositiveIntegerField(default=0) 
    comments = models.PositiveIntegerField(default=0) 
    keywords = models.CharField(max_length=1000, null=True, blank=True)
    
    objects = models.Manager()


class hotword(models.Model):
    hotword = models.CharField(max_length=50)
    num = models.IntegerField()
    objects = models.Manager()

class recommend(models.Model):
    userid = models.IntegerField(primary_key=True)
    newsid = models.IntegerField()
    hadread = models.IntegerField()
    cor = models.FloatField()
    species = models.IntegerField()
    time = models.CharField(max_length=30)
    objects = models.Manager()

class newssimilar(models.Model):
    new_id_base = models.CharField(primary_key=True, max_length=64)
    new_id_sim = models.CharField(max_length=64)
    new_correlation = models.FloatField()
    objects = models.Manager()

class comments(models.Model):
    id = models.AutoField(primary_key=True)
    newsid = models.IntegerField()
    comments = models.CharField(max_length=1000)
    userid = models.IntegerField()
    touserid = models.IntegerField()
    time = models.DateTimeField()
    status = models.CharField(max_length=20)
    objects = models.Manager()

class history(models.Model):
    userid = models.IntegerField()
    history_newsid = models.IntegerField()
    time = models.DateTimeField()
    id = models.AutoField(primary_key=True)
    objects = models.Manager()

class newshot(models.Model):
    news_id = models.IntegerField(primary_key=True)
    news_hot = models.FloatField()
    category = models.IntegerField()
    objects = models.Manager()

class givelike(models.Model):
    id = models.AutoField(primary_key=True)
    userid = models.IntegerField()
    newsid = models.IntegerField()
    givelikeornot = models.IntegerField()
    objects = models.Manager()

class message(models.Model):
    id = models.AutoField(primary_key=True)
    userid = models.IntegerField()
    message = models.CharField(max_length=1000)
    time = models.CharField(max_length=30)
    newsid = models.IntegerField()
    hadread = models.IntegerField()
    title = models.CharField(max_length=255)
    objects = models.Manager()

class spiderstate(models.Model):
    spiderid = models.IntegerField(primary_key=True)
    status = models.IntegerField()
    interval = models.CharField(max_length=30)
    objects = models.Manager()

class urlcollect(models.Model):
    url = models.CharField(primary_key=True, max_length=255)
    # 💡 增加 default=0，新抓取的链接 handle 默认为 0（未处理）
    handle = models.IntegerField(default=0) 
    # 💡 这里建议叫 type（因为你爬虫里用的是 row['type']）
    # 如果数据库里已经是 type 就不动，如果是 category 则需一致
    type = models.IntegerField() 
    time = models.CharField(max_length=30)
    objects = models.Manager()

    class Meta:
        db_table = 'news_api_urlcollect'