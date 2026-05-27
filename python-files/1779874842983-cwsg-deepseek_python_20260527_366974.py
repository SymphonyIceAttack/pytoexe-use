import re
import os
from pypdf import PdfReader, PdfWriter

def clean_filename(s: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', s)

def flatten_bookmarks(bookmark_list, prefix=""):
    items = []
    for bm in bookmark_list:
        if hasattr(bm, "page_number"):
            title = f"{prefix}{bm.title}" if prefix else bm.title
            items.append((title, bm.page_number))
        if hasattr(bm, "children") and bm.children:
            new_prefix = f"{prefix}{bm.title} / " if prefix else f"{bm.title} / "
            items.extend(flatten_bookmarks(bm.children, new_prefix))
    return items

def build_page_to_bookmark_map(reader):
    bookmarks = flatten_bookmarks(reader.outline)
    if not bookmarks:
        return {}
    bookmarks.sort(key=lambda x: x[1])
    total_pages = len(reader.pages)
    page_map = {}
    bm_idx = 0
    for page in range(total_pages):
        while bm_idx + 1 < len(bookmarks) and page >= bookmarks[bm_idx + 1][1]:
            bm_idx += 1
        if page >= bookmarks[bm_idx][1]:
            page_map[page] = bookmarks[bm_idx][0]
        else:
            page_map[page] = None
    return page_map

def main():
    print("=" * 50)
    pdf_path = input("请拖入或输入 PDF 文件路径: ").strip().strip('"')
    if not os.path.isfile(pdf_path):
        print("文件不存在，请重新运行。")
        input("按 Enter 退出...")
        return
    output_dir = input("输出文件夹名（留空则为 'output_pages'）: ").strip()
    if not output_dir:
        output_dir = "output_pages"

    try:
        reader = PdfReader(pdf_path)
        page_map = build_page_to_bookmark_map(reader)
        if not page_map:
            print("警告：PDF 中没有书签，将仍按页码拆分，但无书签名。")
        os.makedirs(output_dir, exist_ok=True)
        total_pages = len(reader.pages)
        pad_width = len(str(total_pages))

        for page_num in range(total_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])
            bookmark = page_map.get(page_num)
            name_part = "Unnamed" if bookmark is None else clean_filename(bookmark)
            filename = f"{str(page_num+1).zfill(pad_width)}_{name_part}.pdf"
            out_path = os.path.join(output_dir, filename)
            with open(out_path, "wb") as f:
                writer.write(f)
            print(f"已生成: {out_path}")
        print(f"\n完成！共生成 {total_pages} 个文件，保存在文件夹：{output_dir}")
    except Exception as e:
        print(f"出错：{e}")
    input("\n按 Enter 退出...")

if __name__ == "__main__":
    main()