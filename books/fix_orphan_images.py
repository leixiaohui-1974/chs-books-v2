from __future__ import annotations
import re
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

BOOKS_DIR = Path("Z:/research/chs-books-v2/books")
LOG_PATH = BOOKS_DIR / "orphan_fix_log.txt"

ORPHAN_LIST = [
    ("ai-for-water-engineering", "figures/ch02_architecture.png", "ch02.md"),
    ("ai-for-water-engineering", "figures/ch02_concept.png", "ch02.md"),
    ("ai-for-water-engineering", "figures/ch02_simulation_result.png", "ch02.md"),
    ("ai-for-water-engineering", "figures/ch04_simulation_result.png", "ch04.md"),
    ("Alumina_Book", "assets/ch01/concept_evaporation_pain.png", "ch01.md"),
    ("Alumina_Book", "assets/ch02/concept_heat_mass_balance.png", "ch02.md"),
    ("Alumina_Book", "assets/ch03/concept_intelligent_control.png", "ch03.md"),
    ("Alumina_Book", "assets/ch06/concept_three_modes.png", "ch06.md"),
    ("Alumina_Book", "assets/ch07/concept_result_dashboard.png", "ch07.md"),
    ("Alumina_Book", "assets/ch08/concept_structural_isomorphism.png", "ch08.md"),
    ("canal-pipeline-control", "assets/ch01/concept_canal_pid_crisis.png", "ch01.md"),
    ("canal-pipeline-control", "assets/ch02/concept_cascade_feedforward.png", "ch02.md"),
    ("canal-pipeline-control", "assets/ch03/concept_dmc_data_driven.png", "ch03.md"),
    ("canal-pipeline-control", "assets/ch04/concept_canal_pump_coupling.png", "ch04.md"),
    ("canal-pipeline-control", "assets/ch05/concept_mixed_flow_coupling.png", "ch05.md"),
    ("CoupledTank_Book", "assets/ch01/concept_level_control_challenges.png", "ch01.md"),
    ("CoupledTank_Book", "assets/ch02/concept_coupled_tank_model.png", "ch02.md"),
    ("CoupledTank_Book", "assets/ch04/concept_l0_to_l4_stack.png", "ch04.md"),
    ("CoupledTank_Book", "assets/ch05/concept_cc_desktop.png", "ch05.md"),
    ("CoupledTank_Book", "assets/ch07/concept_data_to_decision.png", "ch07.md"),
    ("CoupledTank_Book", "assets/ch08/concept_scale_up_isomorphism.png", "ch08.md"),
    ("dam-safety-monitoring", "figures/ch01_simulation_result.png", "ch01.md"),
    ("dam-safety-monitoring", "figures/ch04_simulation_result.png", "ch04.md"),
    ("dam-safety-monitoring", "figures/ch06_simulation_result.png", "ch06.md"),
    ("dam-safety-monitoring", "figures/dam_seepage_sim.png", None),
    ("digital-twin-river-basin", "figures/ch01_simulation_result.png", "ch01.md"),
    ("digital-twin-river-basin", "figures/ch02_simulation_result.png", "ch02.md"),
    ("digital-twin-river-basin", "figures/ch03_simulation_result.png", "ch03.md"),
    ("digital-twin-river-basin", "figures/ch04_simulation_result.png", "ch04.md"),
    ("digital-twin-river-basin", "figures/ch06_simulation_result.png", "ch06.md"),
    ("digital-twin-river-basin", "figures/ch07_simulation_result.png", "ch07.md"),
    ("digital-twin-river-basin", "figures/ch08_simulation_result.png", "ch08.md"),
    ("distributed-hydrological-model", "assets/ch05/concept_river_network_parallel.png", "ch05.md"),
    ("distributed-hydrological-model", "assets/ch06/concept_calibration_optimization.png", "ch06.md"),
    ("distributed-hydrological-model", "assets/ch12/concept_reservoir_scheduling.png", "ch12.md"),
    ("ecohydraulics", "assets/ch01/concept_baseflow_threshold.png", "ch01.md"),
    ("energy-storage-system-modeling-control", "assets/ch02/problem_nano.png", "ch02.md"),
    ("energy-storage-system-modeling-control", "assets/ch02/thevenin_model_sim.png", "ch02.md"),
    ("energy-storage-system-modeling-control", "assets/ch03/ekf_soc_estimation_sim.png", "ch03.md"),
    ("energy-storage-system-modeling-control", "assets/ch03/problem_nano.png", "ch03.md"),
    ("energy-storage-system-modeling-control", "assets/ch05/bms_balancing_sim.png", "ch05.md"),
    ("energy-storage-system-modeling-control", "assets/ch05/problem_nano.png", "ch05.md"),
    ("energy-storage-system-modeling-control", "assets/ch06/dispatch_and_droop_sim.png", "ch06.md"),
    ("energy-storage-system-modeling-control", "assets/ch06/problem_nano.png", "ch06.md"),
    ("flood-forecasting-control", "figures/ch01_simulation_result.png", "ch01.md"),
    ("flood-forecasting-control", "figures/ch02_simulation_result.png", "ch02.md"),
    ("flood-forecasting-control", "figures/ch03_simulation_result.png", "ch03.md"),
    ("flood-forecasting-control", "figures/ch05_simulation_result.png", "ch05.md"),
    ("flood-forecasting-control", "figures/ch07_simulation_result.png", "ch07.md"),
    ("flood-forecasting-control", "figures/ch08_simulation_result.png", "ch08.md"),
    ("graduate-exam-prep", "assets/ch02/bode_step_sim.png", "ch02.md"),
    ("graduate-exam-prep", "assets/ch02/problem_nano.png", "ch02.md"),
    ("graduate-exam-prep", "assets/ch06/ch06_exam_problems.png", "ch06.md"),
    ("inland-waterway-navigation", "figures/ch01_simulation_result.png", "ch01.md"),
    ("inland-waterway-navigation", "figures/ch03_simulation_result.png", "ch03.md"),
    ("inland-waterway-navigation", "figures/chapter2_navigation_dispatch.png", "ch02.md"),
    ("inland-waterway-navigation", "figures/chapter5_dispatch.png", "ch05.md"),
    ("integrated-energy-system-simulation-optimization", "assets/ch04/problem_nano.png", "ch04.md"),
    ("intelligent-water-network-design", "assets/ch01/concept_digital_foundation.png", "ch01.md"),
    ("intelligent-water-network-design", "assets/ch02/concept_edge_iot.png", "ch02.md"),
    ("intelligent-water-network-design", "assets/ch03/concept_cloud_edge_device.png", "ch03.md"),
    ("intelligent-water-network-design", "assets/ch04/concept_disaster_recovery.png", "ch04.md"),
    ("intelligent-water-network-design", "assets/ch05/concept_hil_sil_testing.png", "ch05.md"),
    ("open-channel-hydraulics", "assets/ch07/problem_nano.png", "ch07.md"),
    ("open-channel-hydraulics", "assets/ch08/problem_nano.png", "ch08.md"),
    ("open-channel-hydraulics", "assets/ch09/problem_nano.png", "ch09.md"),
    ("open-channel-hydraulics", "assets/ch10/problem_nano.png", "ch10.md"),
    ("photovoltaic-system-modeling-control", "assets/ch03/concept_inverter_grid_control.png", "ch03.md"),
    ("photovoltaic-system-modeling-control", "assets/ch05/concept_hydro_solar_complement.png", "ch05.md"),
    ("renewable-energy-system-identification-testing", "assets/ch02/problem_nano.png", "ch02.md"),
    ("renewable-energy-system-identification-testing", "assets/ch02/rls_pmsm_sim.png", "ch02.md"),
    ("renewable-energy-system-identification-testing", "assets/ch04/concept_hil_testing.png", "ch04.md"),
    ("reservoir-operation-optimization", "figures/ch01_reservoir_dispatch_simulation.png", "ch01.md"),
    ("reservoir-operation-optimization", "figures/ch02_architecture.png", "ch02.md"),
    ("reservoir-operation-optimization", "figures/ch05_simulation_result.png", "ch05.md"),
    ("reservoir-operation-optimization", "figures/ch07_simulation_result.png", "ch07.md"),
    ("river-sediment-dynamics", "figures/ch01_simulation_result.png", "ch01.md"),
    ("river-sediment-dynamics", "figures/ch03_simulation_result.png", "ch03.md"),
    ("river-sediment-dynamics", "figures/ch04_simulation_result.png", "ch04.md"),
    ("river-sediment-dynamics", "figures/ch05_bed_evolution.png", "ch05.md"),
    ("river-sediment-dynamics", "figures/ch05_simulation_result.png", "ch05.md"),
    ("river-sediment-dynamics", "figures/ch06_simulation_result.png", "ch06.md"),
    ("ship-lock-automation", "figures/ch01_simulation_result.png", "ch01.md"),
    ("ship-lock-automation", "figures/ch02_simulation_result.png", "ch02.md"),
    ("ship-lock-automation", "figures/ch03_simulation_result.png", "ch03.md"),
    ("ship-lock-automation", "figures/ch04_simulation_result.png", "ch04.md"),
    ("underground-water-dynamics", "assets/ch01/concept_groundwater_fundamentals.png", "ch01.md"),
    ("underground-water-dynamics", "assets/ch02/concept_parameter_calibration.png", "ch02.md"),
    ("underground-water-dynamics", "assets/ch03/concept_sw_gw_coupling.png", "ch03.md"),
    ("underground-water-dynamics", "assets/ch04/concept_human_impact.png", "ch04.md"),
    ("underground-water-dynamics", "assets/ch05/concept_intelligent_digital_twin.png", "ch05.md"),
    ("water-energy-food-nexus", "figures/ch01_simulation_result.png", "ch01.md"),
    ("water-energy-food-nexus", "figures/ch02_simulation_result.png", "ch02.md"),
    ("water-energy-food-nexus", "figures/ch04_simulation_result.png", "ch04.md"),
    ("water-energy-food-nexus", "figures/ch05_simulation_result.png", "ch05.md"),
    ("water-energy-food-nexus", "figures/ch06_simulation_result.png", "ch06.md"),
    ("water-resource-planning-management", "assets/ch03/concept_dp_reservoir.png", "ch03.md"),
    ("water-resource-planning-management", "assets/ch03/problem_nano.png", "ch03.md"),
    ("water-system-control", "assets/ch01/tank_diagram.png", "ch01.md"),
    ("water-system-control", "assets/ch01/tank_nano_diagram.png", "ch01.md"),
    ("water-system-control", "assets/ch01/tank_nano_diagram_v2.png", "ch01.md"),
    ("water-system-control", "assets/ch01/tank_nano_diagram_v3.png", "ch01.md"),
    ("water-system-control", "assets/ch02/tank_windup_diagram.png", "ch02.md"),
    ("water-system-control", "assets/ch02/tank_windup_diagram_nano.png", "ch02.md"),
    ("water-system-control", "assets/ch03/problem_nano.png", "ch03.md"),
    ("water-system-control", "assets/ch04/coupled_tanks_nano.png", "ch04.md"),
    ("water-system-control", "assets/ch04/coupled_tanks_sim.png", "ch04.md"),
    ("water-system-control", "assets/ch04/problem_nano.png", "ch04.md"),
    ("water-system-control", "assets/ch05/kalman_nano.png", "ch05.md"),
    ("water-system-control", "assets/ch06/lqr_diagram.png", "ch06.md"),
    ("water-system-control", "assets/ch06/lqr_nano_diagram.png", "ch06.md"),
    ("water-system-control", "assets/ch06/lqr_sim.png", "ch06.md"),
    ("water-system-control", "assets/ch07/mpc_diagram.png", "ch07.md"),
    ("water-system-control", "assets/ch07/mpc_sim.png", "ch07.md"),
    ("water-system-control", "assets/ch08/canal_delay_sim.png", "ch08.md"),
    ("water-system-control", "assets/ch08/canal_nano_diagram.png", "ch08.md"),
    ("water-system-control", "assets/ch09/smc_diagram.png", "ch09.md"),
    ("water-system-control", "assets/ch09/smc_sim.png", "ch09.md"),
    ("water-system-control", "assets/ch10/problem_nano.png", "ch10.md"),
    ("water-system-control", "assets/ch10/rl_learning_curve.png", "ch10.md"),
    ("wind-power-system-modeling-control", "assets/ch03/concept_full_converter_pmsg.png", "ch03.md"),
    ("wind-power-system-modeling-control", "assets/ch04/concept_wake_cooperative.png", "ch04.md"),
    ("wind-power-system-modeling-control", "assets/ch05/concept_wind_hydro_dispatch.png", "ch05.md"),
]

SPECIAL_ALT = {
    "dam_seepage_sim.png": "渗流仿真结果",
    "chapter2_navigation_dispatch.png": "调度示意图",
    "chapter5_dispatch.png": "调度示意图",
    "ch02_concept.png": "本章概念图",
    "ch06_exam_problems.png": "考试题目概化图",
    "bode_step_sim.png": "仿真结果",
    "rls_pmsm_sim.png": "仿真结果",
    "ekf_soc_estimation_sim.png": "仿真结果",
    "thevenin_model_sim.png": "仿真结果",
    "bms_balancing_sim.png": "仿真结果",
    "dispatch_and_droop_sim.png": "仿真结果",
    "canal_delay_sim.png": "仿真结果",
    "ch05_bed_evolution.png": "河床演变仿真结果",
    "rl_learning_curve.png": "强化学习收敛曲线",
    "coupled_tanks_nano.png": "系统概化图",
    "tank_nano_diagram.png": "水箱概化图",
    "tank_nano_diagram_v2.png": "水箱概化图",
    "tank_nano_diagram_v3.png": "水箱概化图",
    "tank_windup_diagram_nano.png": "水箱抗积分饱和概化图",
    "kalman_nano.png": "卡尔曼滤波概化图",
    "lqr_nano_diagram.png": "LQR控制概化图",
    "canal_nano_diagram.png": "运河时延概化图",
    "ch01_reservoir_dispatch_simulation.png": "仿真结果",
    "ch02_architecture.png": "系统架构图",
}


def get_img_type(filename: str) -> str:
    stem = Path(filename).stem
    name = Path(filename).name
    if stem.startswith("concept_") or name == "ch02_concept.png":
        return "CONCEPT"
    if name == "problem_nano.png":
        return "PROBLEM"
    if (stem.endswith("_simulation_result") or stem.endswith("_dispatch_simulation")
            or stem.endswith("_bed_evolution") or "_sim" in stem):
        return "SIMULATION"
    if stem.endswith("_architecture"):
        return "ARCH"
    if "_diagram" in stem or "_nano" in stem:
        return "DIAGRAM"
    if stem.endswith("_learning_curve") or stem.endswith("_dispatch"):
        return "OTHER"
    return "OTHER"


def get_alt_text(filename: str) -> str:
    name = Path(filename).name
    if name in SPECIAL_ALT:
        return SPECIAL_ALT[name]
    img_type = get_img_type(filename)
    if img_type == "CONCEPT":
        return "本章概念图"
    if img_type == "PROBLEM":
        return "问题概化图"
    if img_type == "SIMULATION":
        return "仿真结果"
    if img_type == "ARCH":
        return "系统架构图"
    stem = Path(filename).stem
    stem = re.sub(r"^ch\d+_", "", stem)
    KEYWORD_MAP = {
        "tank": "水箱", "lqr": "LQR", "mpc": "MPC", "smc": "SMC",
        "pid": "PID", "canal": "运河", "coupled": "耦合", "windup": "抗积分饱和",
        "diagram": "示意图", "nano": "概化图", "dispatch": "调度",
    }
    parts = stem.split("_")
    translated = [KEYWORD_MAP.get(p.lower(), p.upper()) for p in parts]
    return "".join(translated) + "图"


def infer_chapter_from_filename(filename: str, book_dir: Path):
    stem = Path(filename).stem
    keywords = [kw for kw in stem.split("_") if len(kw) > 2]
    md_files = sorted(book_dir.glob("ch*.md"))
    if not md_files:
        return None
    best_file = None
    best_count = 0
    for md in md_files:
        try:
            text = md.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        count = sum(1 for kw in keywords if kw.lower() in text)
        if count > best_count:
            best_count = count
            best_file = md.name
    return best_file or md_files[0].name


def find_insert_position_concept(lines: list) -> int:
    for i, line in enumerate(lines):
        if line.startswith("## "):
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "":
                    return j
            return i + 1
    return 1


def find_insert_position_problem(lines: list) -> int:
    KEYWORDS = ("问题", "案例", "例题", "思考", "练习", "习题")
    for i, line in enumerate(lines):
        if (line.startswith("## ") or line.startswith("### ")) and any(k in line for k in KEYWORDS):
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "":
                    return j
            return i + 1
    return int(len(lines) * 0.6)


def find_second_last_para(lines: list) -> int:
    para_starts = []
    in_para = False
    for i, line in enumerate(lines):
        if line.strip():
            if not in_para:
                para_starts.append(i)
                in_para = True
        else:
            in_para = False
    if len(para_starts) >= 2:
        return para_starts[-2]
    elif para_starts:
        return para_starts[-1]
    return max(0, len(lines) - 2)


def find_insert_position_simulation(lines: list) -> int:
    SIM_KEYWORDS = ("仿真", "结果", "实验", "验证", "分析", "讨论")
    target_start = -1
    for i, line in enumerate(lines):
        if (line.startswith("## ") or line.startswith("### ")) and any(k in line for k in SIM_KEYWORDS):
            target_start = i
            break
    if target_start == -1:
        return find_second_last_para(lines)
    section_level = 2 if lines[target_start].startswith("## ") else 3
    section_end = len(lines)
    for i in range(target_start + 1, len(lines)):
        line = lines[i]
        if section_level == 2 and line.startswith("## "):
            section_end = i
            break
        if section_level == 3 and (line.startswith("## ") or line.startswith("### ")):
            section_end = i
            break
    last_table_end = -1
    in_table = False
    for i in range(target_start, section_end):
        stripped = lines[i].strip()
        if stripped.startswith("|"):
            in_table = True
            last_table_end = i
        elif in_table and stripped == "":
            in_table = False
    if last_table_end != -1:
        for j in range(last_table_end + 1, section_end):
            if lines[j].strip() == "":
                return j
        return last_table_end + 1
    else:
        for j in range(target_start + 1, section_end):
            if lines[j].strip() == "":
                return j
        return target_start + 1


def find_insert_position_diagram(lines: list, filename: str) -> int:
    stem = Path(filename).stem
    STOP_WORDS = {"diagram", "nano", "v2", "v3", "sim", "result"}
    parts = [p for p in stem.split("_") if p.lower() not in STOP_WORDS and len(p) > 1
             and not re.match(r"ch\d+", p)]
    KEYWORD_MAP = {
        "tank": ["水箱", "tank", "水位"],
        "lqr": ["lqr", "LQR", "最优控制"],
        "mpc": ["mpc", "MPC", "预测控制"],
        "smc": ["smc", "SMC", "滑模"],
        "canal": ["渠", "运河", "canal"],
        "windup": ["积分", "windup", "抗饱和"],
        "coupled": ["耦合", "coupled"],
        "kalman": ["卡尔曼", "kalman", "状态估计"],
        "delay": ["时延", "delay", "纯滞后"],
        "rl": ["强化", "RL", "reinforcement"],
        "learning": ["学习", "learning"],
    }
    for i, line in enumerate(lines):
        if not (line.startswith("## ") or line.startswith("### ")):
            continue
        line_lower = line.lower()
        for part in parts:
            matched_words = KEYWORD_MAP.get(part.lower(), [part.lower()])
            if any(w.lower() in line_lower for w in matched_words):
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == "":
                        return j
                return i + 1
    return find_insert_position_concept(lines)


def image_already_referenced(lines: list, filename: str) -> bool:
    img_name = Path(filename).name
    return any(img_name in line for line in lines)


def build_image_ref(img_path: str, alt: str) -> str:
    return f"\![{alt}]({img_path})"


def insert_image_into_lines(lines: list, insert_after: int, img_ref: str):
    insert_after = max(0, min(insert_after, len(lines) - 1))
    before_is_blank = lines[insert_after].strip() == "" if insert_after < len(lines) else True
    next_idx = insert_after + 1
    after_is_blank = lines[next_idx].strip() == "" if next_idx < len(lines) else True
    insert_block = []
    if not before_is_blank:
        insert_block.append("\n")
    insert_block.append(img_ref + "\n")
    if not after_is_blank:
        insert_block.append("\n")
    new_lines = lines[: insert_after + 1] + insert_block + lines[insert_after + 1 :]
    actual_line = insert_after + (0 if before_is_blank else 1) + 1
    return new_lines, actual_line


class InsertResult(NamedTuple):
    status: str
    book: str
    md_file: str
    img_path: str
    line_no: int
    reason: str


def process_orphan(book: str, img_rel: str, chapter_hint) -> InsertResult:
    book_dir = BOOKS_DIR / book
    if not book_dir.is_dir():
        return InsertResult("warning", book, "", img_rel, 0, f"书籍目录不存在: {book_dir}")
    if chapter_hint:
        md_path = book_dir / chapter_hint
    else:
        inferred = infer_chapter_from_filename(img_rel, book_dir)
        if not inferred:
            return InsertResult("warning", book, "", img_rel, 0, "无法推断目标章节文件")
        md_path = book_dir / inferred
    if not md_path.exists():
        return InsertResult("warning", book, str(md_path.name), img_rel, 0, f"目标文件不存在: {md_path}")
    try:
        content = md_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as e:
        return InsertResult("warning", book, md_path.name, img_rel, 0, f"读取文件失败: {e}")
    lines = content.splitlines(keepends=True)
    img_filename = Path(img_rel).name
    if image_already_referenced(lines, img_filename):
        return InsertResult("skipped", book, md_path.name, img_rel, 0, "已存在引用")
    img_type = get_img_type(img_filename)
    alt = get_alt_text(img_filename)
    img_ref = build_image_ref(img_rel, alt)
    if img_type in ("CONCEPT", "ARCH"):
        insert_after = find_insert_position_concept(lines)
    elif img_type == "PROBLEM":
        insert_after = find_insert_position_problem(lines)
    elif img_type == "SIMULATION":
        insert_after = find_insert_position_simulation(lines)
    else:
        insert_after = find_insert_position_diagram(lines, img_filename)
    new_lines, actual_line = insert_image_into_lines(lines, insert_after, img_ref)
    try:
        md_path.write_text("".join(new_lines), encoding="utf-8")
    except OSError as e:
        return InsertResult("warning", book, md_path.name, img_rel, 0, f"写文件失败: {e}")
    return InsertResult("success", book, md_path.name, img_rel, actual_line, "")


def main() -> None:
    results = []
    total = len(ORPHAN_LIST)
    print(f"开始处理 {total} 个孤儿图片...")
    print(f"工作目录: {BOOKS_DIR}")
    print("-" * 60)
    for idx, (book, img_rel, chapter_hint) in enumerate(ORPHAN_LIST, 1):
        result = process_orphan(book, img_rel, chapter_hint)
        results.append(result)
        status_char = {"success": "OK  ", "skipped": "SKIP", "warning": "WARN"}[result.status]
        print(f"[{idx:3d}/{total}] [{status_char}] {book}/{img_rel}")
        if result.status == "warning":
            print(f"         原因: {result.reason}")
    success = sum(1 for r in results if r.status == "success")
    skipped = sum(1 for r in results if r.status == "skipped")
    warnings = sum(1 for r in results if r.status == "warning")
    print("-" * 60)
    print(f"处理完成: 成功 {success} 个, 跳过 {skipped} 个, 警告 {warnings} 个")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lines = [
        "孤儿图片修复日志",
        f"生成时间: {now}",
        "=" * 60,
        "",
    ]
    for r in results:
        if r.status == "success":
            log_lines.append(
                f"[成功] 书籍: {r.book}, 文件: {r.md_file}, 行号: {r.line_no}, 图片: {r.img_path}"
            )
        elif r.status == "skipped":
            log_lines.append(
                f"[跳过] 书籍: {r.book}, 文件: {r.md_file}, 图片: {r.img_path}, 原因: {r.reason}"
            )
        else:
            fn = r.md_file if r.md_file else "(未知)"
            log_lines.append(
                f"[警告] 书籍: {r.book}, 文件: {fn}, 图片: {r.img_path}, 原因: {r.reason}"
            )
    log_lines += [
        "",
        "=" * 60,
        f"总计: 成功 {success} 个, 跳过 {skipped} 个, 警告 {warnings} 个",
    ]
    LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"\n日志已保存到: {LOG_PATH}")


if __name__ == "__main__":
    main()
