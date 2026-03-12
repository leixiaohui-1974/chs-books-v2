# -*- coding: utf-8 -*-
"""
教材：《人工智能与水利水电工程》
章节：第3章 大语言模型（LLM）原理 - 3.1 基本概念与理论框架
功能：构建“词元嵌入 -> 自注意力 -> 概率预测”的最小仿真，打印KPI结果表并生成可视化图。
依赖：numpy / scipy / matplotlib
"""

import numpy as np
from scipy.special import softmax
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt


# =========================
# 1) 关键参数（集中定义，便于教学调参）
# =========================
RANDOM_SEED = 42
VOCAB_SIZE = 18          # 词表规模
SEQ_LEN = 8              # 上下文长度
EMBED_DIM = 24           # 词向量维度
TRAIN_SAMPLES = 1200     # 训练样本数
TEST_SAMPLES = 300       # 测试样本数
MAX_ITER = 140           # 优化最大迭代次数
L2_REG = 1e-3            # L2正则
ATTN_TEMP = 1.0          # 注意力温度（越小越“尖锐”）
TOPK = 3                 # Top-k准确率
SAVE_FIG = True
FIG_PATH = "llm_ch3_1_simulation.png"

np.random.seed(RANDOM_SEED)


# =========================
# 2) 构造“水利工程语境”词元
# =========================
vocab = [
    "降雨", "径流", "蒸发", "水位", "流量", "闸门", "泵站", "渠道",
    "水库", "洪峰", "预报", "调度", "传感器", "泥沙", "渗流", "坝体",
    "告警", "优化"
]


# =========================
# 3) 构造语料统计规律（马尔可夫转移）
# =========================
base = np.ones((VOCAB_SIZE, VOCAB_SIZE)) * 0.2
for i in range(VOCAB_SIZE):
    base[i, (i + 1) % VOCAB_SIZE] += 2.0
    base[i, (i + 2) % VOCAB_SIZE] += 1.2

# 强化一些与水利业务相关的语义链路
def boost(a, b, w):
    ia, ib = vocab.index(a), vocab.index(b)
    base[ia, ib] += w

boost("降雨", "径流", 4.0)
boost("径流", "洪峰", 3.5)
boost("洪峰", "告警", 3.0)
boost("传感器", "预报", 3.5)
boost("预报", "调度", 3.0)
boost("调度", "闸门", 3.2)
boost("闸门", "水位", 2.8)
boost("水库", "调度", 2.5)
boost("坝体", "渗流", 2.8)

P = base / base.sum(axis=1, keepdims=True)


def sample_sequence(length):
    """按转移矩阵采样一个词元序列"""
    seq = np.zeros(length, dtype=np.int64)
    seq[0] = np.random.randint(0, VOCAB_SIZE)
    for t in range(1, length):
        seq[t] = np.random.choice(VOCAB_SIZE, p=P[seq[t - 1]])
    return seq


def build_dataset(n_samples):
    """构造监督学习数据：X为上下文，y为下一词"""
    X = np.zeros((n_samples, SEQ_LEN), dtype=np.int64)
    y = np.zeros(n_samples, dtype=np.int64)
    for i in range(n_samples):
        seq = sample_sequence(SEQ_LEN + 1)
        X[i] = seq[:SEQ_LEN]
        y[i] = seq[SEQ_LEN]
    return X, y


X_train, y_train = build_dataset(TRAIN_SAMPLES)
X_test, y_test = build_dataset(TEST_SAMPLES)


# =========================
# 4) 词嵌入 + 位置嵌入（固定表示，模拟预训练）
# =========================
E = np.random.randn(VOCAB_SIZE, EMBED_DIM) * 0.5       # 词嵌入
Pos = np.random.randn(SEQ_LEN, EMBED_DIM) * 0.1        # 位置嵌入


def attention_features(X, temp=1.0):
    """
    计算注意力上下文向量：
    输入 X: [N, L]
    输出 C: [N, D], alpha: [N, L]
    """
    H = E[X] + Pos[None, :, :]          # [N, L, D]
    q = H[:, -1, :]                     # 使用最后位置作为查询向量
    scores = np.einsum("nld,nd->nl", H, q) / np.sqrt(EMBED_DIM)
    scores = scores / max(temp, 1e-8)
    alpha = softmax(scores, axis=1)     # 注意力分布
    C = np.einsum("nl,nld->nd", alpha, H)
    return C, alpha


C_train, alpha_train = attention_features(X_train, ATTN_TEMP)
C_test, alpha_test = attention_features(X_test, ATTN_TEMP)


# =========================
# 5) 训练输出层（SciPy优化）
# logits = C @ W + b
# =========================
D, K = EMBED_DIM, VOCAB_SIZE

def unpack(theta):
    W = theta[:D * K].reshape(D, K)
    b = theta[D * K:]
    return W, b


def nll_and_grad(theta, Xf, y, reg):
    W, b = unpack(theta)
    logits = Xf @ W + b
    probs = softmax(logits, axis=1)

    n = Xf.shape[0]
    loss = -np.log(probs[np.arange(n), y] + 1e-12).mean()
    loss += 0.5 * reg * np.sum(W * W)

    G = probs.copy()
    G[np.arange(n), y] -= 1.0
    G /= n
    gW = Xf.T @ G + reg * W
    gb = G.sum(axis=0)
    grad = np.concatenate([gW.ravel(), gb])
    return loss, grad


init = np.random.randn(D * K + K) * 0.01
loss_trace = []

def callback(theta):
    l, _ = nll_and_grad(theta, C_train, y_train, L2_REG)
    loss_trace.append(l)

res = minimize(
    fun=lambda th: nll_and_grad(th, C_train, y_train, L2_REG),
    x0=init,
    jac=True,
    method="L-BFGS-B",
    callback=callback,
    options={"maxiter": MAX_ITER, "disp": False}
)

W_opt, b_opt = unpack(res.x)


# =========================
# 6) 评估指标（KPI）
# =========================
def evaluate_attention(C, y, W, b, topk=3):
    logits = C @ W + b
    probs = softmax(logits, axis=1)
    n = len(y)
    ce = -np.log(probs[np.arange(n), y] + 1e-12).mean()
    ppl = np.exp(ce)
    pred1 = np.argmax(probs, axis=1)
    acc1 = (pred1 == y).mean()
    topk_idx = np.argpartition(-probs, kth=topk - 1, axis=1)[:, :topk]
    acck = np.mean([y[i] in topk_idx[i] for i in range(n)])
    return ce, ppl, acc1, acck, probs


# Bigram基线：仅看最后一个词预测下一词
counts = np.ones((VOCAB_SIZE, VOCAB_SIZE)) * 0.1
for x, yt in zip(X_train, y_train):
    counts[x[-1], yt] += 1.0
P_bigram = counts / counts.sum(axis=1, keepdims=True)

def evaluate_bigram(X, y, Pbg, topk=3):
    probs = Pbg[X[:, -1]]
    n = len(y)
    ce = -np.log(probs[np.arange(n), y] + 1e-12).mean()
    ppl = np.exp(ce)
    pred1 = np.argmax(probs, axis=1)
    acc1 = (pred1 == y).mean()
    topk_idx = np.argpartition(-probs, kth=topk - 1, axis=1)[:, :topk]
    acck = np.mean([y[i] in topk_idx[i] for i in range(n)])
    return ce, ppl, acc1, acck, probs


ce_b, ppl_b, acc1_b, acck_b, probs_b = evaluate_bigram(X_test, y_test, P_bigram, TOPK)
ce_t, ppl_t, acc1_t, acck_t, probs_t = evaluate_attention(C_test, y_test, W_opt, b_opt, TOPK)


# =========================
# 7) 打印KPI表格
# =========================
print("\n=== KPI结果表（测试集）===")
print(f"{'模型':<20}{'CrossEntropy':>14}{'Perplexity':>12}{'Top1Acc':>10}{'Top3Acc':>10}")
print("-" * 66)
print(f"{'Bigram基线':<20}{ce_b:>14.4f}{ppl_b:>12.4f}{acc1_b:>10.4f}{acck_b:>10.4f}")
print(f"{'注意力+线性头':<20}{ce_t:>14.4f}{ppl_t:>12.4f}{acc1_t:>10.4f}{acck_t:>10.4f}")


# =========================
# 8) 生成matplotlib图
# =========================
idx = 0
x_demo = X_test[idx]
y_demo = y_test[idx]
_, alpha_demo = attention_features(X_test[idx:idx + 1], ATTN_TEMP)
alpha_demo = alpha_demo[0]
demo_probs = probs_t[idx]

topn = 8
top_idx = np.argsort(-demo_probs)[:topn]

fig, axes = 
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.subplots(1, 3, figsize=(16, 4.8))

# 图1：训练损失下降
if len(loss_trace) > 0:
    axes[0].plot(np.arange(1, len(loss_trace) + 1), loss_trace, color="#2a9d8f", lw=2)
axes[0].set_title("优化过程：训练损失")
axes[0].set_xlabel("迭代步")
axes[0].set_ylabel("NLL Loss")

# 图2：注意力权重
axes[1].bar(np.arange(SEQ_LEN), alpha_demo, color="#1f77b4", alpha=0.85)
axes[1].set_xticks(np.arange(SEQ_LEN))
axes[1].set_xticklabels([vocab[t] for t in x_demo], rotation=30)
axes[1].set_title("自注意力权重")
axes[1].set_xlabel("上下文词元位置")
axes[1].set_ylabel("权重")

# 图3：下一词Top概率
axes[2].bar(np.arange(topn), demo_probs[top_idx], color="#ff7f0e", alpha=0.85)
axes[2].set_xticks(np.arange(topn))
axes[2].set_xticklabels([vocab[t] for t in top_idx], rotation=30)
axes[2].set_title("下一词预测Top概率")
axes[2].set_xlabel("候选词元")
axes[2].set_ylabel("概率")

plt.tight_layout()
if SAVE_FIG:
    plt.savefig(FIG_PATH, dpi=150)
    print(f"\n图已保存：{FIG_PATH}")
# plt.show()  # 禁用弹窗

print("\n示例上下文：", " | ".join(vocab[t] for t in x_demo))
print("真实下一词：", vocab[y_demo])
print("模型预测：", vocab[np.argmax(demo_probs)])
