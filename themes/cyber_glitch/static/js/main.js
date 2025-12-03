document.addEventListener('DOMContentLoaded', () => {
    const glitchIntensity = document.body.dataset.glitchIntensity || 'medium';
    initNavToggle();
    initAuthModal();
    initCommentForm();
    const heroTitle = document.querySelector('.hero h1');
    if (heroTitle) {
        const text = heroTitle.textContent.trim();
        heroTitle.textContent = '';
        heroTitle.dataset.text = '';

        const typingSpeeds = {
            low: 140,
            medium: 90,
            high: 60,
        };

        let i = 0;
        function typeWriter() {
            if (i < text.length) {
                const currentText = heroTitle.textContent + text.charAt(i);
                heroTitle.textContent = currentText;
                heroTitle.dataset.text = currentText;
                i++;
                setTimeout(typeWriter, typingSpeeds[glitchIntensity] || typingSpeeds.medium);
            }
        }
        typeWriter();
    }

    const canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '-1';
    canvas.style.opacity = '0.1';
    canvas.style.pointerEvents = 'none';
    document.body.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    const computedStyle = window.getComputedStyle(document.body);
    const primaryColorValue = computedStyle.getPropertyValue('--cg-primary');
    const matrixColor = primaryColorValue ? primaryColorValue.trim() : '#0f0';

    const intensitySettings = {
        low: {
            matrixSpeed: 80,
            dropWidth: 32,
            matrixFont: '12pt monospace',
            stepFall: 14
        },
        medium: {
            matrixSpeed: 55,
            dropWidth: 24,
            matrixFont: '15pt monospace',
            stepFall: 18
        },
        high: {
            matrixSpeed: 35,
            dropWidth: 18,
            matrixFont: '18pt monospace',
            stepFall: 22
        }
    };

    const settings = intensitySettings[glitchIntensity] || intensitySettings.medium;

    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;
    let cols = Math.floor(width / settings.dropWidth) + 1;
    let ypos = Array(cols).fill(0);

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
        cols = Math.floor(width / settings.dropWidth) + 1;
        ypos = Array(cols).fill(0);
    });

    function matrix() {
        if (!ctx) return;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.15)';
        ctx.fillRect(0, 0, width, height);

        ctx.fillStyle = matrixColor;
        ctx.font = settings.matrixFont;

        ypos.forEach((y, ind) => {
            const text = String.fromCharCode(0x30A0 + Math.floor(Math.random() * 96));
            const x = ind * settings.dropWidth;
            ctx.fillText(text, x, y);
            if (y > 100 + Math.random() * 10000) {
                ypos[ind] = 0;
            } else {
                ypos[ind] = y + settings.stepFall;
            }
        });
    }

    setInterval(matrix, settings.matrixSpeed);

    function initNavToggle() {
        const navToggle = document.querySelector('[data-nav-toggle]');
        const nav = document.querySelector('[data-nav]');
        if (!navToggle || !nav) {
            return;
        }
        navToggle.addEventListener('click', () => {
            const expanded = navToggle.getAttribute('aria-expanded') === 'true';
            const newState = !expanded;
            navToggle.setAttribute('aria-expanded', String(newState));
            nav.classList.toggle('is-open', newState);
        });
    }

    function initAuthModal() {
        const authOverlay = document.querySelector('[data-auth-overlay]');
        if (!authOverlay) {
            return;
        }
        const panels = authOverlay.querySelectorAll('[data-auth-panel]');
        const openButtons = document.querySelectorAll('[data-auth-open]');
        const switchButtons = authOverlay.querySelectorAll('[data-auth-switch]');
        const closeButtons = authOverlay.querySelectorAll('[data-auth-close]');

        const showPanel = (panelName) => {
            if (!panelName) {
                return;
            }
            const target = authOverlay.querySelector(`[data-auth-panel="${panelName}"]`);
            if (!target) {
                return;
            }
            panels.forEach((panel) => {
                if (panel === target) {
                    panel.removeAttribute('hidden');
                } else {
                    panel.setAttribute('hidden', 'hidden');
                }
            });
            authOverlay.classList.add('visible');
            authOverlay.removeAttribute('hidden');
            document.body.classList.add('cg-auth-locked');
        };

        const hideOverlay = () => {
            authOverlay.classList.remove('visible');
            authOverlay.setAttribute('hidden', 'hidden');
            document.body.classList.remove('cg-auth-locked');
        };

        openButtons.forEach((btn) => {
            btn.addEventListener('click', (event) => {
                if (btn.tagName === 'A') {
                    event.preventDefault();
                }
                showPanel(btn.dataset.authOpen);
            });
        });

        switchButtons.forEach((btn) => {
            btn.addEventListener('click', () => {
                showPanel(btn.dataset.authSwitch);
            });
        });

        closeButtons.forEach((btn) => {
            btn.addEventListener('click', hideOverlay);
        });

        authOverlay.addEventListener('click', (event) => {
            if (event.target === authOverlay) {
                hideOverlay();
            }
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && authOverlay.classList.contains('visible')) {
                hideOverlay();
            }
        });

        const params = new URLSearchParams(window.location.search);
        const modalValue = params.get('modal');
        const allowedPanels = ['login', 'register', 'forgot_password'];
        if (modalValue && allowedPanels.includes(modalValue)) {
            showPanel(modalValue);
        }
    }

    function initCommentForm() {
        const form = document.querySelector('[data-comment-form]');
        if (!form) {
            return;
        }

        const messageEl = form.querySelector('[data-comment-message]');
        const parentInput = form.querySelector('[data-comment-parent]');
        const indicator = form.querySelector('[data-reply-indicator]');
        const targetLabel = form.querySelector('[data-reply-target]');
        const cancelReply = form.querySelector('[data-reply-cancel]');
        const setMessage = (text, isError = false) => {
            if (messageEl) {
                messageEl.textContent = text || '';
                messageEl.style.color = isError ? '#ff5f6d' : 'var(--cg-secondary)';
            }
        };

        const resetReply = () => {
            if (parentInput) {
                parentInput.value = '';
            }
            if (indicator) {
                indicator.hidden = true;
            }
            if (targetLabel) {
                targetLabel.textContent = '';
            }
        };

        if (cancelReply) {
            cancelReply.addEventListener('click', () => {
                resetReply();
            });
        }

        const replyButtons = document.querySelectorAll('[data-reply-button]');
        replyButtons.forEach((button) => {
            button.addEventListener('click', () => {
                const commentId = button.dataset.commentId;
                const author = button.dataset.author || '';
                if (parentInput) {
                    parentInput.value = commentId;
                }
                if (indicator) {
                    indicator.hidden = false;
                }
                if (targetLabel) {
                    targetLabel.textContent = author;
                }
                form.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });

        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = '提交中...';
            }
            setMessage('');

            const formData = new FormData(form);
            fetch('/comment', {
                method: 'POST',
                body: formData,
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data && data.success) {
                        setMessage(data.message || '评论已提交');
                        form.reset();
                        resetReply();
                        setTimeout(() => window.location.reload(), 800);
                    } else {
                        setMessage((data && (data.error || data.message)) || '提交失败，请稍后重试', true);
                    }
                })
                .catch(() => {
                    setMessage('网络异常，请稍后再试', true);
                })
                .finally(() => {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.textContent = '提交评论';
                    }
                });
        });
    }
});
