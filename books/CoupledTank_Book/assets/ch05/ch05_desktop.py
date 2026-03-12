import json
import pandas as pd
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\CoupledTank_Book\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# CC-Desktop 工作台与智能决策助理 (Dashboard & LLM Agent)
# 场景：展示如何将底层的原始数据映射为大模型能够理解的 MBD 结构，
# 并模拟大模型解析自然语言意图并生成控制建议的过程。

# 1. 底层原始工业数据 (Raw PLC Data)
# 这是一段极其晦涩的工业数据，大模型直接看会产生“幻觉”
raw_scada_data = {
    "TANK1_LVL_AI01": 4.8,     # 水箱1水位(m) (极高，逼近 5.0m 极限)
    "TANK2_LVL_AI02": 1.2,     # 水箱2水位(m) (偏低)
    "PUMP_VFD_FREQ_AO01": 45.0, # 水泵频率(Hz)
    "VALVE_12_POS_AI03": 100.0, # 连通阀开度(%)
    "SYS_ALARM_CODE": "0x00F1"  # 告警码
}

# 2. MBD 映射器 (Model-Based Definition)
# 将底层信号翻译为结构化、具有水务工程语义的 JSON
class MBD_Mapper:
    @staticmethod
    def map_to_semantic_state(raw_data):
        return {
            "System_Type": "Coupled_Water_Tank_Network",
            "Nodes": [
                {
                    "id": "Tank_1_Upstream",
                    "current_level_m": raw_data["TANK1_LVL_AI01"],
                    "capacity_limit_m": 5.0,
                    "status": "CRITICAL_HIGH" if raw_data["TANK1_LVL_AI01"] > 4.5 else "SAFE"
                },
                {
                    "id": "Tank_2_Downstream",
                    "current_level_m": raw_data["TANK2_LVL_AI02"],
                    "capacity_limit_m": 5.0,
                    "status": "LOW" if raw_data["TANK2_LVL_AI02"] < 1.5 else "SAFE"
                }
            ],
            "Actuators": [
                {
                    "id": "Main_Inlet_Pump",
                    "running_freq_hz": raw_data["PUMP_VFD_FREQ_AO01"],
                    "max_freq_hz": 50.0
                }
            ]
        }

mbd_state = MBD_Mapper.map_to_semantic_state(raw_scada_data)

# 3. 模拟大模型意图解析 (Natural Language Understanding)
# 调度员的语音输入
user_prompt = "二号水箱怎么快见底了？马上给我把二号水箱的水位拉到 3 米去！别管一号水箱，抽快点！"

# 假设的大模型提取结果 (Function Calling)
llm_intent = {
    "action": "set_target_level",
    "target_node": "Tank_2_Downstream",
    "target_value": 3.0,
    "urgency": "HIGH",
    "user_override_safety": True # 用户说“别管一号水箱”
}

# 4. 智能体逻辑校验层 (Agent Safety Guardrail)
# 即使大模型解析出用户要“不管一号水箱狂抽水”，智能体会利用底层约束进行拦截
def agent_decision_engine(mbd_state, intent):
    tank1_level = mbd_state["Nodes"][0]["current_level_m"]
    limit = mbd_state["Nodes"][0]["capacity_limit_m"]
    
    if intent["target_node"] == "Tank_2_Downstream" and intent["target_value"] > mbd_state["Nodes"][1]["current_level_m"]:
        # 用户要求加水
        if tank1_level >= limit - 0.2:
            return {
                "execution": "DENIED",
                "reason": f"Physical Constraint Violation: Tank 1 is currently at {tank1_level}m. Pumping more water will cause immediate OVERFLOW (Limit: {limit}m).",
                "counter_proposal": "Executing MPC optimization to slowly raise Tank 2 while strictly holding Tank 1 below 5.0m."
            }
        else:
            return {"execution": "APPROVED", "reason": "Safe to proceed."}

decision = agent_decision_engine(mbd_state, llm_intent)

# 5. 生成综合数字孪生诊断报告 (JSON)
dashboard_payload = {
    "Semantic_State": mbd_state,
    "Human_Input": user_prompt,
    "LLM_Extracted_Intent": llm_intent,
    "Agent_Decision": decision
}

with open(os.path.join(output_dir, "cc_desktop_state.json"), "w", encoding="utf-8") as f:
    json.dump(dashboard_payload, f, indent=4, ensure_ascii=False)

# 6. 生成图表和 Markdown 表格
history = [
    {'Data Format': 'Raw PLC Tags', 'Example': 'TANK1_LVL_AI01 = 4.8', 'LLM Comprehension': 'Very Low (Causes Hallucinations)', 'Usage': 'DCS/SCADA base layer'},
    {'Data Format': 'MBD JSON', 'Example': '"status": "CRITICAL_HIGH"', 'LLM Comprehension': 'Perfect (Semantic anchor)', 'Usage': 'Digital Twin API'},
    {'Data Format': 'NLP Intent', 'Example': '{"target": 3.0}', 'LLM Comprehension': 'Native', 'Usage': 'Human-Machine Interface'},
    {'Data Format': 'Safety Guardrail', 'Example': '"execution": "DENIED"', 'LLM Comprehension': 'Logical Constraint', 'Usage': 'Preventing AI disasters'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "llm_mapping_table.md"), "w", encoding="utf-8") as f:
    f.write(md_table)

# 占位图生成
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch05: CC-Desktop & AI Assistant", "Diagram showing a furious human operator shouting into a microphone. The AI Assistant translates the angry words into a precise JSON command. But before it hits the water tanks, a 'Safety Guardrail' shield blocks the command to prevent an overflow.")

print("Files generated successfully.")
