"""
古风美学图片生成 — 水墨山水·月下孤亭
Ancient Chinese Aesthetic Image Generator
"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Arc, Ellipse
from matplotlib.patches import Rectangle, Polygon, Circle, Wedge
from scipy.ndimage import gaussian_filter
import matplotlib.font_manager as fm
import os

# ── 画布设置 ──────────────────────────────────────────
DPI = 150
W, H = 16, 10  # 英寸
fig, ax = plt.subplots(figsize=(W, H), dpi=DPI, facecolor='#f5f0e8')
ax.set_xlim(0, 1600)
ax.set_ylim(0, 1000)
ax.set_aspect('equal')
ax.axis('off')

# ── 配色 ──────────────────────────────────────────────
BG_DARK   = '#e8e0d0'   # 背景底
BG_LIGHT  = '#f5f0e8'   # 背景亮
MOON      = '#fef9ed'   # 月色
INK_1     = '#2c2c2c'   # 浓墨
INK_2     = '#4a4a4a'   # 中墨
INK_3     = '#7a7a7a'   # 淡墨
INK_4     = '#b0a89c'   # 极淡
RED       = '#c04040'   # 朱砂红 (印章/梅花)
RED_DARK  = '#8b2020'   # 深红
GOLD      = '#d4a853'   # 金
GREEN_1   = '#5a7040'   # 松绿
GREEN_2   = '#3a5030'   # 深松绿

# ── 辅助函数 ──────────────────────────────────────────
def draw_cloud(x, y, w, h, alpha):
    """画水墨云雾"""
    cloud = np.zeros((h, w))
    yy, xx = np.ogrid[:h, :w]
    cx, cy = w//2, h//2
    # 椭圆高斯团
    for i in range(np.random.randint(3, 7)):
        rx = np.random.randint(w//6, w//3)
        ry = np.random.randint(h//8, h//4)
        cx_i = cx + np.random.randint(-w//4, w//4)
        cy_i = cy + np.random.randint(-h//4, h//4)
        dist2 = ((xx - cx_i)**2 / rx**2 + (yy - cy_i)**2 / ry**2)
        cloud += np.exp(-dist2 * 3)
    cloud = np.clip(cloud / cloud.max(), 0, 1)
    cloud = gaussian_filter(cloud, sigma=max(w, h) / 20)
    extent = [x, x + w, y, y + h]
    ax.imshow(cloud.T, extent=extent, origin='lower',
              cmap='Greys', alpha=alpha * 0.5, vmin=0, vmax=1.5,
              interpolation='bilinear')

def draw_mountain_peaks(x_base, y_base, peaks, color, alpha=1.0):
    """画水墨山峰 — 半透明叠加层"""
    for i, (px, py, pw, ph) in enumerate(peaks):
        layers = 4
        for j in range(layers):
            beta = j / layers
            h_eff = ph * (1 - beta * 0.5)
            offset = -beta * 20
            pts = np.array([
                [px - pw * (1 - beta * 0.3), y_base + offset],
                [px - pw * 0.5 * (1 - beta), y_base + h_eff * 0.6 + offset],
                [px,                y_base + h_eff + offset],
                [px + pw * 0.5 * (1 - beta), y_base + h_eff * 0.6 + offset],
                [px + pw * (1 - beta * 0.3), y_base + offset],
            ])
            a = alpha * (0.4 + 0.15 * (layers - 1 - j))
            ax.fill(pts[:, 0], pts[:, 1], color=color, alpha=a,
                    edgecolor='none', zorder=2 + j)

def draw_tree(x, y, size, angle=0):
    """画松树 (写意)"""
    from matplotlib.transforms import Affine2D
    import matplotlib.transforms as transforms
    # 树干
    trunk_h = size * 0.4
    trunk_w = size * 0.04
    ax.fill_between([x - trunk_w, x + trunk_w],
                    [y, y], [y + trunk_h, y + trunk_h],
                    color=INK_1, alpha=0.85, zorder=6)
    # 松针层
    for k in range(3):
        cy = y + trunk_h + k * size * 0.18
        cw = size * (0.25 - k * 0.04)
        ch = size * 0.15
        nx = 40
        xs = np.linspace(x - cw, x + cw, nx)
        ys_top = cy + ch + np.random.randn(nx) * ch * 0.15
        ys_bot = cy - ch * 0.3 + np.random.randn(nx) * ch * 0.1
        pts_top = np.column_stack([xs, ys_top])
        pts_bot = np.column_stack([xs[::-1], ys_bot[::-1]])
        pts = np.vstack([pts_top, pts_bot])
        shade = [GREEN_1, GREEN_2, GREEN_2][k]
        ax.fill(pts[:, 0], pts[:, 1], color=shade, alpha=0.8, zorder=6)

def draw_plum_blossom(x, y, size, angle=0):
    """画梅花 (五瓣)"""
    from matplotlib.transforms import Affine2D
    for p in range(5):
        theta = p * np.pi * 2 / 5 + angle
        px = x + np.cos(theta) * size * 0.6
        py = y + np.sin(theta) * size * 0.6
        circ = Circle((px, py), size * 0.35, color=RED, alpha=0.85, zorder=9)
        ax.add_patch(circ)
    # 花蕊
    for _ in range(6):
        sx = x + np.random.randn() * size * 0.15
        sy = y + np.random.randn() * size * 0.15
        ax.plot(sx, sy, '.', color=GOLD, markersize=size * 2, alpha=0.8, zorder=10)

def draw_pavilion(x, y, size):
    """画凉亭 (简笔)"""
    w = size
    h = size * 1.0
    # 基石
    ax.fill([x - w * 0.5, x + w * 0.5, x + w * 0.45, x - w * 0.45],
            [y, y, y + h * 0.06, y + h * 0.06],
            color=INK_3, alpha=0.7, zorder=6)
    # 柱子
    for col_x in [x - w * 0.35, x + w * 0.35]:
        ax.fill([col_x - w * 0.03, col_x + w * 0.03],
                [y + h * 0.06, y + h * 0.45],
                color=INK_1, alpha=0.8, zorder=6)
    # 飞檐屋顶
    roof_pts = np.array([
        [x - w * 0.55, y + h * 0.42],
        [x - w * 0.62, y + h * 0.60],
        [x - w * 0.20, y + h * 0.58],
        [x,           y + h * 0.75],
        [x + w * 0.20, y + h * 0.58],
        [x + w * 0.62, y + h * 0.60],
        [x + w * 0.55, y + h * 0.42],
    ])
    ax.fill(roof_pts[:, 0], roof_pts[:, 1], color=INK_1, alpha=0.85, zorder=7)
    # 翘角弧线
    arc_l = Arc((x - w * 0.55, y + h * 0.52), w * 0.2, h * 0.1,
                angle=15, theta1=160, theta2=340, color=INK_1, lw=1.5, zorder=8)
    arc_r = Arc((x + w * 0.55, y + h * 0.52), w * 0.2, h * 0.1,
                angle=-15, theta1=200, theta2=380, color=INK_1, lw=1.5, zorder=8)
    ax.add_patch(arc_l)
    ax.add_patch(arc_r)

def draw_lantern(x, y, size=1.0):
    """画灯笼"""
    w = 8 * size
    h = 10 * size
    # 灯笼主体
    body = Ellipse((x, y), w, h, color=RED, alpha=0.75, zorder=9)
    ax.add_patch(body)
    # 上下盖
    for dy in [-h/2 - 1.5*size, h/2 + 1.5*size]:
        rect = Rectangle((x - w * 0.35, dy - 1.5*size), w * 0.7, 3*size,
                          color=GOLD, alpha=0.9, zorder=9)
        ax.add_patch(rect)
    # 流苏
    for i in range(5):
        sx = x + (i - 2) * w * 0.12
        ax.plot([sx, sx], [y - h/2 - 3*size, y - h/2 - 10*size],
                color=GOLD, lw=0.5, alpha=0.6, zorder=9)
    # 线
    ax.plot([x, x], [y + h/2 + 4.5*size, y + h/2 + 15*size],
            color=INK_3, lw=0.4, alpha=0.5, zorder=8)

# ====================================================
#  开始绘制
# ====================================================

# ── 背景渐变 ──────────────────────────────────────────
gy, gx = np.mgrid[:1000, :1600]
gradient = np.ones((1000, 1600))
# 上暗下亮 (仿古纸做旧感)
gradient = gradient * (0.85 + 0.15 * (gy / 1000))
# 加一些做旧纹理
np.random.seed(42)
texture = 1 + 0.03 * np.random.randn(1000 // 4, 1600 // 4)
texture = np.kron(texture, np.ones((4, 4)))
texture = gaussian_filter(texture, sigma=2)
gradient = gradient * np.clip(texture, 0.92, 1.08)
ax.imshow(gradient, extent=[0, 1600, 0, 1000], origin='lower',
          cmap='YlOrBr', alpha=0.15, vmin=0.85, vmax=1.15,
          interpolation='bilinear')
ax.set_facecolor(BG_LIGHT)

# ── 圆月 ─────────────────────────────────────────────
moon = Circle((1200, 820), 120, color=MOON, alpha=0.9, zorder=1)
ax.add_patch(moon)
# 月晕
for r in [140, 160, 185]:
    halo = Circle((1200, 820), r, color=MOON, alpha=0.08, zorder=1, fill=False, lw=3)
    ax.add_patch(halo)

# ── 远山云雾 ──────────────────────────────────────────
draw_cloud(200, 350, 500, 180, alpha=0.3)
draw_cloud(700, 280, 700, 200, alpha=0.4)
draw_cloud(50, 200, 600, 220, alpha=0.25)
draw_cloud(900, 400, 500, 160, alpha=0.35)

# 远山
draw_mountain_peaks(0, 100, [
    (200, 100, 350, 420),
    (500, 100, 300, 350),
    (750, 100, 380, 480),
    (1050, 100, 420, 550),
    (1350, 100, 350, 400),
], INK_4, alpha=0.55)

# 中景云雾
draw_cloud(100, 600, 600, 120, alpha=0.5)
draw_cloud(800, 550, 550, 100, alpha=0.45)

# ── 中景山脉 ──────────────────────────────────────────
draw_mountain_peaks(0, 200, [
    (300, 200, 320, 380),
    (600, 200, 350, 420),
    (900, 200, 380, 460),
    (1200, 200, 300, 350),
], INK_3, alpha=0.7)

# ── 近景山脉 ──────────────────────────────────────────
draw_mountain_peaks(0, 250, [
    (180, 250, 280, 320),
    (420, 250, 240, 280),
    (650, 250, 260, 340),
    (870, 250, 220, 260),
    (1080, 250, 250, 300),
], INK_2, alpha=0.8)

# ── 松树群 ────────────────────────────────────────────
tree_positions = [
    (80, 330, 90),
    (140, 360, 100),
    (200, 390, 75),
    (1380, 380, 100),
    (1440, 350, 85),
    (1500, 370, 78),
    (1520, 340, 65),
]
for tx, ty, ts in tree_positions:
    draw_tree(tx, ty, ts)

# ── 凉亭 ──────────────────────────────────────────────
draw_pavilion(300, 480, 90)

# ── 梅花树 ────────────────────────────────────────────
# 梅枝
branch_pts_start = (420, 480)
for i_main in range(3):
    bx = branch_pts_start[0] + i_main * 40
    by = branch_pts_start[1]
    for seg in range(4):
        ex = bx + np.random.randint(-25, 35)
        ey = by + np.random.randint(15, 45)
        n_pts = 20
        bx_vals = np.linspace(bx, ex, n_pts)
        by_vals = np.linspace(by, ey, n_pts) + np.sin(np.linspace(0, np.pi, n_pts)) * 15
        ax.plot(bx_vals, by_vals, color=INK_2, lw=1.3, alpha=0.7, zorder=5)
        # 侧枝
        if seg >= 1:
            for _ in range(2):
                side_x = ex + np.random.randint(-20, 20)
                side_y = ey + np.random.randint(10, 30)
                ax.plot([ex, side_x], [ey, side_y], color=INK_3, lw=0.7, alpha=0.5, zorder=5)
                # 梅花
                if np.random.rand() > 0.3:
                    draw_plum_blossom(side_x, side_y, 5 + np.random.rand() * 6,
                                      np.random.rand() * np.pi * 2)
        bx, by = ex, ey
    # 梅花
    for _ in range(np.random.randint(3, 8)):
        px = ex + np.random.randint(-15, 15)
        py = ey + np.random.randint(-10, 20)
        draw_plum_blossom(px, py, 5 + np.random.rand() * 6)

# ── 水面 ──────────────────────────────────────────────
water_y = 300
water_grid = np.zeros((100, 1600))
for i in range(100):
    water_grid[i, :] = 0.5 + 0.05 * np.sin(np.linspace(0, 6*np.pi, 1600) + i * 0.3)
    water_grid[i, :] += 0.02 * np.sin(np.linspace(0, 20*np.pi, 1600) + i * 0.15)
water_grid = gaussian_filter(water_grid, sigma=(1, 3))
ax.imshow(water_grid, extent=[0, 1600, 0, water_y], origin='lower',
          cmap='Greys', alpha=0.18, vmin=0.2, vmax=0.8,
          interpolation='bilinear')

# 水面倒影
ax.fill_between([0, 1600], [0, 0], [water_y, water_y],
                color='#d5cfc5', alpha=0.12, zorder=0)

# ── 小船 ──────────────────────────────────────────────
boat_x, boat_y = 700, 260
boat_pts = np.array([
    [boat_x - 30, boat_y + 3],
    [boat_x - 18, boat_y - 2],
    [boat_x,    boat_y - 4],
    [boat_x + 20, boat_y - 2],
    [boat_x + 32, boat_y + 2],
    [boat_x + 28, boat_y + 5],
    [boat_x - 26, boat_y + 5],
])
ax.fill(boat_pts[:, 0], boat_pts[:, 1], color=INK_2, alpha=0.7, zorder=4)
# 船篷
ax.fill([boat_x - 8, boat_x + 8, boat_x + 6, boat_x - 6],
        [boat_y + 1, boat_y + 1, boat_y + 16, boat_y + 16],
        color=INK_1, alpha=0.6, zorder=4)
# 渔翁
ax.plot(boat_x - 2, boat_y + 18, 'o', color=INK_1, markersize=4, alpha=0.7, zorder=4)
# 钓竿
ax.plot([boat_x + 5, boat_x + 25, boat_x + 30],
        [boat_y + 8, boat_y + 22, boat_y + 28],
        color=INK_2, lw=0.5, alpha=0.5, zorder=4)

# ── 岸边 ──────────────────────────────────────────────
bank_y = 260
# 不规则岸线
bank_x = np.linspace(0, 1600, 400)
bank_y_vals = bank_y + np.sin(bank_x * 0.02) * 10 + np.sin(bank_x * 0.05) * 6 + np.random.randn(400) * 2
bank_y_vals = gaussian_filter(bank_y_vals, sigma=3)
ax.fill_between(bank_x, 0, bank_y_vals, color='#c8bfb0', alpha=0.3, zorder=1)
# 岸上石块
for _ in range(30):
    sx = np.random.randint(50, 1550)
    sy = bank_y + np.random.randint(-5, 15)
    sr = np.random.randint(3, 10)
    ax.plot(sx, sy, 'o', color=INK_3, markersize=sr, alpha=0.35, zorder=2)

# ── 灯笼 ──────────────────────────────────────────────
draw_lantern(330, 590, size=1.2)
draw_lantern(410, 610, size=0.9)
draw_lantern(270, 560, size=1.0)

# ── 飞鸟 ──────────────────────────────────────────────
bird_positions = [
    (1100, 780), (1125, 795), (1150, 785),
    (1060, 750), (1085, 765), (1110, 755),
    (1180, 800), (1200, 815),
    (960, 700), (980, 710),
]
for bx, by in bird_positions:
    ax.plot(bx, by, 'v', color=INK_3, markersize=3, alpha=0.5, zorder=8)

# ── 落花 (飘散的梅花瓣) ───────────────────────────────
for _ in range(40):
    px = np.random.randint(350, 600)
    py = np.random.randint(200, 550)
    ax.plot(px, py, 'o', color=RED, markersize=np.random.rand()*4 + 2,
            alpha=np.random.rand() * 0.5 + 0.15, zorder=9)

# ── 印章 (落款) ───────────────────────────────────────
seal_x, seal_y = 1350, 120
seal = FancyBboxPatch((seal_x - 22, seal_y - 22), 44, 44,
                       boxstyle="round,pad=3", color=RED_DARK,
                       alpha=0.85, zorder=11)
ax.add_patch(seal)
# 印章内部纹理
for i in range(6):
    line_y = seal_y - 15 + i * 6
    ax.plot([seal_x - 14, seal_x + 14], [line_y, line_y],
            color=RED, lw=0.8, alpha=0.5, zorder=11)
# 印章文字
ax.text(seal_x, seal_y + 6, '山\n水', fontsize=11, color=RED,
        ha='center', va='center', fontweight='bold',
        alpha=0.85, zorder=12, fontfamily='SimSun')

# ── 题诗 ──────────────────────────────────────────────
poem_lines = [
    '千山鸟飞绝',
    '万径人踪灭',
    '孤舟蓑笠翁',
    '独钓寒江雪',
]
for i, line in enumerate(poem_lines):
    ax.text(1220, 680 - i * 34, line, fontsize=12,
            color=INK_2, alpha=0.7, fontfamily='STKaiti',
            zorder=10)

# ── 边框 ──────────────────────────────────────────────
border = Rectangle((20, 20), 1560, 960, linewidth=2,
                    edgecolor=INK_4, facecolor='none', alpha=0.5, zorder=15)
ax.add_patch(border)
# 内框
border2 = Rectangle((28, 28), 1544, 944, linewidth=0.5,
                     edgecolor=INK_4, facecolor='none', alpha=0.3, zorder=15)
ax.add_patch(border2)

# ── 保存 ──────────────────────────────────────────────
output_path = os.path.join(os.path.dirname(__file__), 'gufeng_landscape.png')
fig.savefig(output_path, dpi=DPI, bbox_inches='tight', pad_inches=0.5,
            facecolor=BG_LIGHT, edgecolor='none')
plt.close(fig)
import sys
sys.stdout.reconfigure(encoding='utf-8')
print(f'古风美学图片已生成: {output_path}')
