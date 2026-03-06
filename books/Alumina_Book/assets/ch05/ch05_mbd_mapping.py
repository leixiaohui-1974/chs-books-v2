import json
import pandas as pd
import os

# Ensure the directory exists
output_dir = r"D:\cowork\教材\chs-books-v2\books\Alumina_Book\assets\ch05"
os.makedirs(output_dir, exist_ok=True)

# 工业大模型知识映射仿真 (MBD Mapping & LLM Parsing)
# 场景：将氧化铝车间极其复杂的底层 PLC 变量点名 (Tag Names)，
# 强行降维、清洗并装载进大模型能够看懂的 MBD 结构化字典中，
# 从而让通用的“水网调度大模型”能直接指挥复杂的“冶金蒸发器”。

# 1. 底层恶劣的工业数据源 (Raw SCADA/PLC Data)
raw_industrial_data = {
    "A_EVAP_EFF1_TEMP_PT101": 155.4,  # 第一效温度
    "A_EVAP_EFF1_LVL_LT102": 45.2,    # 第一效液位 %
    "A_EVAP_EFF1_LIQ_CONC_AT105": 145.0, # 一效内物料浓度 g/L
    "STEAM_MAIN_VALVE_CV201_FB": 78.5, # 蒸汽主阀反馈 %
    "STEAM_MAIN_FLOW_FT202": 65.0,     # 蒸汽流量 t/h
    "CONDENSATE_PUMP_P301_SPD": 1450,  # 冷凝水泵转速 rpm
}

# 2. MBD 知识映射类 (Model-Based Definition Mapper)
class MBD_Mapper:
    @staticmethod
    def map_to_storage_node(raw_data, effect_num):
        # 降维：把一个复杂的闪蒸罐，看作一个水文学里的“蓄水节点”
        # 水位(%) 映射为 蓄水量(库容)；浓度映射为 节点水质
        lvl_key = f"A_EVAP_EFF{effect_num}_LVL_LT102"
        conc_key = f"A_EVAP_EFF{effect_num}_LIQ_CONC_AT105"
        
        return {
            "node_type": "storage_node",
            "node_id": f"Evaporator_Tank_{effect_num}",
            "capacity_percent": raw_data.get(lvl_key, 0.0),
            "quality_index": raw_data.get(conc_key, 0.0),
            "risk_status": "CRITICAL_HIGH" if raw_data.get(lvl_key, 0.0) > 85.0 else "SAFE"
        }
        
    @staticmethod
    def map_to_control_equipment(raw_data, equip_type):
        # 降维：把工业阀门或泵，统一映射为水网调度中的“动作执行器”
        if equip_type == "steam_valve":
            return {
                "equipment_type": "control_equipment",
                "equipment_id": "Main_Steam_Valve",
                "current_action_state": raw_data.get("STEAM_MAIN_VALVE_CV201_FB", 0.0),
                "flow_rate": raw_data.get("STEAM_MAIN_FLOW_FT202", 0.0),
                "constraint_status": "SATURATED" if raw_data.get("STEAM_MAIN_VALVE_CV201_FB", 0) > 95.0 else "FLEXIBLE"
            }

# 执行映射
mapped_tank = MBD_Mapper.map_to_storage_node(raw_industrial_data, 1)
mapped_valve = MBD_Mapper.map_to_control_equipment(raw_industrial_data, "steam_valve")

# 3. 模拟大模型 (LLM) 自然语言指令解析 (NLP Extraction)
# 场景：厂长在手机上语音说：“现在进料浓度突然掉到了 130 吨，马上给我把主蒸汽阀门关小点，别浪费煤！”
user_voice_input = "现在进料浓度突然掉到了130克每升，马上给我把主蒸汽阀门关小点，别浪费煤！"

# 模拟大模型通过 Prompt 提取出的实体结构 (Entity Extraction)
# 实际工程中这里调用 OpenAI/DeepSeek API，我们这里直接写死结果展示逻辑
llm_extracted_entities = {
    "intent": "OPTIMIZE_STEAM_CONSUMPTION",
    "detected_disturbances": [
        {"parameter": "feed_concentration", "value": 130.0, "unit": "g/L"}
    ],
    "target_equipment": "Main_Steam_Valve",
    "action_direction": "DECREASE"
}

# 4. 生成统一的大模型工作台诊断卡片 (Dashboard Card)
# 将底层状态与高层指令融合，生成人机可读的 JSON 报文
dashboard_card = {
    "System_State": {
        "Storage_Nodes": [mapped_tank],
        "Control_Equipment": [mapped_valve]
    },
    "AI_Agent_Diagnosis": {
        "Voice_Command_Parsed": llm_extracted_entities,
        "Action_Proposal": f"Detected Feed Conc drop to 130.0 g/L. Current Valve is at {mapped_valve['current_action_state']}%. Recommending calling SQP Optimizer to calculate new target to DECREASE steam flow."
    }
}

# 将 JSON 保存到文件 (代表发送给前端 Web 界面)
with open(os.path.join(output_dir, "mbd_state_card.json"), "w", encoding="utf-8") as f:
    json.dump(dashboard_card, f, indent=4, ensure_ascii=False)

# 5. 生成用于 Markdown 的追踪表格
history = [
    {'Data Layer': 'Raw SCADA Tag', 'Variable': 'A_EVAP_EFF1_LVL_LT102', 'Value': 45.2, 'Format': 'Float', 'Readability for LLM': 'Extremely Low (Crypto)'},
    {'Data Layer': 'MBD Storage Node', 'Variable': 'capacity_percent', 'Value': 45.2, 'Format': 'Standard JSON', 'Readability for LLM': 'Perfect (Semantic)'},
    {'Data Layer': 'Raw SCADA Tag', 'Variable': 'STEAM_MAIN_VALVE_CV201_FB', 'Value': 78.5, 'Format': 'Float', 'Readability for LLM': 'Extremely Low'},
    {'Data Layer': 'MBD Control Equip', 'Variable': 'current_action_state', 'Value': 78.5, 'Format': 'Standard JSON', 'Readability for LLM': 'Perfect (Actionable)'}
]

df = pd.DataFrame(history)
md_table = df.to_markdown(index=False)
with open(os.path.join(output_dir, "mbd_mapping_table.md"), "w", encoding="utf-8") as f:
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

create_schematic(os.path.join(output_dir, "problem_nano.png"), "Ch05: MBD Knowledge Mapping", "Diagram showing a chaotic, messy cloud of raw PLC tags (e.g., PT101, CV201) being funneled through a filter. Out comes a clean, structured MBD JSON object that an LLM brain can easily read and use to command the factory.")

print("Files generated successfully.")
