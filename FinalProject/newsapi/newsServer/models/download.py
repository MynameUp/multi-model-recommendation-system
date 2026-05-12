import os
from django.http import FileResponse, Http404
from django.utils.encoding import escape_uri_path

def download(request):
    if request.method == "GET":
        filepath = request.GET.get('filepath')
        # 💡 优化 1：增加路径存在性检查[cite: 1]
        if not filepath or not os.path.exists(filepath):
            raise Http404("Log file not found.")

        try:
            # 获取原始文件名[cite: 1]
            original_filename = os.path.basename(filepath)
            
            # 💡 优化 2：强制补全 .log 后缀，方便 Windows 识别[cite: 1]
            if not original_filename.endswith('.log'):
                display_name = original_filename + ".log"
            else:
                display_name = original_filename

            # 💡 优化 3：使用 FileResponse 处理二进制流，更安全[cite: 1]
            response = FileResponse(open(filepath, 'rb'))
            response['Content-Type'] = "application/octet-stream"
            
            # 💡 优化 4：解决中文文件名乱码及识别问题[cite: 1]
            # 使用 RFC 5987 标准指定文件名
            response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path(display_name))
            
            return response
        except Exception as e:
            # 打印具体错误方便调试
            print(f"Download Error: {e}")
            raise Http404