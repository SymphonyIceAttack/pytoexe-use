import hashlib
import sys

def compute_key(sn: str) -> str:
    return hashlib.md5(sn.encode()).hexdigest()

def main():
    print("=== SN -> KEY 注册机 (MD5) ===\n")
    if len(sys.argv) > 1:
        sn = sys.argv[1]
        key = compute_key(sn)
        print(f"SN: {sn}\nKEY: {key}")
    else:
        while True:
            sn = input("请输入 SN (直接回车退出): ").strip()
            if not sn:
                break
            key = compute_key(sn)
            print(f"KEY: {key}\n")

if __name__ == "__main__":
    main()