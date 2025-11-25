"""
Markdown处理服务
"""
import markdown
from markdown.extensions import codehilite, tables, toc, fenced_code
from bleach import clean
from bleach.sanitizer import ALLOWED_TAGS, ALLOWED_ATTRIBUTES
import re

class MarkdownService:
    """Markdown处理服务类"""
    
    def __init__(self):
        # 配置允许的HTML标签和属性
        self.allowed_tags = list(ALLOWED_TAGS) + [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'br', 'strong', 'em', 'u', 's', 'del', 'ins',
            'ul', 'ol', 'li', 'dl', 'dt', 'dd',
            'blockquote', 'pre', 'code',
            'a', 'img',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'hr', 'div', 'span'
        ]
        
        self.allowed_attributes = {
            **ALLOWED_ATTRIBUTES,
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'code': ['class'],
            'pre': ['class'],
            'div': ['class'],
            'span': ['class'],  # 数学公式会使用span标签
            'th': ['align'],
            'td': ['align'],
            'h1': ['id'],
            'h2': ['id'],
            'h3': ['id'],
            'h4': ['id'],
            'h5': ['id'],
            'h6': ['id']
        }
        
        # 初始化Markdown处理器
        self.md = markdown.Markdown(
            extensions=[
                'codehilite',
                'fenced_code',
                'tables',
                'toc',
                'nl2br',
                'attr_list',
                'def_list',
                'footnotes',
                'admonition',
                'pymdownx.arithmatex'
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True
                },
                'toc': {
                    'permalink': True,
                    'permalink_class': 'headerlink'
                },
                'pymdownx.arithmatex': {
                    'generic': True
                }
            }
        )
    
    def render(self, text, sanitize=True):
        """
        将Markdown文本转换为HTML
        
        Args:
            text (str): Markdown文本
            sanitize (bool): 是否进行HTML清理，默认为True
            
        Returns:
            str: HTML文本
        """
        if not text:
            return ''
        
        # 转换Markdown为HTML
        html = self.md.convert(text)
        
        # 如果需要，进行HTML清理
        if sanitize:
            html = clean(
                html,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                strip=True
            )
        
        return html
    
    def render_excerpt(self, text, length=150, sanitize=True):
        """
        生成摘要，去除HTML标签
        
        Args:
            text (str): Markdown文本
            length (int): 摘要长度
            sanitize (bool): 是否进行HTML清理
            
        Returns:
            str: 摘要文本
        """
        if not text:
            return ''
        
        # 先转换为HTML
        html = self.render(text, sanitize)
        
        # 去除HTML标签
        text_only = re.sub(r'<[^>]+>', '', html)
        
        # 清理多余的空白字符
        text_only = re.sub(r'\s+', ' ', text_only).strip()
        
        # 截取指定长度
        if len(text_only) > length:
            text_only = text_only[:length] + '...'
        
        return text_only
    
    def get_toc(self, text):
        """
        获取目录
        
        Args:
            text (str): Markdown文本
            
        Returns:
            str: 目录HTML
        """
        if not text:
            return ''
        
        # 重置Markdown处理器状态
        self.md.reset()
        
        # 转换文本
        self.md.convert(text)
        
        # 获取目录
        toc = getattr(self.md, 'toc', '')
        return toc
    
    def is_markdown(self, text):
        """
        检查文本是否包含Markdown语法
        
        Args:
            text (str): 要检查的文本
            
        Returns:
            bool: 是否包含Markdown语法
        """
        if not text:
            return False
        
        # 检查常见的Markdown语法模式
        markdown_patterns = [
            r'^#{1,6}\s+',  # 标题
            r'\*\*.*?\*\*',  # 粗体
            r'\*.*?\*',  # 斜体
            r'```.*?```',  # 代码块
            r'`.*?`',  # 行内代码
            r'\[.*?\]\(.*?\)',  # 链接
            r'!\[.*?\]\(.*?\)',  # 图片
            r'^\s*[-*+]\s+',  # 无序列表
            r'^\s*\d+\.\s+',  # 有序列表
            r'^\s*>\s+',  # 引用
            r'\|.*\|',  # 表格
        ]
        
        for pattern in markdown_patterns:
            if re.search(pattern, text, re.MULTILINE | re.DOTALL):
                return True
        
        return False

# 创建全局实例
markdown_service = MarkdownService()
