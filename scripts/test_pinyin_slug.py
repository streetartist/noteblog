#!/usr/bin/env python3
"""
测试拼音slug生成功能
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pypinyin import lazy_pinyin, Style
import re

def generate_slug(title):
    """生成slug的函数"""
    # 转换为拼音
    pinyin_list = lazy_pinyin(title, style=Style.NORMAL)
    slug = '-'.join(pinyin_list)
    
    # 清理特殊字符
    slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    
    return slug

def test_slug_generation():
    """测试slug生成"""
    test_cases = [
        "六种主要极限类型的标准证明步骤模板",
        "Hello World",
        "Python编程入门",
        "Flask Web开发",
        "数据库设计与优化",
        "机器学习算法详解",
        "中文标题测试",
        "Mixed 中英文 Title"
    ]
    
    print("测试拼音slug生成功能:")
    print("=" * 50)
    
    for title in test_cases:
        slug = generate_slug(title)
        print(f"标题: {title}")
        print(f"Slug: {slug}")
        print("-" * 30)

if __name__ == "__main__":
    test_slug_generation()
