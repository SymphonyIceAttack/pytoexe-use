import numpy as np
import json
from datetime import datetime

def main():
    print("="*60)
    print("    压缩机曲线插值工具 v2.0")
    print("="*60)
    print("功能: 输入两条压缩机特性曲线，进行马赫数间的线性插值")
    print("支持: 曲线点数可以不同")
    print("="*60)
    
    try:
        # 输入参数
        mach1 = float(input("\n请输入第一条曲线的马赫数: "))
        mach2 = float(input("请输入第二条曲线的马赫数: "))
        target_mach = float(input("请输入要插值的马赫数: "))
        
        # 输入曲线1
        print(f"\n--- 输入第一条曲线 (马赫数={mach1}) ---")
        points1 = []
        while True:
            flow = input("流量系数(回车结束): ")
            if not flow:
                if len(points1) < 2:
                    print("至少需要2个点，继续输入")
                    continue
                break
            value = input("对应的能头/效率值: ")
            try:
                points1.append((float(flow), float(value)))
                print(f"已添加: ({flow}, {value})")
            except:
                print("输入无效，请重新输入")
        
        # 输入曲线2
        print(f"\n--- 输入第二条曲线 (马赫数={mach2}) ---")
        points2 = []
        while True:
            flow = input("流量系数(回车结束): ")
            if not flow:
                if len(points2) < 2:
                    print("至少需要2个点，继续输入")
                    continue
                break
            value = input("对应的能头/效率值: ")
            try:
                points2.append((float(flow), float(value)))
                print(f"已添加: ({flow}, {value})")
            except:
                print("输入无效，请重新输入")
        
        # 转换为数组
        flow1 = np.array([p[0] for p in points1])
        val1 = np.array([p[1] for p in points1])
        flow2 = np.array([p[0] for p in points2])
        val2 = np.array([p[1] for p in points2])
        
        # 排序
        idx1 = np.argsort(flow1)
        idx2 = np.argsort(flow2)
        flow1, val1 = flow1[idx1], val1[idx1]
        flow2, val2 = flow2[idx2], val2[idx2]
        
        # 计算插值
        weight = (target_mach - mach1) / (mach2 - mach1)
        min_flow = max(flow1.min(), flow2.min())
        max_flow = min(flow1.max(), flow2.max())
        
        # 生成结果
        n_points = 50
        interp_flow = np.linspace(min_flow, max_flow, n_points)
        v1_interp = np.interp(interp_flow, flow1, val1)
        v2_interp = np.interp(interp_flow, flow2, val2)
        result = v1_interp + weight * (v2_interp - v1_interp)
        
        # 输出结果
        print(f"\n✅ 插值完成!")
        print(f"   目标马赫数: {target_mach}")
        print(f"   插值点数: {n_points}")
        print(f"   流量范围: [{min_flow:.4f}, {max_flow:.4f}]")
        print("\n结果预览:")
        print("-"*40)
        for i in range(min(5, len(interp_flow))):
            print(f"流量={interp_flow[i]:.4f}, 结果={result[i]:.4f}")
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"结果_马赫数{target_mach}_{timestamp}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("压缩机曲线插值结果\n")
            f.write(f"生成时间: {datetime.now()}\n")
            f.write(f"目标马赫数: {target_mach}\n")
            f.write(f"已知曲线1: 马赫数={mach1}, 点数={len(points1)}\n")
            f.write(f"已知曲线2: 马赫数={mach2}, 点数={len(points2)}\n")
            f.write("="*50 + "\n")
            f.write("流量系数\t插值结果\n")
            for f_val, r_val in zip(interp_flow, result):
                f.write(f"{f_val:.6f}\t{r_val:.6f}\n")
        
        print(f"\n📁 结果已保存到: {filename}")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
    
    input("\n按Enter键退出...")

if __name__ == "__main__":
    main()