const width = (document.getElementById("myCanvas").width = window.innerWidth);
const height = (document.getElementById("myCanvas").height = window.innerHeight);
const ctx = document.getElementById("myCanvas").getContext("2d");

// 粒子数量
const particleCount = 100;

// 粒子数组
const particles = [];

// 摩擦系数
const friction = 0.9; // 摩擦系数，值越小，摩擦力越大

// 粒子类
class Particle {
    constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = Math.random() * 2 - 1;
        this.vy = Math.random() * 2 - 1;
        this.hue = Math.random() * 360; // 随机生成色相
        this.color = `hsla(${this.hue}, 100%, 50%, 0.2)`;
        this.size = Math.random() * 10 + 10; // 随机生成粒子大小
        this.corner = this.getCorner(); // 根据色相确定受影响的角落
        this.colorChangeTimer = 0; // 颜色变化计时器
    }

    // 根据色相确定受影响的角落
    getCorner() {
        if (this.hue < 90) return 'top-left';
        if (this.hue < 180) return 'top-right';
        if (this.hue < 270) return 'bottom-right';
        return 'bottom-left';
    }

    update(deltaTime) {
        this.x += this.vx;
        this.y += this.vy;

        // 应用摩擦力
        this.vx *= friction;
        this.vy *= friction;

        // 边界检测
        if (this.x < 0 || this.x > width) this.vx = -this.vx;
        if (this.y < 0 || this.y > height) this.vy = -this.vy;

        // 根据角落施加吸引力
        const attractionStrength = 0.1;
        let distance;
        const corner = Math.sqrt(width * width + height * height);
        switch (this.corner) {
            case 'top-left':
                distance = Math.sqrt(Math.pow(this.x - 0, 2) + Math.pow(this.y - 0, 2));
                this.vx -= attractionStrength * distance / corner;
                this.vy -= attractionStrength * distance / corner;
                break;
            case 'top-right':
                distance = Math.sqrt(Math.pow(this.x - width, 2) + Math.pow(this.y - 0, 2));
                this.vx += attractionStrength * distance / corner;
                this.vy -= attractionStrength * distance / corner;
                break;
            case 'bottom-right':
                distance = Math.sqrt(Math.pow(this.x - width, 2) + Math.pow(this.y - height, 2));
                this.vx += attractionStrength * distance / corner;
                this.vy += attractionStrength * distance / corner;
                break;
            case 'bottom-left':
                distance = Math.sqrt(Math.pow(this.x - 0, 2) + Math.pow(this.y - height, 2));
                this.vx -= attractionStrength * distance / corner;
                this.vy += attractionStrength * distance / corner;
                break;
        }

        // 碰撞检测
        for (let i = 0; i < particles.length; i++) {
            if (this === particles[i]) continue;

            const dx = this.x - particles[i].x;
            const dy = this.y - particles[i].y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < this.size + particles[i].size) {
                // 碰撞时根据动量守恒计算新的速度
                const vxTotal = this.vx - particles[i].vx;
                const vyTotal = this.vy - particles[i].vy;
                const dvx = (vxTotal * (this.size - particles[i].size) + 2 * particles[i].size * vxTotal) / (this.size + particles[i].size);
                const dvy = (vyTotal * (this.size - particles[i].size) + 2 * particles[i].size * vyTotal) / (this.size + particles[i].size);
            
                this.vx -= dvx;
                this.vy -= dvy;
                particles[i].vx += dvx;
                particles[i].vy += dvy;
            
                // 将粒子稍微分开，避免再次碰撞
                const separation = (this.size + particles[i].size) - distance;
                const separationX = dx / distance * separation / 2;
                const separationY = dy / distance * separation / 2;
                this.x += separationX;
                this.y += separationY;
                particles[i].x -= separationX;
                particles[i].y -= separationY;
            
                // 如果计时器为0，则交换色相并翻倍
                if (this.colorChangeTimer <= 0 && particles[i].colorChangeTimer <= 0) {
                    // 交换色相
                    [this.hue, particles[i].hue] = [particles[i].hue * 2 % 360, this.hue * 2 % 360];
                    // 更新颜色
                    this.color = `hsla(${this.hue}, 100%, 50%, 0.2)`;
                    particles[i].color = `hsla(${particles[i].hue}, 100%, 50%, 0.2)`;
            
                    // 更新吸引力的方向
                    this.corner = this.getCorner();
                    particles[i].corner = particles[i].getCorner();
            
                    // 设置计时器
                    this.colorChangeTimer = 1000; // 1秒内不再变化
                    particles[i].colorChangeTimer = 1000; // 1秒内不再变化
                }
            }
        }

        // 更新计时器
        if (this.colorChangeTimer > 0) {
            this.colorChangeTimer -= deltaTime;
        }
    }

    draw() {
        ctx.beginPath();
        ctx.strokeStyle = this.color; // 设置线条颜色
        ctx.lineWidth = 2; // 设置线条宽度，可以根据需要调整
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.stroke(); // 绘制空心圆
    }

}

// 初始化粒子
function init() {
    for (let i = 0; i < particleCount; i++) {
        particles.push(new Particle());
    }
}

// 动画函数
let lastTime = 0;
function animate(currentTime) {
    const deltaTime = currentTime - lastTime;
    lastTime = currentTime;

    ctx.clearRect(0, 0, width, height);

    particles.forEach(particle => {
        particle.update(deltaTime);
        particle.draw();
    });
    console.log(deltaTime, particles.length);

    requestAnimationFrame(animate);
}

init();
requestAnimationFrame(animate);
