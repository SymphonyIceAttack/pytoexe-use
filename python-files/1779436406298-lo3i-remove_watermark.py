#!/usr/bin/env python3
"""
PDF 背景水印去除工具
自动识别并删除 PDF 中作为背景的全页图片水印，保留文字和前景图片（如 logo）。
用法：
    python3 remove_watermark.py <输入PDF> [输出PDF]
"""

import sys
import os
import fitz  # PyMuPDF


def is_background_image(img_info: dict, page_rect: fitz.Rect, tolerance: float = 0.80) -> bool:
    """
    判断图片是否为全页背景图。
    规则：图片显示面积占页面面积比例超过 tolerance 即视为背景。
    """
    try:
        bbox = fitz.Rect(img_info.get("bbox", (0, 0, 0, 0)))
        if bbox.is_empty:
            return False
        area_ratio = (bbox.width * bbox.height) / (page_rect.width * page_rect.height)
        return area_ratio >= tolerance
    except Exception:
        return False


def remove_image_from_stream(doc, page, img_name: str) -> bool:
    """
    从页面内容流中删除引用 img_name 的 q...Do...Q 块。
    直接操作 xref 流字节，不做 clean_contents，保持 xref 稳定。
    返回是否成功修改。
    """
    img_do_marker = f"/{img_name} Do".encode("utf-8")
    xrefs = page.get_contents()
    modified = False

    for xref in xrefs:
        try:
            stream_bytes = doc.xref_stream(xref)
        except Exception:
            continue

        if img_do_marker not in stream_bytes:
            continue

        # 按行解析，找到包含 img_name Do 的 q...Q 块并删除
        lines = stream_bytes.split(b"\n")
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if stripped == b"q":
                # 查看从当前行到匹配 Q 之间是否包含目标 Do 指令
                block_lines = []
                depth = 0
                found_do = False
                j = i
                while j < len(lines):
                    bl = lines[j].strip()
                    block_lines.append(lines[j])
                    if bl == b"q":
                        depth += 1
                    elif bl == b"Q":
                        depth -= 1
                        if depth == 0:
                            # 检查这个块是否包含目标 Do
                            for bl2 in block_lines:
                                if img_do_marker in bl2:
                                    found_do = True
                                    break
                            break
                    j += 1

                if found_do:
                    # 跳过整个块（i 跳到 j+1）
                    i = j + 1
                    modified = True
                    continue

            new_lines.append(line)
            i += 1

        if modified:
            new_stream = b"\n".join(new_lines)
            # 清理可能残留的空 q\nQ\n
            new_stream = new_stream.replace(b"q\nQ\n", b"")
            new_stream = new_stream.replace(b"q\r\nQ\r\n", b"")
            doc.update_stream(xref, new_stream)
            break  # 通常只需要修改第一个内容流

    return modified


def remove_watermark(input_path: str, output_path: str = None) -> str:
    """
    主函数：去除 PDF 背景水印。
    返回输出文件路径。
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_no_watermark{ext}"

    doc = fitz.open(input_path)
    total_pages = len(doc)
    removed_count = 0

    print(f"正在处理：{input_path}")
    print(f"总页数：{total_pages}")

    # 先建立 xref -> 图片名 的映射（通过 get_images）
    # get_images(full=True) 返回列表，每项 10 个字段：
    # (xref, smask, w, h, bpc, colorspace, _, name, filter, ...)
    # name 在第 7 位（index=7）
    xref_to_name = {}
    for page_num in range(total_pages):
        imgs = doc[page_num].get_images(full=True)
        for img_tuple in imgs:
            xref = img_tuple[0]
            name = img_tuple[7] if len(img_tuple) > 7 and isinstance(img_tuple[7], str) else f"img{xref}"
            xref_to_name[xref] = name

    for page_num, page in enumerate(doc, start=1):
        page_rect = page.rect
        img_info_list = page.get_image_info(xrefs=True)

        if not img_info_list:
            continue

        # 找出所有背景图
        bg_xrefs = []
        for info in img_info_list:
            if is_background_image(info, page_rect):
                xref = info.get("xref")
                if xref:
                    bg_xrefs.append(xref)

        if not bg_xrefs:
            continue

        print(f"  第 {page_num} 页：发现 {len(bg_xrefs)} 张背景图，正在移除...")
        for xref in set(bg_xrefs):
            img_name = xref_to_name.get(xref)
            if not img_name:
                # 从 get_images 直接查找（name 在 index=7）
                imgs = page.get_images(full=True)
                for img_tuple in imgs:
                    if img_tuple[0] == xref:
                        if len(img_tuple) > 7 and isinstance(img_tuple[7], str):
                            img_name = img_tuple[7]
                        break

            if not img_name:
                print(f"    ✗ 无法找到 xref={xref} 的图片名，跳过")
                continue

            success = remove_image_from_stream(doc, page, img_name)
            if success:
                removed_count += 1
                print(f"    ✓ 已移除图片 '{img_name}' (xref={xref})")
            else:
                print(f"    ✗ 未能在内容流中找到 '{img_name} Do' 指令")

    # 保存（garbage=1 回收未引用对象，deflate=True 压缩）
    doc.save(output_path, garbage=1, deflate=True)
    doc.close()

    print(f"\n完成！")
    print(f"  移除背景图数量：{removed_count}")
    print(f"  输出文件：{output_path}")
    return output_path


def main():
    if len(sys.argv) < 2:
        print("用法：python3 remove_watermark.py <输入PDF> [输出PDF]")
        print()
        print("示例：")
        print("  python3 remove_watermark.py ~/Downloads/我的文件.pdf")
        print("  python3 remove_watermark.py ~/Downloads/我的文件.pdf ~/Downloads/输出.pdf")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = remove_watermark(input_path, output_path)
        print(f"\n✅ 处理完成，文件保存在：{result}")
    except Exception as e:
        print(f"\n❌ 处理失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
