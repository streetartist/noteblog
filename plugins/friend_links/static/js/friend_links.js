/**
 * 友情链接插件JavaScript功能
 * 提供logo图片自动缩放和优化功能
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化友情链接logo优化
    initFriendLinkLogoOptimization();
});

/**
 * 初始化友情链接logo优化功能
 */
function initFriendLinkLogoOptimization() {
    const friendLinkLogos = document.querySelectorAll('.friend-link-logo');
    
    friendLinkLogos.forEach(function(logo) {
        // 图片加载完成后进行优化
        if (logo.complete) {
            optimizeLogo(logo);
        } else {
            logo.addEventListener('load', function() {
                optimizeLogo(logo);
            });
        }
        
        // 图片加载错误处理
        logo.addEventListener('error', function() {
            handleLogoError(logo);
        });
    });
}

/**
 * 优化单个logo图片
 * @param {HTMLImageElement} logo - logo图片元素
 */
function optimizeLogo(logo) {
    const naturalWidth = logo.naturalWidth;
    const naturalHeight = logo.naturalHeight;
    const aspectRatio = naturalWidth / naturalHeight;
    
    // 根据图片宽高比调整显示尺寸
    if (aspectRatio > 1.5) {
        // 宽图片，限制宽度
        logo.style.maxWidth = '28px';
        logo.style.maxHeight = '20px';
    } else if (aspectRatio < 0.67) {
        // 高图片，限制高度
        logo.style.maxWidth = '20px';
        logo.style.maxHeight = '28px';
    } else {
        // 接近正方形的图片，使用默认尺寸
        logo.style.maxWidth = '24px';
        logo.style.maxHeight = '24px';
    }
    
    // 添加加载完成的动画效果
    logo.style.opacity = '0';
    logo.style.transform = 'scale(0.8)';
    
    setTimeout(function() {
        logo.style.transition = 'all 0.3s ease';
        logo.style.opacity = '1';
        logo.style.transform = 'scale(1)';
    }, 100);
    
    // 为SVG图标添加特殊处理
    if (logo.src.includes('.svg') || logo.src.includes('data:image/svg')) {
        logo.style.padding = '0';
        logo.style.backgroundColor = 'transparent';
    }
}

/**
 * 处理logo加载错误
 * @param {HTMLImageElement} logo - logo图片元素
 */
function handleLogoError(logo) {
    // 创建一个默认的图标作为替代
    const defaultIcon = document.createElement('div');
    defaultIcon.className = 'friend-link-default-icon';
    defaultIcon.innerHTML = '🔗';
    defaultIcon.style.cssText = `
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #f0f0f0;
        border-radius: 4px;
        font-size: 14px;
        margin-right: 8px;
        flex-shrink: 0;
    `;
    
    // 在暗色主题下的样式
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        defaultIcon.style.backgroundColor = '#34495e';
        defaultIcon.style.color = '#ecf0f1';
    }
    
    // 替换失败的图片
    logo.parentNode.insertBefore(defaultIcon, logo);
    logo.remove();
}

/**
 * 动态调整logo容器布局
 */
function adjustLogoContainerLayout() {
    const friendLinkItems = document.querySelectorAll('.friend-link-item');
    
    friendLinkItems.forEach(function(item) {
        const logo = item.querySelector('.friend-link-logo, .friend-link-default-icon');
        const name = item.querySelector('.friend-link-name');
        
        if (logo && name) {
            // 确保logo和文字的对齐
            logo.style.flexShrink = '0';
            name.style.flex = '1';
            name.style.minWidth = '0'; // 允许文字换行
        }
    });
}

/**
 * 监听主题变化，调整logo样式
 */
function watchThemeChanges() {
    if (window.matchMedia) {
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        darkModeQuery.addListener(function(e) {
            // 主题变化时重新初始化logo优化
            setTimeout(function() {
                initFriendLinkLogoOptimization();
                adjustLogoContainerLayout();
            }, 100);
        });
    }
}

/**
 * 为友情链接添加懒加载功能
 */
function initLazyLoading() {
    const friendLinkLogos = document.querySelectorAll('.friend-link-logo[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        friendLinkLogos.forEach(function(img) {
            imageObserver.observe(img);
        });
    } else {
        // 降级处理，直接加载所有图片
        friendLinkLogos.forEach(function(img) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        });
    }
}

// 导出主要函数供外部使用
window.FriendLinks = {
    init: initFriendLinkLogoOptimization,
    adjustLayout: adjustLogoContainerLayout,
    watchTheme: watchThemeChanges,
    initLazyLoading: initLazyLoading
};

// 页面加载完成后执行初始化
window.addEventListener('load', function() {
    adjustLogoContainerLayout();
    watchThemeChanges();
    initLazyLoading();
});
