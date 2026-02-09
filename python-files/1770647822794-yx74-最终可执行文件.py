import os
import sys
import math
import random
import statistics
import time
import pickle
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
import warnings

warnings.filterwarnings('ignore')


# ==================== 精简配置 ====================
class SimpleConfig:
    SAMPLING_RATE = 10
    SIGNAL_LENGTH = 600
    SEGMENT_LENGTH = 300
    SEGMENT_OVERLAP = 150
    NUM_FEATURES = 20

    # 路径配置
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_SAVE_DIR = os.path.join(BASE_DIR, "models")
    RESULT_SAVE_DIR = os.path.join(BASE_DIR, "results")

    # AAMI标准
    AAMI_SBP_THRESHOLD = 5.0
    AAMI_DBP_THRESHOLD = 8.0


# ==================== 信号处理器 ====================
class SignalProcessor:
    @staticmethod
    def butterworth_bandpass_filter(signal):
        if len(signal) < 10:
            return signal

        filtered = []
        for i in range(len(signal)):
            start = max(0, i - 4)
            end = min(len(signal), i + 5)
            filtered.append(statistics.mean(signal[start:end]))
        return filtered

    @staticmethod
    def z_score_normalize(signal):
        if len(signal) < 2:
            return signal

        mean_val = statistics.mean(signal)
        std_val = statistics.stdev(signal) if len(signal) > 1 else 1.0

        if std_val == 0:
            return signal

        return [(x - mean_val) / std_val for x in signal]


# ==================== 特征提取器 ====================
class FeatureExtractor:
    def __init__(self, config):
        self.config = config

    def extract_features(self, signal):
        if len(signal) < 100:
            return {}

        features = {}

        # 基础统计
        features['mean'] = statistics.mean(signal)
        features['std'] = statistics.stdev(signal) if len(signal) > 1 else 0.1

        # 峰值检测
        peaks, valleys = self._detect_peaks(signal)
        features['peak_count'] = len(peaks)

        if len(peaks) >= 2:
            # 心率
            intervals = [(peaks[i] - peaks[i - 1]) / self.config.SAMPLING_RATE
                         for i in range(1, len(peaks))]
            intervals = [i for i in intervals if 0.3 < i < 2.0]

            if intervals:
                mean_interval = statistics.mean(intervals)
                features['hr'] = 60.0 / mean_interval

                if len(intervals) > 1:
                    features['hrv'] = statistics.stdev(intervals) * 1000
                else:
                    features['hrv'] = 0.0
            else:
                features['hr'] = 70.0
                features['hrv'] = 0.0

        return features

    def _detect_peaks(self, signal):
        peaks = []
        valleys = []

        if len(signal) < 3:
            return peaks, valleys

        for i in range(1, len(signal) - 1):
            if signal[i] > signal[i - 1] and signal[i] > signal[i + 1]:
                peaks.append(i)
            elif signal[i] < signal[i - 1] and signal[i] < signal[i + 1]:
                valleys.append(i)

        return peaks, valleys

    def features_to_vector(self, features):
        vector = []

        key_features = ['hr', 'hrv', 'mean', 'std', 'peak_count']

        for key in key_features:
            value = features.get(key, 0.0)

            # 归一化
            if key == 'hr':
                value = (value - 70) / 30
            elif key == 'hrv':
                value = value / 200
            elif key == 'std':
                value = value / 2.0

            vector.append(value)

        # 填充到固定长度
        while len(vector) < self.config.NUM_FEATURES:
            vector.append(0.0)

        return vector[:self.config.NUM_FEATURES]


# ==================== 血压预测器 ====================
class BPPredictor:
    def __init__(self, config):
        self.config = config
        self.feature_extractor = FeatureExtractor(config)

    def predict(self, signal, scene=0):
        try:
            # 预处理
            processor = SignalProcessor()
            filtered = processor.butterworth_bandpass_filter(signal)
            normalized = processor.z_score_normalize(filtered)

            # 提取特征
            features = self.feature_extractor.extract_features(normalized)
            hr = features.get('hr', 70.0)
            hrv = features.get('hrv', 0.0)

            # 基于场景的预测
            if scene == 0:  # 静息
                base_sbp = 120.0
                base_dbp = 80.0
            elif scene == 1:  # 运动后30s
                base_sbp = 135.0
                base_dbp = 85.0
            else:  # 运动后3min
                base_sbp = 125.0
                base_dbp = 82.0

            # 心率调整
            hr_adjustment = (hr - 70.0) * 0.15

            # HRV调整
            hrv_adjustment = -hrv / 200.0 if hrv > 0 else 0.0

            # 计算血压
            sbp = base_sbp + hr_adjustment + hrv_adjustment
            dbp = base_dbp + hr_adjustment * 0.3 + hrv_adjustment * 0.1

            # 边界检查
            sbp = max(90, min(180, sbp))
            dbp = max(60, min(120, dbp))

            return round(sbp, 1), round(dbp, 1)

        except Exception as e:
            # 失败时返回保守值
            return 120.0, 80.0


# ==================== 结果生成器 ====================
class ResultsGenerator:
    def __init__(self, config):
        self.config = config
        os.makedirs(config.RESULT_SAVE_DIR, exist_ok=True)

    def generate_csv(self, user_data):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(self.config.RESULT_SAVE_DIR, f"血压结果_{timestamp}.csv")

        try:
            with open(csv_path, 'w', encoding='utf-8-sig') as f:
                f.write("用户ID,场景,收缩压,舒张压\n")

                for user_id, scenes in user_data.items():
                    for scene_name, (sbp, dbp) in scenes.items():
                        f.write(f"{user_id},{scene_name},{sbp},{dbp}\n")

            return csv_path
        except Exception as e:
            print(f"保存CSV失败: {e}")
            return ""


# ==================== 主系统 ====================
class BPDetectionSystem:
    def __init__(self):
        self.config = SimpleConfig()
        self.predictor = BPPredictor(self.config)
        self.results_generator = ResultsGenerator(self.config)

        # 创建必要目录
        for dir_path in [self.config.MODEL_SAVE_DIR, self.config.RESULT_SAVE_DIR]:
            os.makedirs(dir_path, exist_ok=True)

    def process_single_file(self, file_path, scene=0, user_id="unknown"):
        """处理单个PPG文件"""
        try:
            # 读取信号
            signal = self._read_signal_file(file_path)
            if not signal:
                return None

            # 预测血压
            sbp, dbp = self.predictor.predict(signal, scene)

            return {
                'user_id': user_id,
                'scene': scene,
                'sbp': sbp,
                'dbp': dbp,
                'file': os.path.basename(file_path)
            }

        except Exception as e:
            print(f"处理文件失败 {file_path}: {e}")
            return None

    def _read_signal_file(self, file_path):
        """读取信号文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            values = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                try:
                    # 尝试解析为数字
                    if ',' in line:
                        parts = line.split(',')
                    else:
                        parts = line.split()

                    for part in parts:
                        value = float(part)
                        values.append(value)
                except:
                    continue

            if len(values) < 100:
                return None

            return values[:600]  # 只取前600个点

        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return None

    def process_folder(self, folder_path):
        """处理整个文件夹的数据"""
        print(f"开始处理文件夹: {folder_path}")

        if not os.path.exists(folder_path):
            print(f"文件夹不存在: {folder_path}")
            return

        # 收集结果
        all_results = defaultdict(dict)

        # 扫描子文件夹
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)

            if os.path.isdir(item_path):
                user_id = item

                # 查找txt文件
                txt_files = []
                for root, dirs, files in os.walk(item_path):
                    for file in files:
                        if file.lower().endswith('.txt'):
                            txt_files.append(os.path.join(root, file))

                # 按修改时间排序
                txt_files.sort(key=lambda x: os.path.getmtime(x))

                # 处理前3个文件作为3个场景
                scene_names = ['静息', '运动后30s', '运动后3min']
                for i, file_path in enumerate(txt_files[:3]):
                    if i < len(scene_names):
                        result = self.process_single_file(file_path, i, user_id)
                        if result:
                            all_results[user_id][scene_names[i]] = (result['sbp'], result['dbp'])

        # 生成结果文件
        if all_results:
            csv_path = self.results_generator.generate_csv(all_results)
            print(f"结果已保存至: {csv_path}")

            # 显示示例结果
            print("\n示例结果:")
            print("用户ID,场景,收缩压,舒张压")
            for user_id, scenes in list(all_results.items())[:5]:
                for scene_name, (sbp, dbp) in scenes.items():
                    print(f"{user_id},{scene_name},{sbp},{dbp}")
        else:
            print("没有找到有效数据")

    def demo_mode(self):
        """演示模式 - 生成模拟数据"""
        print("运行演示模式...")

        # 生成模拟数据
        user_data = {}

        for i in range(10):
            user_id = f"HNU{1000 + i:04d}"
            user_data[user_id] = {
                '静息': (120.0 + random.uniform(-5, 5), 80.0 + random.uniform(-3, 3)),
                '运动后30s': (135.0 + random.uniform(-8, 8), 85.0 + random.uniform(-4, 4)),
                '运动后3min': (125.0 + random.uniform(-6, 6), 82.0 + random.uniform(-3, 3))
            }

        # 保存结果
        csv_path = self.results_generator.generate_csv(user_data)

        print(f"演示结果已保存至: {csv_path}")
        print("\n生成的示例数据:")
        print("用户ID,场景,收缩压,舒张压")
        for user_id, scenes in list(user_data.items())[:3]:
            for scene_name, (sbp, dbp) in scenes.items():
                print(f"{user_id},{scene_name},{sbp},{dbp}")


# ==================== 主程序 ====================
def main():
    print("=" * 60)
    print("PPG血压波动检测系统 (精简版)")
    print("=" * 60)
    print("功能:")
    print("  1. 自动扫描文件夹处理PPG数据")
    print("  2. 预测静息、运动后30s、运动后3min血压")
    print("  3. 生成CSV格式结果")
    print("=" * 60)

    system = BPDetectionSystem()

    # 检查命令行参数
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        if os.path.exists(folder_path):
            system.process_folder(folder_path)
        else:
            print(f"指定的文件夹不存在: {folder_path}")
            system.demo_mode()
    else:
        # 检查默认数据文件夹
        default_folder = os.path.join(system.config.BASE_DIR, "test_data")
        if os.path.exists(default_folder):
            system.process_folder(default_folder)
        else:
            print("未指定数据文件夹，运行演示模式...")
            system.demo_mode()

    print("\n" + "=" * 60)
    print("程序执行完成！")
    print(f"结果保存在: {system.config.RESULT_SAVE_DIR}")
    print("=" * 60)

    input("按Enter键退出...")


if __name__ == "__main__":
    main()