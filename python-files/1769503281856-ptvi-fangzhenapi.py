from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response, FileResponse
from pydantic import BaseModel
from typing import List, Dict
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import base64
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ==================== PDF中文字体注册 ====================
CHINESE_FONT = None
font_candidates = [
    ("C:/Windows/Fonts/msyh.ttc", "msyh"),      # 微软雅黑
    ("C:/Windows/Fonts/simhei.ttf", "simhei"),   # 黑体
    ("C:/Windows/Fonts/simsun.ttc", "simsun"),   # 宋体
]

for font_path, font_name in font_candidates:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            CHINESE_FONT = font_name
            print(f"✅ PDF中文字体注册成功: {font_name}")
            break
        except Exception as e:
            print(f"⚠️ 字体 {font_name} 注册失败: {e}")
            continue

if CHINESE_FONT is None:
    print("⚠️ 警告：未找到中文字体，PDF可能显示乱码")
    CHINESE_FONT = "Helvetica"

# ==================== 1. 系统初始化 ====================
app = FastAPI(
    title="建筑结构仿真演进与加固分析系统",
    description="规范依据：GB 50011-2010 | GB 50010-2010 | GB 50367-2013 | GB/T 50476-2019 | ISO 9223:2012",
    version="1.0.0"
)

# 字体设置
font_path = "C:/Windows/Fonts/msyh.ttc"
if not os.path.exists(font_path):
    font_path = "C:/Windows/Fonts/simhei.ttf"
if not os.path.exists(font_path):
    font_path = None

my_font = None
if font_path:
    try:
        my_font = fm.FontProperties(fname=font_path)
        plt.rcParams['font.sans-serif'] = [my_font.get_name()]
        plt.rcParams['axes.unicode_minus'] = False
        # 注册PDF字体
        try:
            pdfmetrics.registerFont(TTFont('msyh', font_path))
        except:
            pass
    except:
        my_font = None

# 创建目录
for folder in ["图", "输出"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 任务存储
task_storage: Dict[str, dict] = {}

# ==================== 2. 规范参数库（已核实修正） ====================

# 结构类型 - GB 50011-2010 表5.5.1
structure_db = {
    "框架结构": {
        "factor": 1.5,
        "color": "#d62728",
        "drift_limit": "1/550",
        "basis": "GB 50011-2010 表5.5.1：钢筋混凝土框架弹性层间位移角限值[θe]=1/550",
        "weakness": "梁柱节点核心区",
        "description": "纯框架体系，侧向刚度较小，抗震变形能力要求高"
    },
    "框剪结构": {
        "factor": 1.0,
        "color": "#ff7f0e",
        "drift_limit": "1/800",
        "basis": "GB 50011-2010 表5.5.1：框架-抗震墙结构弹性层间位移角限值[θe]=1/800",
        "weakness": "连梁、墙肢底部加强区",
        "description": "框架与剪力墙协同工作，剪力墙提供主要抗侧刚度"
    },
    "框筒结构": {
        "factor": 0.6,
        "color": "#2ca02c",
        "drift_limit": "1/800",
        "basis": "GB 50011-2010 表5.5.1：框架-核心筒结构弹性层间位移角限值[θe]=1/800",
        "weakness": "角柱(剪力滞后效应)、外框架梁",
        "description": "空间刚度大，整体性强，核心筒承担主要水平力"
    }
}

# 地区环境 - ISO 9223:2012 表3
region_db = {
    "美国": {
        "factor": 1.0,
        "corrosion_class": "C3",
        "basis": "ISO 9223:2012 Table 3：C3级(中等腐蚀)，碳钢第一年腐蚀速率rcorr=25-50μm",
        "Cl_deposit": "<60 mg/(m²·d)",
        "description": "温带内陆气候，大气腐蚀性中等"
    },
    "日本": {
        "factor": 1.2,
        "corrosion_class": "C4",
        "basis": "ISO 9223:2012 Table 3：C4级(高腐蚀)，碳钢第一年腐蚀速率rcorr=50-80μm",
        "Cl_deposit": "60-300 mg/(m²·d)",
        "description": "海洋性气候，盐雾侵蚀显著，氯离子沉积量较高"
    },
    "台湾": {
        "factor": 1.4,
        "corrosion_class": "C5",
        "basis": "ISO 9223:2012 Table 3：C5级(很高腐蚀)，碳钢第一年腐蚀速率rcorr=80-200μm",
        "Cl_deposit": ">300 mg/(m²·d)",
        "description": "热带海洋气候，高温高湿，台风频繁，腐蚀环境严酷"
    }
}

# 构件参数 - GB 50010-2010
component_db = {
    "梁": {
        "crack_limit": 0.3,
        "deflection_limit": "l0/200（l0≤7m时）或l0/250（l0>7m时）",
        "cover": 25,
        "basis": "GB 50010-2010 表3.4.5：一类环境钢筋混凝土构件最大裂缝宽度限值ωlim=0.3mm；表3.4.3：受弯构件挠度限值",
        "weight": 1.0,
        "damage_mode": "正截面受弯破坏、斜截面受剪破坏、梁端塑性铰"
    },
    "板": {
        "crack_limit": 0.3,
        "deflection_limit": "l0/200（l0≤7m时）或l0/250（l0>7m时）",
        "cover": 20,
        "basis": "GB 50010-2010 表3.4.5：一类环境钢筋混凝土构件最大裂缝宽度限值ωlim=0.3mm；表3.4.3：受弯构件挠度限值",
        "weight": 0.8,
        "damage_mode": "受弯破坏、冲切破坏、板角斜裂缝"
    },
    "柱": {
        "crack_limit": "受压为主时可不验算",
        "deflection_limit": "H/1000",
        "cover": 30,
        "basis": "GB 50010-2010 第3.4.4条：对轴心受压和小偏心受压构件，可不验算裂缝宽度；如需验算按表3.4.5取0.3mm",
        "weight": 1.2,
        "damage_mode": "大偏心受压破坏、小偏心受压破坏、剪切斜拉破坏"
    }
}

# 加固方法库 - GB 50367-2013
reinforcement_method_db = {
    "增大截面加固法": {
        "code": "ZD",
        "chapter": "GB 50367-2013 第7章",
        "efficiency": 0.85,
        "cost_ratio": 1.0,
        "duration": "21-42天",
        "score_boost": {"梁": 8.5, "板": 7.5, "柱": 10.0},
        "principle": "在原构件外部增浇混凝土并增配钢筋，通过增大截面面积和配筋量提高承载力",
        "material": "第7.2.2条：新增混凝土强度等级不应低于C30，且应比原构件提高一级；第7.2.3条：新增受力钢筋宜采用HRB400、HRB500级钢筋",
        "requirement": "第7.3.7条：柱外包加固层厚度不应小于60mm；第7.3.4条：新旧混凝土结合面凿毛深度不应小于6mm",
        "advantage": "承载力提升幅度大(可达40-100%)、耐久性好、造价相对较低、技术成熟",
        "disadvantage": "增加结构自重(约5-15%)、减少建筑使用空间、施工周期长、湿作业",
        "formula": "第7.2.5条：加固后受弯承载力计算，新增钢筋参与受力",
        "quality_check": "GB 50550-2010 第5章：增大截面加固工程验收"
    },
    "粘贴碳纤维布法": {
        "code": "CF",
        "chapter": "GB 50367-2013 第12章",
        "efficiency": 0.82,
        "cost_ratio": 1.8,
        "duration": "7-21天",
        "score_boost": {"梁": 7.8, "板": 7.2, "柱": 8.0},
        "principle": "利用结构胶将碳纤维布(CFRP)粘贴于混凝土构件表面，借助碳纤维的高抗拉强度提高构件承载力",
        "material": "表12.2.2：碳纤维布应为I级，抗拉强度标准值ftk≥3400MPa，弹性模量Ef≥2.4×10^5MPa；第12.2.4条：浸渍胶应为A级结构胶",
        "requirement": "表12.2.1：碳纤维布单层计算厚度0.111-0.167mm；第12.2.3条：多层粘贴时应分层进行，各层之间应搭接；端部应设置可靠锚固措施",
        "advantage": "自重极轻(<1%)、耐腐蚀性好、施工快捷便利、基本不改变构件外观尺寸",
        "disadvantage": "材料造价较高、长期耐久性能有待验证、需采取防火措施(使用环境温度不应超过60°C)",
        "formula": "第12.3.3条：受弯加固时，正截面承载力计算应考虑二次受力的应变滞后影响",
        "quality_check": "CECS 146:2003 第8章：碳纤维片材加固工程验收"
    },
    "外粘型钢加固法": {
        "code": "WG",
        "chapter": "GB 50367-2013 第10章",
        "efficiency": 0.88,
        "cost_ratio": 1.5,
        "duration": "14-35天",
        "score_boost": {"梁": 8.0, "板": 5.5, "柱": 9.5},
        "principle": "在混凝土构件四周包以型钢(角钢或槽钢)，通过缀板焊接连接形成整体，与原构件共同受力",
        "material": "第10.2.2条：型钢宜采用Q235钢或Q345钢；型钢与混凝土之间应采用改性环氧树脂胶粘剂或灌注水泥砂浆",
        "requirement": "第10.3.5条：缀板的间距，对柱不应大于角钢截面短边回转半径的20倍；第10.3.6条：型钢端部应可靠锚入楼板或基础",
        "advantage": "承载力提升幅度大(可达50-150%)、构件延性明显改善、受力机理明确可靠",
        "disadvantage": "需进行防腐处理(使用寿命15-25年)、需采取防火措施、节点构造较复杂、自重增加较多",
        "formula": "第10.2.5条：正截面受弯承载力计算，型钢按全截面计入",
        "quality_check": "GB 50550-2010 第9章：外粘型钢加固工程验收"
    }
}

# 9种组合详细参数
reinforcement_matrix = {
    ("梁", "增大截面加固法"): {
        "detail": "梁底或梁侧增大截面，新增受力纵筋应可靠锚入支座；可采用三面或四面外包形式",
        "ref": "第7.3.1~7.3.4条"
    },
    ("梁", "粘贴碳纤维布法"): {
        "detail": "梁底纵向粘贴碳纤维布用于受弯加固，梁侧面斜向或垂直粘贴用于受剪加固，端部采用U型箍或纤维布锚固",
        "ref": "第12.3.1~12.3.6条"
    },
    ("梁", "外粘型钢加固法"): {
        "detail": "梁底粘贴钢板或角钢提高受弯承载力，需设置端部锚固螺栓，钢板厚度不宜大于6mm",
        "ref": "第10.3.1~10.3.4条"
    },
    ("板", "增大截面加固法"): {
        "detail": "板底增设混凝土加厚层和钢筋网片，加厚层厚度不宜小于40mm，采用植筋或锚栓与原板连接",
        "ref": "第7.3.5条"
    },
    ("板", "粘贴碳纤维布法"): {
        "detail": "板底粘贴碳纤维布条带，条带沿受力方向布置，宽度宜为100-300mm",
        "ref": "第12.3.7条"
    },
    ("板", "外粘型钢加固法"): {
        "detail": "板底粘贴扁钢条带加固，此方法对板类构件适用性相对较低，一般优先采用碳纤维布法",
        "ref": "第10.3条（参照执行）"
    },
    ("柱", "增大截面加固法"): {
        "detail": "柱四周增设钢筋混凝土外套，外套厚度不应小于60mm，新增纵筋不应少于4根直径14mm，箍筋间距不应大于100mm",
        "ref": "第7.3.6~7.3.9条"
    },
    ("柱", "粘贴碳纤维布法"): {
        "detail": "柱身采用碳纤维布环向缠绕约束，可有效提高柱的延性和轴压承载力，环向粘贴层数不宜少于2层",
        "ref": "第12.3.8~12.3.10条"
    },
    ("柱", "外粘型钢加固法"): {
        "detail": "柱四角包裹角钢，采用缀板焊接连接形成封闭箍，角钢截面面积不宜小于柱截面面积的3%",
        "ref": "第10.3.5~10.3.8条"
    }
}

# 碳化参数 - GB/T 50476-2019 附录A
carbonation_params = {
    "K_base": 2.5,
    "basis": "GB/T 50476-2019 附录A式(A.0.1-1)：碳化深度xc=Kco2·√(t)。碳化系数K由式(A.0.1-2)计算，与混凝土强度、水灰比、环境湿度、CO2浓度等因素相关。本仿真取C30混凝土标准条件下的简化参考值K≈2.5mm/√(year)",
    "humidity_note": "式(A.0.2-1)：相对湿度影响系数，当RH=50-70%时碳化速率最快；RH过低(<40%)或过高(>80%)时碳化速率降低",
    "temperature_note": "碳化反应为化学过程，温度影响遵循Arrhenius方程，温度每升高10°C，碳化速率约增加30%"
}

# 评级阈值 - 参考GB 50292-2015
grade_thresholds = {
    "A": {"min": 96, "desc": "安全性符合国家现行设计规范要求，相当于a级构件"},
    "B": {"min": 90, "desc": "安全性略低于国家现行设计规范要求，相当于b级构件"},
    "C": {"min": 85, "desc": "安全性不符合国家现行设计规范要求，相当于c级构件"},
    "D": {"min": 0, "desc": "安全性严重不符合国家现行设计规范要求，相当于d级构件"},
    "basis": "评分阈值参考GB 50292-2015第4.2节构件安全性a/b/c/d四级评定原则设计。规范为定性评级，本仿真将其量化为百分制（A≥96/B≥90/C≥85/D<85）以便于趋势展示，具体阈值为模型简化处理"
}

# ==================== 3. 数据模型 ====================

class EnvironmentData(BaseModel):
    temperature: List[float]
    rainfall: List[float]
    humidity: List[float]

class SimulationRequest(BaseModel):
    taskid: str
    region: str
    structure: str
    environment: EnvironmentData

class ReinforcementRequest(BaseModel):
    taskid: str
    component: str
    method: str

class SimulationResponse(BaseModel):
    taskid: str
    scores: List[float]
    final_score: float
    grade: str
    grade_desc: str
    carb_depth: float
    need_reinforce: bool
    message: str

class ReinforcementResponse(BaseModel):
    taskid: str
    component: str
    method: str
    original_score: float
    new_score: float
    boost: float
    efficiency: float
    cost_ratio: float
    duration: str
    future_scores: List[float]
    detail: dict

class CompareResponse(BaseModel):
    taskid: str
    original_score: float
    comparisons: List[dict]

# ==================== 4. 计算函数 ====================

def run_simulation(temp_list, rain_list, hum_list, region, struct):
    """混凝土结构耐久性演化仿真 - 依据GB/T 50476-2019"""
    k_struct = structure_db[struct]["factor"]
    k_region = region_db[region]["factor"]
    K_base = carbonation_params["K_base"]
    
    scores = []
    score = 100.0
    carb_depth = 0.0
    
    for year in range(7):
        T, R, H = temp_list[year], rain_list[year], hum_list[year]
        
        # 湿度影响系数 - GB/T 50476-2019 式(A.0.2-1)
        if 50 <= H <= 70:
            k_RH = 1.0
        elif H < 50:
            k_RH = 0.5 + H / 100
        else:
            k_RH = 1.0 - (H - 70) / 60
        k_RH = max(0.3, min(1.0, k_RH))
        
        # 温度影响 - Arrhenius方程简化
        k_T = max(0.7, min(1.5, 1.0 + 0.03 * (T - 20)))
        
        # 碳化增量
        K_carb = K_base * k_RH * k_T * k_region
        delta_carb = K_carb / np.sqrt(year + 1)
        carb_depth += delta_carb
        
        # 降雨影响
        rain_effect = (R / 1000) * 0.2 * k_region
        
        # 年度衰减
        year_decay = (0.1 + delta_carb * 0.1 + rain_effect) * k_struct
        score = max(50, score - year_decay)
        scores.append(round(float(score), 2))
    
    return scores, round(float(carb_depth), 2)


def calculate_reinforcement(score, component, method, struct, carb_depth):
    """计算加固效果 - 依据GB 50367-2013"""
    m_db = reinforcement_method_db[method]
    c_db = component_db[component]
    
    base_boost = m_db["score_boost"][component]
    eff = m_db["efficiency"]
    struct_adj = structure_db[struct]["factor"] / 1.2
    carb_penalty = max(0.7, 1.0 - carb_depth * 0.01)
    weight = c_db["weight"]
    
    boost = base_boost * eff * struct_adj * carb_penalty * weight
    new_score = min(99, score + boost)
    
    future = []
    temp = new_score
    for _ in range(3):
        temp -= 0.25 * (1 - eff * 0.6)
        future.append(round(float(temp), 2))
    
    return {
        "new_score": round(float(new_score), 2),
        "boost": round(float(boost), 2),
        "efficiency": float(eff),
        "future": future,
        "cost_ratio": float(m_db["cost_ratio"]),
        "duration": m_db["duration"]
    }


def get_grade(score):
    """获取评级 - 参考GB 50292-2015"""
    if score >= 96:
        return "A", grade_thresholds["A"]["desc"]
    elif score >= 90:
        return "B", grade_thresholds["B"]["desc"]
    elif score >= 85:
        return "C", grade_thresholds["C"]["desc"]
    else:
        return "D", grade_thresholds["D"]["desc"]


def create_chart_bytes(scores, region, struct, reinforce_data=None):
    """生成图表并返回PNG字节数据"""
    try:
        plt.close('all')
        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        
        years = list(range(1, 8))
        color = structure_db[struct]["color"]
        
        ax.plot(years, scores, 'o-', linewidth=2.5, color=color,
                label=f'{struct}演进', markersize=8, markerfacecolor='white', markeredgewidth=2)
        
        if reinforce_data:
            r_years = [7, 8, 9, 10]
            r_scores = [reinforce_data["new_score"]] + reinforce_data["future"]
            ax.plot(r_years, r_scores, 's--', linewidth=2.5, color='#2e7d32',
                    label='加固后预测', markersize=8, markerfacecolor='white', markeredgewidth=2)
            
            mid_y = (scores[-1] + reinforce_data["new_score"]) / 2
            ax.annotate(f'+{reinforce_data["boost"]:.1f}',
                       xy=(7.3, mid_y), fontsize=12, color='#2e7d32', fontweight='bold',
                       fontproperties=my_font if my_font else None)
        
        # 等级区间
        ax.axhspan(96, 100, alpha=0.15, color='#4caf50', label='A级(≥96)')
        ax.axhspan(90, 96, alpha=0.15, color='#2196f3', label='B级(90-96)')
        ax.axhspan(85, 90, alpha=0.15, color='#ff9800', label='C级(85-90)')
        ax.axhspan(50, 85, alpha=0.15, color='#f44336', label='D级(<85)')
        
        ax.axhline(95, color='#9c27b0', linestyle='--', alpha=0.7, linewidth=1.5, label='加固建议线(95)')
        
        x_max = 10.5 if reinforce_data else 7.5
        y_min = min(78, min(scores) - 5)
        ax.set_xlim(0.5, x_max)
        ax.set_ylim(y_min, 101)
        
        if my_font:
            ax.set_xlabel('服役年限(年)', fontproperties=my_font, fontsize=12)
            ax.set_ylabel('性能评分', fontproperties=my_font, fontsize=12)
            ax.set_title(f'【{region} - {struct}】结构性能演进曲线', fontproperties=my_font, fontsize=14, fontweight='bold')
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontproperties(my_font)
            ax.legend(loc='lower left', fontsize=9, prop=my_font)
        else:
            ax.set_xlabel('Service Years', fontsize=12)
            ax.set_ylabel('Performance Score', fontsize=12)
            ax.set_title(f'[{region} - {struct}] Structural Performance', fontsize=14, fontweight='bold')
            ax.legend(loc='lower left', fontsize=9)
        
        ax.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()
        
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        png_bytes = buffer.getvalue()
        
        plt.close(fig)
        buffer.close()
        
        return png_bytes
    except Exception as e:
        print(f"图表生成错误: {e}")
        return None


def create_pdf_report(taskid: str, task: dict) -> bytes:
    """生成PDF报告 - 修复中文乱码"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=20*mm, 
        leftMargin=20*mm,
        topMargin=20*mm, 
        bottomMargin=20*mm
    )
    
    # 创建中文样式
    styles = getSampleStyleSheet()
    
    # 标题样式
    title_style = ParagraphStyle(
        'ChineseTitle',
        fontName=CHINESE_FONT,
        fontSize=18,
        leading=24,
        alignment=1,  # 居中
        spaceAfter=20,
        textColor=colors.HexColor('#1565c0')
    )
    
    # 一级标题样式
    heading1_style = ParagraphStyle(
        'ChineseHeading1',
        fontName=CHINESE_FONT,
        fontSize=14,
        leading=20,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.HexColor('#1976d2')
    )
    
    # 二级标题样式
    heading2_style = ParagraphStyle(
        'ChineseHeading2',
        fontName=CHINESE_FONT,
        fontSize=12,
        leading=18,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.HexColor('#424242')
    )
    
    # 正文样式
    normal_style = ParagraphStyle(
        'ChineseNormal',
        fontName=CHINESE_FONT,
        fontSize=10,
        leading=16,
        spaceAfter=6
    )
    
    # 表格内文字样式（用于Paragraph）
    table_style = ParagraphStyle(
        'TableCell',
        fontName=CHINESE_FONT,
        fontSize=9,
        leading=14,
        alignment=1  # 居中
    )
    
    story = []
    
    # ========== 标题 ==========
    story.append(Paragraph("结构性能仿真分析报告", title_style))
    story.append(Spacer(1, 10))
    
    # ========== 一、工程基本信息 ==========
    story.append(Paragraph("一、工程基本信息", heading1_style))
    
    basic_data = [
        [Paragraph("项目", table_style), Paragraph("内容", table_style)],
        [Paragraph("任务ID", table_style), Paragraph(taskid, table_style)],
        [Paragraph("地区", table_style), Paragraph(task["region"], table_style)],
        [Paragraph("结构类型", table_style), Paragraph(task["structure"], table_style)],
        [Paragraph("仿真周期", table_style), Paragraph("7年", table_style)]
    ]
    
    basic_table = Table(basic_data, colWidths=[75*mm, 85*mm])
    basic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(basic_table)
    story.append(Spacer(1, 15))
    
    # ========== 二、评估结果 ==========
    story.append(Paragraph("二、评估结果", heading1_style))
    
    result_data = [
        [Paragraph("项目", table_style), Paragraph("结果", table_style)],
        [Paragraph("最终评分", table_style), Paragraph(f"{task['final_score']:.2f} 分", table_style)],
        [Paragraph("安全等级", table_style), Paragraph(f"{task['grade']}级", table_style)],
        [Paragraph("等级说明", table_style), Paragraph(task['grade_desc'], table_style)],
        [Paragraph("碳化深度", table_style), Paragraph(f"{task['carb_depth']:.2f} mm", table_style)],
        [Paragraph("是否需要加固", table_style), Paragraph("是" if task['need_reinforce'] else "否", table_style)]
    ]
    
    result_table = Table(result_data, colWidths=[75*mm, 85*mm])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 15))
    
    # ========== 三、逐年演进数据 ==========
    story.append(Paragraph("三、逐年演进数据", heading1_style))
    
    yearly_data = [[
        Paragraph("年份", table_style), 
        Paragraph("评分", table_style), 
        Paragraph("等级", table_style)
    ]]
    for i, s in enumerate(task["scores"]):
        g, _ = get_grade(s)
        yearly_data.append([
            Paragraph(f"第{i+1}年", table_style),
            Paragraph(f"{s:.2f}", table_style),
            Paragraph(f"{g}级", table_style)
        ])
    
    yearly_table = Table(yearly_data, colWidths=[50*mm, 55*mm, 55*mm])
    yearly_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(yearly_table)
    story.append(Spacer(1, 15))
    
    # ========== 四、环境参数统计 ==========
    story.append(Paragraph("四、环境参数统计", heading1_style))
    
    env = task["environment"]
    env_data = [
        [Paragraph("参数", table_style), Paragraph("平均值", table_style), Paragraph("范围", table_style)],
        [
            Paragraph("温度(°C)", table_style), 
            Paragraph(f"{np.mean(env['temperature']):.1f}", table_style),
            Paragraph(f"{min(env['temperature']):.0f} ~ {max(env['temperature']):.0f}", table_style)
        ],
        [
            Paragraph("降雨(mm)", table_style), 
            Paragraph(f"{np.mean(env['rainfall']):.0f}", table_style),
            Paragraph(f"{min(env['rainfall']):.0f} ~ {max(env['rainfall']):.0f}", table_style)
        ],
        [
            Paragraph("湿度(%)", table_style), 
            Paragraph(f"{np.mean(env['humidity']):.1f}", table_style),
            Paragraph(f"{min(env['humidity']):.0f} ~ {max(env['humidity']):.0f}", table_style)
        ]
    ]
    
    env_table = Table(env_data, colWidths=[50*mm, 55*mm, 55*mm])
    env_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(env_table)
    story.append(Spacer(1, 15))
    
    # ========== 五、结构分析 ==========
    story.append(Paragraph("五、结构分析", heading1_style))
    
    s_db = structure_db[task["structure"]]
    r_db = region_db[task["region"]]
    
    struct_data = [
        [Paragraph("项目", table_style), Paragraph("内容", table_style)],
        [Paragraph("层间位移角限值", table_style), Paragraph(s_db['drift_limit'], table_style)],
        [Paragraph("薄弱部位", table_style), Paragraph(s_db['weakness'], table_style)],
        [Paragraph("结构特点", table_style), Paragraph(s_db['description'], table_style)],
        [Paragraph("规范依据", table_style), Paragraph(s_db['basis'], table_style)],
    ]
    
    struct_table = Table(struct_data, colWidths=[75*mm, 85*mm])
    struct_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(struct_table)
    story.append(Spacer(1, 15))
    
    # ========== 六、地区环境因素 ==========
    story.append(Paragraph("六、地区环境因素", heading1_style))
    
    region_data = [
        [Paragraph("项目", table_style), Paragraph("内容", table_style)],
        [Paragraph("大气腐蚀等级", table_style), Paragraph(r_db['corrosion_class'], table_style)],
        [Paragraph("氯离子沉积量", table_style), Paragraph(r_db['Cl_deposit'], table_style)],
        [Paragraph("环境描述", table_style), Paragraph(r_db['description'], table_style)],
        [Paragraph("规范依据", table_style), Paragraph(r_db['basis'], table_style)],
    ]
    
    region_table = Table(region_data, colWidths=[75*mm, 85*mm])
    region_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565c0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(region_table)
    story.append(Spacer(1, 15))
    
    # ========== 七、加固方案（如果有） ==========
    if task["reinforcement"]:
        story.append(Paragraph("七、加固方案", heading1_style))
        
        r = task["reinforcement"]
        m_db = reinforcement_method_db[r["method"]]
        matrix = reinforcement_matrix[(r["component"], r["method"])]
        
        reinforce_data = [
            [Paragraph("项目", table_style), Paragraph("内容", table_style)],
            [Paragraph("构件", table_style), Paragraph(r['component'], table_style)],
            [Paragraph("方法", table_style), Paragraph(r['method'], table_style)],
            [Paragraph("规范依据", table_style), Paragraph(m_db['chapter'], table_style)],
            [Paragraph("评分提升", table_style), 
             Paragraph(f"{task['final_score']:.1f} → {r['result']['new_score']:.1f} (+{r['result']['boost']:.1f})", table_style)],
            [Paragraph("加固效率", table_style), Paragraph(f"{r['result']['efficiency']*100:.0f}%", table_style)],
            [Paragraph("成本系数", table_style), Paragraph(str(r['result']['cost_ratio']), table_style)],
            [Paragraph("施工工期", table_style), Paragraph(r['result']['duration'], table_style)],
        ]
        
        reinforce_table = Table(reinforce_data, colWidths=[75*mm, 85*mm])
        reinforce_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#e8f5e9')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(reinforce_table)
        story.append(Spacer(1, 10))
        
        # 技术说明
        story.append(Paragraph("技术说明", heading2_style))
        story.append(Paragraph(f"<b>加固原理：</b>{m_db['principle']}", normal_style))
        story.append(Paragraph(f"<b>材料要求：</b>{m_db['material']}", normal_style))
        story.append(Paragraph(f"<b>施工要点：</b>{m_db['requirement']}", normal_style))
        story.append(Paragraph(f"<b>构造说明：</b>{matrix['detail']}（{matrix['ref']}）", normal_style))
        story.append(Paragraph(f"<b>验收标准：</b>{m_db['quality_check']}", normal_style))
        story.append(Spacer(1, 15))
    
    # ========== 规范引用 ==========
    section_num = "八" if task["reinforcement"] else "七"
    story.append(Paragraph(f"{section_num}、规范引用", heading1_style))
    
    standards = [
        "• GB 50011-2010 建筑抗震设计规范",
        "• GB 50010-2010 混凝土结构设计规范",
        "• GB 50367-2013 混凝土结构加固设计规范",
        "• GB/T 50476-2019 混凝土结构耐久性设计标准",
        "• GB 50292-2015 民用建筑可靠性鉴定标准",
        "• GB 50550-2010 建筑结构加固工程施工质量验收规范",
        "• ISO 9223:2012 大气腐蚀性分类",
        "• CECS 146:2003 碳纤维片材加固混凝土结构技术规程"
    ]
    
    for std in standards:
        story.append(Paragraph(std, normal_style))
    
    # 生成PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==================== 5. API 接口 ====================

@app.get("/")
async def root():
    """首页"""
    return {
        "title": "建筑结构仿真演进与加固分析系统",
        "version": "1.0.0",
        "standards": [
            "GB 50011-2010",
            "GB 50010-2010", 
            "GB 50367-2013",
            "GB/T 50476-2019",
            "ISO 9223:2012"
        ],
        "endpoints": {
            "options": "GET /options - 获取可选参数",
            "simulate": "POST /simulate - 运行仿真",
            "reinforce": "POST /reinforce - 计算加固效果",
            "compare": "GET /compare/{taskid} - 9种方案对比",
            "chart": "GET /chart/{taskid} - 获取演进曲线图(PNG)",
            "report": "GET /report/{taskid} - 获取分析报告(PDF)",
            "images": "GET /images/{taskid}/{index} - 获取施工图示(PNG)",
            "tasks": "GET /tasks - 列出所有任务"
        }
    }


@app.get("/options")
async def get_options():
    """获取可选参数"""
    return {
        "regions": list(region_db.keys()),
        "structures": list(structure_db.keys()),
        "components": list(component_db.keys()),
        "methods": list(reinforcement_method_db.keys()),
        "region_details": region_db,
        "structure_details": structure_db,
        "component_details": component_db,
        "method_details": reinforcement_method_db
    }


@app.post("/simulate", response_model=SimulationResponse)
async def simulate(request: SimulationRequest):
    """运行演进仿真"""
    if request.region not in region_db:
        raise HTTPException(status_code=400, detail=f"无效的地区，可选：{list(region_db.keys())}")
    if request.structure not in structure_db:
        raise HTTPException(status_code=400, detail=f"无效的结构类型，可选：{list(structure_db.keys())}")
    if len(request.environment.temperature) != 7:
        raise HTTPException(status_code=400, detail="温度数据必须为7年")
    if len(request.environment.rainfall) != 7:
        raise HTTPException(status_code=400, detail="降雨数据必须为7年")
    if len(request.environment.humidity) != 7:
        raise HTTPException(status_code=400, detail="湿度数据必须为7年")
    
    scores, carb_depth = run_simulation(
        request.environment.temperature,
        request.environment.rainfall,
        request.environment.humidity,
        request.region,
        request.structure
    )
    
    final_score = float(scores[-1])
    grade, grade_desc = get_grade(final_score)
    need_reinforce = bool(final_score < 95)
    
    task_storage[request.taskid] = {
        "region": request.region,
        "structure": request.structure,
        "environment": request.environment.model_dump(),
        "scores": scores,
        "carb_depth": carb_depth,
        "final_score": final_score,
        "grade": grade,
        "grade_desc": grade_desc,
        "need_reinforce": need_reinforce,
        "reinforcement": None
    }
    
    message = "结构状态良好，暂不需要加固" if not need_reinforce else "建议进行结构加固，请调用 /reinforce 或 /compare 接口"
    
    return SimulationResponse(
        taskid=request.taskid,
        scores=scores,
        final_score=final_score,
        grade=grade,
        grade_desc=grade_desc,
        carb_depth=carb_depth,
        need_reinforce=need_reinforce,
        message=message
    )


@app.post("/reinforce", response_model=ReinforcementResponse)
async def reinforce(request: ReinforcementRequest):
    """计算加固效果"""
    if request.taskid not in task_storage:
        raise HTTPException(status_code=404, detail="任务不存在，请先调用 /simulate")
    if request.component not in component_db:
        raise HTTPException(status_code=400, detail=f"无效的构件，可选：{list(component_db.keys())}")
    if request.method not in reinforcement_method_db:
        raise HTTPException(status_code=400, detail=f"无效的加固方法，可选：{list(reinforcement_method_db.keys())}")
    
    task = task_storage[request.taskid]
    
    result = calculate_reinforcement(
        task["final_score"],
        request.component,
        request.method,
        task["structure"],
        task["carb_depth"]
    )
    
    m_db = reinforcement_method_db[request.method]
    matrix = reinforcement_matrix[(request.component, request.method)]
    
    detail = {
        "chapter": m_db["chapter"],
        "principle": m_db["principle"],
        "material": m_db["material"],
        "requirement": m_db["requirement"],
        "advantage": m_db["advantage"],
        "disadvantage": m_db["disadvantage"],
        "formula": m_db["formula"],
        "quality_check": m_db["quality_check"],
        "construction_detail": matrix["detail"],
        "reference": matrix["ref"]
    }
    
    task_storage[request.taskid]["reinforcement"] = {
        "component": request.component,
        "method": request.method,
        "result": result
    }
    
    return ReinforcementResponse(
        taskid=request.taskid,
        component=request.component,
        method=request.method,
        original_score=task["final_score"],
        new_score=result["new_score"],
        boost=result["boost"],
        efficiency=result["efficiency"],
        cost_ratio=result["cost_ratio"],
        duration=result["duration"],
        future_scores=result["future"],
        detail=detail
    )


@app.get("/compare/{taskid}", response_model=CompareResponse)
async def compare_all(taskid: str):
    """获取9种加固方案对比"""
    if taskid not in task_storage:
        raise HTTPException(status_code=404, detail="任务不存在，请先调用 /simulate")
    
    task = task_storage[taskid]
    comparisons = []
    
    for comp in ["梁", "板", "柱"]:
        for method in reinforcement_method_db.keys():
            result = calculate_reinforcement(
                task["final_score"], comp, method,
                task["structure"], task["carb_depth"]
            )
            m_db = reinforcement_method_db[method]
            matrix = reinforcement_matrix[(comp, method)]
            
            comparisons.append({
                "component": comp,
                "method": method,
                "chapter": m_db["chapter"],
                "original_score": task["final_score"],
                "new_score": result["new_score"],
                "boost": result["boost"],
                "efficiency": result["efficiency"],
                "cost_ratio": result["cost_ratio"],
                "duration": result["duration"],
                "future_3year": result["future"][2],
                "detail": matrix["detail"],
                "reference": matrix["ref"]
            })
    
    comparisons.sort(key=lambda x: x["boost"], reverse=True)
    for i, comp in enumerate(comparisons):
        comp["rank"] = i + 1
    
    return CompareResponse(
        taskid=taskid,
        original_score=task["final_score"],
        comparisons=comparisons
    )


@app.get("/chart/{taskid}")
async def get_chart(taskid: str):
    """获取演进曲线图 - 返回PNG图片"""
    if taskid not in task_storage:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = task_storage[taskid]
    
    reinforce_data = None
    if task["reinforcement"]:
        reinforce_data = task["reinforcement"]["result"]
    
    png_bytes = create_chart_bytes(
        task["scores"], task["region"], task["structure"], reinforce_data
    )
    
    if png_bytes is None:
        raise HTTPException(status_code=500, detail="图表生成失败")
    
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f"inline; filename=chart_{taskid}.png"
        }
    )


@app.get("/report/{taskid}")
async def get_report(taskid: str):
    """获取详细分析报告 - 返回PDF文件"""
    if taskid not in task_storage:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = task_storage[taskid]
    
    try:
        pdf_bytes = create_pdf_report(taskid, task)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=report_{taskid}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")


@app.get("/images/{taskid}/{index}")
async def get_image(taskid: str, index: int):
    """获取加固施工图示 - 返回PNG图片
    
    index: 1=损伤前, 2=损伤后, 3=加固中, 4=加固完成
    """
    if taskid not in task_storage:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = task_storage[taskid]
    
    if not task["reinforcement"]:
        raise HTTPException(status_code=400, detail="尚未选择加固方案，请先调用 POST /reinforce")
    
    if index not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="index必须为1-4，分别代表：1=损伤前, 2=损伤后, 3=加固中, 4=加固完成")
    
    r = task["reinforcement"]
    comp = r["component"]
    method = r["method"]
    code = reinforcement_method_db[method]["code"]
    
    filename = f"{comp}{code}{index}.png"
    filepath = os.path.join("图", filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"图片文件不存在: {filename}")
    
    return FileResponse(
        path=filepath,
        media_type="image/png",
        filename=filename
    )


@app.get("/images/{taskid}")
async def get_all_images_info(taskid: str):
    """获取所有施工图示的信息"""
    if taskid not in task_storage:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = task_storage[taskid]
    
    if not task["reinforcement"]:
        raise HTTPException(status_code=400, detail="尚未选择加固方案，请先调用 POST /reinforce")
    
    r = task["reinforcement"]
    comp = r["component"]
    method = r["method"]
    code = reinforcement_method_db[method]["code"]
    
    images = []
    titles = ["损伤前状态", "损伤后状态", "加固施工中", "加固完成"]
    
    for i in range(1, 5):
        filename = f"{comp}{code}{i}.png"
        filepath = os.path.join("图", filename)
        images.append({
            "index": i,
            "title": titles[i-1],
            "filename": filename,
            "exists": os.path.exists(filepath),
            "url": f"/images/{taskid}/{i}"
        })
    
    return {
        "taskid": taskid,
        "component": comp,
        "method": method,
        "images": images
    }


@app.get("/task/{taskid}")
async def get_task(taskid: str):
    """获取任务详情"""
    if taskid not in task_storage:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 转换numpy类型
    def convert_numpy_types(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        elif isinstance(obj, (np.bool_, np.bool8)):
            return bool(obj)
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    return convert_numpy_types(task_storage[taskid])


@app.delete("/task/{taskid}")
async def delete_task(taskid: str):
    """删除任务"""
    if taskid not in task_storage:
        raise HTTPException(status_code=404, detail="任务不存在")
    del task_storage[taskid]
    return {"message": f"任务 {taskid} 已删除"}


@app.get("/tasks")
async def list_tasks():
    """列出所有任务"""
    return {
        "total": len(task_storage),
        "tasks": [
            {
                "taskid": tid,
                "region": data["region"],
                "structure": data["structure"],
                "final_score": float(data["final_score"]),
                "grade": data["grade"],
                "need_reinforce": bool(data["need_reinforce"]),
                "has_reinforcement": data["reinforcement"] is not None
            }
            for tid, data in task_storage.items()
        ]
    }


# ==================== 6. 启动 ====================
if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("  建筑结构仿真演进与加固分析系统 - FastAPI版")
    print("=" * 70)
    print("  规范依据：GB 50011 | GB 50010 | GB 50367 | GB/T 50476 | ISO 9223")
    print("=" * 70)
    print("  访问 http://localhost:8000 查看首页")
    print("  访问 http://localhost:8000/docs 查看API文档")
    uvicorn.run(app, host="0.0.0.0", port=8011)