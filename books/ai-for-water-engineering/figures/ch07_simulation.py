# -*- coding: utf-8 -*-
"""
教材：《人工智能与水利水电工程》
章节：第7章 计算机视觉（7.1 基本概念与理论框架）
脚本功能：
1) 仿真大坝裂缝识别
2) 仿真水位线识别
3) 仿真遥感水体提取
4) 打印KPI结果表格并生成matplotlib图
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy import ndimage as ndi

# =========================
# 关键参数（统一变量定义）
# =========================
RANDOM_SEED = 42
EPS = 1e-9

# 裂缝场景参数
CRACK_H, CRACK_W = 256, 256
CRACK_HALF_WIDTH = 1
CRACK_CONTRAST = 0.35
CRACK_NOISE_STD = 0.06
CRACK_BG_SMOOTH_SIGMA = 1.2
CRACK_DETECT_SMOOTH_SIGMA = 1.0
CRACK_DARK_PERCENTILE = 40
CRACK_EDGE_PERCENTILE = 88

# 水位场景参数
LEVEL_H, LEVEL_W = 220, 320
TRUE_WATER_LEVEL = 128
WAVE_AMPLITUDE = 0.03
LEVEL_NOISE_STD = 0.02
LEVEL_ROI_X0, LEVEL_ROI_X1 = 20, 60

# 遥感场景参数
RS_H, RS_W = 220, 220
RS_NOISE_STD = 0.05

np.random.seed(RANDOM_SEED)


def compute_binary_metrics(gt, pred, eps=EPS):
    """计算二值分割常用指标"""
    gt = gt.astype(bool)
    pred = pred.astype(bool)

    tp = np.logical_and(gt, pred).sum()
    fp = np.logical_and(~gt, pred).sum()
    fn = np.logical_and(gt, ~pred).sum()
    tn = np.logical_and(~gt, ~pred).sum()

    precision = tp / (tp + fp + eps)
    recall = tp / (tp + fn + eps)
    f1 = 2 * precision * recall / (precision + recall + eps)
    iou = tp / (tp + fp + fn + eps)
    oa = (tp + tn) / (tp + tn + fp + fn + eps)

    return {
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "IoU": iou,
        "OA": oa,
    }


def print_kpi_table(rows):
    """打印KPI结果表格（纯文本）"""
    headers = ["模块", "Precision", "Recall", "F1", "IoU", "OA", "误差(px)"]
    print("\n" + "=" * 86)
    print("{:<16s}{:<11s}{:<11s}{:<11s}{:<11s}{:<11s}{:<11s}".format(*headers))
    print("-" * 86)

    for row in rows:
        vals = []
        for h in headers:
            v = row.get(h, "-")
            if isinstance(v, (float, np.floating)):
                vals.append(f"{v:.3f}")
            else:
                vals.append(str(v))
        print("{:<16s}{:<11s}{:<11s}{:<11s}{:<11s}{:<11s}{:<11s}".format(*vals))

    print("=" * 86 + "\n")


def simulate_crack_detection():
    """大坝裂缝识别仿真：合成图像 + 视觉检测"""
    h, w = CRACK_H, CRACK_W

    # 1) 生成背景纹理（模拟混凝土表面）
    background = 0.65 + 0.08 * np.random.randn(h, w)
    background = ndi.gaussian_filter(background, sigma=CRACK_BG_SMOOTH_SIGMA)

    # 2) 生成裂缝真值掩膜（弯曲细线）
    gt_mask = np.zeros((h, w), dtype=bool)
    xs = np.arange(20, w - 20)
    ys = (0.35 * xs + 28 * np.sin(xs / 28.0) + 60).astype(int)

    for x, y in zip(xs, ys):
        y0 = max(0, y - CRACK_HALF_WIDTH)
        y1 = min(h, y + CRACK_HALF_WIDTH + 1)
        x0 = max(0, x - 1)
        x1 = min(w, x + 2)
        gt_mask[y0:y1, x0:x1] = True

    # 3) 注入裂缝与噪声
    img = background.copy()
    img[gt_mask] -= CRACK_CONTRAST
    img += CRACK_NOISE_STD * np.random.randn(h, w)
    img = np.clip(img, 0, 1)

    # 4) 裂缝检测：暗区域 + 边缘强响应
    smooth = ndi.gaussian_filter(img, sigma=CRACK_DETECT_SMOOTH_SIGMA)
    gx = ndi.sobel(smooth, axis=1)
    gy = ndi.sobel(smooth, axis=0)
    grad = np.hypot(gx, gy)

    dark_mask = smooth < np.percentile(smooth, CRACK_DARK_PERCENTILE)
    edge_mask = grad > np.percentile(grad, CRACK_EDGE_PERCENTILE)
    pred_mask = np.logical_and(dark_mask, edge_mask)

    # 5) 形态学后处理（去噪 + 连通）
    pred_mask = ndi.binary_closing(pred_mask, structure=np.ones((3, 3)), iterations=1)
    pred_mask = ndi.binary_opening(pred_mask, structure=np.ones((2, 2)), iterations=1)

    metrics = compute_binary_metrics(gt_mask, pred_mask)
    return img, gt_mask, pred_mask, grad, metrics


def simulate_water_level_detection():
    """水位识别仿真：通过水平边缘峰值定位水位线"""
    h, w = LEVEL_H, LEVEL_W
    img = np.zeros((h, w), dtype=float)

    # 1) 构造天空/水体亮度分布
    for r in range(h):
        if r < TRUE_WATER_LEVEL:
            img[r, :] = 0.78 - 0.0015 * r
        else:
            img[r, :] = 0.35 + 0.0009 * (r - TRUE_WATER_LEVEL)

    # 2) 在水位附近加入波纹扰动
    x = np.arange(w)
    wave = WAVE_AMPLITUDE * np.sin(x / 7.0) + 0.02 * np.sin(x / 17.0)
    rows = np.arange(TRUE_WATER_LEVEL - 2, TRUE_WATER_LEVEL + 3)
    for rr in rows:
        if 0 <= rr < h:
            img[rr, :] -= (0.12 + wave)

    # 3) 构造简化“尺杆”区域
    img[:, 25:35] = 0.62
    for rr in range(0, h, 10):
        img[rr:rr + 2, 25:35] = 0.2

    img += LEVEL_NOISE_STD * np.random.randn(h, w)
    img = np.clip(img, 0, 1)

    # 4) 在尺杆ROI内，按行统计梯度，寻找最强边缘行
    roi = img[:, LEVEL_ROI_X0:LEVEL_ROI_X1]
    roi_smooth = ndi.gaussian_filter(roi, sigma=1.0)
    row_grad = np.abs(np.diff(roi_smooth, axis=0)).mean(axis=1)
    pred_level = int(np.argmax(row_grad) + 1)

    # 5) 将水位线转为二值分割，以复用统一KPI
    gt_mask = np.zeros((h, w), dtype=bool)
    gt_mask[TRUE_WATER_LEVEL:, :] = True
    pred_mask = np.zeros((h, w), dtype=bool)
    pred_mask[pred_level:, :] = True

    metrics = compute_binary_metrics(gt_mask, pred_mask)
    metrics["误差(px)"] = abs(pred_level - TRUE_WATER_LEVEL)

    return img, gt_mask, pred_mask, row_grad, pred_level, metrics


def otsu_threshold(arr):
    """使用Otsu法自动阈值分割"""
    vmin, vmax = float(arr.min()), float(arr.max())
    hist, bin_edges = np.histogram(arr.ravel(), bins=256, range=(vmin, vmax))
    prob = hist.astype(float) / (hist.sum() + EPS)

    omega = np.cumsum(prob)
    mu = np.cumsum(prob * np.arange(256))
    mu_t = mu[-1]

    sigma_b = (mu_t * omega - mu) ** 2 / (omega * (1.0 - omega) + EPS)
    idx = int(np.nanargmax(sigma_b))
    return bin_edges[idx]


def simulate_remote_sensing_water_extraction():
    """遥感仿真：构造Green/NIR波段并用NDWI提取水体"""
    h, w = RS_H, RS_W
    yy, xx = np.mgrid[0:h, 0:w]

    # 1) 生成水体真值（湖泊 + 河流）
    lake1 = ((xx - 120) ** 2) / (65 ** 2) + ((yy - 125) ** 2) / (45 ** 2) < 1.0
    lake2 = (xx - 62) ** 2 + (yy - 70) ** 2 < 25 ** 2
    river = np.abs(yy - (0.55 * xx + 15 + 8 * np.sin(xx / 15.0))) < 3
    gt_mask = lake1 | lake2 | river

    # 2) 合成Green/NIR光谱
    green = 0.35 + 0.08 * np.random.randn(h, w)
    nir = 0.45 + 0.08 * np.random.randn(h, w)

    # 水体区域：Green偏高、NIR偏低
    green[gt_mask] = 0.62 + RS_NOISE_STD * np.random.randn(gt_mask.sum())
    nir[gt_mask] = 0.18 + RS_NOISE_STD * np.random.randn(gt_mask.sum())

    # 植被干扰区域：NIR高，考察鲁棒性
    veg = (xx - 38) ** 2 + (yy - 170) ** 2 < 30 ** 2
    green[veg] = 0.28 + RS_NOISE_STD * np.random.randn(veg.sum())
    nir[veg] = 0.72 + RS_NOISE_STD * np.random.randn(veg.sum())

    green = np.clip(green, 0, 1)
    nir = np.clip(nir, 0, 1)

    # 3) NDWI + Otsu自动阈值分割
    ndwi = (green - nir) / (green + nir + EPS)
    th = otsu_threshold(ndwi)
    pred_mask = ndwi > th

    # 4) 形态学后处理
    pred_mask = ndi.binary_opening(pred_mask, structure=np.ones((2, 2)))
    pred_mask = ndi.binary_closing(pred_mask, structure=np.ones((3, 3)))

    metrics = compute_binary_metrics(gt_mask, pred_mask)
    return green, nir, ndwi, gt_mask, pred_mask, th, metrics


def main():
    # 任务1：裂缝识别
    crack_img, crack_gt, crack_pred, crack_grad, crack_m = simulate_crack_detection()

    # 任务2：水位识别
    level_img, level_gt, level_pred, row_grad, pred_level, level_m = simulate_water_level_detection()

    # 任务3：遥感水体提取
    green, nir, ndwi, rs_gt, rs_pred, ndwi_th, rs_m = simulate_remote_sensing_water_extraction()

    # KPI表格输出
    rows = [
        {
            "模块": "大坝裂缝识别",
            "Precision": crack_m["Precision"],
            "Recall": crack_m["Recall"],
            "F1": crack_m["F1"],
            "IoU": crack_m["IoU"],
            "OA": crack_m["OA"],
            "误差(px)": "-",
        },
        {
            "模块": "水位线识别",
            "Precision": level_m["Precision"],
            "Recall": level_m["Recall"],
            "F1": level_m["F1"],
            "IoU": level_m["IoU"],
            "OA": level_m["OA"],
            "误差(px)": level_m["误差(px)"],
        },
        {
            "模块": "遥感水体提取",
            "Precision": rs_m["Precision"],
            "Recall": rs_m["Recall"],
            "F1": rs_m["F1"],
            "IoU": rs_m["IoU"],
            "OA": rs_m["OA"],
            "误差(px)": "-",
        },
    ]
    print_kpi_table(rows)

    # 可视化
    fig, axs = 
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.subplots(3, 4, figsize=(16, 11))

    # 第一行：裂缝
    axs[0, 0].imshow(crack_img, cmap="gray")
    axs[0, 0].set_title("裂缝场景-原图")
    axs[0, 1].imshow(crack_gt, cmap="gray")
    axs[0, 1].set_title("裂缝真值")
    axs[0, 2].imshow(crack_pred, cmap="gray")
    axs[0, 2].set_title("裂缝预测")
    axs[0, 3].imshow(crack_grad, cmap="magma")
    axs[0, 3].set_title("梯度幅值")

    # 第二行：水位
    axs[1, 0].imshow(level_img, cmap="gray")
    axs[1, 0].axhline(TRUE_WATER_LEVEL, color="lime", linestyle="--", linewidth=1.5, label="真值")
    axs[1, 0].axhline(pred_level, color="red", linestyle="-", linewidth=1.5, label="预测")
    axs[1, 0].legend(loc="lower right", fontsize=8)
    axs[1, 0].set_title("水位场景与真值/预测")

    axs[1, 1].imshow(level_img[:, LEVEL_ROI_X0:LEVEL_ROI_X1], cmap="gray")
    axs[1, 1].set_title("尺杆ROI")

    axs[1, 2].plot(row_grad, color="tab:blue")
    axs[1, 2].axvline(TRUE_WATER_LEVEL - 1, color="lime", linestyle="--", label="真值")
    axs[1, 2].axvline(pred_level - 1, color="red", linestyle="-", label="预测")
    axs[1, 2].legend(fontsize=8)
    axs[1, 2].set_title("按行梯度响应")
    axs[1, 2].set_xlabel("行号")

    axs[1, 3].imshow(level_pred, cmap="gray")
    axs[1, 3].set_title("水体区域预测掩膜")

    # 第三行：遥感
    axs[2, 0].imshow(green, cmap="Greens")
    axs[2, 0].set_title("Green波段")
    axs[2, 1].imshow(ndwi, cmap="RdYlBu")
    axs[2, 1].set_title(f"NDWI (阈值={ndwi_th:.3f})")
    axs[2, 2].imshow(rs_gt, cmap="gray")
    axs[2, 2].set_title("遥感水体真值")
    axs[2, 3].imshow(rs_pred, cmap="gray")
    axs[2, 3].set_title("遥感水体预测")

    for ax in axs.ravel():
        ax.set_xticks([])
        ax.set_yticks([])

    plt.tight_layout()
    plt.savefig('ch07_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch07_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
