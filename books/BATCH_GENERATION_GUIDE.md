# Phase 4 配图批量生成使用指南

## 概述

为Phase 4的9本书（63章）批量生成189张配图：
- **数据曲线图**: 63张（Python matplotlib）
- **架构图**: 63张（nano-banana-pro）
- **概念图**: 63张（nano-banana-pro）

## 前置准备

### 1. 环境要求
```bash
# Python 3.8+
python --version

# 必要的Python包
pip install numpy matplotlib scipy
```

### 2. 设置Gemini API Key
```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY=your_api_key_here
```

### 3. 验证nano脚本路径
确认文件存在：`D:/cowork/openclaw-sync/skills/nano-banana-pro/scripts/generate_image.py`

## 使用方法

### 方式1：一键批量生成（推荐）

```bash
cd D:/cowork/教材/chs-books-v2/books
python batch_generate_all_figures.py
```

该脚本会：
1. 检查环境配置
2. 生成63张数据曲线图
3. 生成126张架构图和概念图
4. 生成统计报告

**预计耗时**: 2-3小时（取决于API速度）

### 方式2：分步执行

#### 步骤1：生成数据曲线图（快速）
```bash
cd D:/cowork/教材/chs-books-v2/books
python batch_generate_simulation_figures.py
```
**耗时**: 约10分钟

#### 步骤2：生成架构图和概念图（较慢）
```bash
cd D:/cowork/教材/chs-books-v2/books
python batch_generate_nano_figures.py
```
**耗时**: 约2-3小时（126张图 × 每张1-2分钟）

## 输出结构

```
D:/cowork/教材/chs-books-v2/books/
├── reservoir-operation-optimization/
│   ├── figures/
│   │   ├── ch01_simulation_result.png      # 数据曲线图
│   │   ├── ch01_architecture.png           # 架构图
│   │   ├── ch01_concept.png                # 概念图
│   │   ├── ch01_simulation.py              # 生成脚本
│   │   ├── ch02_*.png
│   │   └── ...
│   ├── ch01.md
│   └── ...
├── flood-forecasting-control/
│   ├── figures/
│   └── ...
└── ...
```

## 配图规范

### 数据曲线图
- **格式**: PNG
- **分辨率**: 300dpi
- **尺寸**: 自适应（通常14×5.2英寸）
- **中文标注**: 标题、坐标轴、图例
- **配色**: 深蓝#1565C0 + 橙红#FF7043
- **无弹窗**: matplotlib.use('Agg')

### 架构图/概念图
- **格式**: PNG
- **分辨率**: 300dpi
- **尺寸**: 180mm × 120mm
- **中文标注**: 宋体/黑体
- **配色**:
  - 主色：深蓝#1565C0
  - 辅色1：绿色#4CAF50
  - 辅色2：紫色#7B1FA2
  - 辅色3：橙红#FF7043
- **风格**: 扁平矢量，学术教材风格

## 插入章节文件

生成图片后，需要在章节Markdown文件中插入图片引用：

### 插入位置
1. **架构图**: 第1节理论框架后
2. **仿真结果图**: 第3节仿真分析后
3. **概念图**: 第2节方法介绍后

### 插入格式
```markdown
![图1-1 系统架构](figures/ch01_architecture.png)

**图1-1 系统架构**

*该图展示了XXX系统的整体架构，包含YYY模块和ZZZ接口。主要特点是...*
```

## 故障排查

### 问题1：Python脚本执行失败
**症状**: 提示"No module named 'numpy'"
**解决**: `pip install numpy matplotlib scipy`

### 问题2：nano生成失败
**症状**: "Error: No API key provided"
**解决**: 设置环境变量 `set GEMINI_API_KEY=your_key`

### 问题3：中文显示乱码
**症状**: 图片中中文显示为方框
**解决**:
- Windows: 确保安装了SimHei或Microsoft YaHei字体
- Linux: `sudo apt-get install fonts-wqy-zenhei`

### 问题4：图片生成超时
**症状**: "TimeoutExpired"
**解决**: 增加timeout参数（脚本中默认60秒）

### 问题5：API限流
**症状**: nano生成时提示"Rate limit exceeded"
**解决**: 脚本已内置2秒延迟，如仍限流可增加延迟时间

## 手动生成单张图片

### 生成数据曲线图
```bash
cd D:/cowork/教材/chs-books-v2/books/ai-for-water-engineering/figures
python ch01_simulation.py
```

### 生成架构图
```bash
cd D:/cowork/教材/chs-books-v2/books/ai-for-water-engineering/figures
python D:/cowork/openclaw-sync/skills/nano-banana-pro/scripts/generate_image.py \
  --prompt "为教材《人工智能与水利水电工程》第1章生成AI全景架构图..." \
  --filename ch01_architecture.png
```

## 质量检查清单

生成完成后，检查：
- [ ] 所有图片文件存在且大小>10KB
- [ ] 图片中文字清晰可读
- [ ] 配色符合统一方案
- [ ] 数据曲线图坐标轴标注完整
- [ ] 架构图逻辑关系清晰
- [ ] 概念图简洁易懂

## 批量检查脚本

```python
import os
from PIL import Image

base_dir = 'D:/cowork/教材/chs-books-v2/books'
books = ['reservoir-operation-optimization', ...]  # 9本书

for book in books:
    figures_dir = os.path.join(base_dir, book, 'figures')
    for file in os.listdir(figures_dir):
        if file.endswith('.png'):
            path = os.path.join(figures_dir, file)
            size = os.path.getsize(path)
            if size < 10000:
                print(f'警告: {book}/{file} 文件过小 ({size} bytes)')

            # 检查图片尺寸
            img = Image.open(path)
            print(f'{book}/{file}: {img.size[0]}×{img.size[1]}px, {size//1024}KB')
```

## 下一步工作

1. ✅ 批量生成189张图片
2. ⬜ 在63章Markdown文件中插入图片引用
3. ⬜ 添加图注说明
4. ⬜ 质量检查和修正
5. ⬜ 生成最终统计报告

## 联系与支持

如遇问题，检查：
1. `batch_generate_all_figures.py` 的环境检查输出
2. `figures/` 目录下的 `.py` 脚本是否正确生成
3. nano脚本的错误输出

---

**预计总耗时**: 2-3小时
**预计总文件大小**: 约200-300MB（189张图片）
