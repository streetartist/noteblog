// Theme helper JS — 当页面已由服务器端渲染并且 base.html 提供了全局 Vue 应用时，
// 避免重复创建/挂载 Vue 实例。此脚本只提供一些全局辅助方法。

// 全局搜索函数
function searchPosts(query) {
    if (!query.trim()) {
        if (typeof ElMessage !== 'undefined') {
            ElMessage.warning('请输入搜索关键词');
        } else {
            alert('请输入搜索关键词');
        }
        return;
    }
    window.location.href = `/search?q=${encodeURIComponent(query)}`;
}

// 全局分享函数
function sharePost(title, url, description) {
    if (navigator.share) {
        navigator.share({
            title: title,
            text: description,
            url: url
        }).catch(error => {
            console.log('分享取消或失败:', error);
        });
    } else {
        // 复制链接到剪贴板
        copyToClipboard(url);
    }
}

// 全局复制到剪贴板函数
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            if (typeof ElMessage !== 'undefined') {
                ElMessage.success('链接已复制到剪贴板');
            } else {
                alert('链接已复制到剪贴板');
            }
        }).catch(error => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

// 备用复制方法
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        if (typeof ElMessage !== 'undefined') {
            ElMessage.success('链接已复制到剪贴板');
        } else {
            alert('链接已复制到剪贴板');
        }
    } catch (error) {
        if (typeof ElMessage !== 'undefined') {
            ElMessage.error('复制失败，请手动复制链接');
        } else {
            alert('复制失败，请手动复制链接');
        }
    }
    
    document.body.removeChild(textArea);
}

// 全局点赞函数
function likePost(postId) {
    fetch(`/api/posts/${postId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 200) {
            if (typeof ElMessage !== 'undefined') {
                ElMessage.success('点赞成功！');
            } else {
                alert('点赞成功！');
            }
            // 更新点赞数
            const likeButton = document.querySelector(`[data-post-id="${postId}"] .like-count`);
            if (likeButton) {
                likeButton.textContent = data.data.like_count;
            }
        } else {
            if (typeof ElMessage !== 'undefined') {
                ElMessage.error(data.message || '点赞失败');
            } else {
                alert(data.message || '点赞失败');
            }
        }
    })
    .catch(error => {
        if (typeof ElMessage !== 'undefined') {
            ElMessage.error('点赞失败，请稍后重试');
        } else {
            alert('点赞失败，请稍后重试');
        }
    });
}

// 全局收藏函数
function bookmarkPost(postId) {
    fetch(`/api/posts/${postId}/bookmark`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 200) {
            if (typeof ElMessage !== 'undefined') {
                ElMessage.success(data.message);
            } else {
                alert(data.message);
            }
        } else {
            if (typeof ElMessage !== 'undefined') {
                ElMessage.error(data.message || '收藏失败');
            } else {
                alert(data.message || '收藏失败');
            }
        }
    })
    .catch(error => {
        if (typeof ElMessage !== 'undefined') {
            ElMessage.error('收藏失败，请稍后重试');
        } else {
            alert('收藏失败，请稍后重试');
        }
    });
}

// 全局格式化日期函数
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 30) {
        return date.toLocaleDateString();
    } else if (days > 0) {
        return `${days}天前`;
    } else if (hours > 0) {
        return `${hours}小时前`;
    } else if (minutes > 0) {
        return `${minutes}分钟前`;
    } else {
        return '刚刚';
    }
}

// 全局滚动到顶部函数
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// 全局处理滚动函数
function handleScroll() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const backToTopButton = document.querySelector('.back-to-top');
    
    if (backToTopButton) {
        if (scrollTop > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    }
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 添加返回顶部按钮
    const backToTopButton = document.createElement('div');
    backToTopButton.className = 'back-to-top';
    backToTopButton.innerHTML = '<i class="el-icon-arrow-up"></i>';
    backToTopButton.onclick = () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    };
    document.body.appendChild(backToTopButton);
    
    // 监听滚动事件
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        if (scrollTop > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });
    
    // 初始化代码高亮
    if (typeof Prism !== 'undefined') {
        Prism.highlightAll();
    }
    
    // 初始化图片懒加载
    initLazyLoading();
    
    // 初始化搜索框
    initSearchBox();
});

// 懒加载图片
function initLazyLoading() {
    const images = document.querySelectorAll('img[loading="lazy"]');
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    }
}

// 初始化搜索框
function initSearchBox() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    window.location.href = `/search?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }
}

// 添加返回顶部按钮样式
const style = document.createElement('style');
style.textContent = `
    .back-to-top {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        background: var(--primary-color, #409EFF);
        color: white;
        border-radius: 50%;
        display: none;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 2px 12px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        z-index: 1000;
    }
    
    .back-to-top:hover {
        background: #66b1ff;
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }
    
    .back-to-top i {
        font-size: 20px;
    }
    
    .search-input {
        border-radius: 20px;
    }
    
    .lazy {
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .lazy.loaded {
        opacity: 1;
    }
`;
document.head.appendChild(style);

// 导出全局函数
window.noteblog = {
    searchPosts: searchPosts,
    sharePost: sharePost,
    copyToClipboard: copyToClipboard,
    likePost: likePost,
    bookmarkPost: bookmarkPost,
    formatDate: formatDate,
    scrollToTop: scrollToTop,
    handleScroll: handleScroll
};

// 也将函数直接挂载到 window 对象上，方便直接调用
window.searchPosts = searchPosts;
window.sharePost = sharePost;
window.copyToClipboard = copyToClipboard;
window.likePost = likePost;
window.bookmarkPost = bookmarkPost;
window.formatDate = formatDate;
window.scrollToTop = scrollToTop;
window.handleScroll = handleScroll;
