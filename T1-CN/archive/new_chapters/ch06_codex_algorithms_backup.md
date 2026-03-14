技能使用：未触发可用 skill（当前任务是控制理论算法内容编写，与已列 skill 场景不匹配）。

# 《统一传递函数族理论》参数辨识算法（Markdown+LaTeX）

统一对象模型（以一阶惯性纯滞后 FOPDT 为核心）：
\[
G(s)=\frac{A_s e^{-\tau_d s}}{\tau_m s+1}
\]
其中 \(A_s\) 为静态增益，\(\tau_d\) 为纯滞后，\(\tau_m\) 为惯性时间常数。

---

## 1. 基于阶跃响应的辨识（\(A_s,\tau_d,\tau_m\)）

### 理论基础（约200字）
阶跃响应辨识基于对象在时域中的典型过渡特性。对输入阶跃 \(\Delta u\)，FOPDT 模型输出为
\[
y(t)=y_0+A_s\Delta u\left(1-e^{-\frac{t-\tau_d}{\tau_m}}\right)H(t-\tau_d)
\]
先由稳态增量比得到静态增益 \(A_s=\Delta y_\infty/\Delta u\)。再将输出归一化 \(z(t)=\frac{y(t)-y_0}{\Delta y_\infty}\)，可得 \(z=1-e^{-(t-\tau_d)/\tau_m}\)。取 \(z=0.283\) 与 \(z=0.632\) 两个特征点，分别对应 \(t_{28}= \tau_d+0.333\tau_m\)、\(t_{63}= \tau_d+\tau_m\)。由此可解
\[
\tau_m=1.5(t_{63}-t_{28}),\quad \tau_d=t_{63}-\tau_m
\]
该法计算量小、解释性强，适合章节教学与工程初值估计。

### 伪代码
```text
输入: 时间序列 t, 输入 u, 输出 y
1) 估计阶跃前后平均值: u0, uf, y0, y∞
2) 计算 Δu = uf-u0, Δy∞ = y∞-y0
3) 计算 As = Δy∞ / Δu
4) 归一化 z = (y-y0)/Δy∞
5) 线性插值求 z 首次达到 0.283 和 0.632 的时刻: t28, t63
6) τm = 1.5*(t63-t28)
7) τd = t63-τm
输出: As, τd, τm
```

### Python实现（详细注释）
```python
import numpy as np

def _first_crossing_time(t, z, target):
    """
    在线性插值意义下，求 z 首次达到 target 的时刻。
    若未达到则返回 None。
    """
    for i in range(1, len(z)):
        if z[i - 1] < target <= z[i]:
            # 线性插值：t = t1 + (target-z1)/(z2-z1)*(t2-t1)
            z1, z2 = z[i - 1], z[i]
            t1, t2 = t[i - 1], t[i]
            if np.isclose(z2, z1):
                return t2
            return t1 + (target - z1) * (t2 - t1) / (z2 - z1)
    return None

def identify_fopdt_from_step(t, u, y):
    """
    基于阶跃响应辨识 FOPDT 参数 As, tau_d, tau_m。
    参数:
        t: 时间数组 (N,)
        u: 输入数组 (N,)
        y: 输出数组 (N,)
    返回:
        dict: {"As":..., "tau_d":..., "tau_m":..., "t28":..., "t63":...}
    """
    t = np.asarray(t, dtype=float)
    u = np.asarray(u, dtype=float)
    y = np.asarray(y, dtype=float)

    # 使用前后 10% 数据估计稳态前后均值，降低噪声影响
    n = len(t)
    n_seg = max(3, n // 10)

    u0 = np.mean(u[:n_seg])
    uf = np.mean(u[-n_seg:])
    y0 = np.mean(y[:n_seg])
    y_inf = np.mean(y[-n_seg:])

    delta_u = uf - u0
    delta_y = y_inf - y0

    if np.isclose(delta_u, 0.0):
        raise ValueError("输入未形成有效阶跃，Δu≈0，无法辨识。")
    if np.isclose(delta_y, 0.0):
        raise ValueError("输出稳态变化过小，Δy≈0，无法辨识。")

    # 1) 静态增益
    As = delta_y / delta_u

    # 2) 归一化输出
    z = (y - y0) / delta_y

    # 3) 查找 28.3% 和 63.2% 特征时刻
    t28 = _first_crossing_time(t, z, 0.283)
    t63 = _first_crossing_time(t, z, 0.632)

    if (t28 is None) or (t63 is None):
        raise ValueError("未找到足够特征点，请检查数据长度或信噪比。")

    # 4) 由特征点解析计算 tau_m, tau_d
    tau_m = 1.5 * (t63 - t28)
    tau_d = t63 - tau_m

    return {"As": As, "tau_d": tau_d, "tau_m": tau_m, "t28": t28, "t63": t63}
```

### 使用示例
```python
# 生成仿真阶跃数据
np.random.seed(0)
As_true, tau_d_true, tau_m_true = 2.0, 1.2, 3.5
t = np.linspace(0, 30, 601)
u = np.ones_like(t)  # 幅值为1的阶跃

y = np.zeros_like(t)
idx = t >= tau_d_true
y[idx] = As_true * (1 - np.exp(-(t[idx] - tau_d_true) / tau_m_true))

# 加噪声
y_noisy = y + 0.02 * np.random.randn(len(t))

# 辨识
res = identify_fopdt_from_step(t, u, y_noisy)
print("Step-ID result:", res)
```

---

## 2. 基于频域数据的辨识

### 理论基础（约200字）
频域辨识直接利用实验频响 \(G(j\omega)\) 的幅值和相位信息。FOPDT 的频率响应为
\[
G(j\omega)=\frac{A_s e^{-j\omega\tau_d}}{1+j\omega\tau_m}
\]
其幅值与相位分别满足
\[
|G|=\frac{A_s}{\sqrt{1+(\omega\tau_m)^2}},\quad
\phi=-\omega\tau_d-\arctan(\omega\tau_m)
\]
先用幅值线性化得到初值：令 \(Y=1/|G|^2,\ X=[1,\omega^2]\)，则 \(Y=a+b\omega^2\)，其中 \(a=1/A_s^2,\ b=\tau_m^2/A_s^2\)。可由最小二乘求 \(a,b\)，进而得 \(A_s,\tau_m\)。再将相位展开并按
\[
\tau_d \approx -\frac{\phi+\arctan(\omega\tau_m)}{\omega}
\]
估计滞后，最后可用复频响非线性最小二乘整体精修。该法对噪声鲁棒，适合扫频或频响测试数据。

### 伪代码
```text
输入: 角频率 ωk, 复频响 Gk
1) 计算 |Gk|, φk=unwrap(angle(Gk))
2) 线性最小二乘拟合: 1/|Gk|^2 = a + b*ωk^2
3) As0 = 1/sqrt(a), τm0 = sqrt(b/a)
4) 用相位公式估计 τd0，并取中值增强鲁棒性
5) 以 [As0, τm0, τd0] 为初值做复频响最小二乘精修
输出: As, τd, τm
```

### Python实现（详细注释）
```python
import numpy as np

def identify_fopdt_from_frequency(w, G_meas, refine=True):
    """
    基于频域复数据辨识 FOPDT 参数。
    参数:
        w: 角频率数组 (N,), 单位 rad/s
        G_meas: 测得复频响数组 (N,), complex
        refine: 是否使用 scipy 做非线性精修
    返回:
        dict: {"As":..., "tau_d":..., "tau_m":...}
    """
    w = np.asarray(w, dtype=float)
    G_meas = np.asarray(G_meas, dtype=complex)

    # ---- 第1步: 幅值线性化初值 ----
    mag = np.abs(G_meas)
    inv_mag2 = 1.0 / np.maximum(mag ** 2, 1e-12)  # 防止除零

    # 线性模型: inv_mag2 = a + b * w^2
    X = np.column_stack([np.ones_like(w), w ** 2])
    theta, *_ = np.linalg.lstsq(X, inv_mag2, rcond=None)
    a, b = theta

    # 由 a,b 反算 As, tau_m，使用 max 防止数值异常
    a = max(a, 1e-12)
    b = max(b, 1e-12)
    As0 = 1.0 / np.sqrt(a)
    tau_m0 = np.sqrt(b / a)

    # ---- 第2步: 相位估计 tau_d 初值 ----
    phase = np.unwrap(np.angle(G_meas))

    # 避开过低频点（w太小时除法不稳定）
    mask = w > 1e-3
    tau_d_candidates = -(phase[mask] + np.arctan(w[mask] * tau_m0)) / w[mask]
    tau_d0 = float(np.median(tau_d_candidates))
    tau_d0 = max(tau_d0, 0.0)

    if not refine:
        return {"As": As0, "tau_d": tau_d0, "tau_m": tau_m0}

    # ---- 第3步: 非线性精修（可选）----
    try:
        from scipy.optimize import least_squares
    except ImportError:
        # 若无 scipy，直接返回初值
        return {"As": As0, "tau_d": tau_d0, "tau_m": tau_m0}

    def model(p):
        As, tau_m, tau_d = p
        return As * np.exp(-1j * w * tau_d) / (1.0 + 1j * w * tau_m)

    def residuals(p):
        G_hat = model(p)
        # 将复残差拆成实部+虚部，供 least_squares 处理
        r = G_hat - G_meas
        return np.hstack([r.real, r.imag])

    p0 = np.array([As0, tau_m0, tau_d0], dtype=float)
    lb = np.array([1e-8, 1e-8, 0.0])       # 参数下界
    ub = np.array([np.inf, np.inf, np.inf])  # 参数上界

    sol = least_squares(residuals, p0, bounds=(lb, ub))
    As, tau_m, tau_d = sol.x

    return {"As": float(As), "tau_d": float(tau_d), "tau_m": float(tau_m)}
```

### 使用示例
```python
# 构造仿真频域数据
np.random.seed(1)
As_true, tau_d_true, tau_m_true = 2.0, 1.2, 3.5
w = np.logspace(-2, 1.2, 120)  # 0.01~约15.8 rad/s

G_true = As_true * np.exp(-1j * w * tau_d_true) / (1 + 1j * w * tau_m_true)

# 叠加复噪声
noise = 0.01 * (np.random.randn(len(w)) + 1j * np.random.randn(len(w)))
G_meas = G_true + noise

res = identify_fopdt_from_frequency(w, G_meas, refine=True)
print("Freq-ID result:", res)
```

---

## 3. 在线递推最小二乘（RLS）辨识

### 理论基础（约200字）
在线辨识需要“边采样边更新”。将连续模型离散化为含输入延迟的 ARX 结构：
\[
y[k]=a\,y[k-1]+b\,u[k-d]+e[k]
\]
其中 \(a=e^{-T_s/\tau_m}\)，\(b=A_s(1-a)\)，\(d\approx \tau_d/T_s\)。对给定 \(d\)，定义回归向量 \(\varphi_k=[y[k-1],u[k-d]]^\top\)，参数 \(\theta=[a,b]^\top\)。RLS 递推为
\[
K_k=\frac{P_{k-1}\varphi_k}{\lambda+\varphi_k^\top P_{k-1}\varphi_k},\;
\theta_k=\theta_{k-1}+K_k(y_k-\varphi_k^\top\theta_{k-1})
\]
\[
P_k=\frac{1}{\lambda}(I-K_k\varphi_k^\top)P_{k-1}
\]
其中 \(\lambda\in(0,1]\) 为遗忘因子。若 \(d\) 未知，可并行多模型（delay bank）并按预测误差选择最优 \(d\)。最终反算
\[
\tau_m=-\frac{T_s}{\ln a},\quad A_s=\frac{b}{1-a},\quad \tau_d=dT_s
\]
实现实时自适应参数跟踪。

### 伪代码
```text
输入: u[k], y[k], Ts, 候选延迟集合 D
1) 对每个 d∈D 初始化 RLS(θd, Pd, err_d)
2) 对每个时刻 k:
   2.1) 对每个 d 更新 RLS: 用 φ=[y[k-1], u[k-d]]
   2.2) 递推累计误差 err_d
   2.3) 选误差最小的 d* 作为当前最优延迟
   2.4) 从 θ(d*) 反算 As, τm, τd
3) 输出最终参数与在线轨迹
```

### Python实现（详细注释）
```python
import numpy as np

class RLS2Param:
    """
    二参数 RLS 估计器，针对模型: y = theta^T * phi
    theta = [a, b]
    """
    def __init__(self, lam=0.995, delta=1000.0):
        self.lam = lam
        self.theta = np.zeros(2, dtype=float)
        self.P = delta * np.eye(2, dtype=float)

    def update(self, phi, y):
        """
        单步更新:
            phi: 回归向量 shape=(2,)
            y: 当前观测值
        返回:
            预测误差 e
        """
        phi = np.asarray(phi, dtype=float)
        y_hat = float(phi @ self.theta)      # 预测输出
        e = float(y - y_hat)                 # 预测误差

        # RLS 增益
        denom = self.lam + phi @ self.P @ phi
        K = (self.P @ phi) / denom

        # 参数更新
        self.theta = self.theta + K * e

        # 协方差更新
        self.P = (self.P - np.outer(K, phi) @ self.P) / self.lam
        return e

def online_identify_fopdt_rls(u, y, Ts, d_candidates, lam=0.995, delta=1000.0):
    """
    在线 RLS + 延迟模型组辨识 FOPDT 参数。
    参数:
        u, y: 输入输出序列
        Ts: 采样周期
        d_candidates: 延迟候选（整数样本）
    返回:
        final_result: 最终估计参数
        history: 每步估计轨迹（列表）
    """
    u = np.asarray(u, dtype=float)
    y = np.asarray(y, dtype=float)
    N = len(y)

    estimators = {d: RLS2Param(lam=lam, delta=delta) for d in d_candidates}
    # 指数加权误差，用于比较不同延迟模型优劣
    score = {d: 0.0 for d in d_candidates}

    history = []

    for k in range(1, N):
        valid_ds = []

        # 更新所有可用延迟模型
        for d in d_candidates:
            if k - d < 0:
                continue  # 当前时刻还拿不到 u[k-d]
            phi = np.array([y[k - 1], u[k - d]], dtype=float)
            e = estimators[d].update(phi, y[k])

            # 误差递推：越小代表该延迟模型越匹配
            score[d] = lam * score[d] + e * e
            valid_ds.append(d)

        if not valid_ds:
            history.append(None)
            continue

        # 选当前误差最小的延迟
        d_best = min(valid_ds, key=lambda d: score[d])
        a_hat, b_hat = estimators[d_best].theta

        # 数值保护：a 应在 (0,1) 才能对应稳定一阶惯性
        a_hat = float(np.clip(a_hat, 1e-6, 0.999999))

        # 连续参数反算
        tau_m_hat = -Ts / np.log(a_hat)
        As_hat = b_hat / (1.0 - a_hat)
        tau_d_hat = d_best * Ts

        history.append({
            "k": k,
            "As": float(As_hat),
            "tau_m": float(tau_m_hat),
            "tau_d": float(tau_d_hat),
            "a": float(a_hat),
            "b": float(b_hat),
            "d_best": int(d_best),
        })

    # 最后一个有效结果
    valid_hist = [h for h in history if h is not None]
    final_result = valid_hist[-1] if valid_hist else None
    return final_result, history
```

### 使用示例
```python
# 生成离散仿真数据（用于在线辨识）
np.random.seed(2)
As_true, tau_d_true, tau_m_true = 2.0, 1.2, 3.5
Ts = 0.1
N = 800

d_true = int(round(tau_d_true / Ts))
a_true = np.exp(-Ts / tau_m_true)
b_true = As_true * (1 - a_true)

# 激励信号：随机二值序列（保证持续激励）
u = (np.random.rand(N) > 0.5).astype(float)
y = np.zeros(N, dtype=float)

for k in range(1, N):
    ukd = u[k - d_true] if (k - d_true) >= 0 else 0.0
    y[k] = a_true * y[k - 1] + b_true * ukd + 0.01 * np.random.randn()

# 在线辨识
d_candidates = list(range(0, 30))  # 候选延迟 0~2.9s
final_res, hist = online_identify_fopdt_rls(u, y, Ts, d_candidates, lam=0.995)

print("Online RLS final:", final_res)
```

---

如果你愿意，我可以下一步把这三种算法整合成同一份“章节可直接粘贴版”（含统一符号表、复杂度对比表、适用场景表）。