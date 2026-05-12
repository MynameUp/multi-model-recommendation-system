# -*- coding: utf-8 -*-
# test_dependencies.py
import sys
import os

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

dependencies = {
    'setuptools': 'pkg_resources',
    'sentence_transformers': 'sentence_transformers',
    'faiss': 'faiss',
    'numpy': 'numpy',
    'pymysql': 'pymysql',
    'django': 'django',
}

print("检查项目依赖...")
print("=" * 50)

for package_name, import_name in dependencies.items():
    try:
        __import__(import_name)
        print(f"[OK] {package_name:30s} - 已安装")
    except ImportError as e:
        print(f"[FAIL] {package_name:30s} - 未安装 ({e})")
    except Exception as e:
        print(f"[ERROR] {package_name:30s} - 检查失败 ({e})")

print("=" * 50)
print("依赖检查完成")
