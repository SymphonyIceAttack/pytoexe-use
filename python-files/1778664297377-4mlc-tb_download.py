import os
import re
import requests

# 配置区
SAVE_DIR = "淘宝商品图片"

def download_taobao_images(goods_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Referer": "https://www.taobao.com/",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    }

    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    try:
        print(f"正在访问商品页面：{goods_url}")
        resp = requests.get(goods_url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"请求失败：{e}")
        input("\n按回车退出...")
        return

    id_match = re.search(r'id=(\d+)', goods_url)
    goods_id = id_match.group(1) if id_match else "unknown"
    goods_dir = os.path.join(SAVE_DIR, f"商品_{goods_id}")
    os.makedirs(goods_dir, exist_ok=True)

    # 🔥 关键修复：支持淘宝+天猫所有图片
    img_pattern = r'https?://[\w\-]+\.(alicdn|taobao)\.com/imgextra/[^"\s]+\.(jpg|jpeg|png|webp)'
    img_list = list(set(re.findall(img_pattern, html)))

    all_imgs = []
    for img in img_list:
        url = img[0]
        if url not in all_imgs:
            all_imgs.append(url)

    if not all_imgs:
        print("未抓取到图片，链接可能加密或无效！")
        input("\n按回车退出...")
        return

    print(f"共找到 {len(all_imgs)} 张图片，开始下载...")
    success = 0

    for idx, img_url in enumerate(all_imgs, 1):
        try:
            img_resp = requests.get(img_url, headers=headers, timeout=10)
            img_resp.raise_for_status()
            ext = img_url.split('.')[-1].split('!')[0].split('&')[0]
            img_path = os.path.join(goods_dir, f"{idx}.{ext}")
            with open(img_path, "wb") as f:
                f.write(img_resp.content)
            print(f"✅ 下载成功：{idx}.{ext}")
            success += 1
        except Exception as e:
            print(f"❌ 下载失败：{img_url}")

    print(f"\n下载完成！成功 {success} 张")
    print(f"保存目录：{os.path.abspath(goods_dir)}")
    input("\n按回车关闭窗口...")

if __name__ == "__main__":
    print("===== 淘宝/天猫商品图片批量下载工具 =====")
    url = input("请粘贴淘宝/天猫商品链接：")
    download_taobao_images(url)