"""
Markdown处理服务
"""
from html import escape

from markdown_it import MarkdownIt
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound
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
            'hr', 'div', 'span',
            'section',
            'input', 'label', 'mark', 'kbd', 'sub', 'sup',
            'details', 'summary'
        ]

        self.allowed_attributes = {
            **ALLOWED_ATTRIBUTES,
            'a': ['href', 'title', 'target', 'rel', 'id', 'class'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'code': ['class'],
            'pre': ['class'],
            'div': ['class'],
            'span': ['class'],
            'section': ['class'],
            'ul': ['class'],
            'ol': ['class'],
            'hr': ['class'],
            'th': ['align'],
            'td': ['align'],
            'h1': ['id', 'class'],
            'h2': ['id', 'class'],
            'h3': ['id', 'class'],
            'h4': ['id', 'class'],
            'h5': ['id', 'class'],
            'h6': ['id', 'class'],
            'input': ['type', 'checked', 'disabled', 'class'],
            'label': ['class'],
            'li': ['id', 'class'],
            'sup': ['id', 'class']
        }
        
        self.md = (
            MarkdownIt(
                'commonmark',
                {
                    'html': True,
                    'breaks': False,
                    'linkify': False,
                    'typographer': False,
                    'langPrefix': 'language-',
                    'highlight': self._highlight_code
                }
            )
            .enable('table')
            .enable('strikethrough')
            .use(deflist_plugin)
            .use(dollarmath_plugin)
            .use(footnote_plugin)
            .use(tasklists_plugin, enabled=True, label=True)
        )

    def _highlight_code(self, code, lang, attrs):
        """使用 Pygments 高亮代码块，并保持 markdown-it 的代码块结构。"""
        if not lang:
            return ''

        try:
            lexer = get_lexer_by_name(lang)
        except ClassNotFound:
            lexer = TextLexer()

        formatter = HtmlFormatter(nowrap=True)
        class_name = f'language-{escape(lang, quote=True)}'
        highlighted = highlight(code, lexer, formatter)
        return f'<pre class="highlight"><code class="{class_name}">{highlighted}</code></pre>'

    def _parse_tokens(self, text):
        env = {}
        tokens = self.md.parse(text, env)
        self._apply_heading_ids(tokens)
        return tokens, env

    def _apply_heading_ids(self, tokens):
        seen_slugs = {}

        for index, token in enumerate(tokens):
            if token.type != 'heading_open':
                continue

            existing_id = token.attrGet('id')
            if existing_id:
                seen_slugs[existing_id] = seen_slugs.get(existing_id, 0) + 1
                continue

            inline = tokens[index + 1] if index + 1 < len(tokens) else None
            heading_text = self._token_text(inline) if inline else ''
            token.attrSet('id', self._unique_slug(heading_text, seen_slugs))

    def _token_text(self, token):
        if not token:
            return ''

        if token.children:
            return ''.join(self._token_text(child) for child in token.children)

        return token.content or ''

    def _unique_slug(self, text, seen_slugs):
        base = re.sub(r'[^\w\s-]', '', text, flags=re.UNICODE).strip().lower()
        base = re.sub(r'[-\s]+', '-', base).strip('-') or 'section'
        count = seen_slugs.get(base, 0)
        seen_slugs[base] = count + 1
        return base if count == 0 else f'{base}-{count}'
    
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
        
        tokens, env = self._parse_tokens(text)
        html = self.md.renderer.render(tokens, self.md.options, env)
        
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
        
        tokens, _ = self._parse_tokens(text)
        items = []

        for index, token in enumerate(tokens):
            if token.type != 'heading_open':
                continue

            inline = tokens[index + 1] if index + 1 < len(tokens) else None
            title = self._token_text(inline).strip()
            if not title:
                continue

            items.append({
                'level': token.tag[1],
                'id': token.attrGet('id'),
                'title': title
            })

        if not items:
            return ''

        html = ['<div class="toc">', '<ul>']
        for item in items:
            html.append(
                f'<li class="toc-level-{item["level"]}">'
                f'<a href="#{escape(item["id"], quote=True)}">{escape(item["title"])}</a>'
                '</li>'
            )
        html.extend(['</ul>', '</div>'])
        return ''.join(html)
    
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
