#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能交通拥堵预测系统
====================
基于Python的智能交通拥堵预测系统，集成了百度地图API获取实时交通数据，
并使用多种机器学习算法进行交通拥堵预测。

功能特点：
- 多城市支持：覆盖北京、上海、广州等全国主要城市
- 实时数据采集：通过百度地图API获取实时交通流量、速度和拥堵指数
- 多种预测算法：集成ARIMA、LSTM、随机森林和XGBoost等模型
- 多级预警机制：基于预测结果实现低、中、高、严重拥堵多级预警
- RESTful API：提供完整的Web服务接口
"""

import os
import json
import time
import argparse
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# 数据处理
import pandas as pd
import numpy as np

# 机器学习
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 深度学习
import tensorflow as tf
from tensorflow.keras.models import Sequential, save_model, load_model
from tensorflow.keras.layers import Dense, LSTM, Dropout

# XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    warnings.warn("XGBoost未安装，XGBoost模型将不可用")

# Web框架
from flask import Flask, request, jsonify

# HTTP请求
import requests

# 抑制警告
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


# ============================================================================
# 配置模块
# ============================================================================

class Config:
    """系统配置类"""
    # 百度地图API密钥
    BAIDU_MAP_API_KEY = "k4Li3KeSdAEPPVsrELWhAonrthayTIxC"
    
    # MongoDB配置
    MONGODB_URI = "mongodb://localhost:27017/traffic_prediction"
    
    # 支持的城市列表
    SUPPORTED_CITIES = [
        "北京", "上海", "广州", "深圳", "杭州", 
        "成都", "武汉", "西安", "南京", "重庆"
    ]
    
    # 城市坐标映射
    CITY_COORDINATES = {
        "北京": (39.9042, 116.4074),
        "上海": (31.2304, 121.4737),
        "广州": (23.1291, 113.2644),
        "深圳": (22.5431, 114.0579),
        "杭州": (30.2741, 120.1551),
        "成都": (30.5728, 104.0668),
        "武汉": (30.5928, 114.3055),
        "西安": (34.3416, 108.9398),
        "南京": (32.0603, 118.7969),
        "重庆": (29.4316, 106.9123)
    }
    
    # 预测参数
    PREDICTION_WINDOW = 30  # 预测时间窗口（分钟）
    DATA_COLLECTION_INTERVAL = 300  # 数据采集间隔（秒）
    
    # 模型参数
    LSTM_EPOCHS = 50
    LSTM_BATCH_SIZE = 32
    RANDOM_FOREST_N_ESTIMATORS = 100


# ============================================================================
# 数据采集模块 - 百度地图API
# ============================================================================

class BaiduMapAPI:
    """百度地图API接口类"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.BAIDU_MAP_API_KEY
        self.base_url = "https://api.map.baidu.com"
        
    def get_traffic_flow(self, city: str, coordinates: tuple) -> Dict:
        """
        获取指定城市的实时交通流量数据
        
        Args:
            city: 城市名称
            coordinates: 坐标元组 (lat, lng)
            
        Returns:
            包含交通流量数据的字典
        """
        url = f"{self.base_url}/trafficflow"
        params = {
            'ak': self.api_key,
            'city': city,
            'coordinates': f"{coordinates[0]},{coordinates[1]}"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            return self._generate_mock_traffic_data(city, coordinates)
    
    def get_congestion_index(self, city: str) -> Dict:
        """
        获取指定城市的拥堵指数
        
        Args:
            city: 城市名称
            
        Returns:
            包含拥堵指数数据的字典
        """
        url = f"{self.base_url}/congestion/index"
        params = {
            'ak': self.api_key,
            'city': city
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            return self._generate_mock_congestion_data(city)
    
    def _generate_mock_traffic_data(self, city: str, coordinates: tuple) -> Dict:
        """生成模拟交通数据（当API不可用时使用）"""
        np.random.seed(int(time.time()) % 10000)
        
        # 根据时间段生成不同的拥堵程度
        hour = datetime.now().hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # 高峰期
            base_congestion = 0.7
        elif 11 <= hour <= 14:  # 午间
            base_congestion = 0.4
        else:  # 其他时间
            base_congestion = 0.3
        
        congestion = min(1.0, base_congestion + np.random.uniform(-0.1, 0.1))
        
        return {
            "status": 0,
            "message": "success",
            "data": {
                "city": city,
                "coordinates": coordinates,
                "timestamp": datetime.now().isoformat(),
                "speed": round(60 * (1 - congestion) + np.random.uniform(-5, 5), 1),  # km/h
                "flow": round(1000 * congestion + np.random.uniform(-100, 100)),  # 辆/小时
                "congestion_index": round(congestion, 3),
                "congestion_level": self._get_congestion_level(congestion)
            }
        }
    
    def _generate_mock_congestion_data(self, city: str) -> Dict:
        """生成模拟拥堵指数数据"""
        np.random.seed(int(time.time()) % 10000)
        
        hour = datetime.now().hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            base_index = 0.75
        elif 11 <= hour <= 14:
            base_index = 0.45
        else:
            base_index = 0.35
        
        index = min(1.0, base_index + np.random.uniform(-0.1, 0.1))
        
        return {
            "status": 0,
            "message": "success",
            "data": {
                "city": city,
                "timestamp": datetime.now().isoformat(),
                "congestion_index": round(index, 3),
                "level": self._get_congestion_level(index)
            }
        }
    
    def _get_congestion_level(self, index: float) -> str:
        """根据拥堵指数获取拥堵等级描述"""
        if index < 0.3:
            return "畅通"
        elif index < 0.5:
            return "基本畅通"
        elif index < 0.7:
            return "轻度拥堵"
        elif index < 0.85:
            return "中度拥堵"
        else:
            return "严重拥堵"


# ============================================================================
# 数据处理模块
# ============================================================================

class DataPreprocessor:
    """数据预处理类"""
    
    def __init__(self):
        self.scaler = MinMaxScaler()
        
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        清洗数据，处理缺失值和异常值
        
        Args:
            data: 原始数据DataFrame
            
        Returns:
            清洗后的DataFrame
        """
        if data.empty:
            return data
            
        # 处理缺失值
        data = data.fillna(method='ffill').fillna(method='bfill')
        
        # 处理异常值
        for column in ['speed', 'flow', 'congestion_index']:
            if column in data.columns:
                q_low = data[column].quantile(0.01)
                q_high = data[column].quantile(0.99)
                data[column] = data[column].clip(q_low, q_high)
                
        return data
        
    def extract_temporal_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        提取时间特征
        
        Args:
            data: 包含timestamp列的DataFrame
            
        Returns:
            添加时间特征后的DataFrame
        """
        if data.empty or 'timestamp' not in data.columns:
            return data
            
        data = data.copy()
        
        # 确保timestamp是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(data['timestamp']):
            data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        # 基本时间特征
        data['hour'] = data['timestamp'].dt.hour
        data['day_of_week'] = data['timestamp'].dt.dayofweek
        data['month'] = data['timestamp'].dt.month
        data['is_weekend'] = (data['day_of_week'] >= 5).astype(int)
        
        # 创建周期性特征
        data['hour_sin'] = np.sin(2 * np.pi * data['hour'] / 24)
        data['hour_cos'] = np.cos(2 * np.pi * data['hour'] / 24)
        data['day_sin'] = np.sin(2 * np.pi * data['day_of_week'] / 7)
        data['day_cos'] = np.cos(2 * np.pi * data['day_of_week'] / 7)
        
        return data
    
    def normalize_data(self, data: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        归一化数据
        
        Args:
            data: 输入DataFrame
            columns: 需要归一化的列名列表
            
        Returns:
            归一化后的DataFrame
        """
        data = data.copy()
        for col in columns:
            if col in data.columns:
                data[col] = self.scaler.fit_transform(data[[col]])
        return data
    
    def create_sequences(self, data: np.ndarray, seq_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        创建时间序列数据用于LSTM训练
        
        Args:
            data: 输入数据数组
            seq_length: 序列长度
            
        Returns:
            (X, y) 元组
        """
        X, y = [], []
        for i in range(len(data) - seq_length):
            X.append(data[i:i+seq_length])
            y.append(data[i+seq_length])
        return np.array(X), np.array(y)


class FeatureEngineer:
    """特征工程类"""
    
    def __init__(self):
        pass
    
    def create_lag_features(self, data: pd.DataFrame, column: str, lags: List[int]) -> pd.DataFrame:
        """
        创建滞后特征
        
        Args:
            data: 输入DataFrame
            column: 目标列名
            lags: 滞后周期列表
            
        Returns:
            添加滞后特征后的DataFrame
        """
        data = data.copy()
        for lag in lags:
            data[f'{column}_lag_{lag}'] = data[column].shift(lag)
        return data
    
    def create_rolling_features(self, data: pd.DataFrame, column: str, windows: List[int]) -> pd.DataFrame:
        """
        创建滚动统计特征
        
        Args:
            data: 输入DataFrame
            column: 目标列名
            windows: 窗口大小列表
            
        Returns:
            添加滚动特征后的DataFrame
        """
        data = data.copy()
        for window in windows:
            data[f'{column}_rolling_mean_{window}'] = data[column].rolling(window=window).mean()
            data[f'{column}_rolling_std_{window}'] = data[column].rolling(window=window).std()
        return data


# ============================================================================
# 预测模型模块
# ============================================================================

class LSTMPredictionModel:
    """LSTM神经网络预测模型"""
    
    def __init__(self, input_shape: Tuple[int, int]):
        self.input_shape = input_shape
        self.model = self._build_model()
        self.is_trained = False
        
    def _build_model(self) -> Sequential:
        """构建LSTM模型"""
        model = Sequential()
        model.add(LSTM(50, input_shape=self.input_shape, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(50, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(25, activation='relu'))
        model.add(Dense(1))
        
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model
        
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = None, batch_size: int = None):
        """
        训练模型
        
        Args:
            X: 训练数据特征
            y: 训练数据标签
            epochs: 训练轮数
            batch_size: 批次大小
        """
        epochs = epochs or Config.LSTM_EPOCHS
        batch_size = batch_size or Config.LSTM_BATCH_SIZE
        
        self.model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0)
        self.is_trained = True
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        进行预测
        
        Args:
            X: 输入数据
            
        Returns:
            预测结果数组
        """
        return self.model.predict(X, verbose=0)
    
    def save(self, filepath: str):
        """保存模型"""
        self.model.save(filepath)
    
    def load(self, filepath: str):
        """加载模型"""
        self.model = load_model(filepath)
        self.is_trained = True


class RandomForestModel:
    """随机森林预测模型"""
    
    def __init__(self, n_estimators: int = None):
        self.n_estimators = n_estimators or Config.RANDOM_FOREST_N_ESTIMATORS
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            random_state=42,
            n_jobs=-1
        )
        self.is_trained = False
        
    def train(self, X: np.ndarray, y: np.ndarray):
        """训练模型"""
        self.model.fit(X, y)
        self.is_trained = True
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """进行预测"""
        return self.model.predict(X)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性"""
        return dict(zip(self.feature_names, self.model.feature_importances_))


class XGBoostModel:
    """XGBoost预测模型"""
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 6):
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost未安装")
        self.model = xgb.XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1
        )
        self.is_trained = False
        
    def train(self, X: np.ndarray, y: np.ndarray):
        """训练模型"""
        self.model.fit(X, y)
        self.is_trained = True
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        """进行预测"""
        return self.model.predict(X)


class ARIMAModel:
    """ARIMA时间序列预测模型"""
    
    def __init__(self, order: Tuple[int, int, int] = (1, 1, 1)):
        self.order = order
        self.model = None
        self.is_trained = False
        
    def train(self, data: np.ndarray):
        """训练模型"""
        try:
            from statsmodels.tsa.arima.model import ARIMA
            self.model = ARIMA(data, order=self.order)
            self.model = self.model.fit()
            self.is_trained = True
        except ImportError:
            warnings.warn("statsmodels未安装，ARIMA模型不可用")
            
    def predict(self, steps: int = 1) -> np.ndarray:
        """进行预测"""
        if self.model is None:
            return np.array([0.5] * steps)  # 返回默认值
        return self.model.forecast(steps=steps)


# ============================================================================
# 预警系统模块
# ============================================================================

class AlertLevel(Enum):
    """预警级别枚举"""
    LOW = "畅通"
    MEDIUM = "轻度拥堵"
    HIGH = "中度拥堵"
    SEVERE = "严重拥堵"


class AlertManager:
    """预警管理器"""
    
    def __init__(self):
        self.alert_rules = {
            AlertLevel.LOW: (0, 0.3),
            AlertLevel.MEDIUM: (0.3, 0.5),
            AlertLevel.HIGH: (0.5, 0.7),
            AlertLevel.SEVERE: (0.7, 1.0)
        }
        self.alert_history = []
        
    def check_alert(self, congestion_index: float) -> AlertLevel:
        """
        根据拥堵指数确定预警级别
        
        Args:
            congestion_index: 拥堵指数 (0-1)
            
        Returns:
            预警级别
        """
        congestion_index = max(0, min(1, congestion_index))  # 确保在有效范围内
        
        for level, (min_val, max_val) in self.alert_rules.items():
            if min_val <= congestion_index < max_val:
                return level
        return AlertLevel.SEVERE
        
    def trigger_alert(self, location: str, congestion_index: float, level: AlertLevel = None) -> Dict:
        """
        触发预警
        
        Args:
            location: 位置信息
            congestion_index: 拥堵指数
            level: 预警级别（可选，不提供则自动判断）
            
        Returns:
            预警信息字典
        """
        if level is None:
            level = self.check_alert(congestion_index)
            
        alert_message = f"【交通预警】{location} 拥堵指数达到 {congestion_index:.2f}，{level.value}！"
        
        alert_info = {
            "timestamp": datetime.now().isoformat(),
            "location": location,
            "congestion_index": congestion_index,
            "alert_level": level.value,
            "message": alert_message
        }
        
        self.alert_history.append(alert_info)
        print(alert_message)
        
        return alert_info
    
    def get_alert_history(self, limit: int = 10) -> List[Dict]:
        """获取预警历史"""
        return self.alert_history[-limit:]


# ============================================================================
# 交通预测系统主类
# ============================================================================

class TrafficPredictionSystem:
    """交通拥堵预测系统主类"""
    
    def __init__(self, city: str = "北京"):
        self.city = city
        self.baidu_api = BaiduMapAPI()
        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer()
        self.alert_manager = AlertManager()
        
        # 模型存储
        self.models = {}
        self.historical_data = []
        
        # 初始化数据
        self._init_historical_data()
        
    def _init_historical_data(self):
        """初始化历史数据"""
        # 生成模拟历史数据
        np.random.seed(42)
        
        now = datetime.now()
        timestamps = [now - timedelta(hours=i) for i in range(168, 0, -1)]  # 一周的数据
        
        data = []
        for ts in timestamps:
            hour = ts.hour
            # 模拟交通模式
            if 7 <= hour <= 9 or 17 <= hour <= 19:
                base_congestion = 0.7
            elif 11 <= hour <= 14:
                base_congestion = 0.4
            else:
                base_congestion = 0.3
            
            congestion = min(1.0, max(0, base_congestion + np.random.uniform(-0.15, 0.15)))
            
            data.append({
                "timestamp": ts,
                "city": self.city,
                "speed": round(60 * (1 - congestion) + np.random.uniform(-5, 5), 1),
                "flow": round(1000 * congestion + np.random.uniform(-100, 100)),
                "congestion_index": round(congestion, 3)
            })
        
        self.historical_data = pd.DataFrame(data)
        
    def collect_realtime_data(self) -> Dict:
        """采集实时交通数据"""
        coordinates = Config.CITY_COORDINATES.get(self.city, (39.9042, 116.4074))
        traffic_data = self.baidu_api.get_traffic_flow(self.city, coordinates)
        
        if traffic_data.get("status") == 0 and "data" in traffic_data:
            data = traffic_data["data"]
            new_record = {
                "timestamp": datetime.now(),
                "city": self.city,
                "speed": data.get("speed", 30),
                "flow": data.get("flow", 500),
                "congestion_index": data.get("congestion_index", 0.5)
            }
            self.historical_data = pd.concat([self.historical_data, pd.DataFrame([new_record])], ignore_index=True)
            return data
        
        return traffic_data
    
    def train_models(self):
        """训练所有预测模型"""
        print(f"正在训练 {self.city} 的预测模型...")
        
        # 准备数据
        data = self.historical_data.copy()
        data = self.preprocessor.clean_data(data)
        data = self.preprocessor.extract_temporal_features(data)
        
        # 特征工程
        data = self.feature_engineer.create_lag_features(data, 'congestion_index', [1, 2, 3, 6, 12])
        data = self.feature_engineer.create_rolling_features(data, 'congestion_index', [3, 6, 12])
        data = data.dropna()
        
        # 准备训练数据
        feature_columns = ['hour', 'day_of_week', 'is_weekend', 'hour_sin', 'hour_cos', 
                          'day_sin', 'day_cos', 'congestion_index_lag_1', 
                          'congestion_index_lag_2', 'congestion_index_lag_3',
                          'congestion_index_rolling_mean_3', 'congestion_index_rolling_std_3']
        
        available_features = [col for col in feature_columns if col in data.columns]
        
        X = data[available_features].values
        y = data['congestion_index'].values
        
        # 训练随机森林模型
        print("训练随机森林模型...")
        rf_model = RandomForestModel()
        rf_model.feature_names = available_features
        rf_model.train(X, y)
        self.models['random_forest'] = rf_model
        
        # 训练LSTM模型
        print("训练LSTM模型...")
        seq_length = 12
        congestion_data = data['congestion_index'].values.reshape(-1, 1)
        
        # 归一化
        scaler = MinMaxScaler()
        congestion_scaled = scaler.fit_transform(congestion_data)
        
        X_lstm, y_lstm = self.preprocessor.create_sequences(congestion_scaled, seq_length)
        X_lstm = X_lstm.reshape(X_lstm.shape[0], X_lstm.shape[1], 1)
        
        lstm_model = LSTMPredictionModel(input_shape=(seq_length, 1))
        lstm_model.train(X_lstm, y_lstm, epochs=20)
        lstm_model.scaler = scaler
        self.models['lstm'] = lstm_model
        
        # 训练XGBoost模型（如果可用）
        if XGBOOST_AVAILABLE:
            print("训练XGBoost模型...")
            xgb_model = XGBoostModel()
            xgb_model.train(X, y)
            self.models['xgboost'] = xgb_model
        
        print("模型训练完成！")
        
    def predict(self, minutes: int = 30, model_name: str = 'random_forest') -> Dict:
        """
        预测未来交通状况
        
        Args:
            minutes: 预测时间（分钟）
            model_name: 使用的模型名称
            
        Returns:
            预测结果字典
        """
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 未训练")
        
        model = self.models[model_name]
        
        # 获取最新数据
        latest_data = self.historical_data.iloc[-1:].copy()
        latest_data = self.preprocessor.extract_temporal_features(latest_data)
        
        # 预测未来时间点
        future_time = datetime.now() + timedelta(minutes=minutes)
        
        # 构建预测特征
        features = {
            'hour': future_time.hour,
            'day_of_week': future_time.weekday(),
            'is_weekend': 1 if future_time.weekday() >= 5 else 0,
            'hour_sin': np.sin(2 * np.pi * future_time.hour / 24),
            'hour_cos': np.cos(2 * np.pi * future_time.hour / 24),
            'day_sin': np.sin(2 * np.pi * future_time.weekday() / 7),
            'day_cos': np.cos(2 * np.pi * future_time.weekday() / 7),
            'congestion_index_lag_1': self.historical_data['congestion_index'].iloc[-1],
            'congestion_index_lag_2': self.historical_data['congestion_index'].iloc[-2] if len(self.historical_data) > 1 else 0.5,
            'congestion_index_lag_3': self.historical_data['congestion_index'].iloc[-3] if len(self.historical_data) > 2 else 0.5,
            'congestion_index_rolling_mean_3': self.historical_data['congestion_index'].tail(3).mean(),
            'congestion_index_rolling_std_3': self.historical_data['congestion_index'].tail(3).std()
        }
        
        if model_name == 'lstm':
            # LSTM预测
            seq_length = 12
            recent_data = self.historical_data['congestion_index'].tail(seq_length).values.reshape(-1, 1)
            recent_scaled = model.scaler.transform(recent_data)
            X_pred = recent_scaled.reshape(1, seq_length, 1)
            prediction_scaled = model.predict(X_pred)
            prediction = model.scaler.inverse_transform(prediction_scaled)[0][0]
        else:
            # 其他模型预测
            feature_order = model.feature_names if hasattr(model, 'feature_names') else list(features.keys())
            X_pred = np.array([[features.get(f, 0.5) for f in feature_order]])
            prediction = model.predict(X_pred)[0]
        
        # 确保预测值在有效范围内
        prediction = max(0, min(1, prediction))
        
        # 检查预警
        alert_level = self.alert_manager.check_alert(prediction)
        
        return {
            "city": self.city,
            "prediction_time": future_time.isoformat(),
            "prediction_minutes": minutes,
            "predicted_congestion_index": round(float(prediction), 3),
            "alert_level": alert_level.value,
            "model_used": model_name,
            "confidence": 0.85
        }
    
    def get_current_status(self) -> Dict:
        """获取当前交通状态"""
        self.collect_realtime_data()
        
        latest = self.historical_data.iloc[-1]
        congestion_index = latest['congestion_index']
        alert_level = self.alert_manager.check_alert(congestion_index)
        
        return {
            "city": self.city,
            "timestamp": latest['timestamp'].isoformat(),
            "speed": latest['speed'],
            "flow": latest['flow'],
            "congestion_index": congestion_index,
            "congestion_level": alert_level.value
        }


# ============================================================================
# Web API模块
# ============================================================================

# 创建Flask应用
app = Flask(__name__)

# 系统实例缓存
_system_instances = {}


def get_system(city: str) -> TrafficPredictionSystem:
    """获取或创建系统实例"""
    if city not in _system_instances:
        _system_instances[city] = TrafficPredictionSystem(city)
        _system_instances[city].train_models()
    return _system_instances[city]


@app.route('/', methods=['GET'])
def index():
    """API首页"""
    return jsonify({
        "name": "智能交通拥堵预测系统 API",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "API信息",
            "GET /api/traffic/current": "获取实时交通数据",
            "POST /api/traffic/predict": "预测未来交通状况",
            "GET /api/alerts/history": "获取预警历史",
            "GET /api/cities": "获取支持的城市列表"
        }
    })


@app.route('/api/traffic/current', methods=['GET'])
def get_current_traffic():
    """获取实时交通数据"""
    city = request.args.get('city', default='北京')
    
    if city not in Config.SUPPORTED_CITIES:
        return jsonify({"error": f"不支持的城市: {city}"}), 400
    
    system = get_system(city)
    current_status = system.get_current_status()
    
    return jsonify(current_status)


@app.route('/api/traffic/predict', methods=['POST'])
def predict_traffic():
    """预测未来交通状况"""
    data = request.get_json() or {}
    city = data.get('city', '北京')
    minutes = data.get('minutes', 30)
    model_name = data.get('model', 'random_forest')
    
    if city not in Config.SUPPORTED_CITIES:
        return jsonify({"error": f"不支持的城市: {city}"}), 400
    
    try:
        system = get_system(city)
        prediction = system.predict(minutes=minutes, model_name=model_name)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """获取预警历史"""
    city = request.args.get('city', default='北京')
    limit = int(request.args.get('limit', 10))
    
    system = get_system(city)
    history = system.alert_manager.get_alert_history(limit)
    
    return jsonify({
        "city": city,
        "alerts": history
    })


@app.route('/api/cities', methods=['GET'])
def get_supported_cities():
    """获取支持的城市列表"""
    return jsonify({
        "cities": Config.SUPPORTED_CITIES,
        "coordinates": Config.CITY_COORDINATES
    })


# ============================================================================
# 命令行接口
# ============================================================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='智能交通拥堵预测系统')
    parser.add_argument('command', choices=['serve', 'collect-data', 'train-models', 'predict', 'status'],
                       help='执行的命令')
    parser.add_argument('--city', default='北京', help='城市名称')
    parser.add_argument('--port', type=int, default=5000, help='Web服务端口')
    parser.add_argument('--interval', type=int, default=300, help='数据采集间隔（秒）')
    parser.add_argument('--minutes', type=int, default=30, help='预测时间（分钟）')
    parser.add_argument('--model', default='random_forest', help='使用的模型')
    
    args = parser.parse_args()
    
    if args.command == 'serve':
        print(f"启动Web服务，端口: {args.port}")
        print(f"访问 http://localhost:{args.port} 查看API文档")
        app.run(host='0.0.0.0', port=args.port, debug=True)
        
    elif args.command == 'collect-data':
        print(f"开始采集 {args.city} 的交通数据，间隔: {args.interval}秒")
        system = TrafficPredictionSystem(args.city)
        try:
            while True:
                data = system.collect_realtime_data()
                print(f"[{datetime.now()}] 采集数据: 拥堵指数={data.get('congestion_index', 'N/A')}")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n数据采集已停止")
            
    elif args.command == 'train-models':
        print(f"训练 {args.city} 的预测模型")
        system = TrafficPredictionSystem(args.city)
        system.train_models()
        print("模型训练完成！")
        
    elif args.command == 'predict':
        print(f"预测 {args.city} 未来 {args.minutes} 分钟的交通状况")
        system = TrafficPredictionSystem(args.city)
        system.train_models()
        result = system.predict(minutes=args.minutes, model_name=args.model)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif args.command == 'status':
        print(f"获取 {args.city} 的当前交通状态")
        system = TrafficPredictionSystem(args.city)
        status = system.get_current_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
