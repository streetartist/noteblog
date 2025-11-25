/**
 * Hello World Plugin JavaScript
 * 提供插件的前端交互功能
 */

class HelloWorldPlugin {
    constructor() {
        this.name = 'hello_world';
        this.version = '1.0.0';
        this.config = {};
        this.init();
    }

    /**
     * 初始化插件
     */
    init() {
        this.loadConfig();
        this.bindEvents();
        this.createWidgets();
        console.log(`Hello World Plugin ${this.version} initialized`);
    }

    /**
     * 加载插件配置
     */
    async loadConfig() {
        try {
            const response = await fetch('/api/plugins/hello_world/config');
            if (response.ok) {
                this.config = await response.json();
            }
        } catch (error) {
            console.error('Failed to load plugin config:', error);
            this.config = {
                message: 'Hello from HelloWorld Plugin!',
                show_in_footer: true,
                append_message: false,
                add_prefix: false
            };
        }
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 页面加载完成后的处理
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.onDOMReady();
            });
        } else {
            this.onDOMReady();
        }

        // 监听自定义事件
        document.addEventListener('hello_world:show_message', (event) => {
            this.showMessage(event.detail.message || this.config.message);
        });

        document.addEventListener('hello_world:update_config', (event) => {
            this.updateConfig(event.detail);
        });
    }

    /**
     * DOM准备就绪时的处理
     */
    onDOMReady() {
        this.addFooterWidget();
        this.addAdminNavigation();
        this.initializeTooltips();
        this.setupFormHandlers();
    }

    /**
     * 创建插件小部件
     */
    createWidgets() {
        // 创建侧边栏小部件
        this.createSidebarWidget();
        
        // 创建内容插入点
        this.createContentInserts();
    }

    /**
     * 创建侧边栏小部件
     */
    createSidebarWidget() {
        const sidebar = document.querySelector('.sidebar, .widget-area');
        if (!sidebar) return;

        const widget = document.createElement('div');
        widget.className = 'hello-world-widget';
        widget.innerHTML = `
            <h3>Hello World</h3>
            <p>${this.config.message}</p>
            <button class="hello-world-button" onclick="helloWorldPlugin.showInteractiveMessage()">
                点击我
            </button>
        `;

        sidebar.appendChild(widget);
    }

    /**
     * 创建内容插入点
     */
    createContentInserts() {
        // 在文章内容后插入
        if (this.config.append_message) {
            const articles = document.querySelectorAll('article, .post-content');
            articles.forEach(article => {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'hello-world-alert';
                messageDiv.innerHTML = `
                    <strong>Hello World Plugin:</strong> ${this.config.message}
                `;
                article.appendChild(messageDiv);
            });
        }

        // 修改页面标题
        if (this.config.add_prefix) {
            const title = document.querySelector('title');
            if (title) {
                title.textContent = `👋 ${title.textContent}`;
            }
        }
    }

    /**
     * 添加页脚小部件
     */
    addFooterWidget() {
        if (!this.config.show_in_footer) return;

        const footer = document.querySelector('footer, .site-footer');
        if (!footer) return;

        const footerWidget = document.createElement('div');
        footerWidget.className = 'hello-world-footer';
        footerWidget.innerHTML = `
            <p>
                Powered by 
                <span class="message">${this.config.message}</span>
                - Hello World Plugin
            </p>
        `;

        footer.appendChild(footerWidget);
    }

    /**
     * 添加管理后台导航
     */
    addAdminNavigation() {
        const adminNav = document.querySelector('.admin-navigation, .admin-menu');
        if (!adminNav) return;

        const navItem = document.createElement('li');
        navItem.innerHTML = `
            <a href="/admin/hello_world" class="admin-nav-item">
                <i class="el-icon-chat-dot-round"></i>
                Hello World
            </a>
        `;

        adminNav.appendChild(navItem);
    }

    /**
     * 初始化工具提示
     */
    initializeTooltips() {
        const elements = document.querySelectorAll('[data-hello-world-tooltip]');
        elements.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.dataset.helloWorldTooltip);
            });

            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }

    /**
     * 设置表单处理器
     */
    setupFormHandlers() {
        const forms = document.querySelectorAll('.hello-world-form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit(form);
            });
        });
    }

    /**
     * 显示交互式消息
     */
    showInteractiveMessage() {
        this.showModal('Hello World!', `
            <div class="hello-world-modal-content">
                <h3>欢迎使用 Hello World 插件!</h3>
                <p>${this.config.message}</p>
                <div class="hello-world-stats">
                    <div class="hello-world-stat-item">
                        <div class="number">1.0.0</div>
                        <div class="label">插件版本</div>
                    </div>
                    <div class="hello-world-stat-item">
                        <div class="number">∞</div>
                        <div class="label">可能性</div>
                    </div>
                </div>
                <button class="hello-world-button" onclick="helloWorldPlugin.closeModal()">
                    关闭
                </button>
            </div>
        `);
    }

    /**
     * 显示消息
     */
    showMessage(message, type = 'info') {
        // 创建消息元素
        const messageEl = document.createElement('div');
        messageEl.className = `hello-world-alert ${type}`;
        messageEl.innerHTML = `
            <strong>Hello World:</strong> ${message}
            <button class="hello-world-close" onclick="this.parentElement.remove()">×</button>
        `;

        // 添加到页面顶部
        const container = document.querySelector('.container, main, body');
        if (container) {
            container.insertBefore(messageEl, container.firstChild);
        }

        // 自动移除
        setTimeout(() => {
            if (messageEl.parentElement) {
                messageEl.remove();
            }
        }, 5000);
    }

    /**
     * 显示模态框
     */
    showModal(title, content) {
        // 移除现有模态框
        this.closeModal();

        const modal = document.createElement('div');
        modal.className = 'hello-world-modal';
        modal.innerHTML = `
            <div class="hello-world-modal-content">
                <h2>${title}</h2>
                ${content}
            </div>
        `;

        document.body.appendChild(modal);

        // 点击背景关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal();
            }
        });
    }

    /**
     * 关闭模态框
     */
    closeModal() {
        const modal = document.querySelector('.hello-world-modal');
        if (modal) {
            modal.remove();
        }
    }

    /**
     * 显示工具提示
     */
    showTooltip(element, text) {
        this.hideTooltip();

        const tooltip = document.createElement('div');
        tooltip.className = 'hello-world-tooltip';
        tooltip.textContent = text;

        document.body.appendChild(tooltip);

        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
    }

    /**
     * 隐藏工具提示
     */
    hideTooltip() {
        const tooltip = document.querySelector('.hello-world-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    /**
     * 处理表单提交
     */
    async handleFormSubmit(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            this.showLoading(form);

            const response = await fetch('/api/plugins/hello_world/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.showMessage('操作成功!', 'success');
                form.reset();
            } else {
                this.showMessage(result.error || '操作失败!', 'error');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            this.showMessage('网络错误，请稍后重试', 'error');
        } finally {
            this.hideLoading(form);
        }
    }

    /**
     * 显示加载状态
     */
    showLoading(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="hello-world-loading"></span> 处理中...';
        }
    }

    /**
     * 隐藏加载状态
     */
    hideLoading(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = submitBtn.dataset.originalText || '提交';
        }
    }

    /**
     * 更新配置
     */
    async updateConfig(newConfig) {
        try {
            const response = await fetch('/api/plugins/hello_world/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newConfig)
            });

            if (response.ok) {
                this.config = { ...this.config, ...newConfig };
                this.showMessage('配置已更新', 'success');
                
                // 触发重新初始化
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                this.showMessage('配置更新失败', 'error');
            }
        } catch (error) {
            console.error('Config update error:', error);
            this.showMessage('网络错误', 'error');
        }
    }

    /**
     * 获取插件统计信息
     */
    async getStats() {
        try {
            const response = await fetch('/api/plugins/hello_world/stats');
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Failed to get stats:', error);
        }
        return null;
    }

    /**
     * 导出配置
     */
    exportConfig() {
        const dataStr = JSON.stringify(this.config, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = 'hello_world_config.json';
        link.click();
        
        URL.revokeObjectURL(url);
    }

    /**
     * 导入配置
     */
    importConfig(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const config = JSON.parse(e.target.result);
                this.updateConfig(config);
            } catch (error) {
                this.showMessage('配置文件格式错误', 'error');
            }
        };
        reader.readAsText(file);
    }
}

// 全局实例
window.helloWorldPlugin = new HelloWorldPlugin();

// 导出模块（如果支持）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HelloWorldPlugin;
}
