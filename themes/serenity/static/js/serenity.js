class SerenityTheme {
    constructor() {
        this.nav = document.querySelector('[data-nav]');
        this.navToggle = document.querySelector('[data-nav-toggle]');
        this.searchModal = document.querySelector('.serenity-search-modal');
        this.searchToggle = document.querySelector('[data-search-toggle]');
        this.searchClose = document.querySelector('[data-search-close]');
        this.backToTop = document.querySelector('.serenity-back-to-top');
        this.themeToggle = document.querySelector('.theme-toggle');
        this.activeModal = null;
        this.modalMap = {};
        this.init();
    }

    init() {
        this.restoreTheme();
        this.initNav();
        this.initSearch();
        this.initModals();
        this.initBackToTop();
        this.initCommentForm();
        this.observeHeader();
        this.registerGlobalShortcuts();
        this.initLikeInteractions();
    }

    restoreTheme() {
        if (!this.themeToggle) {
            return;
        }
        const saved = localStorage.getItem('serenity-theme');
        const initial = saved || document.documentElement.getAttribute('data-theme') || 'light';
        this.applyTheme(initial);
        this.themeToggle.addEventListener('click', () => {
            const next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
            this.applyTheme(next);
            localStorage.setItem('serenity-theme', next);
        });
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        if (this.themeToggle) {
            this.themeToggle.textContent = theme === 'dark' ? '🌙' : '☀️';
        }
        window.dispatchEvent(new CustomEvent('noteblog:theme-change', { detail: { theme: theme } }));
    }

    initNav() {
        if (!this.nav || !this.navToggle) {
            return;
        }
        this.navToggle.addEventListener('click', () => {
            this.nav.classList.toggle('open');
        });
        this.nav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                this.nav.classList.remove('open');
            });
        });
        document.addEventListener('click', (event) => {
            if (!this.nav.contains(event.target) && !this.navToggle.contains(event.target)) {
                this.nav.classList.remove('open');
            }
        });
    }

    initSearch() {
        if (!this.searchModal) {
            return;
        }
        const toggleModal = (open) => {
            this.searchModal.classList.toggle('active', open);
            document.body.classList.toggle('serenity-backdrop-open', open);
            const input = this.searchModal.querySelector('input');
            if (open && input) {
                setTimeout(() => input.focus(), 60);
            }
        };
        this.searchToggle?.addEventListener('click', () => toggleModal(true));
        this.searchClose?.addEventListener('click', () => toggleModal(false));
        this.searchModal.addEventListener('click', (event) => {
            if (event.target === this.searchModal) {
                toggleModal(false);
            }
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                toggleModal(false);
            }
        });
    }

    initModals() {
        document.querySelectorAll('.serenity-modal').forEach(modal => {
            const key = modal.dataset.modal;
            if (key) {
                this.modalMap[key] = modal;
            }
        });
        const toggleBodyLock = () => {
            const active = Object.values(this.modalMap).some(modal => modal.classList.contains('active'));
            document.body.classList.toggle('serenity-backdrop-open', active);
        };
        const openModal = (name) => {
            const modal = this.modalMap[name];
            if (!modal) return;
            Object.values(this.modalMap).forEach(item => item.classList.remove('active'));
            modal.classList.add('active');
            this.activeModal = name;
            toggleBodyLock();
            const firstField = modal.querySelector('input, textarea, button');
            if (firstField) {
                setTimeout(() => firstField.focus(), 80);
            }
        };
        const closeAll = () => {
            Object.values(this.modalMap).forEach(item => item.classList.remove('active'));
            this.activeModal = null;
            toggleBodyLock();
        };
        document.querySelectorAll('[data-modal-trigger]').forEach(btn => {
            btn.addEventListener('click', (event) => {
                event.preventDefault();
                openModal(btn.dataset.modalTrigger);
            });
        });
        document.querySelectorAll('[data-modal-close]').forEach(btn => {
            btn.addEventListener('click', closeAll);
        });
        document.querySelectorAll('[data-modal-switch]').forEach(btn => {
            btn.addEventListener('click', (event) => {
                event.preventDefault();
                openModal(btn.dataset.modalSwitch);
            });
        });
        Object.values(this.modalMap).forEach(modal => {
            modal.addEventListener('click', (event) => {
                if (event.target === modal) {
                    closeAll();
                }
            });
        });
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.activeModal) {
                closeAll();
            }
        });
    }

    initBackToTop() {
        if (!this.backToTop) return;
        const update = () => {
            if (window.scrollY > 360) {
                this.backToTop.classList.add('visible');
            } else {
                this.backToTop.classList.remove('visible');
            }
        };
        this.backToTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
        window.addEventListener('scroll', update, { passive: true });
        update();
    }

    initCommentForm() {
        const form = document.querySelector('.comment-form');
        if (!form) return;
        const cancelBtn = form.querySelector('[data-cancel-reply]');
        const parentInput = form.querySelector('input[name="parent_id"]');
        const replyInfo = form.querySelector('[data-reply-info]');
        const replyNameTarget = form.querySelector('[data-reply-name]');
        const textarea = form.querySelector('textarea[name="content"], textarea');

        // autosize helper for textarea
        const autosize = (el) => {
            if (!el) return;
            el.style.height = 'auto';
            const max = Math.min(window.innerHeight * 0.6, 9999);
            el.style.height = Math.min(el.scrollHeight, max) + 'px';
        };
        if (textarea) {
            autosize(textarea);
            textarea.addEventListener('input', () => autosize(textarea));
            window.addEventListener('resize', () => autosize(textarea));
            form.addEventListener('reset', () => setTimeout(() => autosize(textarea), 30));
        }

        const toggleReplyInfo = (active, authorName = '') => {
            if (!replyInfo) return;
            if (active) {
                replyInfo.removeAttribute('hidden');
                replyInfo.classList.add('active');
                if (replyNameTarget) {
                    replyNameTarget.textContent = authorName || '该评论';
                }
            } else {
                replyInfo.setAttribute('hidden', 'hidden');
                replyInfo.classList.remove('active');
                if (replyNameTarget) {
                    replyNameTarget.textContent = '';
                }
            }
        };

        const resetReply = () => {
            if (parentInput) {
                parentInput.value = '';
            }
            toggleReplyInfo(false);
            if (textarea) {
                if (textarea.dataset.replyPrefill && textarea.value === textarea.dataset.replyPrefill) {
                    textarea.value = '';
                }
                delete textarea.dataset.replyPrefill;
            }
        };

        const bindReplyButtons = () => {
            document.querySelectorAll('.comment-reply-btn').forEach(btn => {
                if (btn.dataset.serenityBound) return;
                btn.dataset.serenityBound = '1';
                btn.addEventListener('click', (event) => {
                    event.preventDefault();
                    if (!parentInput) return;
                    const commentId = btn.dataset.commentId;
                    if (!commentId) return;

                    parentInput.value = commentId;
                    const authorName = btn.dataset.authorName || '';
                    toggleReplyInfo(true, authorName);

                    if (textarea && authorName) {
                        const mentionText = `@${authorName} `;
                        const onlyAutoFill = textarea.dataset.replyPrefill && textarea.value === textarea.dataset.replyPrefill;
                        if (!textarea.value || onlyAutoFill) {
                            textarea.value = mentionText;
                            textarea.dataset.replyPrefill = mentionText;
                        }
                    }

                    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    textarea?.focus();
                    if (textarea && typeof textarea.setSelectionRange === 'function') {
                        const length = textarea.value.length;
                        textarea.setSelectionRange(length, length);
                    }
                });
            });
        };

        bindReplyButtons();
        window.addEventListener('serenity:content-updated', bindReplyButtons);

        cancelBtn?.addEventListener('click', (event) => {
            event.preventDefault();
            resetReply();
        });

        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const submit = form.querySelector('button[type="submit"]');
            submit.disabled = true;
            submit.textContent = '提交中...';
            const payload = Object.fromEntries(new FormData(form).entries());
            fetch('/api/comments', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
                .then(async (res) => {
                    if (!res.ok) {
                        const error = await res.json().catch(() => ({}));
                        throw new Error(error.message || '提交失败');
                    }
                    return res.json();
                })
                .then((response) => {
                    this.showToast(response.message || '评论提交成功');
                    form.reset();
                    resetReply();
                    window.dispatchEvent(new CustomEvent('serenity:content-updated', {
                        detail: { root: document.querySelector('.comments-block') }
                    }));
                })
                .catch((error) => this.showToast(error.message || '提交失败，请稍后重试', 'error'))
                .finally(() => {
                    submit.disabled = false;
                    submit.textContent = '提交评论';
                });
        });
    }

    observeHeader() {
        const header = document.querySelector('.serenity-header');
        if (!header) return;
        let last = 0;
        window.addEventListener('scroll', () => {
            const current = window.scrollY;
            header.classList.toggle('shadow', current > 20);
            const scrollingUp = current < last;
            header.classList.toggle('hidden', current > 120 && !scrollingUp);
            last = current;
        }, { passive: true });
    }

    registerGlobalShortcuts() {
        document.addEventListener('keydown', (event) => {
            if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
                event.preventDefault();
                this.searchToggle?.click();
            }
        });
    }

    initLikeInteractions() {
        this.bindPostLikeButton();
        this.bindCommentLikeButtons(document);
        window.addEventListener('serenity:content-updated', (event) => {
            const root = event?.detail?.root;
            this.bindCommentLikeButtons(root instanceof Element ? root : document);
        });
    }

    bindPostLikeButton() {
        const button = document.querySelector('[data-like-post][data-post-id]');
        if (!button || button.dataset.likeBound) {
            return;
        }
        button.dataset.likeBound = '1';

        button.addEventListener('click', async () => {
            const postId = Number(button.dataset.postId);
            if (!postId || button.dataset.likeProcessing === '1') {
                return;
            }

            button.dataset.likeProcessing = '1';
            button.disabled = true;

            const currentlyLiked = button.dataset.liked === 'true';
            const payload = { action: currentlyLiked ? 'unlike' : 'like' };

            try {
                const result = await this.postJson(`/api/posts/${postId}/like`, payload);
                this.applyPostLikeState(button, result?.data);
                this.showToast(result?.message || (result?.data?.liked ? '谢谢喜欢！' : '已取消喜欢'));
            } catch (error) {
                console.error('[SerenityTheme] 点赞文章失败', error);
                this.showToast(error.message || '点赞失败，请稍后重试', 'error');
            } finally {
                button.dataset.likeProcessing = '0';
                button.disabled = false;
            }
        });
    }

    bindCommentLikeButtons(root = document) {
        const scope = root && typeof root.querySelectorAll === 'function' ? root : document;
        const buttons = scope.querySelectorAll?.('.comment-like-btn[data-comment-id]') || [];
        buttons.forEach(button => {
            if (button.dataset.likeBound) {
                return;
            }
            button.dataset.likeBound = '1';

            button.addEventListener('click', async () => {
                const commentId = Number(button.dataset.commentId);
                if (!commentId || button.dataset.likeProcessing === '1') {
                    return;
                }

                button.dataset.likeProcessing = '1';
                button.disabled = true;

                const currentlyLiked = button.dataset.liked === 'true';
                const payload = { action: currentlyLiked ? 'unlike' : 'like' };

                try {
                    const result = await this.postJson(`/api/comments/${commentId}/like`, payload);
                    this.applyCommentLikeState(button, result?.data);
                    this.showToast(result?.message || (result?.data?.liked ? '感谢点赞评论' : '已取消对评论的点赞'));
                } catch (error) {
                    console.error('[SerenityTheme] 点赞评论失败', error);
                    this.showToast(error.message || '点赞评论失败，请稍后重试', 'error');
                } finally {
                    button.dataset.likeProcessing = '0';
                    button.disabled = false;
                }
            });
        });
    }

    applyPostLikeState(button, data = {}) {
        const liked = Boolean(data?.liked);
        button.dataset.liked = liked ? 'true' : 'false';
        button.classList.toggle('liked', liked);
        const likeCount = typeof data?.like_count === 'number' ? data.like_count : null;
        if (likeCount !== null) {
            const counter = button.querySelector('[data-like-count]');
            if (counter) {
                counter.textContent = likeCount;
            } else {
                button.textContent = `喜欢 · ${likeCount}`;
            }
        }
    }

    applyCommentLikeState(button, data = {}) {
        const liked = Boolean(data?.liked);
        button.dataset.liked = liked ? 'true' : 'false';
        button.classList.toggle('liked', liked);
        const likeCount = typeof data?.like_count === 'number' ? data.like_count : null;
        if (likeCount !== null) {
            const counter = button.querySelector('[data-like-count]');
            if (counter) {
                counter.textContent = likeCount;
            } else {
                button.textContent = `赞 · ${likeCount}`;
            }
        }
    }

    async postJson(url, payload) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload || {})
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || (data?.status && data.status >= 400)) {
            const error = new Error(data?.message || '请求失败');
            error.data = data;
            throw error;
        }
        return data;
    }

    hydratePostPage() {
        const holder = document.getElementById('serenity-post-data');
        if (!holder) return;
        this.postData = {
            id: Number(holder.dataset.postId || 0),
            title: holder.dataset.postTitle || '',
            siteTitle: holder.dataset.siteTitle || ''
        };
    }

    copyLink(url) {
        // 优先使用现代 Clipboard API（需要 HTTPS 或 localhost）
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(url)
                .then(() => this.showToast('链接已复制'))
                .catch(() => this.fallbackCopy(url));
            return;
        }
        // 回退到传统方法
        this.fallbackCopy(url);
    }

    fallbackCopy(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        textarea.style.top = '0';
        textarea.setAttribute('readonly', '');
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            this.showToast('链接已复制');
        } catch (err) {
            this.showToast('复制失败，请手动选择链接', 'error');
        }
        document.body.removeChild(textarea);
    }

    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `serenity-toast serenity-toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add('visible'));
        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => toast.remove(), 300);
        }, 2400);
    }
}

window.serenityTheme = new SerenityTheme();
window.serenityTheme.hydratePostPage();
window.serenityTheme.copyLink = window.serenityTheme.copyLink.bind(window.serenityTheme);
