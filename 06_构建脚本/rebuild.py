# -*- coding: utf-8 -*-
"""重建 docx（嵌入最新图片）"""
import subprocess, sys, os
ROOT = r"C:\dev\projects\software engineering\yi-yue"
subprocess.run([sys.executable, os.path.join(ROOT, "06_构建脚本", "md2docx.py")], check=True)
