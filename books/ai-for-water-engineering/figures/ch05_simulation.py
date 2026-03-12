"""
教材：《人工智能与水利水电工程》
章节：第5章 RAG与知识库（5.1 基本概念与理论框架）
功能：仿真“知识库检索 + 大模型生成”流程，计算关键KPI并绘制性能曲线。
"""

import numpy as np
from scipy.spatial.distance import cdist
from scipy.special import expit
from scipy import stats
import matplotlib
matplotlib.use('Agg')  # 禁用GUI
import matplotlib.pyplot as plt

# ===================== 关键参数区（可按教学需要调整） =====================
RANDOM_SEED = 42             # 随机种子，保证实验可复现
N_TOPICS = 8                 # 水利知识主题数（如水文、调度、地质等抽象主题）
N_DOCS = 600                 # 知识库文档总量
N_QUERIES = 160              # 测试问题数量
EMBED_DIM = 32               # 向量维度
DOC_NOISE_STD = 0.55         # 文档向量噪声
QUERY_NOISE_STD = 0.65       # 问题向量噪声
TOPK_CANDIDATES = np.arange(1, 13)  # 待评估的Top-K范围

# 生成阶段参数（用来模拟“答案忠实度/幻觉率”）
FAITH_ALPHA = 9.0            # Sigmoid斜率：越大越敏感
FAITH_BETA = 0.55            # Sigmoid阈值：相关性超过该值后忠实度上升更快
HALLU_NOISE_STD = 0.05       # 幻觉率噪声

# 时延模型参数（毫秒）
BASE_LAT_MS = 65.0           # 固定开销
RETRIEVAL_COEF = 6.5         # 检索复杂度系数
GENERATION_COEF = 3.2        # 上下文长度（Top-K）对生成耗时影响

SAVE_FIG = True              # True时保存图片；False时仅弹窗显示
FIG_NAME = "rag_kpi_simulation.png"

rng = np.random.default_rng(RANDOM_SEED)

# ===================== 1) 构建“知识库”与“查询集” =====================
# 主题中心向量：代表不同水利领域知识簇
topic_centers = rng.normal(0, 1, size=(N_TOPICS, EMBED_DIM))
topic_centers = topic_centers / np.linalg.norm(topic_centers, axis=1, keepdims=True)

# 每篇文档分配一个真实主题，文档向量=主题中心+噪声
doc_topics = rng.integers(0, N_TOPICS, size=N_DOCS)
doc_embeddings = topic_centers[doc_topics] + rng.normal(0, DOC_NOISE_STD, size=(N_DOCS, EMBED_DIM))
doc_embeddings = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)

# 每个查询同样对应一个真实主题
query_topics = rng.integers(0, N_TOPICS, size=N_QUERIES)
query_embeddings = topic_centers[query_topics] + rng.normal(0, QUERY_NOISE_STD, size=(N_QUERIES, EMBED_DIM))
query_embeddings = query_embeddings / np.linalg.norm(query_embeddings, axis=1, keepdims=True)

# ===================== 2) 定义检索与指标函数 =====================
def retrieve_topk(q_emb, d_emb, k):
    """基于余弦距离检索Top-K文档。"""
    dist = cdist(q_emb[None, :], d_emb, metric="cosine")[0]  # 距离越小越相似
    topk_idx = np.argpartition(dist, k - 1)[:k]              # 先快速取k个候选
    topk_idx = topk_idx[np.argsort(dist[topk_idx])]          # 再精确排序
    topk_sim = 1.0 - dist[topk_idx]                          # 距离转相似度
    return topk_idx, topk_sim


def ndcg_at_k(relevance):
    """计算nDCG@K，relevance为排序后的分级相关性(0~1)。"""
    gains = (2 ** relevance - 1)
    discounts = 1 / np.log2(np.arange(2, len(relevance) + 2))
    dcg = np.sum(gains * discounts)
    ideal = np.sort(relevance)[::-1]
    idcg = np.sum((2 ** ideal - 1) * discounts)
    return float(dcg / idcg) if idcg > 0 else 0.0


# ===================== 3) 在不同Top-K下评估KPI =====================
results = []

for k in TOPK_CANDIDATES:
    recall_hits, reciprocal_ranks, ndcgs = [], [], []
    faith_scores, hallu_rates, latencies = [], [], []

    for qi in range(N_QUERIES):
        idx, sim = retrieve_topk(query_embeddings[qi], doc_embeddings, int(k))

        # 主题一致视为相关（教学仿真标签）
        rel_binary = (doc_topics[idx] == query_topics[qi]).astype(float)

        # Recall@K
        recall_hits.append(float(rel_binary.max() > 0))

        # MRR
        if rel_binary.max() > 0:
            first_rank = np.where(rel_binary > 0)[0][0] + 1
            reciprocal_ranks.append(1.0 / first_rank)
        else:
            reciprocal_ranks.append(0.0)

        # nDCG@K（分级相关性）
        rel_graded = np.clip((sim + 1) / 2, 0, 1)
        ndcgs.append(ndcg_at_k(rel_graded))

        # 忠实度：平均相关性经过Sigmoid映射
        mean_rel = float(np.mean(rel_graded))
        faith = float(expit(FAITH_ALPHA * (mean_rel - FAITH_BETA)))
        faith_scores.append(faith)

        # 幻觉率：与忠实度负相关+噪声
        hallu = np.clip(1.0 - faith + rng.normal(0, HALLU_NOISE_STD), 0, 1)
        hallu_rates.append(float(hallu))

        # 端到端时延：固定项+检索复杂度+Top-K上下文长度成本
        latency = (
            BASE_LAT_MS
            + RETRIEVAL_COEF * np.log2(N_DOCS)
            + GENERATION_COEF * k
            + rng.normal(0, 2.5)
        )
        latencies.append(float(max(latency, 1.0)))

    recall_k = float(np.mean(recall_hits))
    mrr = float(np.mean(reciprocal_ranks))
    ndcg = float(np.mean(ndcgs))
    faith_mean = float(np.mean(faith_scores))
    hallu_mean = float(np.mean(hallu_rates))
    lat_mean = float(np.mean(latencies))
    lat_ci95 = float(1.96 * stats.sem(latencies))

    # 综合效用：教学中用于演示“质量-风险-时延”折中
    utility = (0.45 * recall_k + 0.35 * faith_mean + 0.20 * ndcg) - 0.0015 * lat_mean

    results.append({
        "k": int(k),
        "Recall@K": recall_k,
        "MRR": mrr,
        "nDCG@K": ndcg,
        "Faithfulness": faith_mean,
        "Hallucination": hallu_mean,
        "Latency(ms)": lat_mean,
        "LatencyCI95": lat_ci95,
        "Utility": utility,
    })

# ===================== 4) 打印KPI结果表格 =====================
header = (
    f"{'K':>3} | {'Recall@K':>8} | {'MRR':>6} | {'nDCG@K':>7} | "
    f"{'Faith':>7} | {'Hallu':>7} | {'Latency(ms)':>11} | {'CI95':>6} | {'Utility':>7}"
)
print("\nRAG仿真KPI结果表")
print("-" * len(header))
print(header)
print("-" * len(header))
for r in results:
    print(
        f"{r['k']:3d} | {r['Recall@K']:8.3f} | {r['MRR']:6.3f} | {r['nDCG@K']:7.3f} | "
        f"{r['Faithfulness']:7.3f} | {r['Hallucination']:7.3f} | {r['Latency(ms)']:11.2f} | "
        f"{r['LatencyCI95']:6.2f} | {r['Utility']:7.3f}"
    )
print("-" * len(header))

best = max(results, key=lambda x: x["Utility"])
print(
    f"\n综合效用最优Top-K = {best['k']}，"
    f"Recall@K={best['Recall@K']:.3f}，Faith={best['Faithfulness']:.3f}，"
    f"Hallu={best['Hallucination']:.3f}，Latency={best['Latency(ms)']:.2f} ms"
)

# ===================== 5) 生成matplotlib图 =====================
ks = np.array([r["k"] for r in results])
recall_vals = np.array([r["Recall@K"] for r in results])
mrr_vals = np.array([r["MRR"] for r in results])
ndcg_vals = np.array([r["nDCG@K"] for r in results])
faith_vals = np.array([r["Faithfulness"] for r in results])
hallu_vals = np.array([r["Hallucination"] for r in results])
lat_vals = np.array([r["Latency(ms)"] for r in results])
util_vals = np.array([r["Utility"] for r in results])

fig, axes = 
# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.subplots(1, 3, figsize=(15, 4.5))

# 图1：检索指标
axes[0].plot(ks, recall_vals, marker='o', label='Recall@K')
axes[0].plot(ks, mrr_vals, marker='s', label='MRR')
axes[0].plot(ks, ndcg_vals, marker='^', label='nDCG@K')
axes[0].set_title('检索质量指标')
axes[0].set_xlabel('Top-K')
axes[0].set_ylabel('Score')
axes[0].grid(alpha=0.3)
axes[0].legend()

# 图2：可靠性指标
axes[1].plot(ks, faith_vals, marker='o', label='Faithfulness')
axes[1].plot(ks, hallu_vals, marker='x', label='Hallucination')
axes[1].set_title('生成可靠性指标')
axes[1].set_xlabel('Top-K')
axes[1].set_ylabel('Rate')
axes[1].grid(alpha=0.3)
axes[1].legend()

# 图3：效用-时延权衡
ax3 = axes[2]
ax3.plot(ks, util_vals, marker='o', color='tab:green', label='Utility')
ax3.set_xlabel('Top-K')
ax3.set_ylabel('Utility', color='tab:green')
ax3.tick_params(axis='y', labelcolor='tab:green')
ax3.grid(alpha=0.3)

ax3b = ax3.twinx()
ax3b.plot(ks, lat_vals, marker='d', color='tab:red', label='Latency(ms)')
ax3b.set_ylabel('Latency (ms)', color='tab:red')
ax3b.tick_params(axis='y', labelcolor='tab:red')
ax3.set_title('效用-时延权衡')

best_idx = np.where(ks == best['k'])[0][0]
ax3.scatter(ks[best_idx], util_vals[best_idx], color='black', zorder=5)
ax3.annotate(f"Best K={best['k']}", (ks[best_idx], util_vals[best_idx]),
             textcoords="offset points", xytext=(6, 8), fontsize=9)

fig.suptitle('第5章 5.1：RAG与知识库仿真结果', fontsize=13)
fig.tight_layout()

if SAVE_FIG:
    plt.savefig(FIG_NAME, dpi=160)
    print(f"\n图像已保存：{FIG_NAME}")
else:
    # plt.show()  # 禁用弹窗

# 额外理论验证：检索命中率与忠实度相关性
rho, p_value = stats.spearmanr(recall_vals, faith_vals)
print(f"\nSpearman相关(Recall@K, Faithfulness) = {rho:.3f}, p = {p_value:.4f}")
