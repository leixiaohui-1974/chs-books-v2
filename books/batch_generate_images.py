# coding: utf-8
# 批量图片生成脚本：合并 corrupted 和 missing 清单，自动调用 API 或生成占位图

from __future__ import annotations

import argparse, base64, json, logging, os, textwrap, time
from datetime import datetime
from pathlib import Path

BOOKS_DIR = Path("Z:/research/chs-books-v2/books")
CORRUPTED_MANIFEST = BOOKS_DIR / "corrupted_images_manifest.json"
MISSING_MANIFEST = BOOKS_DIR / "missing_images_manifest.json"
LOG_FILE = BOOKS_DIR / "batch_gen_log.txt"
PLACEHOLDER_SIZE = (1024, 768)
WRAP_WIDTH = 40
SLEEP_BETWEEN = 3  # 秒


def setup_logging() -> logging.Logger:
    # 配置同时输出到控制台和日志文件的 logger
    logger = logging.getLogger("batch_gen")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8", mode="a")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


logger = setup_logging()


def load_tasks() -> list[dict]:
    # 读取并合并两个清单，返回统一格式的任务列表。
    tasks: list[dict] = []
    with open(CORRUPTED_MANIFEST, encoding="utf-8") as f:
        corrupted = json.load(f)
    for rec in corrupted:
        tasks.append({
            "output_path": Path(rec["path"]),
            "prompt": rec["prompt"],
            "source": "corrupted",
        })
    logger.info(f"加载 corrupted 清单：{len(corrupted)} 条")
    with open(MISSING_MANIFEST, encoding="utf-8") as f:
        missing = json.load(f)
    for rec in missing:
        tasks.append({
            "output_path": BOOKS_DIR / rec["target_path"],
            "prompt": rec["prompt"],
            "source": "missing",
        })
    logger.info(f"加载 missing 清单：{len(missing)} 条")
    logger.info(f"合并后总任务数：{len(tasks)}")
    return tasks


def should_skip(path: Path) -> bool:
    # 已存在且大于 1 KB 则跳过。
    return path.exists() and path.stat().st_size > 1024


def generate_openai(prompt: str, output_path: Path) -> bool:
    # 通过 OpenAI 兼容接口生成图片，成功返回 True。
    try:
        import httpx
    except ImportError:
        logger.warning("httpx 未安装，跳过 OpenAI 方式")
        return False
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = "https://api.openai.com/v1"
    if not api_key:
        api_key = os.environ.get("AICODE_API_KEY", "")
        base_url = "https://aicode.cat/v1"
    if not api_key:
        logger.debug("未找到 OPENAI_API_KEY / AICODE_API_KEY，跳过 OpenAI 方式")
        return False
    payload = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": "1536x1024",
        "quality": "medium",
        "response_format": "b64_json",
    }
    try:
        resp = httpx.post(
            f"{base_url}/images/generations",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        b64 = data["data"][0]["b64_json"]
        img_bytes = base64.b64decode(b64)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(img_bytes)
        return True
    except httpx.HTTPStatusError as e:
        logger.warning(f"OpenAI API HTTP 错误：{e.response.status_code}")
    except httpx.RequestError as e:
        logger.warning(f"OpenAI API 网络错误：{e}")
    except (KeyError, ValueError) as e:
        logger.warning(f"OpenAI API 响应解析失败：{e}")
    return False


def generate_gemini(prompt: str, output_path: Path) -> bool:
    # 通过 Gemini API 生成图片，成功返回 True。
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.debug("未找到 GEMINI_API_KEY，跳过 Gemini 方式")
        return False
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.warning("google-genai 未安装，跳过 Gemini 方式")
        return False
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1))
        if response.generated_images:
            img_bytes = response.generated_images[0].image.image_bytes
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(img_bytes)
            return True
        logger.warning("Gemini 未返回图片数据")
    except Exception as e:
        logger.warning(f"Gemini API 错误：{e}")
    return False


def _get_font(size: int):
    # 尝试加载系统中文字体，失败时返回默认字体。
    from PIL import ImageFont
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def generate_placeholder(prompt: str, output_path: Path) -> bool:
    # 生成 PIL 占位图，成功返回 True。
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        logger.error("Pillow 未安装，请 pip install Pillow")
        return False
    w, h = PLACEHOLDER_SIZE
    img = Image.new("RGB", (w, h), color=(200, 200, 200))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "[PLACEHOLDER]", fill=(180, 0, 0), font=_get_font(20))
    body_font = _get_font(16)
    lines = textwrap.wrap(prompt, width=WRAP_WIDTH)
    total_h = len(lines) * 22
    y = (h - total_h) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=body_font)
        x = (w - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, fill=(50, 50, 50), font=body_font)
        y += 22
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return True


def detect_method() -> str:
    # 自动检测可用方式，返回 openai / gemini / placeholder。
    if os.environ.get("OPENAI_API_KEY") or os.environ.get("AICODE_API_KEY"):
        return "openai"
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    return "placeholder"


def generate_image(prompt: str, output_path: Path, method: str) -> bool:
    # 按指定方式生成图片，OpenAI/Gemini 失败时自动降级到占位图。
    if method == "openai":
        if generate_openai(prompt, output_path):
            return True
        logger.info("OpenAI 失败，降级到 Gemini")
        if generate_gemini(prompt, output_path):
            return True
        logger.info("Gemini 失败，降级到占位图")
        return generate_placeholder(prompt, output_path)
    elif method == "gemini":
        if generate_gemini(prompt, output_path):
            return True
        logger.info("Gemini 失败，降级到占位图")
        return generate_placeholder(prompt, output_path)
    return generate_placeholder(prompt, output_path)


def run(
    dry_run: bool = False,
    start: int = 0,
    limit: int | None = None,
    method: str = "auto",
) -> None:
    # 主流程：加载清单、过滤、生成图片。
    tasks = load_tasks()
    end = (start + limit) if limit is not None else len(tasks)
    subset = tasks[start:end]
    if method == "auto":
        method = detect_method()
    logger.info(f"使用方式：{method}")
    total = len(subset)
    success_count = skip_count = fail_count = 0
    logger.info(f"本次处理范围：{start} ~ {start + total - 1}，共 {total} 条")
    logger.info("-" * 60)
    for idx, task in enumerate(subset, start=start):
        output_path: Path = task["output_path"]
        prompt: str = task["prompt"]
        try:
            short_path = output_path.relative_to(BOOKS_DIR)
        except ValueError:
            short_path = output_path
        prefix = f"[{idx + 1:3d}/{start + total}]"
        if should_skip(output_path):
            skip_count += 1
            logger.info(f"{prefix} SKIP   {short_path}  (已存在)")
            continue
        if dry_run:
            logger.info(f"{prefix} DRY    {task['source']:9s}  {short_path}")
            continue
        t0 = time.monotonic()
        try:
            ok = generate_image(prompt, output_path, method)
        except Exception as e:
            logger.error(f"{prefix} ERROR  {short_path}  未预期异常：{e}")
            ok = False
        elapsed = time.monotonic() - t0
        if ok:
            success_count += 1
            logger.info(f"{prefix} OK     {short_path}  ({elapsed:.1f}s)")
        else:
            fail_count += 1
            logger.error(f"{prefix} FAIL   {short_path}  ({elapsed:.1f}s)")
        if idx < start + total - 1:
            time.sleep(SLEEP_BETWEEN)
    logger.info("=" * 60)
    if dry_run:
        logger.info(f"DRY-RUN 完成：共 {total} 条待处理（start={start}）")
    else:
        logger.info(f"完成：总计={total}  成功={success_count}  失败={fail_count}  跳过={skip_count}")
    logger.info(f"日志文件：{LOG_FILE}")


def parse_args() -> argparse.Namespace:
    # 解析命令行参数。
    parser = argparse.ArgumentParser(description="批量图片生成脚本")
    parser.add_argument("--dry-run", action="store_true", help="仅列出待生成图片，不实际生成")
    parser.add_argument("--start", type=int, default=0, metavar="N", help="从第 N 条记录开始（0-indexed）")
    parser.add_argument("--limit", type=int, default=None, metavar="N", help="最多处理 N 条记录")
    parser.add_argument(
        "--method",
        choices=["auto", "openai", "gemini", "placeholder"],
        default="auto",
        help="强制指定生成方式（默认 auto 自动检测）",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logger.info(
        "========== 批量图片生成开始 "
        + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        + " =========="
    )
    logger.info(f"参数：dry_run={args.dry_run}, start={args.start}, limit={args.limit}, method={args.method}")
    run(dry_run=args.dry_run, start=args.start, limit=args.limit, method=args.method)