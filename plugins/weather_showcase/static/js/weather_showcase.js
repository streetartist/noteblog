(function() {
    const root = document.querySelector('[data-weather-stage]');
    if (!root) return;

    // Keep overlay above content but non-blocking for page interactions.
    root.style.zIndex = root.style.zIndex || '9999';
    root.style.pointerEvents = 'none';

    const ds = root.dataset || {};
    const cfg = Object.assign({
        default_type: 'rain',
        intensity: 3,
        auto_rotate: false,
        rotate_seconds: 18,
        show_toggle: true,
        accent_color: '#7dd3fc'
    }, window.__WEATHER_SHOWCASE_CONFIG || {});

    const config = {
        type: (ds.weatherType || cfg.default_type || 'rain').toLowerCase(),
        intensity: clampInt(ds.weatherIntensity || cfg.intensity || 3, 1, 5),
        autoRotate: ds.weatherRotate === 'true' || cfg.auto_rotate === true,
        rotateSeconds: clampInt(ds.weatherRotateSeconds || cfg.rotate_seconds || 18, 5, 120),
        showToggle: ds.weatherToggle !== 'false' && cfg.show_toggle !== false,
        accent: ds.weatherAccent || cfg.accent_color || '#7dd3fc'
    };

    const allowedTypes = ['rain', 'snow', 'stars', 'meteors'];
    if (!allowedTypes.includes(config.type)) {
        config.type = 'rain';
    }

    const stage = root.querySelector('.weather-stage') || root;
    const toggleBtn = root.querySelector('[data-weather-toggle]');
    const legend = root.querySelector('[data-weather-legend]');

    if (!config.showToggle && toggleBtn) {
        toggleBtn.style.display = 'none';
    }

    const canvas = document.createElement('canvas');
    stage && stage.appendChild(canvas);
    const ctx = canvas.getContext('2d');

    // aurora feature removed

    let particles = [];
    let meteors = [];
    let stars = [];
    
    let stopped = false;
    let rotateTimer = null;
    let currentType = config.type;
    let rafId = null;
    

    // NOTE: aurora removed


    // aurora removed — no band data needed

    function hexToRgb(hex) {
        const cleaned = (hex || '').replace('#', '');
        if (cleaned.length !== 3 && cleaned.length !== 6) return [125, 211, 252];
        const full = cleaned.length === 3 ? cleaned.split('').map(c => c + c).join('') : cleaned;
        const num = parseInt(full, 16);
        return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
    }

    // colorWithAlpha removed; aurora colors no longer used

    function clampInt(val, min, max) {
        const n = parseInt(val, 10);
        if (isNaN(n)) return min;
        return Math.max(min, Math.min(max, n));
    }

    function resize() {
        canvas.width = window.innerWidth * window.devicePixelRatio;
        canvas.height = window.innerHeight * window.devicePixelRatio;
        canvas.style.width = window.innerWidth + 'px';
        canvas.style.height = window.innerHeight + 'px';
        // no aurora layer — keep main canvas full-window
    }

    function setLegend(text) {
        if (!legend) return;
        const dot = legend.querySelector('.legend-dot');
        if (dot) {
            dot.style.background = `linear-gradient(135deg, ${config.accent}, #60a5fa)`;
            dot.style.boxShadow = `0 0 12px ${config.accent}`;
        }
        const label = legend.querySelector('.legend-text');
        if (label) {
            label.textContent = text;
        }
    }

    function initParticles(type) {
        particles = [];
        meteors = [];
        stars = [];
        const base = config.intensity * 60;
        const width = canvas.width;
        const height = canvas.height;
        if (type === 'rain') {
            for (let i = 0; i < base; i++) {
                particles.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    len: 20 + Math.random() * 20,
                    speed: 6 + Math.random() * 10 * config.intensity,
                    alpha: 0.25 + Math.random() * 0.3
                });
            }
        } else if (type === 'snow') {
            for (let i = 0; i < base * 0.6; i++) {
                particles.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    r: 1 + Math.random() * (config.intensity + 1),
                    speedY: 0.5 + Math.random() * (1 + config.intensity * 0.4),
                    drift: (Math.random() - 0.5) * 0.8
                });
            }
        } else if (type === 'stars') {
            for (let i = 0; i < base * 0.5; i++) {
                stars.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    r: Math.random() * 1.4 + 0.6,
                    alpha: Math.random(),
                    pulse: Math.random() * 0.02 + 0.01
                });
            }
        } else if (type === 'meteors') {
            for (let i = 0; i < base * 0.3; i++) {
                stars.push({
                    x: Math.random() * width,
                    y: Math.random() * height,
                    r: Math.random() * 1.3 + 0.5,
                    alpha: 0.6 + Math.random() * 0.3,
                    pulse: Math.random() * 0.02 + 0.01
                });
            }
        }
    }

    function spawnMeteor() {
        const width = canvas.width;
        const height = canvas.height;
        meteors.push({
            x: Math.random() * width,
            y: -50,
            len: 80 + Math.random() * 120,
            speed: 10 + Math.random() * (6 + config.intensity * 2),
            angle: Math.PI / 3.2,
            life: 0,
            maxLife: 120 + Math.random() * 60
        });
    }

    function drawRain() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = `rgba(125, 211, 252, 0.55)`;
        ctx.lineWidth = 1.2 * window.devicePixelRatio;
        particles.forEach(p => {
            p.y += p.speed;
            p.x += 0.5;
            if (p.y > canvas.height) {
                p.y = -10;
                p.x = Math.random() * canvas.width;
            }
            ctx.globalAlpha = p.alpha;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p.x, p.y + p.len);
            ctx.stroke();
        });
    }

    function drawSnow() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'rgba(255,255,255,0.9)';
        particles.forEach(p => {
            p.y += p.speedY;
            p.x += p.drift;
            if (p.y > canvas.height) {
                p.y = -5;
                p.x = Math.random() * canvas.width;
            }
            if (p.x > canvas.width) p.x = 0;
            if (p.x < 0) p.x = canvas.width;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r * window.devicePixelRatio, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    function drawStars() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#c7d2fe';
        stars.forEach(s => {
            s.alpha += s.pulse * (Math.random() > 0.5 ? 1 : -1);
            s.alpha = Math.max(0.1, Math.min(1, s.alpha));
            ctx.globalAlpha = s.alpha;
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.r * window.devicePixelRatio, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    function drawMeteors() {
        drawStars();
        if (Math.random() < 0.02 * config.intensity) {
            spawnMeteor();
        }
        meteors = meteors.filter(m => m.life < m.maxLife);
        meteors.forEach(m => {
            m.x += Math.cos(m.angle) * m.speed * window.devicePixelRatio;
            m.y += Math.sin(m.angle) * m.speed * window.devicePixelRatio;
            m.life += 1;
            const grad = ctx.createLinearGradient(m.x, m.y, m.x - m.len, m.y - m.len * 0.4);
            grad.addColorStop(0, config.accent);
            grad.addColorStop(1, 'rgba(255,255,255,0)');
            ctx.strokeStyle = grad;
            ctx.lineWidth = 2 * window.devicePixelRatio;
            ctx.beginPath();
            ctx.moveTo(m.x, m.y);
            ctx.lineTo(m.x - m.len, m.y - m.len * 0.4);
            ctx.stroke();
        });
    }

    // aurora drawing removed

    function render() {
        if (stopped) return;
        switch (currentType) {
            case 'rain':
                drawRain();
                break;
            case 'snow':
                drawSnow();
                break;
            case 'stars':
                drawStars();
                break;
            case 'meteors':
                drawMeteors();
                break;
            // aurora removed
            default:
                drawRain();
        }
        rafId = requestAnimationFrame(render);
    }

    function setType(type) {
        if (!allowedTypes.includes(type)) return;
        currentType = type;
        setLegend(typeLabel(type));
        initParticles(type);
        root.setAttribute('data-weather-type', type);
        // aurora removed — always use main canvas for drawing
        canvas.style.display = 'block';
    }

    function typeLabel(type) {
        const map = { rain: '雨', snow: '雪', stars: '星空', meteors: '流星' };
        return map[type] || type;
    }

    function toggleVisibility() {
        const hidden = root.getAttribute('data-hidden') === 'true';
        const next = !hidden;
        root.setAttribute('data-hidden', next ? 'true' : 'false');
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-pressed', next ? 'false' : 'true');
            toggleBtn.textContent = next ? '开启天气' : '关闭天气';
        }
        // aurora removed — toggle only affects main canvas layer
        stopped = next;
        if (next) {
            if (rafId) {
                cancelAnimationFrame(rafId);
                rafId = null;
            }
            ctx && ctx.clearRect(0, 0, canvas.width, canvas.height);
        } else {
            canvas.style.display = 'block';
            render();
        }
    }

    function setupRotate() {
        if (!config.autoRotate) return;
        const order = allowedTypes;
        let idx = order.indexOf(currentType);
        rotateTimer = setInterval(function() {
            idx = (idx + 1) % order.length;
            setType(order[idx]);
        }, config.rotateSeconds * 1000);
    }

    function setupToggle() {
        if (!toggleBtn) return;
        toggleBtn.addEventListener('click', function() {
            toggleVisibility();
        });
        toggleBtn.setAttribute('aria-pressed', 'true');
        toggleBtn.textContent = '关闭天气';
        toggleBtn.style.pointerEvents = 'auto';
    }

    function setupLegendCycle() {
        if (!legend) return;
        legend.style.cursor = 'pointer';
        legend.title = '点击切换天气类型';
        legend.addEventListener('click', function() {
            const idx = allowedTypes.indexOf(currentType);
            const next = allowedTypes[(idx + 1) % allowedTypes.length];
            setType(next);
        });
        legend.style.pointerEvents = 'auto';
    }

    function setupVisibilityPause() {
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                stopped = true;
                if (rafId) cancelAnimationFrame(rafId);
                rafId = null;
            } else if (root.getAttribute('data-hidden') !== 'true') {
                stopped = false;
                render();
            }
        });
    }

    // Ensure first render after DOM/layout ready.
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    function init() {
        resize();
        window.addEventListener('resize', resize);
        setLegend(typeLabel(currentType));
        initParticles(currentType);
        // aurora removed — main canvas draws all supported types
        render();
        setupToggle();
        setupRotate();
        setupLegendCycle();
        setupVisibilityPause();
        root.classList.add('weather-showcase--ready');
    }

})();
