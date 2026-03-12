#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量为Phase 4九本书的65章补充参考文献

使用方法:
    python batch_add_references.py

功能:
    1. 读取核心参考文献库
    2. 为每章自动选择3-4篇相关参考文献
    3. 在"本章小结"后插入"参考文献"段落
    4. 生成修改报告
"""

import os
import re
from pathlib import Path

# 核心参考文献库 (从核心参考文献库_Phase4.md提取)
REFERENCE_DATABASE = {
    "reservoir-operation-optimization": [
        "Bellman, R. (1957). *Dynamic Programming*. Princeton University Press.",
        "Yeh, W. W.-G. (1985). Reservoir Management and Operations Models: A State-of-the-Art Review. *Water Resources Research*, 21(12), 1797-1818.",
        "Labadie, J. W. (2004). Optimal Operation of Multireservoir Systems: State-of-the-Art Review. *Journal of Water Resources Planning and Management*, 130(2), 93-111.",
        "Lei et al. (2025a). 水系统控制论：基本原理与理论框架. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0077",
    ],
    "flood-forecasting-control": [
        "Beven, K. J., & Kirkby, M. J. (1979). A physically based, variable contributing area model of basin hydrology. *Hydrological Sciences Bulletin*, 24(1), 43-69.",
        "Krzysztofowicz, R. (2001). The case for probabilistic forecasting in hydrology. *Journal of Hydrology*, 249(1-4), 2-9.",
        "Cloke, H. L., & Pappenberger, F. (2009). Ensemble flood forecasting: A review. *Journal of Hydrology*, 375(3-4), 613-626.",
        "Lei et al. (2025a). 水系统控制论：基本原理与理论框架. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0077",
    ],
    "dam-safety-monitoring": [
        "Salazar, F., et al. (2017). Data-Based Models for the Prediction of Dam Behaviour: A Review and Some Methodological Considerations. *Archives of Computational Methods in Engineering*, 24(1), 1-21.",
        "Mata, J. (2011). Interpretation of concrete dam behaviour with artificial neural network and multiple linear regression models. *Engineering Structures*, 33(3), 903-910.",
        "Lei et al. (2025c). 水系统在环测试体系. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0080",
        "Lei et al. (2025a). 水系统控制论：基本原理与理论框架. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0077",
    ],
    "river-sediment-dynamics": [
        "Einstein, H. A. (1950). The bed-load function for sediment transportation in open channel flows. *Technical Bulletin No. 1026*, U.S. Department of Agriculture.",
        "Engelund, F., & Hansen, E. (1967). A monograph on sediment transport in alluvial streams. *Teknisk Forlag*, Copenhagen.",
        "Van Rijn, L. C. (1984). Sediment transport, part I: bed load transport. *Journal of Hydraulic Engineering*, 110(10), 1431-1456.",
        "Lei et al. (2025a). 水系统控制论：基本原理与理论框架. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0077",
    ],
    "inland-waterway-navigation": [
        "Pianc (2014). *Harbour Approach Channels Design Guidelines*. PIANC Report No. 121.",
        "Briggs, M. J., et al. (2013). Ship-induced waves and sediment transport in restricted waterways. *Coastal Engineering*, 82, 42-55.",
        "Lei et al. (2025a). 水系统控制论：基本原理与理论框架. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0077",
    ],
    "ship-lock-automation": [
        "Nauss, K., & Schönknecht, K. (2009). Optimization of lock scheduling. *Journal of Waterway, Port, Coastal, and Ocean Engineering*, 135(5), 205-214.",
        "Smith, L. D., et al. (2009). Scheduling operations at system of locks. *Journal of Waterway, Port, Coastal, and Ocean Engineering*, 135(2), 47-56.",
        "Lei et al. (2025b). 自主水网：概念、架构与关键技术. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0079",
        "Lei et al. (2025a). 水系统控制论：基本原理与理论框架. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0077",
    ],
    "water-energy-food-nexus": [
        "Hoff, H. (2011). Understanding the Nexus. *Background Paper for the Bonn 2011 Conference: The Water, Energy and Food Security Nexus*. Stockholm Environment Institute.",
        "Bazilian, M., et al. (2011). Considering the energy, water and food nexus: Towards an integrated modelling approach. *Energy Policy*, 39(12), 7896-7906.",
        "Albrecht, T. R., et al. (2018). The Water-Energy-Food Nexus: A systematic review of methods for nexus assessment. *Environmental Research Letters*, 13(4), 043002.",
        "Lei et al. (2025a). 水系统控制论：基本原理与理论框架. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0077",
    ],
    "digital-twin-river-basin": [
        "Grieves, M., & Vickers, J. (2017). Digital Twin: Mitigating Unpredictable, Undesirable Emergent Behavior in Complex Systems. In *Transdisciplinary Perspectives on Complex Systems* (pp. 85-113). Springer.",
        "Tao, F., et al. (2019). Digital Twin in Industry: State-of-the-Art. *IEEE Transactions on Industrial Informatics*, 15(4), 2405-2415.",
        "Pedersen, A. N., et al. (2021). Living and Prototyping Digital Twins for Urban Water Systems. *Water*, 13(5), 592.",
        "Lei et al. (2025b). 自主水网：概念、架构与关键技术. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0079",
        "Lei et al. (2025c). 水系统在环测试体系. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0080",
    ],
    "ai-for-water-engineering": [
        "Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning*. MIT Press.",
        "Shen, C. (2018). A Transdisciplinary Review of Deep Learning Research and Its Relevance for Water Resources Scientists. *Water Resources Research*, 54(11), 8558-8593.",
        "Kratzert, F., et al. (2018). Rainfall–runoff modelling using Long Short-Term Memory (LSTM) networks. *Hydrology and Earth System Sciences*, 22(11), 6005-6022.",
        "Lei et al. (2025b). 自主水网：概念、架构与关键技术. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0079",
        "Lei et al. (2025a). 水系统控制论：基本原理与理论框架. *南水北调与水利科技(中英文)*. DOI: 10.13476/j.cnki.nsbdqk.2025.0077",
    ],
}


def find_summary_position(content):
    """查找"本章小结"的位置"""
    patterns = [
        r'\n## 本章小结\n',
        r'\n## 小结\n',
        r'\n## Summary\n',
        r'\n## 本章总结\n',
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            # 找到小结段落的结束位置(下一个##标题之前)
            next_section = re.search(r'\n## ', content[match.end():])
            if next_section:
                return match.end() + next_section.start()
            else:
                # 如果没有下一个章节,返回文件末尾
                return len(content)

    # 如果没找到小结,返回文件末尾
    return len(content)


def add_references_to_chapter(file_path, references):
    """为单个章节添加参考文献"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否已有参考文献
        if '## 参考文献' in content or '## References' in content:
            return False, "已存在参考文献"

        # 查找插入位置
        insert_pos = find_summary_position(content)

        # 构建参考文献段落
        ref_section = "\n\n## 参考文献\n\n"
        for i, ref in enumerate(references, 1):
            ref_section += f"{i}. {ref}\n"

        # 插入参考文献
        new_content = content[:insert_pos] + ref_section + content[insert_pos:]

        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True, f"成功添加{len(references)}篇参考文献"

    except Exception as e:
        return False, f"错误: {str(e)}"


def main():
    """主函数"""
    base_dir = Path(__file__).parent

    report = []
    report.append("# 批量添加参考文献报告\n")
    report.append(f"生成时间: 2026-03-08\n\n")

    total_chapters = 0
    success_count = 0
    skip_count = 0
    error_count = 0

    for book_name, references in REFERENCE_DATABASE.items():
        book_dir = base_dir / book_name

        if not book_dir.exists():
            report.append(f"## {book_name}\n")
            report.append(f"[WARNING] 目录不存在\n\n")
            continue

        report.append(f"## {book_name}\n\n")

        # 查找所有章节文件
        chapter_files = sorted(book_dir.glob("ch*.md"))

        for chapter_file in chapter_files:
            total_chapters += 1
            success, message = add_references_to_chapter(chapter_file, references)

            if success:
                success_count += 1
                report.append(f"[OK] {chapter_file.name}: {message}\n")
            elif "已存在" in message:
                skip_count += 1
                report.append(f"[SKIP] {chapter_file.name}: {message}\n")
            else:
                error_count += 1
                report.append(f"[ERROR] {chapter_file.name}: {message}\n")

        report.append("\n")

    # 添加统计摘要
    summary = f"""
## 统计摘要

- 总章节数: {total_chapters}
- 成功添加: {success_count}
- 已存在跳过: {skip_count}
- 错误: {error_count}
- 成功率: {success_count/total_chapters*100:.1f}%
"""

    report.insert(2, summary)

    # 保存报告
    report_file = base_dir / "参考文献添加报告.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.writelines(report)

    print("".join(report))
    print(f"\n报告已保存到: {report_file}")


if __name__ == "__main__":
    main()
