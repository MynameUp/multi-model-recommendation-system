from django.http import JsonResponse
from .models import NewsDetail  # 确认你的 model 名是这个

from django.http import JsonResponse
from .models import newsdetail  # 注意：这里要跟你 models.py 里的类名大小写一致

def get_news_by_category(request):
    """根据分类获取新闻列表"""
    try:
        # 获取前端传来的参数，例如：?type=8
        # 注意：如果前端传的是 'type'，我们这里接收 'type'，但查询数据库要用 'category'
        category_id = request.GET.get('type') or request.GET.get('category')
        
        if category_id:
            # 💡 核心修复：这里的 'category' 必须匹配你 models.py 里的变量名
            queryset = newsdetail.objects.filter(category=category_id).order_by('-date')
        else:
            queryset = newsdetail.objects.all().order_by('-date')
            
        # 构造返回数据
        news_list = []
        for item in queryset[:50]:
            news_list.append({
                'news_id': item.news_id,
                'title': item.title,
                'date': item.date,
                'pic_url': item.pic_url,
                'origin': item.origin,
                'category': item.category,
                'type': item.category  # 💡 增加这一行，兼容前端旧的 item.type 调用
            })
            
        return JsonResponse({'code': 200, 'data': news_list, 'msg': 'success'})
    except Exception as e:
        print(f"❌ 分类查询失败: {e}") # 这里的报错会显示在 Django 终端
        return JsonResponse({'code': 500, 'msg': str(e)}, status=500)

def get_recommend_data(request):
    """推荐数据的接口（如果你的全部栏目用的是这个）"""
    # 逻辑类似，确保字段名对齐即可
    pass