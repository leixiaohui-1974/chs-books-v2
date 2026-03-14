"""Generate missing T1-CN figures using Gemini API via proxy."""
import os
import sys
import io
from pathlib import Path

# API config
API_KEY = "sk-253cb0523fb0818434ed0bd4f45e7379161abd56914c7f0f85c57fcbbec7a2f0"
BASE_URL = "https://aicode.cat/v1beta"

OUTPUT_DIR = Path(r"D:\cowork\教材\chs-books-v2\T1-CN\H")

PROMPTS = {
    "fig_08_01_cpss_architecture.png": '创作一幅专业学术插图：CPSS三层架构图。白色背景三层水平排列。顶层紫色Social层含多目标优化经济调度电网协调。中层深蓝色Cyber层含MPC控制器状态观测器故障诊断。底层绿色Physical层含水力系统机械系统电气系统。层间双向箭头连接标注状态反馈和控制指令。扁平矢量学术风格全部中文标注。',
    "fig_08_02_multiphysics_coupling.png": '创作一幅专业学术插图：水利系统多物理场耦合示意图。白色背景三个椭圆交叠维恩图。蓝色椭圆水力系统标注H水头Q流量。绿色椭圆机械系统标注omega转速Mt转矩。橙色椭圆电气系统标注Eq电势Pe电功率。交叠区标注耦合关系。中心三重交叠区7阶统一动态系统。底部标注多时间尺度。扁平矢量学术风格全部中文标注。',
    "fig_08_03_fusion_control.png": '创作一幅专业学术插图：CPSS框架三层融合控制流程图。白色背景自上而下三层闭环。顶层紫色Social层含多目标优化约束管理输出最优轨迹。中层蓝色Cyber层含MPC状态观测器故障诊断输出控制指令。底层绿色Physical层含水力机械电气模型反馈状态量。左侧标注时间尺度右侧红色安全包络贯穿三层。扁平矢量学术风格全部中文标注。',
    "fig_09_04_smith_predictor.png": '创作一幅专业学术控制系统框图：Smith预估补偿器结构图。白色背景经典控制框图。输入r进入求和器误差e进入蓝色控制器C0输出u进入绿色被控对象Gp含时滞输出y。并联通路u同时进入橙色虚线框内部模型Gp hat无时滞输出y hat。y hat和y比较差值反馈到主求和器。标注所有信号名称。橙色虚线框标注Smith预估器。扁平矢量学术风格全部中文标注。',
    "fig_14_03_sensor_fault.png": '创作一幅专业学术流程图：HydroCore传感器故障检测与容错流程。白色背景自上而下。起始蓝色传感器数据采集。两个并行菱形Chi-Square检验和冗余交叉验证。正常绿色正常运行。异常进入橙色三步隔离确认替代。判断有无冗余传感器分两条路径。最终汇合MPC控制不中断。右侧标注15到25秒完成。扁平矢量学术风格全部中文标注。',
    "fig_14_07_evolution_roadmap.png": '创作一幅专业学术时间线图：HydroCore-HydroClaw双引擎技术演进路线图。白色背景水平时间轴。三阶段渐变色块。浅蓝当前2025到2027工具驱动HydroCore主导。中蓝近期2028到2030 Agent自主模式多模态感知。深蓝远期2031加完全自主双引擎融合。时间轴标注里程碑。底部WNAL L2到L5箭头。扁平矢量学术风格全部中文标注。',
}

def generate_one(filename, prompt):
    """Generate a single image using Gemini API via proxy."""
    import requests
    import json
    import base64

    output_path = OUTPUT_DIR / filename
    if output_path.exists() and output_path.stat().st_size > 10000:
        print(f"  SKIP {filename} (already exists, {output_path.stat().st_size} bytes)")
        return True

    url = f"{BASE_URL}/models/gemini-2.0-flash-exp:generateContent"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
        }
    }

    print(f"  Generating {filename}...")
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            print(f"  FAIL {filename}: HTTP {resp.status_code} - {resp.text[:200]}")
            # Try alternate model
            for model in ["gemini-2.0-flash-exp-image-generation", "gemini-3-pro-image-preview"]:
                url2 = f"{BASE_URL}/models/{model}:generateContent"
                resp2 = requests.post(url2, headers=headers, json=payload, timeout=120)
                if resp2.status_code == 200:
                    resp = resp2
                    print(f"  Retried with {model} - OK")
                    break
            else:
                return False

        data = resp.json()
        # Extract image from response
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "inlineData" in part:
                    img_data = base64.b64decode(part["inlineData"]["data"])
                    output_path.write_bytes(img_data)
                    print(f"  OK {filename} ({len(img_data)} bytes)")
                    return True

        print(f"  FAIL {filename}: No image in response")
        print(f"  Response keys: {list(data.keys())}")
        if "candidates" in data:
            for c in data["candidates"]:
                parts = c.get("content", {}).get("parts", [])
                for p in parts:
                    print(f"    Part keys: {list(p.keys())}")
        return False

    except Exception as e:
        print(f"  FAIL {filename}: {e}")
        return False


if __name__ == "__main__":
    print(f"Generating {len(PROMPTS)} figures to {OUTPUT_DIR}\n")
    ok = 0
    for fn, prompt in PROMPTS.items():
        if generate_one(fn, prompt):
            ok += 1
    print(f"\nDone: {ok}/{len(PROMPTS)} succeeded")
