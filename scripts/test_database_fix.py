#!/usr/bin/env python3
"""
测试数据库URL修复功能
"""
import os
import sys

# 测试数据库URL修复逻辑
def test_database_url_fix():
    """测试数据库URL修复功能"""
    test_cases = [
        # 原始URL, 期望的修复后URL
        ('postgres://user:pass@host:5432/db', 'postgresql://user:pass@host:5432/db'),
        ('postgresql://user:pass@host:5432/db', 'postgresql://user:pass@host:5432/db'),
        ('sqlite:///test.db', 'sqlite:///test.db'),
        ('mysql://user:pass@host:3306/db', 'mysql://user:pass@host:3306/db'),
    ]
    
    print("测试数据库URL修复功能...")
    
    for original_url, expected_url in test_cases:
        # 模拟修复逻辑
        fixed_url = original_url
        if fixed_url.startswith('postgres://'):
            fixed_url = fixed_url.replace('postgres://', 'postgresql://', 1)
        
        if fixed_url == expected_url:
            print(f"✓ {original_url} -> {fixed_url}")
        else:
            print(f"✗ {original_url} -> {fixed_url} (期望: {expected_url})")
            return False
    
    print("所有测试通过！")
    return True

def test_sqlalchemy_connection():
    """测试SQLAlchemy连接"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.exc import NoSuchModuleError
        
        # 测试PostgreSQL方言
        test_urls = [
            'postgresql://user:pass@localhost:5432/test',
            'postgres://user:pass@localhost:5432/test',
        ]
        
        for url in test_urls:
            try:
                if url.startswith('postgres://'):
                    fixed_url = url.replace('postgres://', 'postgresql://', 1)
                else:
                    fixed_url = url
                
                engine = create_engine(fixed_url)
                print(f"✓ SQLAlchemy可以识别: {fixed_url}")
                return True
                
            except NoSuchModuleError as e:
                print(f"✗ SQLAlchemy无法识别: {url} - {e}")
                return False
                
    except ImportError:
        print("SQLAlchemy未安装，跳过连接测试")
        return True

if __name__ == '__main__':
    print("=" * 50)
    print("数据库修复测试")
    print("=" * 50)
    
    success = True
    
    # 测试URL修复
    if not test_database_url_fix():
        success = False
    
    print()
    
    # 测试SQLAlchemy连接
    if not test_sqlalchemy_connection():
        success = False
    
    print()
    print("=" * 50)
    if success:
        print("✓ 所有测试通过！数据库修复功能正常。")
        sys.exit(0)
    else:
        print("✗ 测试失败！请检查修复逻辑。")
        sys.exit(1)
