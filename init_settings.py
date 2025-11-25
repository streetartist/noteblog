#!/usr/bin/env python3
"""
初始化数据库设置脚本
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.setting import SettingManager

def init_settings():
    """初始化所有默认设置"""
    app = create_app()
    
    with app.app_context():
        try:
            # 初始化默认设置
            SettingManager.init_default_settings()
            print("✅ 设置初始化成功！")
            
            # 显示所有设置
            print("\n📋 当前设置:")
            general_settings = SettingManager.get_category('general')
            comment_settings = SettingManager.get_category('comment')
            
            print("\n🔧 基本设置:")
            for key, value in general_settings.items():
                print(f"  {key}: {value}")
            
            print("\n💬 评论设置:")
            for key, value in comment_settings.items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            print(f"❌ 设置初始化失败: {e}")
            return False
    
    return True

if __name__ == '__main__':
    init_settings()
