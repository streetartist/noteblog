-- Noteblog数据库初始化脚本

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS noteblog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE noteblog;

-- 创建用户表
CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar VARCHAR(255),
    bio TEXT,
    website VARCHAR(255),
    location VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- 创建文章表
CREATE TABLE IF NOT EXISTS post (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    author_id INT NOT NULL,
    status ENUM('draft', 'published', 'private', 'trash') DEFAULT 'draft',
    comment_status ENUM('open', 'closed') DEFAULT 'open',
    password VARCHAR(255),
    featured_image VARCHAR(255),
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    published_at TIMESTAMP NULL,
    FOREIGN KEY (author_id) REFERENCES user(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_published_at (published_at),
    INDEX idx_author (author_id),
    FULLTEXT idx_title_content (title, content)
);

-- 创建分类表
CREATE TABLE IF NOT EXISTS category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES category(id) ON DELETE SET NULL,
    INDEX idx_parent (parent_id)
);

-- 创建标签表
CREATE TABLE IF NOT EXISTS tag (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建文章分类关联表
CREATE TABLE IF NOT EXISTS post_category (
    post_id INT NOT NULL,
    category_id INT NOT NULL,
    PRIMARY KEY (post_id, category_id),
    FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE CASCADE
);

-- 创建文章标签关联表
CREATE TABLE IF NOT EXISTS post_tag (
    post_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (post_id, tag_id),
    FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

-- 创建评论表
CREATE TABLE IF NOT EXISTS comment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    author_id INT NULL,
    author_name VARCHAR(100),
    author_email VARCHAR(120),
    author_url VARCHAR(255),
    author_ip VARCHAR(45),
    content TEXT NOT NULL,
    status ENUM('pending', 'approved', 'spam', 'trash') DEFAULT 'pending',
    parent_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES user(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_id) REFERENCES comment(id) ON DELETE CASCADE,
    INDEX idx_post (post_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- 创建插件表
CREATE TABLE IF NOT EXISTS plugin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    author VARCHAR(100),
    website VARCHAR(255),
    is_active BOOLEAN DEFAULT FALSE,
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active)
);

-- 创建插件钩子表
CREATE TABLE IF NOT EXISTS plugin_hook (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id INT NOT NULL,
    hook_name VARCHAR(100) NOT NULL,
    hook_type ENUM('action', 'filter') NOT NULL,
    priority INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plugin_id) REFERENCES plugin(id) ON DELETE CASCADE,
    INDEX idx_hook_name (hook_name),
    INDEX idx_plugin (plugin_id)
);

-- 创建主题表
CREATE TABLE IF NOT EXISTS theme (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    author VARCHAR(100),
    website VARCHAR(255),
    is_active BOOLEAN DEFAULT FALSE,
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (is_active)
);

-- 创建主题钩子表
CREATE TABLE IF NOT EXISTS theme_hook (
    id INT AUTO_INCREMENT PRIMARY KEY,
    theme_id INT NOT NULL,
    hook_name VARCHAR(100) NOT NULL,
    hook_type ENUM('action', 'filter') NOT NULL,
    priority INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (theme_id) REFERENCES theme(id) ON DELETE CASCADE,
    INDEX idx_hook_name (hook_name),
    INDEX idx_theme (theme_id)
);

-- 创建系统设置表
CREATE TABLE IF NOT EXISTS setting (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_name VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    value_type ENUM('string', 'integer', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_public (is_public)
);

-- 插入默认设置
INSERT IGNORE INTO setting (key_name, value, value_type, description, is_public) VALUES
('site_title', 'Noteblog', 'string', '网站标题', true),
('site_description', '一个基于Flask的博客系统', 'string', '网站描述', true),
('site_keywords', 'blog, flask, python', 'string', '网站关键词', true),
('site_author', 'Noteblog', 'string', '网站作者', true),
('posts_per_page', '10', 'integer', '每页显示文章数量', false),
('comment_moderation', 'true', 'boolean', '是否需要评论审核', false),
('allow_registration', 'true', 'boolean', '是否允许用户注册', false),
('default_role', 'user', 'string', '默认用户角色', false),
('theme', 'default', 'string', '当前主题', false),
('timezone', 'Asia/Shanghai', 'string', '时区设置', false),
('date_format', '%Y-%m-%d', 'string', '日期格式', false),
('time_format', '%H:%M:%S', 'string', '时间格式', false);

-- 插入默认分类
INSERT IGNORE INTO category (name, slug, description) VALUES
('未分类', 'uncategorized', '默认分类'),
('技术', 'tech', '技术相关文章'),
('生活', 'life', '生活随笔');

-- 插入默认标签
INSERT IGNORE INTO tag (name, slug, description) VALUES
('Flask', 'flask', 'Flask框架相关'),
('Python', 'python', 'Python编程语言'),
('Web开发', 'web-development', 'Web开发相关'),
('教程', 'tutorial', '教程类文章');

-- 创建默认管理员用户（密码：admin123）
INSERT IGNORE INTO user (username, email, password_hash, display_name, is_admin, is_active, email_verified) VALUES
('admin', 'admin@example.com', 'pbkdf2:sha256:260000$salt$hash', '管理员', true, true, true);

-- 创建默认主题记录
INSERT IGNORE INTO theme (name, version, description, author, is_active, config) VALUES
('default', '1.0.0', '默认主题', 'Noteblog Team', true, '{"color_scheme": "default", "layout": "sidebar-right"}');

-- 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_post_slug ON post(slug);
CREATE INDEX IF NOT EXISTS idx_category_slug ON category(slug);
CREATE INDEX IF NOT EXISTS idx_tag_slug ON tag(slug);
CREATE INDEX IF NOT EXISTS idx_user_username ON user(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);

-- 创建视图：文章统计
CREATE OR REPLACE VIEW post_stats AS
SELECT 
    p.id,
    p.title,
    p.view_count,
    p.like_count,
    COUNT(DISTINCT c.id) as comment_count,
    COUNT(DISTINCT pc.category_id) as category_count,
    COUNT(DISTINCT pt.tag_id) as tag_count
FROM post p
LEFT JOIN comment c ON p.id = c.post_id AND c.status = 'approved'
LEFT JOIN post_category pc ON p.id = pc.post_id
LEFT JOIN post_tag pt ON p.id = pt.post_id
WHERE p.status = 'published'
GROUP BY p.id, p.title, p.view_count, p.like_count;

-- 创建视图：用户统计
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    u.display_name,
    COUNT(DISTINCT p.id) as post_count,
    COUNT(DISTINCT c.id) as comment_count,
    SUM(p.view_count) as total_views
FROM user u
LEFT JOIN post p ON u.id = p.author_id AND p.status = 'published'
LEFT JOIN comment c ON u.id = c.author_id AND c.status = 'approved'
GROUP BY u.id, u.username, u.display_name;

-- 设置字符集
ALTER DATABASE noteblog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
