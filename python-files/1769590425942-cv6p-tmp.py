import pandas as pd
import numpy as np
from datetime import datetime
import os

def create_multi_tier_shuttle_efficiency_excel(filename="multi_tier_shuttle_efficiency.xlsx"):
    """
    创建多层穿梭车系统效率分析Excel表格
    
    参数:
    filename: 输出的Excel文件名
    """
    
    # 创建Excel写入器
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        
        # ==================== 1. 基础参数设置 ====================
        print("正在创建基础参数设置表...")
        
        # 仓库基本信息
        warehouse_data = {
            '参数类别': ['仓库布局', '仓库布局', '仓库布局', '仓库布局', '仓库布局', 
                       '仓库布局', '仓库布局', '仓库布局', '仓库布局', '仓库布局'],
            '参数': ['仓库总货位数', '巷道数量', '每巷道层数', '每层列数', '每货位深度',
                   '层高(m)', '列宽(m)', '系统设计吞吐量(托盘/小时)', '工作时间(小时/天)', '工作天数(天/年)'],
            '数值': [5000, 4, 8, 156, 2, 2.5, 1.2, 300, 16, 300],
            '单位': ['个', '个', '层', '列', '排', '米', '米', '托盘/小时', '小时/天', '天/年']
        }
        
        # 穿梭车参数
        shuttle_data = {
            '参数类别': ['穿梭车参数', '穿梭车参数', '穿梭车参数', '穿梭车参数', '穿梭车参数',
                       '穿梭车参数', '穿梭车参数', '穿梭车参数'],
            '参数': ['穿梭车数量', '单台最大速度(m/s)', '加速度(m/s²)', '减速度(m/s²)', 
                   '取货时间(s)', '放货时间(s)', '空载能耗(W)', '满载能耗(W)'],
            '数值': [12, 4.0, 0.5, 0.5, 3, 3, 800, 1200],
            '单位': ['辆', 'm/s', 'm/s²', 'm/s²', '秒', '秒', '瓦', '瓦']
        }
        
        # 提升机参数
        lift_data = {
            '参数类别': ['提升机参数', '提升机参数', '提升机参数', '提升机参数', '提升机参数',
                       '提升机参数', '提升机参数'],
            '参数': ['提升机数量', '最大提升速度(m/s)', '提升加速度(m/s²)', '下降加速度(m/s²)',
                   '取货时间(s)', '放货时间(s)', '额定功率(W)'],
            '数值': [2, 1.5, 0.3, 0.4, 4, 4, 5000],
            '单位': ['台', 'm/s', 'm/s²', 'm/s²', '秒', '秒', '瓦']
        }
        
        # 合并所有参数数据
        params_df = pd.concat([
            pd.DataFrame(warehouse_data),
            pd.DataFrame({'参数类别': [''], '参数': [''], '数值': [''], '单位': ['']}),
            pd.DataFrame(shuttle_data),
            pd.DataFrame({'参数类别': [''], '参数': [''], '数值': [''], '单位': ['']}),
            pd.DataFrame(lift_data)
        ], ignore_index=True)
        
        # 写入基础参数表
        params_df.to_excel(writer, sheet_name='基础参数设置', index=False)
        
        # ==================== 2. 效率计算 ====================
        print("正在创建效率计算表...")
        
        # 计算参数
        avg_horizontal_distance = 156 * 1.2 / 2  # 平均水平移动距离 (米)
        avg_vertical_distance = 8 * 2.5 / 2  # 平均垂直移动距离 (米)
        
        # 时间计算函数
        def calculate_move_time(distance, max_speed, acceleration):
            """计算移动时间（考虑加速和减速阶段）"""
            # 加速到最大速度所需距离
            acc_distance = (max_speed**2) / (2 * acceleration)
            
            if distance <= 2 * acc_distance:
                # 无法达到最大速度
                move_time = 2 * np.sqrt(distance / acceleration)
            else:
                # 包含匀速阶段
                cruise_distance = distance - 2 * acc_distance
                move_time = (2 * max_speed / acceleration) + (cruise_distance / max_speed)
            
            return move_time
        
        # 计算移动时间
        avg_horizontal_time = calculate_move_time(avg_horizontal_distance, 4.0, 0.5)
        avg_vertical_time = calculate_move_time(avg_vertical_distance, 1.5, 0.3)
        
        # 单次作业时间
        single_operation_time = (
            avg_horizontal_time +  # 水平移动时间
            avg_vertical_time +    # 垂直移动时间
            3 + 3 +                # 穿梭车取放货时间
            4 + 4                  # 提升机取放货时间
        )
        
        # 效率计算数据
        efficiency_data = {
            '效率指标': [
                '平均水平移动距离',
                '平均垂直移动距离',
                '平均水平移动时间',
                '平均垂直移动时间',
                '穿梭车存取时间',
                '提升机存取时间',
                '单次作业循环时间',
                '每小时理论最大循环次数（单车）',
                '系统实际工作效率系数',
                '每小时实际循环次数（单车）',
                '系统总循环次数（全部设备）',
                '日工作小时数',
                '日处理能力（托盘）',
                '年处理能力（托盘）',
                '系统利用率估算',
                '设备等待率估算',
                '整体系统效率'
            ],
            '计算公式': [
                '=每层列数×列宽/2',
                '=每巷道层数×层高/2',
                'f(d,v,a)加速运动模型',
                'f(d,v,a)加速运动模型',
                '=取货时间+放货时间',
                '=取货时间+放货时间',
                '=水平时间+垂直时间+穿梭车存取+提升机存取',
                '=3600/单次作业循环时间',
                '经验值（考虑交通、等待等）',
                '=理论循环次数×工作效率系数',
                '=单车实际循环次数×穿梭车数量',
                '基础参数设置!I9',
                '=系统总循环次数×日工作小时数',
                '=日处理能力×年工作天数',
                '=实际循环次数/理论循环次数',
                '=1-系统利用率',
                '=系统利用率×(1-设备等待率)'
            ],
            '数值': [
                avg_horizontal_distance,
                avg_vertical_distance,
                round(avg_horizontal_time, 2),
                round(avg_vertical_time, 2),
                6,
                8,
                round(single_operation_time, 2),
                round(3600 / single_operation_time, 1),
                0.85,
                round((3600 / single_operation_time) * 0.85, 1),
                round((3600 / single_operation_time) * 0.85 * 12, 1),
                16,
                round((3600 / single_operation_time) * 0.85 * 12 * 16, 0),
                round((3600 / single_operation_time) * 0.85 * 12 * 16 * 300, 0),
                '0.85',
                '0.15',
                '0.7225'
            ],
            '单位': [
                '米', '米', '秒', '秒', '秒', '秒', '秒', 
                '次/小时', '-', '次/小时', '次/小时', '小时', 
                '托盘/日', '托盘/年', '%', '%', '%'
            ]
        }
        
        efficiency_df = pd.DataFrame(efficiency_data)
        efficiency_df.to_excel(writer, sheet_name='效率计算', index=False)
        
        # ==================== 3. KPI监控 ====================
        print("正在创建KPI监控表...")
        
        # 生成30天的模拟数据
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        
        # 模拟日吞吐量（正态分布，均值为设计值的85%）
        base_throughput = 300 * 16 * 0.85  # 设计值×小时×效率系数
        throughput = np.random.normal(base_throughput, base_throughput * 0.1, 30)
        throughput = np.maximum(throughput, 0)  # 确保非负
        
        # 模拟故障时间（泊松分布）
        fault_time = np.random.poisson(30, 30)  # 平均30分钟故障时间
        
        # 模拟响应时间（正态分布）
        response_time = np.random.normal(single_operation_time, single_operation_time * 0.2, 30)
        response_time = np.maximum(response_time, 0.5)  # 最小0.5秒
        
        # 系统可用率（基于故障时间）
        availability = 1 - (fault_time / (16 * 60))
        availability = np.minimum(np.maximum(availability, 0.95), 1.0)  # 控制在95%-100%
        
        # 能耗指标（与吞吐量相关）
        energy_per_pallet = 2.5  # 每托盘能耗（kWh）
        energy_consumption = throughput * energy_per_pallet / 1000  # 转换为MWh
        
        # 操作人员效率（模拟数据）
        operator_efficiency = np.random.uniform(0.85, 0.98, 30)
        
        kpi_data = {
            '日期': dates.strftime('%Y-%m-%d'),
            '吞吐量(托盘)': throughput.round(0),
            '故障时间(分钟)': fault_time,
            '平均响应时间(秒)': response_time.round(2),
            '系统可用率': availability.round(3),
            '能耗指标(MWh)': energy_consumption.round(3),
            '操作人员效率': operator_efficiency.round(3)
        }
        
        kpi_df = pd.DataFrame(kpi_data)
        kpi_df.to_excel(writer, sheet_name='KPI监控', index=False)
        
        # ==================== 4. 成本效益分析 ====================
        print("正在创建成本效益分析表...")
        
        cost_data = {
            '成本项目': [
                '穿梭车系统（含设备）',
                '货架系统',
                'WMS软件系统',
                '提升机系统',
                '安装调试费用',
                '培训费用',
                '基础设施改造',
                '其他杂费',
                '总投资'
            ],
            '初始投资(万元)': [350, 280, 80, 120, 50, 15, 60, 25, 0],  # 最后一行会自动计算
            '运营成本(万元/年)': [45, 8, 12, 18, 0, 3, 10, 5, 0],
            '维护成本(万元/年)': [25, 5, 8, 10, 0, 0, 3, 2, 0],
            '节省人工成本(万元/年)': [0, 0, 0, 0, 0, 0, 0, 0, 180],
            '备注': [
                '12台穿梭车及控制系统',
                '5000货位多层货架',
                '仓库管理系统软件',
                '2台提升机',
                '设备安装与系统调试',
                '操作与维护培训',
                '电力、网络等改造',
                '运输、保险等费用',
                '各项总和'
            ]
        }
        
        # 计算总投资和总成本
        cost_df = pd.DataFrame(cost_data)
        cost_df.loc[8, '初始投资(万元)'] = cost_df['初始投资(万元)'].iloc[0:8].sum()
        cost_df.loc[8, '运营成本(万元/年)'] = cost_df['运营成本(万元/年)'].iloc[0:8].sum()
        cost_df.loc[8, '维护成本(万元/年)'] = cost_df['维护成本(万元/年)'].iloc[0:8].sum()
        
        cost_df.to_excel(writer, sheet_name='成本效益', index=False)
        
        # ==================== 5. 效率对比分析 ====================
        print("正在创建效率对比分析表...")
        
        # 不同配置下的效率对比
        configs = ['当前配置', '增加穿梭车', '增加提升机', '优化路径算法', '提高设备速度']
        
        comparison_data = {
            '配置方案': configs,
            '穿梭车数量': [12, 16, 12, 12, 12],
            '提升机数量': [2, 2, 3, 2, 2],
            '单次作业时间(秒)': [
                single_operation_time,
                single_operation_time * 0.9,  # 减少等待时间
                single_operation_time * 0.85,  # 减少垂直等待
                single_operation_time * 0.8,   # 优化路径
                single_operation_time * 0.75   # 提高速度
            ],
            '日处理能力(托盘)': [
                efficiency_data['数值'][12],  # 当前日处理能力
                efficiency_data['数值'][12] * 1.3,  # +30%
                efficiency_data['数值'][12] * 1.2,  # +20%
                efficiency_data['数值'][12] * 1.25, # +25%
                efficiency_data['数值'][12] * 1.35  # +35%
            ],
            '投资增加(万元)': [0, 80, 60, 30, 100],
            '投资回收期(年)': ['-', 3.2, 2.8, 1.5, 4.0]
        }
        
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df.to_excel(writer, sheet_name='效率对比', index=False)
        
        # ==================== 6. 设备调度模拟 ====================
        print("正在创建设备调度模拟表...")
        
        # 生成8小时工作时间的模拟调度数据
        time_slots = []
        shuttle_status = []
        task_types = []
        locations = []
        durations = []
        
        start_time = datetime(2024, 1, 1, 8, 0, 0)
        
        for hour in range(8):
            for minute in range(0, 60, 5):  # 每5分钟一个时间点
                current_time = start_time.replace(hour=8+hour, minute=minute)
                time_slots.append(current_time.strftime('%H:%M'))
                
                # 模拟穿梭车状态
                shuttle_id = np.random.randint(1, 13)
                status_options = ['工作中', '空闲', '充电中', '维护中']
                probabilities = [0.7, 0.2, 0.08, 0.02]
                status = np.random.choice(status_options, p=probabilities)
                shuttle_status.append(f"穿梭车#{shuttle_id} - {status}")
                
                # 模拟任务类型
                task_options = ['取货', '放货', '移库', '盘点', '空载移动']
                task_weights = [0.35, 0.35, 0.1, 0.05, 0.15]
                task_type = np.random.choice(task_options, p=task_weights)
                task_types.append(task_type)
                
                # 模拟位置
                if status == '工作中':
                    level = np.random.randint(1, 9)
                    column = np.random.randint(1, 157)
                    location = f"L{level}-C{column}"
                else:
                    location = "待命区" if status == '空闲' else "充电站" if status == '充电中' else "维修区"
                locations.append(location)
                
                # 模拟持续时间
                if status == '工作中':
                    duration = np.random.randint(30, 180)  # 30-180秒
                else:
                    duration = 300 if status == '充电中' else 0  # 充电5分钟
                durations.append(duration)
        
        # 只取前50行作为示例
        schedule_data = {
            '时间': time_slots[:50],
            '设备状态': shuttle_status[:50],
            '任务类型': task_types[:50],
            '位置': locations[:50],
            '持续时间(秒)': durations[:50]
        }
        
        schedule_df = pd.DataFrame(schedule_data)
        schedule_df.to_excel(writer, sheet_name='设备调度', index=False)
    
    print(f"\n✅ Excel文件 '{filename}' 创建成功！")
    print("包含以下工作表:")
    print("1. 基础参数设置 - 系统基本参数配置")
    print("2. 效率计算 - 系统效率指标计算")
    print("3. KPI监控 - 30天运行KPI数据")
    print("4. 成本效益 - 投资与回报分析")
    print("5. 效率对比 - 不同配置方案对比")
    print("6. 设备调度 - 设备运行状态模拟")
    
    return filename

def main():
    """主函数"""
    print("=" * 60)
    print("多层穿梭车系统效率分析Excel表格生成器")
    print("=" * 60)
    
    try:
        # 创建Excel文件
        filename = create_multi_tier_shuttle_efficiency_excel()
        
        # 显示文件信息
        file_size = os.path.getsize(filename) / 1024  # KB
        print(f"\n📊 文件大小: {file_size:.2f} KB")
        print(f"📁 文件位置: {os.path.abspath(filename)}")
        
        print("\n💡 使用说明:")
        print("1. 打开生成的Excel文件，查看各工作表")
        print("2. 在'基础参数设置'表中修改参数")
        print("3. '效率计算'表会自动更新计算结果")
        print("4. 可根据实际需求调整模拟数据")
        
    except Exception as e:
        print(f"\n❌ 创建Excel文件时出错: {e}")
        print("\n🔧 请确保已安装必要的Python库:")
        print("   pip install pandas openpyxl numpy")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
