#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 配图批量生成主控脚本
生成全部189张图片（63章 × 3张/章）
"""

import os
import sys
import subprocess
import time

base_dir = 'D:/cowork/教材/chs-books-v2/books'

def print_banner(text):
    """打印分隔横幅"""
    print('\n' + '=' * 80)
    print(f'  {text}')
    print('=' * 80 + '\n')

def check_environment():
    """检查环境配置"""
    print('检查环境配置...')

    # 检查Python
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        print(f'  ✓ Python: {result.stdout.strip()}')
    except:
        print('  ✗ Python未安装或不在PATH中')
        return False

    # 检查必要的Python包
    required_packages = ['numpy', 'matplotlib', 'scipy']
    for pkg in required_packages:
        try:
            __import__(pkg)
            print(f'  ✓ {pkg}已安装')
        except ImportError:
            print(f'  ✗ {pkg}未安装，请运行: pip install {pkg}')
            return False

    # 检查nano脚本
    nano_script = 'D:/cowork/openclaw-sync/skills/nano-banana-pro/scripts/generate_image.py'
    if os.path.exists(nano_script):
        print(f'  ✓ nano-banana-pro脚本存在')
    else:
        print(f'  ✗ nano脚本不存在: {nano_script}')
        return False

    # 检查GEMINI_API_KEY
    if os.getenv('GEMINI_API_KEY'):
        print(f'  ✓ GEMINI_API_KEY已设置')
    else:
        print(f'  ⚠ GEMINI_API_KEY未设置，nano生成将失败')
        print(f'    请设置环境变量: set GEMINI_API_KEY=your_api_key')

    return True

def generate_simulation_figures():
    """生成数据曲线图（63张）"""
    print_banner('阶段1: 生成数据曲线图（Python matplotlib）')

    script = os.path.join(base_dir, 'batch_generate_simulation_figures.py')
    if not os.path.exists(script):
        print(f'错误: 脚本不存在: {script}')
        return False

    try:
        result = subprocess.run(
            ['python', script],
            cwd=base_dir,
            encoding='utf-8',
            errors='ignore'
        )
        return result.returncode == 0
    except Exception as e:
        print(f'错误: {e}')
        return False

def generate_nano_figures():
    """生成架构图和概念图（126张）"""
    print_banner('阶段2: 生成架构图和概念图（nano-banana-pro）')

    script = os.path.join(base_dir, 'batch_generate_nano_figures.py')
    if not os.path.exists(script):
        print(f'错误: 脚本不存在: {script}')
        return False

    # 检查API key
    if not os.getenv('GEMINI_API_KEY'):
        print('警告: GEMINI_API_KEY未设置')
        response = input('是否继续？(y/n): ')
        if response.lower() != 'y':
            return False

    try:
        result = subprocess.run(
            ['python', script],
            cwd=base_dir,
            encoding='utf-8',
            errors='ignore'
        )
        return result.returncode == 0
    except Exception as e:
        print(f'错误: {e}')
        return False

def update_chapter_files():
    """更新章节文件，插入图片引用"""
    print_banner('阶段3: 更新章节文件（插入图片引用）')

    # TODO: 实现自动插入图片引用的逻辑
    print('提示: 图片引用需要手动插入或使用专门脚本')
    print('格式:')
    print('  ![图X-Y 标题](figures/chXX_xxx.png)')
    print('  **图X-Y 标题**')
    print('  *图注说明文字*')

    return True

def generate_summary():
    """生成统计报告"""
    print_banner('生成统计报告')

    books = [
        'reservoir-operation-optimization',
        'flood-forecasting-control',
        'dam-safety-monitoring',
        'river-sediment-dynamics',
        'inland-waterway-navigation',
        'ship-lock-automation',
        'water-energy-food-nexus',
        'digital-twin-river-basin',
        'ai-for-water-engineering',
    ]

    total_simulation = 0
    total_architecture = 0
    total_concept = 0

    print('各书图片统计:')
    print('-' * 80)
    print(f'{"书名":<40} {"仿真图":<10} {"架构图":<10} {"概念图":<10} {"合计":<10}')
    print('-' * 80)

    for book in books:
        figures_dir = os.path.join(base_dir, book, 'figures')
        if not os.path.exists(figures_dir):
            continue

        sim_count = len([f for f in os.listdir(figures_dir) if f.endswith('_simulation_result.png')])
        arch_count = len([f for f in os.listdir(figures_dir) if f.endswith('_architecture.png')])
        concept_count = len([f for f in os.listdir(figures_dir) if f.endswith('_concept.png')])

        total_simulation += sim_count
        total_architecture += arch_count
        total_concept += concept_count

        print(f'{book:<40} {sim_count:<10} {arch_count:<10} {concept_count:<10} {sim_count+arch_count+concept_count:<10}')

    print('-' * 80)
    print(f'{"总计":<40} {total_simulation:<10} {total_architecture:<10} {total_concept:<10} {total_simulation+total_architecture+total_concept:<10}')
    print('-' * 80)

def main():
    """主流程"""
    print_banner('Phase 4 配图批量生成')

    print('配图方案:')
    print('  - 数据曲线图: 63张（Python matplotlib自动生成）')
    print('  - 架构图: 63张（nano-banana-pro生成）')
    print('  - 概念图: 63张（nano-banana-pro生成）')
    print('  - 总计: 189张')

    # 检查环境
    if not check_environment():
        print('\n环境检查失败，请修复后重试')
        return 1

    # 询问用户
    print('\n准备开始批量生成...')
    response = input('是否继续？(y/n): ')
    if response.lower() != 'y':
        print('已取消')
        return 0

    start_time = time.time()

    # 阶段1: 生成数据曲线图
    if not generate_simulation_figures():
        print('阶段1失败')
        return 1

    # 阶段2: 生成架构图和概念图
    if not generate_nano_figures():
        print('阶段2失败')
        return 1

    # 阶段3: 更新章节文件
    update_chapter_files()

    # 生成统计报告
    generate_summary()

    elapsed = time.time() - start_time
    print(f'\n总耗时: {elapsed/60:.1f}分钟')

    print_banner('批量生成完成')

    return 0

if __name__ == '__main__':
    sys.exit(main())
