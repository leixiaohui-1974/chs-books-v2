"""
教材：《人工智能与水利水电工程》
章节：第2章 神经网络基础（CNN/RNN/LSTM/Transformer）
功能：基于合成水文时间序列，构建CNN/RNN/LSTM/Transformer四类模型的
     numpy/scipy仿真，对比预测性能，打印KPI结果表并生成matplotlib图。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt
from scipy import linalg

# =========================
# 1) 关键参数（统一变量定义）
# =========================
RANDOM_SEED = 2026
TOTAL_STEPS = 1200          # 总时间步
SEQ_LEN = 24                # 输入序列长度（例如24个时段）
TRAIN_RATIO = 0.8           # 训练集比例

CNN_FILTERS = 12            # CNN卷积核数量
CNN_KERNEL = 5              # CNN卷积核长度
RNN_HIDDEN = 16             # RNN隐藏维度
LSTM_HIDDEN = 16            # LSTM隐藏维度
ATTN_DIM = 16               # Transformer注意力维度

RIDGE_ALPHA = 1e-2          # 岭回归正则系数
PLOT_POINTS = 220           # 绘图展示点数

# Matplotlib中文显示设置（若本机无对应字体会自动回退）
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# =========================
# 2) 工具函数
# =========================
def sigmoid(x):
    """Sigmoid激活函数"""
    return 1.0 / (1.0 + np.exp(-x))


def softmax(x, axis=-1):
    """稳定版Softmax，避免指数溢出"""
    x_shift = x - np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x_shift)
    return exp_x / (np.sum(exp_x, axis=axis, keepdims=True) + 1e-12)


def simulate_hydro_series(total_steps, seed=2026):
    """
    生成简化水文时间序列：
    特征包含 [流量flow, 降雨rain, 蒸发evap]，目标是下一时段流量。
    """
    rng = np.random.default_rng(seed)

    rain = np.zeros(total_steps)
    evap = np.zeros(total_steps)
    flow = np.zeros(total_steps)

    # 初值
    rain[0] = 16.0
    evap[0] = 8.0
    flow[0] = 48.0

    for t in range(1, total_steps):
        # 降雨：短周期 + 长周期 + 随机扰动（非负）
        seasonal_r = 12 + 6 * np.sin(2 * np.pi * t / 24) + 3 * np.sin(2 * np.pi * t / 96)
        rain[t] = max(0.0, seasonal_r + rng.normal(0, 2.0))

        # 蒸发：与降雨存在相位差
        evap[t] = 8 + 2.2 * np.sin(2 * np.pi * (t + 6) / 24) + rng.normal(0, 0.8)

        # 流量：由前一时段状态驱动，叠加轻微非线性与噪声
        nonlinear = 0.015 * rain[t - 1] * np.sqrt(max(flow[t - 1], 1.0))
        flow[t] = (
            0.78 * flow[t - 1]
            + 0.24 * rain[t - 1]
            - 0.16 * evap[t - 1]
            + nonlinear
            + 1.4 * np.sin(2 * np.pi * t / 48)
            + rng.normal(0, 1.2)
        )
        flow[t] = max(0.5, flow[t])

    # 按列拼接为 [flow, rain, evap]
    return np.vstack([flow, rain, evap]).T


def make_supervised(data, seq_len):
    """把时间序列转换为监督学习样本：X为历史窗口，y为下一时刻流量"""
    X, y = [], []
    n = len(data) - seq_len
    for i in range(n):
        X.append(data[i:i + seq_len, :])
        y.append(data[i + seq_len, 0])  # 预测下一时刻flow
    return np.array(X), np.array(y)


def fit_ridge(features, y, alpha):
    """岭回归闭式解（scipy线性代数）"""
    n, p = features.shape
    X_aug = np.hstack([features, np.ones((n, 1))])  # 增加偏置项
    reg = np.eye(p + 1)
    reg[-1, -1] = 0.0  # 偏置项不正则
    w = linalg.solve(X_aug.T @ X_aug + alpha * reg, X_aug.T @ y, assume_a="pos")
    return w


def predict_ridge(features, w):
    """岭回归预测"""
    X_aug = np.hstack([features, np.ones((features.shape[0], 1))])
    return X_aug @ w


def calc_metrics(y_true, y_pred):
    """计算KPI指标"""
    err = y_true - y_pred
    mae = np.mean(np.abs(err))
    rmse = np.sqrt(np.mean(err ** 2))
    ss_res = np.sum(err ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2) + 1e-12
    r2 = 1 - ss_res / ss_tot
    nse = 1 - ss_res / ss_tot  # 在此场景下与R2同式
    mape = np.mean(np.abs(err) / (np.abs(y_true) + 1e-6)) * 100
    return {"MAE": mae, "RMSE": rmse, "R2": r2, "NSE": nse, "MAPE(%)": mape}


def print_kpi_table(records):
    """打印KPI结果表格"""
    print("\nKPI结果表（测试集）")
    print("-" * 76)
    print(f"{'模型':<15}{'MAE':>10}{'RMSE':>10}{'R2':>10}{'NSE':>10}{'MAPE(%)':>12}")
    print("-" * 76)
    for name, m in records:
        print(f"{name:<15}{m['MAE']:>10.3f}{m['RMSE']:>10.3f}{m['R2']:>10.3f}{m['NSE']:>10.3f}{m['MAPE(%)']:>12.2f}")
    print("-" * 76)


# =========================
# 3) 四类模型的“特征提取器”
#    说明：为突出理论框架，本脚本采用“随机特征 + 岭回归读出”
# =========================
def cnn_features(X, kernels, bias):
    """
    简化1D-CNN：
    卷积 -> ReLU -> 时序平均池化
    X: [N, L, D]
    """
    n, L, D = X.shape
    n_filters, K, _ = kernels.shape
    out_len = L - K + 1
    feats = np.zeros((n, n_filters))

    for f in range(n_filters):
        conv_map = np.zeros((n, out_len))
        for p in range(out_len):
            # 对每个窗口做卷积加和
            conv_map[:, p] = np.sum(X[:, p:p + K, :] * kernels[f][None, :, :], axis=(1, 2)) + bias[f]
        relu_map = np.maximum(conv_map, 0.0)
        feats[:, f] = relu_map.mean(axis=1)

    return feats


def rnn_features(X, Wx, Wh, b):
    """
    简化RNN：
    h_t = tanh(x_t Wx + h_{t-1} Wh + b)
    输出：最后状态 + 全时段均值状态
    """
    n, L, _ = X.shape
    h_dim = Wh.shape[0]
    h = np.zeros((n, h_dim))
    states = []

    for t in range(L):
        h = np.tanh(X[:, t, :] @ Wx + h @ Wh + b)
        states.append(h)

    h_stack = np.stack(states, axis=1)
    return np.concatenate([h, h_stack.mean(axis=1)], axis=1)


def lstm_features(X, Wf, Wi, Wo, Wg, bf, bi, bo, bg):
    """
    简化LSTM：
    使用门控机制缓解长依赖中的梯度衰减问题
    """
    n, L, d = X.shape
    h_dim = bf.shape[0]
    h = np.zeros((n, h_dim))
    c = np.zeros((n, h_dim))
    states = []

    for t in range(L):
        z = np.concatenate([X[:, t, :], h], axis=1)  # 拼接输入与上一步隐藏状态
        f = sigmoid(z @ Wf + bf)                     # 遗忘门
        i = sigmoid(z @ Wi + bi)                     # 输入门
        o = sigmoid(z @ Wo + bo)                     # 输出门
        g = np.tanh(z @ Wg + bg)                     # 候选记忆

        c = f * c + i * g
        h = o * np.tanh(c)
        states.append(h)

    h_stack = np.stack(states, axis=1)
    return np.concatenate([h, h_stack.mean(axis=1), h_stack.std(axis=1)], axis=1)


def transformer_features(X, Wq, Wk, Wv):
    """
    简化Transformer编码器核心：
    自注意力 Attention(Q,K,V) = softmax(QK^T/sqrt(dk))V
    输出：上下文向量的均值和标准差拼接
    """
    Q = X @ Wq  # [N, L, A]
    K = X @ Wk
    V = X @ Wv

    scores = np.matmul(Q, np.transpose(K, (0, 2, 1))) / np.sqrt(Wq.shape[1])
    attn = softmax(scores, axis=-1)
    context = np.matmul(attn, V)  # [N, L, A]

    return np.concatenate([context.mean(axis=1), context.std(axis=1)], axis=1)


# =========================
# 4) 主流程
# =========================
def main():
    rng = np.random.default_rng(RANDOM_SEED)

    # 4.1 数据生成与样本构造
    data = simulate_hydro_series(TOTAL_STEPS, seed=RANDOM_SEED)
    X, y = make_supervised(data, SEQ_LEN)

    # 4.2 训练/测试划分
    n_train = int(len(X) * TRAIN_RATIO)
    X_train, X_test = X[:n_train], X[n_train:]
    y_train, y_test = y[:n_train], y[n_train:]

    # 4.3 标准化（只用训练集统计量）
    feat_dim = X.shape[2]
    x_mean = X_train.reshape(-1, feat_dim).mean(axis=0)
    x_std = X_train.reshape(-1, feat_dim).std(axis=0) + 1e-8
    y_mean = y_train.mean()
    y_std = y_train.std() + 1e-8

    X_train_n = (X_train - x_mean) / x_std
    X_test_n = (X_test - x_mean) / x_std
    y_train_n = (y_train - y_mean) / y_std

    # 4.4 初始化四类模型参数（随机特征映射）
    # CNN参数
    cnn_kernels = rng.normal(0, 0.35, size=(CNN_FILTERS, CNN_KERNEL, feat_dim))
    cnn_bias = rng.normal(0, 0.05, size=(CNN_FILTERS,))

    # RNN参数
    Wx_rnn = rng.normal(0, 0.4, size=(feat_dim, RNN_HIDDEN))
    Wh_rnn = rng.normal(0, 0.25, size=(RNN_HIDDEN, RNN_HIDDEN))
    b_rnn = np.zeros(RNN_HIDDEN)

    # LSTM参数
    concat_dim = feat_dim + LSTM_HIDDEN
    Wf = rng.normal(0, 0.25, size=(concat_dim, LSTM_HIDDEN))
    Wi = rng.normal(0, 0.25, size=(concat_dim, LSTM_HIDDEN))
    Wo = rng.normal(0, 0.25, size=(concat_dim, LSTM_HIDDEN))
    Wg = rng.normal(0, 0.25, size=(concat_dim, LSTM_HIDDEN))
    bf = np.zeros(LSTM_HIDDEN)
    bi = np.zeros(LSTM_HIDDEN)
    bo = np.zeros(LSTM_HIDDEN)
    bg = np.zeros(LSTM_HIDDEN)

    # Transformer参数
    Wq = rng.normal(0, 0.35, size=(feat_dim, ATTN_DIM))
    Wk = rng.normal(0, 0.35, size=(feat_dim, ATTN_DIM))
    Wv = rng.normal(0, 0.35, size=(feat_dim, ATTN_DIM))

    # 4.5 特征提取 + 读出层训练
    results = {}

    # CNN
    Ftr = cnn_features(X_train_n, cnn_kernels, cnn_bias)
    Fte = cnn_features(X_test_n, cnn_kernels, cnn_bias)
    w = fit_ridge(Ftr, y_train_n, RIDGE_ALPHA)
    pred_n = predict_ridge(Fte, w)
    pred = pred_n * y_std + y_mean
    results["CNN"] = {"pred": pred, "metrics": calc_metrics(y_test, pred)}

    # RNN
    Ftr = rnn_features(X_train_n, Wx_rnn, Wh_rnn, b_rnn)
    Fte = rnn_features(X_test_n, Wx_rnn, Wh_rnn, b_rnn)
    w = fit_ridge(Ftr, y_train_n, RIDGE_ALPHA)
    pred_n = predict_ridge(Fte, w)
    pred = pred_n * y_std + y_mean
    results["RNN"] = {"pred": pred, "metrics": calc_metrics(y_test, pred)}

    # LSTM
    Ftr = lstm_features(X_train_n, Wf, Wi, Wo, Wg, bf, bi, bo, bg)
    Fte = lstm_features(X_test_n, Wf, Wi, Wo, Wg, bf, bi, bo, bg)
    w = fit_ridge(Ftr, y_train_n, RIDGE_ALPHA)
    pred_n = predict_ridge(Fte, w)
    pred = pred_n * y_std + y_mean
    results["LSTM"] = {"pred": pred, "metrics": calc_metrics(y_test, pred)}

    # Transformer
    Ftr = transformer_features(X_train_n, Wq, Wk, Wv)
    Fte = transformer_features(X_test_n, Wq, Wk, Wv)
    w = fit_ridge(Ftr, y_train_n, RIDGE_ALPHA)
    pred_n = predict_ridge(Fte, w)
    pred = pred_n * y_std + y_mean
    results["Transformer"] = {"pred": pred, "metrics": calc_metrics(y_test, pred)}

    # 4.6 KPI表输出（按RMSE升序）
    ranked = sorted([(k, v["metrics"]) for k, v in results.items()], key=lambda x: x[1]["RMSE"])
    print_kpi_table(ranked)

    # 4.7 画图
    show_n = min(PLOT_POINTS, len(y_test))
    x_idx = np.arange(show_n)

    fig = plt.figure(figsize=(13, 8))

    # 子图1：真实值与各模型预测对比
    ax1 = fig.add_subplot(2, 1, 1)
    ax1.plot(x_idx, y_test[:show_n], color="black", linewidth=2.2, label="真实流量")
    for name in ["CNN", "RNN", "LSTM", "Transformer"]:
        ax1.plot(x_idx, results[name]["pred"][:show_n], linewidth=1.5, alpha=0.9, label=name)
    ax1.set_title("测试集流量预测对比（前若干点）")
    ax1.set_xlabel("测试样本索引")
    ax1.set_ylabel("流量")
    ax1.grid(alpha=0.25)
    ax1.legend(ncol=5, fontsize=9)

    # 子图2：RMSE柱状 + R2折线
    ax2 = fig.add_subplot(2, 1, 2)
    model_names = ["CNN", "RNN", "LSTM", "Transformer"]
    rmse_vals = [results[m]["metrics"]["RMSE"] for m in model_names]
    r2_vals = [results[m]["metrics"]["R2"] for m in model_names]

    bars = ax2.bar(model_names, rmse_vals, alpha=0.85, color=["#5B8FF9", "#61DDAA", "#F6BD16", "#E8684A"])
    ax2.set_ylabel("RMSE（越小越好）")
    ax2.set_title("模型KPI对比")
    ax2.grid(axis="y", alpha=0.25)

    for b, v in zip(bars, rmse_vals):
        ax2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=9)

    ax2b = ax2.twinx()
    ax2b.plot(model_names, r2_vals, "o--", color="#D62728", linewidth=1.8, label="R2")
    ax2b.set_ylabel("R2（越大越好）")
    ax2b.set_ylim(min(0.0, min(r2_vals) - 0.05), 1.0)

    plt.tight_layout()
    plt.savefig('ch02_simulation_result.png', dpi=300, bbox_inches='tight')
print(f"图片已保存: ch02_simulation_result.png")
# plt.show()  # 禁用弹窗


if __name__ == "__main__":
    main()
