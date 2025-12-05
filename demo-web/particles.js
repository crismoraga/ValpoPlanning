// Animación simple de partículas en canvas para fondo
(function() {
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    const particles = Array.from({ length: 80 }, () => spawn());

    function spawn() {
        return {
            x: Math.random() * width,
            y: Math.random() * height,
            r: 1 + Math.random() * 2.2,
            vx: -0.2 + Math.random() * 0.4,
            vy: -0.15 + Math.random() * 0.3,
            alpha: 0.2 + Math.random() * 0.6
        };
    }

    function step() {
        ctx.clearRect(0, 0, width, height);
        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < -10 || p.x > width + 10 || p.y < -10 || p.y > height + 10) {
                Object.assign(p, spawn());
                p.x = width + 10;
            }
            ctx.beginPath();
            const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
            grad.addColorStop(0, `rgba(0,209,255,${p.alpha})`);
            grad.addColorStop(1, 'rgba(0,209,255,0)');
            ctx.fillStyle = grad;
            ctx.arc(p.x, p.y, p.r * 3, 0, Math.PI * 2);
            ctx.fill();
        });
        requestAnimationFrame(step);
    }

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    step();
})();
