#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bocad TXT 转换器 v19
将 Bocad v18 输出的 .txt 文件直接转换为 CAD 通用格式（STEP / DXF 3D / STL）
不依赖任何 CAD 软件，基于 cadquery (OpenCascade) 实现。

支持的图元:
  - NEW BOX (长方体)
  - NEW CYLINDER (圆柱体)
  - NEW NREVOLUTION (旋转体/螺柱，加法)
  - NEW NXTRUSION (拉伸切除，减法，从父 BOX 中切掉)

用法:
  python 紧固件转换器_v19.py --input xxx.txt --format step,dxf,stl --output ./out
  python 紧固件转换器_v19.py --input ./txts/ --format step --output ./steps/
  python 紧固件转换器_v19.py --input xxx.txt --dry-run
"""

import argparse
import os
import re
import sys
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

# ============================================================
# 数据结构
# ============================================================

@dataclass
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_tuple(self):
        return (self.x, self.y, self.z)

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __mul__(self, s):
        return Vec3(self.x * s, self.y * s, self.z * s)


@dataclass
class Primitive:
    """基础图元基类"""
    pos: Vec3 = field(default_factory=Vec3)
    ori_matrix: Tuple[Tuple[float, float, float], ...] = None  # 3x3 旋转矩阵
    children: List['Primitive'] = field(default_factory=list)
    parent: Optional['Primitive'] = None

    def __post_init__(self):
        if self.ori_matrix is None:
            self.ori_matrix = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


@dataclass
class Box(Primitive):
    xlen: float = 0.0
    ylen: float = 0.0
    zlen: float = 0.0


@dataclass
class Cylinder(Primitive):
    diam: float = 0.0
    heig: float = 0.0


@dataclass
class NRevolution(Primitive):
    """旋转体（加法）"""
    vertices: List[Vec3] = field(default_factory=list)
    angl: float = 360.0  # 旋转角度，默认整圈


@dataclass
class NXtrusion(Primitive):
    """拉伸切除（减法）"""
    vertices: List[Vec3] = field(default_factory=list)
    heig: float = 0.0


@dataclass
class Vertex(Primitive):
    """顶点（仅用于循环内）"""
    pass


# ============================================================
# 单位解析
# ============================================================

def parse_value(s: str) -> float:
    """解析带单位的数值，如 '34.64mm' -> 34.64"""
    s = s.strip()
    # 移除常见单位
    s = re.sub(r'(mm|cm|m)\s*$', '', s, flags=re.IGNORECASE)
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_pos(line: str) -> Vec3:
    """从 'POS X -256mm Y 632.22mm Z -46.25mm' 解析坐标"""
    v = Vec3()
    # 匹配 X/Y/Z 后面的值
    mx = re.search(r'X\s+([+-]?[\d.]+\s*mm?)', line, re.IGNORECASE)
    my = re.search(r'Y\s+([+-]?[\d.]+\s*mm?)', line, re.IGNORECASE)
    mz = re.search(r'Z\s+([+-]?[\d.]+\s*mm?)', line, re.IGNORECASE)
    if mx:
        v.x = parse_value(mx.group(1))
    if my:
        v.y = parse_value(my.group(1))
    if mz:
        v.z = parse_value(mz.group(1))
    return v


# ============================================================
# ORI 方向解析
# ============================================================

def parse_ori(line: str) -> Tuple[Tuple[float, float, float], ...]:
    """
    解析 Bocad ORI 语句，返回 3x3 旋转矩阵（列向量为新坐标系的基向量）。
    
    格式示例:
      "ORI Y is -Y and Z is Z"
      "ORI Y is -X and Z is -Y"
    
    规则: 给出两个轴的方向，第三个由右手定则确定。
    返回的矩阵 R 满足: global_vec = R * local_vec
    """
    line = line.strip()
    if not line.upper().startswith('ORI'):
        return ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    
    # 提取轴映射
    # 模式: <axis> is <sign><axis> [and <axis> is <sign><axis>]
    mappings = {}
    
    # 找所有 "X is Y" 模式
    pattern = r'([XYZ])\s+is\s+([+-]?)\s*([XYZ])'
    matches = re.findall(pattern, line, re.IGNORECASE)
    
    for local_axis, sign, global_axis in matches:
        local_axis = local_axis.upper()
        global_axis = global_axis.upper()
        sign_val = -1.0 if sign == '-' else 1.0
        mappings[local_axis] = (global_axis, sign_val)
    
    # 构建基向量
    basis = {'X': [0.0, 0.0, 0.0], 'Y': [0.0, 0.0, 0.0], 'Z': [0.0, 0.0, 0.0]}
    axis_idx = {'X': 0, 'Y': 1, 'Z': 2}
    
    for local_axis, (global_axis, sign) in mappings.items():
        idx = axis_idx[global_axis]
        basis[local_axis][idx] = sign
    
    # 确定缺失的轴（用右手定则）
    defined = [a for a in ['X', 'Y', 'Z'] if a in mappings]
    missing = [a for a in ['X', 'Y', 'Z'] if a not in mappings]
    
    if len(missing) == 1:
        miss = missing[0]
        # 用右手定则: 叉乘
        # 如果定义了 X 和 Y，则 Z = X × Y
        # 如果定义了 X 和 Z，则 Y = Z × X（因为 Z × X = Y）
        # 如果定义了 Y 和 Z，则 X = Y × Z
        if 'X' in defined and 'Y' in defined:
            # Z = X × Y
            basis[miss] = _cross(basis['X'], basis['Y'])
        elif 'X' in defined and 'Z' in defined:
            # Y = Z × X
            basis[miss] = _cross(basis['Z'], basis['X'])
        elif 'Y' in defined and 'Z' in defined:
            # X = Y × Z
            basis[miss] = _cross(basis['Y'], basis['Z'])
    
    # 返回旋转矩阵（列为主，即 R = [x_col | y_col | z_col]）
    # cadquery 中使用的是行向量变换，需要转置
    return (
        tuple(basis['X']),  # 第一行（X 轴在全局的分量）
        tuple(basis['Y']),  # 第二行
        tuple(basis['Z']),  # 第三行
    )


def _cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def matrix_to_euler(matrix):
    """
    将 3x3 旋转矩阵转换为 ZYX 欧拉角（弧度），供 cadquery 使用。
    cadquery 的 rotate 是绕轴旋转，我们用三次旋转来合成。
    返回 (rx, ry, rz) 绕 X/Y/Z 轴的旋转角（弧度），按 Z-Y-X 顺序合成。
    """
    # 从旋转矩阵提取欧拉角 (ZYX order, i.e., yaw-pitch-roll)
    # R = Rz * Ry * Rx
    m = matrix
    
    # 检查 gimbal lock
    sy = math.sqrt(m[0][0] ** 2 + m[1][0] ** 2)
    singular = sy < 1e-6
    
    if not singular:
        rx = math.atan2(m[2][1], m[2][2])  # roll
        ry = math.atan2(-m[2][0], sy)      # pitch
        rz = math.atan2(m[1][0], m[0][0])  # yaw
    else:
        rx = math.atan2(-m[1][2], m[1][1])
        ry = math.atan2(-m[2][0], sy)
        rz = 0.0
    
    return (rx, ry, rz)


# ============================================================
# 解析器
# ============================================================

class BocadParser:
    """Bocad .txt 文件解析器"""
    
    def __init__(self):
        self.primitives: List[Primitive] = []
        self._stack: List[Primitive] = []  # 嵌套栈（BOX/NREVOLUTION/NXTRUSION 等图元）
        self._current_vertex_list: List[Vec3] = None
        self._loop_depth = 0  # LOOP 嵌套深度
        self._in_vertex = False  # 是否在 VERTEX 块内
        self._in_input = False
    
    def parse(self, filepath: str) -> List[Primitive]:
        """解析文件，返回顶层图元列表"""
        self.primitives = []
        self._stack = []
        self._current_vertex_list = None
        self._in_loop = False
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for line in lines:
            self._process_line(line.strip())
        
        return self.primitives
    
    def _process_line(self, line: str):
        """处理一行"""
        if not line:
            return
        
        # 跳过注释和控制语句
        if line.startswith('--') or line.startswith('$'):
            return
        if line.upper().startswith('ONERROR') or line.upper().startswith('LABEL'):
            return
        if line.upper().startswith('handle') or line.upper().startswith('RETURN'):
            return
        if line.upper().startswith('endhandle'):
            return
        
        upper = line.upper()
        
        # INPUT BEGIN / END
        if upper.startswith('INPUT BEGIN'):
            self._in_input = True
            return
        if upper.startswith('INPUT END') or upper.startswith('INPUT FINISH'):
            self._in_input = False
            return
        
        if not self._in_input:
            # 在 INPUT 块外也可能有 EQUIPMENT/SUBEQUIPMENT 声明
            if upper.startswith('NEW EQUIPMENT') or upper.startswith('NEW SUBEQUIPMENT'):
                # 跳过，只是容器
                return
            if upper.startswith('BUIL ') or upper.startswith('DSCO ') or upper.startswith('PTSP ') or upper.startswith('INSC '):
                return
            # 其他不在 INPUT 里的跳过
            return
        
        # NEW 开头的图元
        if upper.startswith('NEW EQUIPMENT') or upper.startswith('NEW SUBEQUIPMENT'):
            # 跳过，只是容器
            return
        
        if upper.startswith('NEW VOLUME'):
            # Volume 模式容器，跳过
            return
        
        if upper.startswith('NEW BOX'):
            box = Box()
            self._add_to_parent(box)
            self._stack.append(box)
            return
        
        if upper.startswith('NEW CYLINDER'):
            cyl = Cylinder()
            self._add_to_parent(cyl)
            self._stack.append(cyl)
            return
        
        if upper.startswith('NEW NREVOLUTION'):
            rev = NRevolution()
            self._add_to_parent(rev)
            self._stack.append(rev)
            return
        
        if upper.startswith('NEW NXTRUSION'):
            ext = NXtrusion()
            self._add_to_parent(ext)
            self._stack.append(ext)
            return
        
        if upper.startswith('NEW LOOP'):
            self._loop_depth += 1
            # 当前图元的顶点列表准备就绪
            top = self._stack[-1] if self._stack else None
            if isinstance(top, (NRevolution, NXtrusion)):
                self._current_vertex_list = top.vertices
            return
        
        if upper.startswith('NEW VERTEX'):
            # 新顶点，默认在原点，后续 POS 行更新
            self._in_vertex = True
            if self._current_vertex_list is not None:
                self._current_vertex_list.append(Vec3())
            return
        
        # 属性行
        if upper.startswith('POS '):
            pos = parse_pos(line)
            
            # 优先级1: 如果在 VERTEX 块内，更新当前顶点
            if self._in_vertex and self._current_vertex_list is not None and len(self._current_vertex_list) > 0:
                self._current_vertex_list[-1] = pos
                return
            
            # 优先级2: 更新当前栈顶图元
            top = self._stack[-1] if self._stack else None
            if top and isinstance(top, Primitive):
                top.pos = pos
            return
        
        if upper.startswith('ORI '):
            matrix = parse_ori(line)
            top = self._stack[-1] if self._stack else None
            if top and isinstance(top, Primitive):
                top.ori_matrix = matrix
            return
        
        if upper.startswith('XLEN '):
            val = parse_value(line.split(None, 1)[1] if len(line.split()) > 1 else '0')
            top = self._stack[-1] if self._stack else None
            if isinstance(top, Box):
                top.xlen = val
            return
        
        if upper.startswith('YLEN '):
            val = parse_value(line.split(None, 1)[1] if len(line.split()) > 1 else '0')
            top = self._stack[-1] if self._stack else None
            if isinstance(top, Box):
                top.ylen = val
            return
        
        if upper.startswith('ZLEN '):
            val = parse_value(line.split(None, 1)[1] if len(line.split()) > 1 else '0')
            top = self._stack[-1] if self._stack else None
            if isinstance(top, Box):
                top.zlen = val
            return
        
        if upper.startswith('DIAM '):
            val = parse_value(line.split(None, 1)[1] if len(line.split()) > 1 else '0')
            top = self._stack[-1] if self._stack else None
            if isinstance(top, Cylinder):
                top.diam = val
            return
        
        if upper.startswith('HEIG '):
            val = parse_value(line.split(None, 1)[1] if len(line.split()) > 1 else '0')
            top = self._stack[-1] if self._stack else None
            if isinstance(top, (Cylinder, NXtrusion)):
                top.heig = val
            return
        
        if upper.startswith('ANGL '):
            val = parse_value(line.split(None, 1)[1] if len(line.split()) > 1 else '360')
            top = self._stack[-1] if self._stack else None
            if isinstance(top, NRevolution):
                top.angl = val
            return
        
        # END 行
        if upper == 'END':
            # 1. 如果在 VERTEX 块内，关闭 VERTEX
            if self._in_vertex:
                self._in_vertex = False
                return
            
            # 2. 如果在 LOOP 内，减少 LOOP 深度
            if self._loop_depth > 0:
                self._loop_depth -= 1
                if self._loop_depth == 0:
                    self._current_vertex_list = None
                return
            
            # 3. 否则是图元的 END，弹出栈
            if self._stack:
                self._stack.pop()
            return
    
    def _add_to_parent(self, prim: Primitive):
        """将图元添加到当前父节点或顶层"""
        if self._stack:
            parent = self._stack[-1]
            parent.children.append(prim)
            prim.parent = parent
        else:
            self.primitives.append(prim)


# ============================================================
# 几何构建器 (cadquery)
# ============================================================

class GeometryBuilder:
    """使用 cadquery 构建几何"""
    
    def __init__(self):
        try:
            import cadquery as cq
            self.cq = cq
        except ImportError:
            print("错误: 未安装 cadquery。请运行: pip install cadquery", file=sys.stderr)
            sys.exit(1)
    
    def build_assembly(self, primitives: List[Primitive]):
        """构建装配体"""
        cq = self.cq
        # 先构建所有顶层实体
        solids = []
        for prim in primitives:
            solid = self._build_primitive(prim)
            if solid is not None:
                solids.append(solid)
        
        if not solids:
            return None
        
        # 合并所有加法实体
        result = solids[0]
        for s in solids[1:]:
            result = result.union(s)
        
        return result
    
    def _build_primitive(self, prim: Primitive):
        """构建单个图元（递归处理子图元）"""
        cq = self.cq
        
        if isinstance(prim, Box):
            return self._build_box(prim)
        elif isinstance(prim, Cylinder):
            return self._build_cylinder(prim)
        elif isinstance(prim, NRevolution):
            return self._build_revolution(prim)
        elif isinstance(prim, NXtrusion):
            return self._build_extrusion(prim)
        else:
            return None
    
    def _apply_transform(self, wp, prim: Primitive):
        """对 Workplane 应用位置和旋转变换"""
        cq = self.cq
        
        # 应用旋转
        rx, ry, rz = matrix_to_euler(prim.ori_matrix)
        
        # cadquery: 先绕 Z 转 (yaw), 再绕 Y 转 (pitch), 再绕 X 转 (roll)
        # 使用 rotate 方法
        if abs(rz) > 1e-10:
            wp = wp.rotate((0, 0, 0), (0, 0, 1), math.degrees(rz))
        if abs(ry) > 1e-10:
            wp = wp.rotate((0, 0, 0), (0, 1, 0), math.degrees(ry))
        if abs(rx) > 1e-10:
            wp = wp.rotate((0, 0, 0), (1, 0, 0), math.degrees(rx))
        
        # 应用平移
        wp = wp.translate(prim.pos.to_tuple())
        
        return wp
    
    def _build_box(self, box: Box):
        """构建长方体（含子图元的布尔运算）"""
        cq = self.cq
        
        # 创建立方体（中心在原点）
        wp = cq.Workplane("XY").box(box.xlen, box.ylen, box.zlen, centered=(True, True, True))
        
        # 处理子图元
        for child in box.children:
            child_solid = self._build_child_local(child, box)
            if child_solid is None:
                continue
            
            if isinstance(child, NXtrusion):
                # 减法：切掉
                wp = wp.cut(child_solid)
            else:
                # 加法：合并
                wp = wp.union(child_solid)
        
        # 应用变换
        wp = self._apply_transform(wp, box)
        
        return wp
    
    def _build_cylinder(self, cyl: Cylinder):
        """构建圆柱体"""
        cq = self.cq
        radius = cyl.diam / 2.0
        
        # cadquery cylinder: height along Z, radius
        wp = cq.Workplane("XY").cylinder(cyl.heig, radius, centered=(True, True, True))
        
        wp = self._apply_transform(wp, cyl)
        
        return wp
    
    def _build_revolution(self, rev: NRevolution):
        """构建旋转体（螺柱/实心圆柱）
        
        Bocad NREVOLUTION 的侧轮廓定义在 X-Y 平面，绕 X 轴旋转。
        对于螺柱：Y=10 是外半径（Ø20mm），X 方向是长度方向。
        轮廓中 Y>10 的部分为头部/参考区域，实际螺柱实体取最小半径。
        """
        cq = self.cq
        
        if len(rev.vertices) < 2:
            return None
        
        # 提取 2D 轮廓点（X-Y 平面）
        points_2d = [(v.x, v.y) for v in rev.vertices]
        
        # 去重（首尾相同的闭合点）
        if len(points_2d) > 1 and points_2d[0] == points_2d[-1]:
            points_2d = points_2d[:-1]
        
        if len(points_2d) < 2:
            return None
        
        # 计算螺柱参数：
        # - 长度 = X 方向范围
        # - 半径 = 最小 |Y| 值（螺柱外半径）
        # 对于标准紧固件，NREVOLUTION 代表螺柱，最小 Y 值即外半径
        xs = [p[0] for p in points_2d]
        ys = [abs(p[1]) for p in points_2d]
        
        length = max(xs) - min(xs)
        radius = min(ys)  # 最小 Y 值 = 螺柱半径
        
        # 找到螺柱的起始 X 位置（靠近头部的一端）
        # 假设 X=0 是 POS 端（自由端），X=-length 是头部端
        x_start = min(xs)  # 头部端（X 最小）
        x_end = max(xs)    # 自由端
        
        try:
            # 构建实心圆柱（绕 X 轴旋转的矩形 = 圆柱）
            # 矩形从 (x_start, 0) 到 (x_end, radius)，绕 X 轴旋转
            profile_pts = [
                (x_start, 0),
                (x_start, radius),
                (x_end, radius),
                (x_end, 0),
            ]
            wp = (
                cq.Workplane("XY")
                .polyline(profile_pts)
                .close()
                .revolve(rev.angl, (x_start - 10, 0, 0), (x_end + 10, 0, 0))
            )
        except Exception as e:
            print(f"  警告: NREVOLUTION 构建失败: {e}", file=sys.stderr)
            # 降级：直接用 cylinder
            try:
                wp = cq.Workplane("XY").cylinder(length, radius, centered=(True, True, True))
                # 调整位置：圆柱中心在 X 方向中点
                center_x = (x_start + x_end) / 2.0
                wp = wp.translate((center_x, 0, 0))
                # 旋转到 X 轴方向（cylinder 默认沿 Z 轴）
                wp = wp.rotate((0, 0, 0), (0, 1, 0), 90)
            except Exception as e2:
                print(f"  错误: NREVOLUTION 降级也失败: {e2}", file=sys.stderr)
                return None
        
        wp = self._apply_transform(wp, rev)
        
        return wp
    
    def _build_extrusion(self, ext: NXtrusion):
        """构建拉伸切除体（三角棱柱）
        
        NXTRUSION 顶点在 X-Y 平面（Z=0），沿 +Z 方向拉伸 HEIG 高度。
        POS 定位拉伸的起始点（底部）。
        """
        cq = self.cq
        
        if len(ext.vertices) < 3:
            return None
        
        # 顶点在 X-Y 平面
        points_2d = [(v.x, v.y) for v in ext.vertices]
        
        # 去重
        if len(points_2d) > 1 and points_2d[0] == points_2d[-1]:
            points_2d = points_2d[:-1]
        
        if len(points_2d) < 3:
            return None
        
        try:
            # 从 Z=0 向 +Z 方向拉伸
            wp = (
                cq.Workplane("XY")
                .polyline(points_2d)
                .close()
                .extrude(ext.heig)
            )
        except Exception as e:
            print(f"  警告: NXTRUSION 构建失败: {e}", file=sys.stderr)
            return None
        
        # 拉伸从 Z=0 开始，向 +Z 方向延伸 heig
        # POS 是拉伸底部的位置（Z=0 处的基准点）
        wp = self._apply_transform(wp, ext)
        
        return wp
    
    def _build_child_local(self, child: Primitive, parent: Primitive):
        """
        在父图元的局部坐标系中构建子图元。
        子图元的 POS 是相对于父图元的。
        """
        # 构建子图元（它自己的变换已经包含了相对位置）
        # 因为子图元的 pos 是在父坐标系中的偏移
        child_solid = self._build_primitive_simple(child)
        return child_solid
    
    def _build_primitive_simple(self, prim: Primitive):
        """简单构建（不递归子图元），用于子图元构建"""
        cq = self.cq
        
        if isinstance(prim, NRevolution):
            return self._build_revolution_simple(prim)
        elif isinstance(prim, NXtrusion):
            return self._build_extrusion_simple(prim)
        else:
            return None
    
    def _build_revolution_simple(self, rev: NRevolution):
        """简单构建旋转体（含自身变换）—— 同 _build_revolution 逻辑"""
        return self._build_revolution(rev)
    
    def _build_extrusion_simple(self, ext: NXtrusion):
        """简单构建拉伸体（含自身变换）"""
        cq = self.cq
        
        if len(ext.vertices) < 3:
            return None
        
        points_2d = [(v.x, v.y) for v in ext.vertices]
        if len(points_2d) > 1 and points_2d[0] == points_2d[-1]:
            points_2d = points_2d[:-1]
        
        if len(points_2d) < 3:
            return None
        
        try:
            wp = (
                cq.Workplane("XY")
                .polyline(points_2d)
                .close()
                .extrude(ext.heig)
            )
        except Exception as e:
            print(f"  警告: NXTRUSION 构建失败: {e}", file=sys.stderr)
            return None
        
        # 拉伸从 Z=0 开始，向 +Z 方向延伸 heig
        # POS 是拉伸底部的位置（Z=0 处的基准点）
        wp = self._apply_transform(wp, ext)
        return wp


# ============================================================
# 导出函数
# ============================================================

def export_step(solid, output_path: str):
    """导出 STEP 文件"""
    import cadquery as cq
    cq.exporters.export(solid, output_path, exportType='STEP')


def export_stl(solid, output_path: str, tolerance: float = 0.1):
    """导出 STL 文件"""
    import cadquery as cq
    cq.exporters.export(solid, output_path, exportType='STL', tolerance=tolerance)


def export_dxf(solid, output_path: str):
    """
    导出 3D DXF 文件（3DFACE 三角网格）。
    使用 cadquery 内置网格化 + ezdxf 写入 3DFACE 实体。
    """
    try:
        import ezdxf
        from ezdxf import units
    except ImportError:
        print("  警告: 未安装 ezdxf，跳过 DXF 导出。pip install ezdxf", file=sys.stderr)
        return False
    
    try:
        # 使用 cadquery 的 tessellate 方法直接获取三角网格
        tolerance = 0.5
        # 从实体获取三角化结果
        faces = []
        # cadquery Workplane.val() 返回 TopoDS_Shape，用 tessellate
        shape = solid.val()
        vertices, triangles = shape.tessellate(tolerance)
        
        # triangles 是三角面的顶点索引列表
        # vertices 是 gp_Vec 或 Vector 对象，用 .x/.y/.z 访问
        for tri in triangles:
            if len(tri) >= 3:
                v0 = vertices[tri[0]]
                v1 = vertices[tri[1]]
                v2 = vertices[tri[2]]
                faces.append((
                    (v0.x, v0.y, v0.z),
                    (v1.x, v1.y, v1.z),
                    (v2.x, v2.y, v2.z),
                ))
        
        # 创建 DXF
        doc = ezdxf.new('R2010')
        doc.units = units.MM
        msp = doc.modelspace()
        
        # 用 3DFACE 写入三角网格
        for face in faces:
            msp.add_3dface(face)
        
        doc.saveas(output_path)
        return True
    except Exception as e:
        print(f"  警告: DXF 导出失败: {e}", file=sys.stderr)
        # 降级：尝试 STL 方式
        try:
            return _export_dxf_via_stl(solid, output_path)
        except Exception as e2:
            print(f"  警告: DXF 降级导出也失败: {e2}", file=sys.stderr)
            return False


def _export_dxf_via_stl(solid, output_path: str) -> bool:
    """降级方案：通过二进制 STL 导出 DXF"""
    import struct
    import tempfile
    import cadquery as cq
    import ezdxf
    from ezdxf import units
    
    tmp_stl = tempfile.mktemp(suffix='.stl')
    try:
        cq.exporters.export(solid, tmp_stl, exportType='STL', tolerance=0.5)
        
        # 读取二进制 STL
        faces = []
        with open(tmp_stl, 'rb') as f:
            header = f.read(80)
            num_faces = struct.unpack('<I', f.read(4))[0]
            for _ in range(num_faces):
                # normal (3 floats) + 3 vertices (9 floats) + attribute (1 uint16)
                data = struct.unpack('<12fH', f.read(50))
                v1 = (data[3], data[4], data[5])
                v2 = (data[6], data[7], data[8])
                v3 = (data[9], data[10], data[11])
                faces.append((v1, v2, v3))
        
        doc = ezdxf.new('R2010')
        doc.units = units.MM
        msp = doc.modelspace()
        for face in faces:
            msp.add_3dface(face)
        doc.saveas(output_path)
        return True
    finally:
        if os.path.exists(tmp_stl):
            os.remove(tmp_stl)


# ============================================================
# 验证与报告
# ============================================================

def validate_solid(solid, name: str) -> dict:
    """验证实体，返回验证报告"""
    import cadquery as cq
    
    report = {
        'name': name,
        'valid': False,
        'volume': 0.0,
        'bbox': None,
        'num_solids': 0,
    }
    
    try:
        # 获取实体数
        solids = solid.solids().vals()
        report['num_solids'] = len(solids)
        
        # 体积
        report['volume'] = solid.val().Volume()
        
        # 边界框
        bb = solid.val().BoundingBox()
        report['bbox'] = {
            'xmin': bb.xmin, 'xmax': bb.xmax,
            'ymin': bb.ymin, 'ymax': bb.ymax,
            'zmin': bb.zmin, 'zmax': bb.zmax,
            'xlen': bb.xmax - bb.xmin,
            'ylen': bb.ymax - bb.ymin,
            'zlen': bb.zmax - bb.zmin,
        }
        
        report['valid'] = True
    except Exception as e:
        report['error'] = str(e)
    
    return report


def print_validation_report(reports: List[dict]):
    """打印验证报告"""
    print("\n" + "=" * 70)
    print("  验证报告")
    print("=" * 70)
    
    for r in reports:
        print(f"\n  文件: {r['name']}")
        print(f"  有效: {'✓' if r['valid'] else '✗'}")
        if not r['valid']:
            print(f"  错误: {r.get('error', '未知')}")
            continue
        print(f"  实体数: {r['num_solids']}")
        print(f"  体积: {r['volume']:,.1f} mm³")
        if r['bbox']:
            b = r['bbox']
            print(f"  边界框:")
            print(f"    X: {b['xmin']:.2f} ~ {b['xmax']:.2f}  (长度 {b['xlen']:.2f})")
            print(f"    Y: {b['ymin']:.2f} ~ {b['ymax']:.2f}  (长度 {b['ylen']:.2f})")
            print(f"    Z: {b['zmin']:.2f} ~ {b['zmax']:.2f}  (长度 {b['zlen']:.2f})")


# ============================================================
# 主函数
# ============================================================

def convert_file(input_path: str, output_dir: str, formats: List[str], dry_run: bool = False) -> dict:
    """转换单个文件"""
    print(f"\n处理: {input_path}")
    
    # 解析
    parser = BocadParser()
    primitives = parser.parse(input_path)
    
    print(f"  解析到 {len(primitives)} 个顶层图元")
    for i, p in enumerate(primitives):
        print(f"    [{i}] {type(p).__name__} (子图元: {len(p.children)})")
        for j, c in enumerate(p.children):
            print(f"      [{j}] {type(c).__name__}")
    
    if dry_run:
        return {'primitives': primitives, 'outputs': {}}
    
    # 构建几何
    print("  构建几何...")
    builder = GeometryBuilder()
    solid = builder.build_assembly(primitives)
    
    if solid is None:
        print("  错误: 未能构建几何实体", file=sys.stderr)
        return {'primitives': primitives, 'outputs': {}, 'error': '构建失败'}
    
    # 验证
    basename = os.path.splitext(os.path.basename(input_path))[0]
    report = validate_solid(solid, basename)
    print(f"  体积: {report['volume']:,.1f} mm³")
    print(f"  实体数: {report['num_solids']}")
    
    # 导出
    os.makedirs(output_dir, exist_ok=True)
    outputs = {}
    
    if 'step' in formats:
        step_path = os.path.join(output_dir, basename + '.step')
        print(f"  导出 STEP: {step_path}")
        export_step(solid, step_path)
        outputs['step'] = step_path
    
    if 'stl' in formats:
        stl_path = os.path.join(output_dir, basename + '.stl')
        print(f"  导出 STL: {stl_path}")
        export_stl(solid, stl_path)
        outputs['stl'] = stl_path
    
    if 'dxf' in formats:
        dxf_path = os.path.join(output_dir, basename + '.dxf')
        print(f"  导出 DXF: {dxf_path}")
        export_dxf(solid, dxf_path)
        outputs['dxf'] = dxf_path
    
    return {
        'primitives': primitives,
        'solid': solid,
        'outputs': outputs,
        'report': report,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Bocad TXT 转换器 v19 - 将 Bocad .txt 转为 STEP/STL/DXF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python 紧固件转换器_v19.py --input M14x80-43.txt --format step,dxf,stl --output ./out
  python 紧固件转换器_v19.py --input ./txts/ --format step --output ./steps/
  python 紧固件转换器_v19.py --input M14x80-43.txt --dry-run
        """
    )
    parser.add_argument('--input', '-i', required=True, help='输入 .txt 文件或目录')
    parser.add_argument('--format', '-f', default='step,stl,dxf', 
                        help='输出格式，逗号分隔 (step,stl,dxf)，默认全部')
    parser.add_argument('--output', '-o', default='./output', help='输出目录，默认 ./output')
    parser.add_argument('--dry-run', action='store_true', help='仅解析不生成文件')
    
    args = parser.parse_args()
    
    formats = [f.strip().lower() for f in args.format.split(',')]
    valid_formats = {'step', 'stl', 'dxf'}
    formats = [f for f in formats if f in valid_formats]
    
    if not formats:
        print("错误: 没有有效的输出格式", file=sys.stderr)
        sys.exit(1)
    
    input_path = args.input
    output_dir = args.output
    
    # 收集输入文件
    input_files = []
    if os.path.isfile(input_path):
        input_files.append(input_path)
    elif os.path.isdir(input_path):
        for f in os.listdir(input_path):
            if f.lower().endswith('.txt'):
                input_files.append(os.path.join(input_path, f))
        input_files.sort()
    else:
        print(f"错误: 输入路径不存在: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    if not input_files:
        print("错误: 未找到 .txt 文件", file=sys.stderr)
        sys.exit(1)
    
    print(f"Bocad TXT 转换器 v19")
    print(f"输入文件数: {len(input_files)}")
    print(f"输出格式: {', '.join(formats)}")
    print(f"输出目录: {output_dir}")
    
    all_reports = []
    
    for f in input_files:
        result = convert_file(f, output_dir, formats, args.dry_run)
        if 'report' in result:
            all_reports.append(result['report'])
    
    if all_reports:
        print_validation_report(all_reports)
    
    print("\n完成!")


if __name__ == '__main__':
    main()
