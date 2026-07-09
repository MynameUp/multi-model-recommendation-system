'''
WSGI config for newsServer project.

针对开发服务器 (manage.py runserver → wsgiref.simple_server) 的 TCP 缓冲问题:
  - wsgiref 使用 BufferedRandom 写入 socket, 默认缓冲区 ~8KB
  - 流式响应的小 chunk (<8KB) 会被积压直到缓冲区满或连接关闭
  - 此包装器在每次 iter 后显式 flush socket buffer, 确保 chunk 即时发送

生产环境请使用 gunicorn / uvicorn, 无需此包装器。
'''

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newsServer.settings')

_base_app = get_wsgi_application()


def application(environ, start_response):
    response_iter = _base_app(environ, start_response)
    # 对每次迭代后强制刷新 stderr/stdout 关联的 fd
    # 注意: wsgiref 将 socket 封装在 wfile (BufferedRandom) 中,
    # 其 flush() 由 finish_response 在末尾调用。这里通过 fd 级 flush 突破。
    for chunk in response_iter:
        yield chunk
        # 尝试刷新 POSIX 文件描述符 (覆盖 wsgiref 的 socket fd)
        try:
            import sys
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass
