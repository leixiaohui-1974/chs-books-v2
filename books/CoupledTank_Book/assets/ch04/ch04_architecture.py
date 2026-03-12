import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\CoupledTank_Book\assets\ch04"
os.makedirs(output_dir, exist_ok=True)

# 全栈架构设计 (Full Stack Architecture: L0 to L4)
# 模拟从 L0 物理引擎到 L4 认知大模型整个链路的信息传递延迟与执行效率。
# 场景：展示一个指令从顶层自然语言下发，经过层层解析，最终作用于底层水泵的完整时序。

# 1. 定义架构层级与时延模型 (Timing Model)
# 模拟一次控制循环 (Control Cycle) 中各层级的耗时 (毫秒)
layers = ['L4 (Cognitive Agent / LLM)', 'L3 (Orchestration / Skill)', 'L2 (MCP Gateway API)', 'L1 (DCS / PLC)', 'L0 (Physical Valves/Pumps)']
latencies_cloud = [2500.0, 150.0, 50.0, 20.0, 500.0] # 云端大模型直连底层，延迟极高且不稳定
latencies_edge = [0.0, 0.0, 5.0, 2.0, 500.0] # 边缘自主控制 (切断 L4，完全由 L1 闭环)，延迟极低

# 2. 生成阶梯图 (Waterfall/Gantt Chart for Latency)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

def plot_waterfall(ax, latencies, title, total_color):
    starts = [0]
    for i in range(len(latencies) - 1):
        starts.append(starts[-1] + latencies[i])
        
    y_pos = np.arange(len(layers))[::-1] # 从上到下画
    
    # 画阶梯
    ax.barh(y_pos, latencies, left=starts, color='skyblue', edgecolor='black')
    
    # 标数值
    for i, (start, duration) in enumerate(zip(starts, latencies)):
        if duration > 0:
            ax.text(start + duration + 50, y_pos[i], f'{int(duration)} ms', va='center')
            
    # 画总线
    total_time = sum(latencies)
    ax.axvline(total_time, color=total_color, linestyle='--', linewidth=2)
    ax.text(total_time / 2, -1, f'Total Response Time: {int(total_time)} ms', ha='center', fontsize=12, color=total_color, weight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(layers)
    ax.set_xlabel('Time (milliseconds)')
    ax.set_title(title, fontsize=14)
    ax.grid(axis='x', linestyle=':', alpha=0.6)
    # 统一刻度以便对比，设为 3500ms
    ax.set_xlim(0, 3500)

plot_waterfall(ax1, latencies_cloud, 'Cloud AI Control Loop (NLP Driven)', 'red')
plot_waterfall(ax2, latencies_edge, 'Local PLC Closed-Loop (Edge Autonomous)', 'green')

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "architecture_latency_sim.png"), dpi=300, bbox_inches='tight')

# 3. 模拟架构的通信解耦 (Payload 转换过程)
# 生成一个展示层级之间传递的 JSON 报文示例表格
payloads = [
    {'Layer': 'L4 -> L3', 'Protocol': 'Natural Language', 'Payload Content': '“帮我把2号水箱的水位稳在4米，绝对不能溢出。”', 'Size': 'Text (High Semantic)'},
    {'Layer': 'L3 -> L2', 'Protocol': 'FastMCP JSON-RPC', 'Payload Content': '{"method": "set_mpc_target", "params": {"tank_id": 2, "target": 4.0, "constraints": {"tank_1_max": 5.0}}}', 'Size': 'JSON (Structured)'},
    {'Layer': 'L2 -> L1', 'Protocol': 'Modbus TCP', 'Payload Content': 'Write Register 40001: 400 (Target = 4.0 * 100)', 'Size': 'Bytes (Binary)'},
    {'Layer': 'L1 -> L0', 'Protocol': '4-20mA Analog', 'Payload Content': '12.8 mA current signal to Pump VFD', 'Size': 'Analog Voltage/Current'}
]

df_payloads = pd.DataFrame(payloads)
md_table = df_payloads.to_markdown(index=False)
with open(os.path.join(output_dir, "architecture_payload_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 4. 占位图生成
def create_schematic(path, title, description):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (1024, 512), color=(240, 245, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, 1014, 502], outline=(100, 100, 150), width=3)
    try: font_title = ImageFont.truetype('arial.ttf', 36); font_desc = ImageFont.truetype('arial.ttf', 24)
    except: font_title = ImageFont.load_default(); font_desc = ImageFont.load_default()
    d.text((40, 40), title, fill=(20, 40, 100), font=font_title)
    
    words = description.split()
    lines, current_line = [], []
    for word in words:
        current_line.append(word)
        if len(current_line) > 12: lines.append(' '.join(current_line)); current_line = []
    if current_line: lines.append(' '.join(current_line))
        
    y_offset = 120
    for line in lines:
        d.text((40, y_offset), line, fill=(50, 50, 50), font=font_desc)
        y_offset += 35
    img.save(path)

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch04: Full Stack L0 to L4", "Diagram showing a vertical technology stack. L0 is a dirty water pump. L1 is a metal PLC box. L2 is an API gateway. L3 is an orchestration engine. L4 is a glowing AI brain (LLM) at the top, handing down high-level commands through the stack.")

print("Files generated successfully.")
