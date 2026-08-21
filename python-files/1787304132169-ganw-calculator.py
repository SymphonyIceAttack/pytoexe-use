#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公安机关办案日期计算器 v3.5 - 2026新法修订版 + 年龄判断功能（支持2010年后出生）
依据2026年1月1日起施行的新修订《治安管理处罚法》更新
涵盖《公安机关办理行政案件程序规定》和《公安机关办理刑事案件程序规定》
中的所有法定办案期限，并附带显示相关法律条文及出处
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
from pathlib import Path
import os
import sys


# ==================== 图标引用 ====================

def get_icon_path():
    """获取图标文件路径，支持打包后的exe"""
    try:
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        possible_paths = [
            os.path.join(base_path, 'icon.ico'),
            os.path.join(os.path.dirname(base_path) if os.path.dirname(base_path) else base_path, 'icon.ico'),
            os.path.join(os.getcwd(), 'icon.ico'),
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        return None
    except Exception:
        return None


# ==================== 法律条文数据库 ====================

class LawReference:
    """法律条文引用数据库 - 2026年新法修订版"""
    
    ADMIN_LAWS = {
        "admin_continuing_interrogation": {
            "title": "继续盘问",
            "source": "《治安管理处罚法》第85条",
            "article": "对形迹可疑、有违法犯罪嫌疑的人员，经当场盘问、检查，不能排除违法嫌疑的，可以依法继续盘问。继续盘问时限：一般不超过12小时；情况复杂的，经批准可延长至24小时；对不讲真实姓名、住址、身份不明的，可延长至48小时。"
        },
        "admin_case_transfer": {
            "title": "案件移送",
            "source": "《公安机关办理行政案件程序规定》",
            "article": "公安机关受理的案件，经审查认为属于其他行政机关管辖的，应当在24小时内移送有管辖权的行政机关处理。"
        },
        "admin_recusal_decision": {
            "title": "回避决定",
            "source": "《公安机关办理行政案件程序规定》",
            "article": "公安机关应当自收到回避申请之日起2日内作出决定，并通知申请人。"
        },
        "admin_quick_case": {
            "title": "快速办理",
            "source": "《治安管理处罚法》第121条",
            "article": "对违法事实清楚、证据确凿的案件，适用快速办理程序，违法嫌疑人到案后48小时内作出处理决定。不适用快速办理的情形：①盲、聋、哑人、未成年人或疑似精神病人；②依法应当适用听证程序的；③可能作出10日以上行政拘留处罚的。"
        },
        "admin_serving_decision": {
            "title": "处罚决定送达",
            "source": "《治安管理处罚法》第116条",
            "article": "治安管理处罚决定书应当在作出决定后2日内送达被处罚人；其他行政处罚决定书应当在作出决定后7日内送达。被处理人不在场的，公安机关应当在作出决定之日起7日内送达。"
        },
        "admin_public_notice": {
            "title": "公告送达",
            "source": "《治安管理处罚法》第116条",
            "article": "行政处罚决定书无法直接送达的，可以公告送达，公告期限不得少于60日。"
        },
        "admin_subpoena_examination": {
            "title": "传唤询问查证",
            "source": "《治安管理处罚法》第97条",
            "article": "对被传唤的违法嫌疑人，询问查证的时间一般不超过8小时；情况复杂，依法可能适用行政拘留处罚的，询问查证的时间不得超过24小时。涉案人数众多或违法嫌疑人身份不明的，询问查证的时间不得超过12小时。"
        },
        "admin_appraisal_serving": {
            "title": "鉴定意见送达",
            "source": "《公安机关办理行政案件程序规定》",
            "article": "公安机关应当自收到鉴定意见之日起5日内，将鉴定意见复印件送达违法嫌疑人和被侵害人。"
        },
        "admin_re_appraisal_application": {
            "title": "申请重新鉴定",
            "source": "《公安机关办理行政案件程序规定》",
            "article": "违法嫌疑人或者被侵害人对鉴定意见有异议的，可以在收到鉴定意见复印件之日起3日内提出重新鉴定的申请。"
        },
        "admin_preserve_evidence": {
            "title": "先行登记保存",
            "source": "《公安机关办理行政案件程序规定》",
            "article": "在证据可能灭失或者以后难以取得的情况下，经批准可以先行登记保存，并在7日内作出处理决定。"
        },
        "admin_seizure_period": {
            "title": "扣押、查封",
            "source": "《公安机关办理行政案件程序规定》",
            "article": "扣押、扣留、查封的期限不得超过30日；案情重大、复杂的，经批准可以延长至60日。检测、检验、检疫或者技术鉴定的期间不计入扣押期限。"
        },
        "admin_hearing_application": {
            "title": "听证申请",
            "source": "《治安管理处罚法》第117条",
            "article": "公安机关拟作出吊销许可证件、处四千元以上罚款的治安管理处罚决定前，应当告知当事人有要求举行听证的权利。当事人要求听证的，应当在收到告知书后3日内提出。"
        },
        "admin_hearing_acceptance": {
            "title": "听证受理",
            "source": "《公安机关办理行政案件程序规定》",
            "article": "公安机关收到听证申请后，应当在2日内作出是否受理的决定。"
        },
        "admin_hearing_notice": {
            "title": "听证通知",
            "source": "《公安机关办理行政案件程序规定》",
            "article": "公安机关应当在举行听证的7日前，将举行听证的时间、地点通知当事人。"
        },
        "admin_hearing_hold": {
            "title": "听证举行",
            "source": "《公安机关办理行政案件程序规定》",
            "article": "公安机关受理听证申请后，应当在10日内举行听证。"
        },
        "admin_case_handling_period": {
            "title": "治安案件办理",
            "source": "《治安管理处罚法》第118条",
            "article": "公安机关办理治安案件的期限，自受理之日起不得超过30日；案情重大、复杂的，经上一级公安机关批准，可以延长至60日。经上级公安机关再次批准，可以再延长30日，最长不超过90日。鉴定、听证期间不计入办案期限。"
        },
        "admin_foreigner_detention": {
            "title": "外国人拘留审查",
            "source": "《公安机关办理行政案件程序规定》",
            "article": "对外国人实施拘留审查的，拘留审查期限不得超过30日；案情复杂的，经批准可以延长至60日。"
        },
        "admin_foreigner_restriction": {
            "title": "限制活动范围",
            "source": "《公安机关办理行政案件程序规定》",
            "article": "对外国人限制活动范围的期限不得超过60日；案情复杂的，经批准可以延长，但延长期限不得超过60日。"
        },
        "admin_enhanced_punishment": {
            "title": "从重处罚",
            "source": "《治安管理处罚法》第22条",
            "article": "违反治安管理行为，在一年内曾受过治安管理处罚的，应当从重处罚。"
        },
        "admin_minor_execution": {
            "title": "未成年人拘留执行",
            "source": "《治安管理处罚法》第23、24条",
            "article": "已满十六周岁不满十八周岁，初次违反治安管理的，依照本法应当给予行政拘留处罚的，不执行行政拘留处罚。但是，情节严重、影响恶劣的，可以执行行政拘留处罚。"
        },
        "age_calculation": {
            "title": "年龄计算与处罚适用",
            "source": "《刑法》第17条、《治安管理处罚法》第23、24条",
            "article": "【刑事责任年龄】已满十六周岁的人犯罪，应当负刑事责任。已满十四周岁不满十六周岁的人，犯故意杀人、故意伤害致人重伤或者死亡、强奸、抢劫、贩卖毒品、放火、爆炸、投放危险物质罪的，应当负刑事责任。已满十二周岁不满十四周岁的人，犯故意杀人、故意伤害罪，致人死亡或者以特别残忍手段致人重伤造成严重残疾，情节恶劣，经最高人民检察院核准追诉的，应当负刑事责任。\n【行政责任年龄】已满十四周岁不满十八周岁的人违反治安管理的，从轻或者减轻处罚；不满十四周岁的人违反治安管理的，不予处罚，但是应当责令其监护人严加管教。"
        }
    }
    
    CRIMINAL_LAWS = {
        "criminal_summons": {
            "title": "拘传/传唤",
            "source": "《刑事诉讼法》第119条",
            "article": "拘传持续的时间不得超过12小时；案情特别重大、复杂，需要采取拘留、逮捕措施的，传唤、拘传的时间不得超过24小时。"
        },
        "criminal_bail": {
            "title": "取保候审",
            "source": "《刑事诉讼法》第79条",
            "article": "取保候审最长不得超过12个月。在取保候审期间，不得中断对案件的侦查、起诉和审理。"
        },
        "criminal_residential_surveillance": {
            "title": "监视居住",
            "source": "《刑事诉讼法》第79条",
            "article": "监视居住最长不得超过6个月。在监视居住期间，不得中断对案件的侦查、起诉和审理。"
        },
        "criminal_detention_period": {
            "title": "拘留提请批捕",
            "source": "《刑事诉讼法》第91条",
            "article": "公安机关对被拘留的人，认为需要逮捕的，应当在拘留后的3日以内提请人民检察院审查批准。特殊情况下，可以延长1至4日。对于流窜作案、多次作案、结伙作案的重大嫌疑分子，提请审查批准的时间可以延长至30日。"
        },
        "criminal_review_arrest": {
            "title": "审查批准逮捕",
            "source": "《刑事诉讼法》第91条",
            "article": "人民检察院应当自接到公安机关提请批准逮捕书后的7日以内，作出批准逮捕或者不批准逮捕的决定。"
        },
        "criminal_arrest_reconsideration": {
            "title": "不批捕复议",
            "source": "《刑事诉讼法》第92条",
            "article": "公安机关对人民检察院不批准逮捕的决定，认为有错误的时候，可以要求复议，但必须将被拘留的人立即释放。要求复议的期限为收到决定书之日起7日内。"
        },
        "criminal_arrest_review": {
            "title": "不批捕复核",
            "source": "《刑事诉讼法》第92条",
            "article": "公安机关对复议后仍不批准逮捕的决定，可以向上一级人民检察院提请复核，期限为收到复议决定书之日起15日内。"
        },
        "criminal_detention_after_arrest": {
            "title": "侦查羁押（2个月）",
            "source": "《刑事诉讼法》第156条",
            "article": "对犯罪嫌疑人逮捕后的侦查羁押期限不得超过2个月。"
        },
        "criminal_detention_extend1": {
            "title": "侦查羁押延长（+1个月）",
            "source": "《刑事诉讼法》第156条",
            "article": "案情复杂、期限届满不能终结的案件，经上一级人民检察院批准，可以延长1个月。"
        },
        "criminal_detention_extend2": {
            "title": "侦查羁押再延长（+2个月）",
            "source": "《刑事诉讼法》第158条",
            "article": "下列案件经省、自治区、直辖市人民检察院批准或者决定，可以再延长2个月：（一）交通十分不便的边远地区的重大复杂案件；（二）重大的犯罪集团案件；（三）流窜作案的重大复杂案件；（四）犯罪涉及面广，取证困难的重大复杂案件。"
        },
        "criminal_detention_extend3": {
            "title": "侦查羁押最终延长（+2个月）",
            "source": "《刑事诉讼法》第159条",
            "article": "对犯罪嫌疑人可能判处10年有期徒刑以上刑罚，依照本法第158条规定延长期限届满，仍不能侦查终结的，经省、自治区、直辖市人民检察院批准或者决定，可以再延长2个月。"
        },
        "criminal_prosecution_review": {
            "title": "审查起诉",
            "source": "《刑事诉讼法》第172条",
            "article": "人民检察院对于监察机关、公安机关移送起诉的案件，应当在1个月以内作出决定，重大、复杂的案件，可以延长15日。"
        },
        "criminal_legal_aid_transfer": {
            "title": "法律援助转交",
            "source": "《刑事诉讼法》第45条",
            "article": "公安机关收到在押犯罪嫌疑人、被告人提出的法律援助申请后，应当在24小时内转交法律援助机构。"
        },
        "criminal_legal_aid_notice": {
            "title": "法律援助通知",
            "source": "《刑事诉讼法》第45条",
            "article": "公安机关应当在3日内通知法律援助机构为符合法定情形的犯罪嫌疑人、被告人指派律师。"
        },
        "criminal_lawyer_meeting": {
            "title": "律师会见安排",
            "source": "《刑事诉讼法》第39条",
            "article": "辩护律师持律师执业证书、律师事务所证明和委托书或者法律援助公函要求会见在押的犯罪嫌疑人、被告人的，看守所应当及时安排会见，至迟不得超过48小时。"
        },
        "age_calculation": {
            "title": "年龄计算与刑事责任",
            "source": "《刑法》第17条",
            "article": "【刑事责任年龄】已满十六周岁的人犯罪，应当负刑事责任。已满十四周岁不满十六周岁的人，犯故意杀人、故意伤害致人重伤或者死亡、强奸、抢劫、贩卖毒品、放火、爆炸、投放危险物质罪的，应当负刑事责任。已满十二周岁不满十四周岁的人，犯故意杀人、故意伤害罪，致人死亡或者以特别残忍手段致人重伤造成严重残疾，情节恶劣，经最高人民检察院核准追诉的，应当负刑事责任。因不满十六周岁不予刑事处罚的，责令其父母或者其他监护人加以管教；在必要的时候，依法进行专门矫治教育。"
        }
    }


# ==================== 年龄计算与处罚判断类 ====================

class AgeCalculator:
    """年龄计算与处罚适用性判断 - 支持2010年后出生"""
    
    @staticmethod
    def calculate_age(birth_date, crime_date):
        """计算精确年龄（年/月/日）"""
        if birth_date > crime_date:
            return {'years': 0, 'months': 0, 'days': 0, 'total_days': 0, 'error': '出生日期不能晚于犯罪日期'}
        
        total_days = (crime_date - birth_date).days
        years = crime_date.year - birth_date.year
        if (crime_date.month, crime_date.day) < (birth_date.month, birth_date.day):
            years -= 1
        
        if years == 0:
            months = crime_date.month - birth_date.month
            if months < 0:
                months += 12
        else:
            birthday_this_year = date(crime_date.year, birth_date.month, birth_date.day)
            if crime_date >= birthday_this_year:
                months = crime_date.month - birth_date.month
                if months < 0:
                    months += 12
            else:
                birthday_last_year = date(crime_date.year - 1, birth_date.month, birth_date.day)
                months = (crime_date - birthday_last_year).days // 30
        
        if years > 0:
            years_days = years * 365 + (years // 4)
            remaining_days = total_days - years_days
            if remaining_days < 0:
                remaining_days = 0
            days = remaining_days % 30
            months = remaining_days // 30
            if months >= 12:
                years += 1
                months -= 12
        else:
            days = total_days % 30
            months = total_days // 30
        
        if months >= 12:
            years += months // 12
            months = months % 12
        
        return {
            'years': years,
            'months': months,
            'days': days,
            'total_days': total_days,
            'age_string': f'{years}岁{months}个月{days}天'
        }
    
    @staticmethod
    def get_age_at_date(birth_date, target_date):
        """获取在目标日期的年龄（周岁）"""
        if birth_date > target_date:
            return 0
        age = target_date.year - birth_date.year
        if (target_date.month, target_date.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    
    @staticmethod
    def judge_criminal_liability(birth_date, crime_date, serious_crime=False):
        """判断刑事责任能力 - 依据：《刑法》第17条（2021年修正）"""
        age = AgeCalculator.get_age_at_date(birth_date, crime_date)
        
        result = {
            'age': age,
            'criminal_liability': False,
            'reason': '',
            'law_ref': '《刑法》第17条（2021年修正）',
            'birth_year': birth_date.year
        }
        
        if birth_date.year >= 2010:
            result['birth_era'] = '2010年后出生'
        else:
            result['birth_era'] = '2010年前出生'
        
        if age >= 16:
            result['criminal_liability'] = True
            result['reason'] = f'已满16周岁（{age:.1f}岁），应当负刑事责任（《刑法》第17条第1款）'
        elif age >= 14:
            if serious_crime:
                result['criminal_liability'] = True
                result['reason'] = f'已满14周岁不满16周岁（{age:.1f}岁），犯法定八类严重暴力犯罪，应当负刑事责任（《刑法》第17条第2款）'
            else:
                result['criminal_liability'] = False
                result['reason'] = f'已满14周岁不满16周岁（{age:.1f}岁），所犯罪行不属于法定八类严重犯罪，不负刑事责任（《刑法》第17条第2款）'
        elif age >= 12:
            if serious_crime:
                result['criminal_liability'] = '需最高检核准'
                result['reason'] = f'已满12周岁不满14周岁（{age:.1f}岁），犯故意杀人、故意伤害罪致人死亡或特别残忍致重伤，情节恶劣，需经最高人民检察院核准追诉（《刑法》第17条第3款，2021年修正）'
            else:
                result['criminal_liability'] = False
                result['reason'] = f'已满12周岁不满14周岁（{age:.1f}岁），所犯罪行不属于法定特殊情形，不负刑事责任（《刑法》第17条第3款）'
        else:
            result['criminal_liability'] = False
            result['reason'] = f'不满12周岁（{age:.1f}岁），不负刑事责任（《刑法》第17条）'
        
        return result
    
    @staticmethod
    def judge_admin_liability(birth_date, crime_date, is_first_offense=True, serious_circumstance=False):
        """判断行政责任能力及拘留执行 - 依据：《治安管理处罚法》第23、24条（2026年修订）"""
        age = AgeCalculator.get_age_at_date(birth_date, crime_date)
        
        result = {
            'age': age,
            'admin_liability': False,
            'can_detention': False,
            'reason': '',
            'law_ref': '《治安管理处罚法》第23、24条（2026年修订）',
            'birth_year': birth_date.year
        }
        
        if birth_date.year >= 2010:
            result['birth_era'] = '2010年后出生'
        else:
            result['birth_era'] = '2010年前出生'
        
        if age < 14:
            result['admin_liability'] = False
            result['can_detention'] = False
            result['reason'] = f'不满14周岁（{age:.1f}岁），不予处罚，责令监护人严加管教（《治安管理处罚法》第24条）'
        elif age < 16:
            result['admin_liability'] = True
            result['can_detention'] = False
            result['reason'] = f'已满14周岁不满16周岁（{age:.1f}岁），从轻或减轻处罚，不执行行政拘留（《治安管理处罚法》第23条）'
        elif age < 18:
            result['admin_liability'] = True
            if is_first_offense:
                if serious_circumstance:
                    result['can_detention'] = True
                    result['reason'] = f'已满16周岁不满18周岁（{age:.1f}岁），初次违法但情节严重、影响恶劣，可以执行行政拘留（《治安管理处罚法》第24条）'
                else:
                    result['can_detention'] = False
                    result['reason'] = f'已满16周岁不满18周岁（{age:.1f}岁），初次违法，不执行行政拘留（《治安管理处罚法》第24条）'
            else:
                result['can_detention'] = True
                result['reason'] = f'已满16周岁不满18周岁（{age:.1f}岁），非初次违法，可以执行行政拘留（《治安管理处罚法》第23条）'
        else:
            result['admin_liability'] = True
            result['can_detention'] = True
            result['reason'] = f'已满18周岁（{age:.1f}岁），完全行政责任能力，可以执行行政拘留（《治安管理处罚法》第23条）'
        
        return result
    
    @staticmethod
    def comprehensive_judgment(birth_date, crime_date, serious_crime=False, is_first_offense=True, serious_circumstance=False):
        """综合判断：刑事和行政责任"""
        age_info = AgeCalculator.calculate_age(birth_date, crime_date)
        criminal = AgeCalculator.judge_criminal_liability(birth_date, crime_date, serious_crime)
        admin = AgeCalculator.judge_admin_liability(birth_date, crime_date, is_first_offense, serious_circumstance)
        
        suggestions = []
        if criminal['criminal_liability']:
            suggestions.append('可以追究刑事责任')
        elif criminal['criminal_liability'] == '需最高检核准':
            suggestions.append('需报请最高人民检察院核准追诉')
        else:
            if admin['admin_liability']:
                suggestions.append('可以给予行政处罚')
            else:
                suggestions.append('建议责令监护人严加管教')
        
        if admin['can_detention']:
            suggestions.append('可以执行行政拘留')
        else:
            if admin['admin_liability']:
                suggestions.append('不执行行政拘留')
            else:
                suggestions.append('不予处罚')
        
        return {
            'age_info': age_info,
            'criminal': criminal,
            'admin': admin,
            'suggestions': suggestions,
            'law_info': {
                'criminal_law': '《刑法》第17条（2021年修正）',
                'admin_law': '《治安管理处罚法》第23、24条（2026年修订）'
            }
        }


# ==================== 核心计算类 ====================

class CaseDateCalculator:
    """办案日期计算核心类 - 2026年新法修订版"""

    @staticmethod
    def _parse_date(date_input):
        if isinstance(date_input, str):
            return datetime.strptime(date_input, '%Y-%m-%d').date()
        elif isinstance(date_input, datetime):
            return date_input.date()
        return date_input

    @staticmethod
    def _build_result(start, end, days, name, description="", law_key="", law_db=None):
        result = {
            'start': start, 'end': end, 'days': days, 'name': name,
            'description': description, 'law_key': law_key,
            'law_info': law_db.get(law_key, {}) if law_db else {}
        }
        return result

    @staticmethod
    def admin_continuing_interrogation(start_date, duration_type='general'):
        start = CaseDateCalculator._parse_date(start_date)
        hours_map = {'general': 12, 'extend': 24, 'max': 48}
        hours = hours_map.get(duration_type, 12)
        end = start + timedelta(days=1) if hours >= 24 else start
        names = {'general': '继续盘问（12小时）', 'extend': '继续盘问（24小时）', 'max': '继续盘问（48小时）'}
        return CaseDateCalculator._build_result(start, end, 1 if hours >= 24 else 0, names.get(duration_type, '继续盘问'),
            f'继续盘问时限{hours}小时', 'admin_continuing_interrogation', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_case_transfer(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=1)
        return CaseDateCalculator._build_result(start, end, 1, '案件移送（24小时）',
            '属于公安机关职责但不属本单位管辖的，24小时内移送', 'admin_case_transfer', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_recusal_decision(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=2)
        return CaseDateCalculator._build_result(start, end, 2, '回避决定（2日）',
            '收到回避申请之日起2日内作出决定', 'admin_recusal_decision', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_quick_case(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=2)
        return CaseDateCalculator._build_result(start, end, 2, '快速办理（48小时）',
            '违法嫌疑人到案后48小时内作出处理决定', 'admin_quick_case', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_serving_decision(start_date, is_public_security=False):
        start = CaseDateCalculator._parse_date(start_date)
        days = 2 if is_public_security else 7
        end = start + timedelta(days=days)
        name = f'处罚决定送达（{"治安2日" if is_public_security else "其他7日"}）'
        return CaseDateCalculator._build_result(start, end, days, name,
            f'决定作出后{days}日内送达', 'admin_serving_decision', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_public_notice(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=60)
        return CaseDateCalculator._build_result(start, end, 60, '公告送达（60日）',
            '公告期限不得少于60日', 'admin_public_notice', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_subpoena_examination(start_date, duration_type='general'):
        start = CaseDateCalculator._parse_date(start_date)
        hours_map = {'general': 8, 'multi_person': 12, 'may_detention': 24}
        hours = hours_map.get(duration_type, 8)
        end = start + timedelta(days=1) if hours >= 24 else start
        names = {'general': '询问查证（8小时）', 'multi_person': '询问查证（12小时）', 'may_detention': '询问查证（24小时）'}
        return CaseDateCalculator._build_result(start, end, 1 if hours >= 24 else 0, names.get(duration_type, '询问查证'),
            f'询问查证时限{hours}小时', 'admin_subpoena_examination', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_appraisal_serving(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=5)
        return CaseDateCalculator._build_result(start, end, 5, '鉴定意见送达（5日）',
            '收到鉴定意见之日起5日内送达复印件', 'admin_appraisal_serving', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_re_appraisal_application(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=3)
        return CaseDateCalculator._build_result(start, end, 3, '申请重新鉴定（3日）',
            '收到鉴定意见复印件之日起3日内提出', 'admin_re_appraisal_application', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_preserve_evidence(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=7)
        return CaseDateCalculator._build_result(start, end, 7, '先行登记保存（7日）',
            '7日内作出处理决定', 'admin_preserve_evidence', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_seizure_period(start_date, complex_case=False):
        start = CaseDateCalculator._parse_date(start_date)
        days = 60 if complex_case else 30
        end = start + timedelta(days=days)
        name = f'扣押/查封（{days}日）'
        return CaseDateCalculator._build_result(start, end, days, name,
            f'扣押查封期限{days}日，鉴定期间不计入', 'admin_seizure_period', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_hearing_application(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=3)
        return CaseDateCalculator._build_result(start, end, 3, '听证申请（3日）',
            '收到告知书后3日内申请听证', 'admin_hearing_application', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_hearing_acceptance(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=2)
        return CaseDateCalculator._build_result(start, end, 2, '听证受理（2日）',
            '收到申请之日起2日内作出受理决定', 'admin_hearing_acceptance', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_hearing_notice(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=7)
        return CaseDateCalculator._build_result(start, end, 7, '听证通知（7日）',
            '举行听证7日前通知当事人', 'admin_hearing_notice', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_hearing_hold(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=10)
        return CaseDateCalculator._build_result(start, end, 10, '听证举行（10日）',
            '受理后10日内举行听证', 'admin_hearing_hold', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_case_handling_period(start_date, extend_count=0):
        start = CaseDateCalculator._parse_date(start_date)
        days = 30 + (extend_count * 30)
        end = start + timedelta(days=days)
        names = {0: '治安案件办理（30日）', 1: '治安案件办理（延长至60日）', 2: '治安案件办理（再延长至90日，最长）'}
        descriptions = {
            0: '治安案件办案期限30日，从受理之日起算',
            1: '治安案件办案期限60日，经上一级公安机关批准延长30日',
            2: '治安案件办案期限90日，经上级公安机关再次批准再延长30日，鉴定、听证期间不计入'
        }
        return CaseDateCalculator._build_result(start, end, days, names.get(extend_count, '治安案件办理'),
            descriptions.get(extend_count, ''), 'admin_case_handling_period', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_foreigner_detention(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=30)
        return CaseDateCalculator._build_result(start, end, 30, '外国人拘留审查（30日）',
            '拘留审查期限30日，经批准可延长至60日', 'admin_foreigner_detention', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_foreigner_restriction(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=60)
        return CaseDateCalculator._build_result(start, end, 60, '限制活动范围（60日）',
            '限制活动范围期限60日，可经批准延长', 'admin_foreigner_restriction', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_enhanced_punishment(previous_date, option=None):
        start = CaseDateCalculator._parse_date(previous_date)
        end = start + timedelta(days=365)
        return CaseDateCalculator._build_result(start, end, 365, '从重处罚追溯（1年）',
            '违法行为人在1年内曾受过治安管理处罚的，应当从重处罚', 'admin_enhanced_punishment', LawReference.ADMIN_LAWS)

    @staticmethod
    def admin_minor_execution(execution_date, option=None):
        start = CaseDateCalculator._parse_date(execution_date)
        end = start
        return CaseDateCalculator._build_result(start, end, 0, '未成年人拘留执行审查',
            '已满十六周岁不满十八周岁初次违法不执行拘留，情节严重、影响恶劣的除外',
            'admin_minor_execution', LawReference.ADMIN_LAWS)

    @staticmethod
    def criminal_summons(start_date, serious_case=False):
        start = CaseDateCalculator._parse_date(start_date)
        hours = 24 if serious_case else 12
        end = start + timedelta(days=1) if serious_case else start
        name = f'拘传（{"24" if serious_case else "12"}小时）'
        return CaseDateCalculator._build_result(start, end, 1 if serious_case else 0, name,
            f'拘传持续时间不得超过{hours}小时', 'criminal_summons', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_bail(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=365)
        return CaseDateCalculator._build_result(start, end, 365, '取保候审（12个月）',
            '取保候审最长不得超过12个月', 'criminal_bail', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_residential_surveillance(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=180)
        return CaseDateCalculator._build_result(start, end, 180, '监视居住（6个月）',
            '监视居住最长不得超过6个月', 'criminal_residential_surveillance', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_detention_period(start_date, detention_type='general'):
        start = CaseDateCalculator._parse_date(start_date)
        period_map = {'general': 3, 'extend': 7, 'max': 30}
        days = period_map.get(detention_type, 3)
        end = start + timedelta(days=days)
        names = {'general': '拘留后提请批捕（3日）', 'extend': '拘留后提请批捕（延长至7日）', 'max': '拘留后提请批捕（延长至30日）'}
        return CaseDateCalculator._build_result(start, end, days, names.get(detention_type, '提请批捕'),
            f'拘留后{days}日内提请审查批准逮捕', 'criminal_detention_period', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_review_arrest(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=7)
        return CaseDateCalculator._build_result(start, end, 7, '审查批准逮捕（7日）',
            '人民检察院应在7日内作出是否批捕决定', 'criminal_review_arrest', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_arrest_reconsideration(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=7)
        return CaseDateCalculator._build_result(start, end, 7, '不批捕复议（7日）',
            '对不批捕决定要求复议的期限为7日', 'criminal_arrest_reconsideration', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_arrest_review(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=15)
        return CaseDateCalculator._build_result(start, end, 15, '不批捕复核（15日）',
            '对复议后仍不批捕提请复核的期限为15日', 'criminal_arrest_review', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_detention_after_arrest(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=60)
        return CaseDateCalculator._build_result(start, end, 60, '侦查羁押（2个月）',
            '逮捕后侦查羁押期限不得超过2个月', 'criminal_detention_after_arrest', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_detention_extend1(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=90)
        return CaseDateCalculator._build_result(start, end, 90, '侦查羁押延长（+1个月，共3个月）',
            '案情复杂可延长1个月', 'criminal_detention_extend1', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_detention_extend2(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=150)
        return CaseDateCalculator._build_result(start, end, 150, '侦查羁押再延长（+2个月，共5个月）',
            '四类重大复杂案件可再延长2个月', 'criminal_detention_extend2', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_detention_extend3(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=210)
        return CaseDateCalculator._build_result(start, end, 210, '侦查羁押最终延长（+2个月，共7个月）',
            '可能判处10年以上可再延长2个月', 'criminal_detention_extend3', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_prosecution_review(start_date, extended=False):
        start = CaseDateCalculator._parse_date(start_date)
        days = 45 if extended else 30
        end = start + timedelta(days=days)
        name = f'审查起诉（{"延长15日" if extended else "1个月"}）'
        return CaseDateCalculator._build_result(start, end, days, name,
            f'审查起诉期限{days}日', 'criminal_prosecution_review', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_legal_aid_transfer(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=1)
        return CaseDateCalculator._build_result(start, end, 1, '法律援助转交（24小时）',
            '收到申请后24小时内转交法律援助机构', 'criminal_legal_aid_transfer', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_legal_aid_notice(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=3)
        return CaseDateCalculator._build_result(start, end, 3, '法律援助通知（3日）',
            '3日内通知法律援助机构指派律师', 'criminal_legal_aid_notice', LawReference.CRIMINAL_LAWS)

    @staticmethod
    def criminal_lawyer_meeting(start_date, option=None):
        start = CaseDateCalculator._parse_date(start_date)
        end = start + timedelta(days=2)
        return CaseDateCalculator._build_result(start, end, 2, '律师会见安排（48小时）',
            '看守所应在48小时内安排律师会见', 'criminal_lawyer_meeting', LawReference.CRIMINAL_LAWS)


# ==================== 日期选择器 ====================

class DatePicker(ttk.Frame):
    def __init__(self, master, label_text="", initial_date=None, **kwargs):
        super().__init__(master, **kwargs)
        if label_text:
            ttk.Label(self, text=label_text, font=('Microsoft YaHei', 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.year_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.day_var = tk.StringVar()
        
        today = initial_date if initial_date else date.today()
        if isinstance(today, str):
            today = datetime.strptime(today, '%Y-%m-%d').date()
        elif isinstance(today, datetime):
            today = today.date()
        
        years = [str(y) for y in range(1900, date.today().year + 11)]
        self.year_combo = ttk.Combobox(self, textvariable=self.year_var, values=years, width=6, state='readonly')
        self.year_combo.set(str(today.year))
        self.year_combo.pack(side=tk.LEFT, padx=1)
        ttk.Label(self, text="年").pack(side=tk.LEFT)
        
        months = [str(m).zfill(2) for m in range(1, 13)]
        self.month_combo = ttk.Combobox(self, textvariable=self.month_var, values=months, width=4, state='readonly')
        self.month_combo.set(str(today.month).zfill(2))
        self.month_combo.pack(side=tk.LEFT, padx=1)
        ttk.Label(self, text="月").pack(side=tk.LEFT)
        
        days = [str(d).zfill(2) for d in range(1, 32)]
        self.day_combo = ttk.Combobox(self, textvariable=self.day_var, values=days, width=4, state='readonly')
        self.day_combo.set(str(today.day).zfill(2))
        self.day_combo.pack(side=tk.LEFT, padx=1)
        ttk.Label(self, text="日").pack(side=tk.LEFT)
        
        self.year_combo.bind('<<ComboboxSelected>>', self.update_days)
        self.month_combo.bind('<<ComboboxSelected>>', self.update_days)
        ttk.Button(self, text="今天", command=self.set_today, width=6).pack(side=tk.LEFT, padx=(5, 0))

    def update_days(self, event=None):
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            if month in [1, 3, 5, 7, 8, 10, 12]:
                days = 31
            elif month in [4, 6, 9, 11]:
                days = 30
            else:
                days = 29 if ((year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)) else 28
            self.day_combo['values'] = [str(d).zfill(2) for d in range(1, days + 1)]
            if int(self.day_var.get()) > days:
                self.day_var.set(str(days).zfill(2))
        except:
            pass

    def set_today(self):
        today = date.today()
        self.year_var.set(str(today.year))
        self.month_var.set(str(today.month).zfill(2))
        self.day_var.set(str(today.day).zfill(2))
        self.update_days()

    def get_date(self):
        try:
            return date(int(self.year_var.get()), int(self.month_var.get()), int(self.day_var.get()))
        except:
            return date.today()


# ==================== 年龄判断结果框架 ====================

class AgeResultFrame(ttk.LabelFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, text="年龄分析与处罚适用判断", **kwargs)
        self.result_text = tk.Text(self, height=14, width=55, font=('Microsoft YaHei', 10), wrap=tk.WORD,
                                   relief=tk.FLAT, bg='#f0fff0')
        self.result_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        self.result_text.tag_configure('title', font=('Microsoft YaHei', 13, 'bold'), foreground='#003399')
        self.result_text.tag_configure('info', font=('Microsoft YaHei', 10), foreground='#006600')
        self.result_text.tag_configure('highlight', font=('Microsoft YaHei', 11, 'bold'), foreground='#cc0000')
        self.result_text.tag_configure('warning', font=('Microsoft YaHei', 10), foreground='#cc6600')
        self.result_text.tag_configure('success', font=('Microsoft YaHei', 10), foreground='#006600')
        self.result_text.tag_configure('law', font=('Microsoft YaHei', 9), foreground='#444444')
    
    def show_result(self, result_dict):
        self.result_text.delete(1.0, tk.END)
        
        age_info = result_dict.get('age_info', {})
        criminal = result_dict.get('criminal', {})
        admin = result_dict.get('admin', {})
        suggestions = result_dict.get('suggestions', [])
        
        self.result_text.insert(tk.END, "年龄分析与处罚适用判断\n", 'title')
        self.result_text.insert(tk.END, "=" * 50 + "\n", 'info')
        
        self.result_text.insert(tk.END, f"年龄：{age_info.get('age_string', '未知')}\n", 'highlight')
        self.result_text.insert(tk.END, f"   (精确计算：{age_info.get('years', 0)}岁{age_info.get('months', 0)}个月{age_info.get('days', 0)}天，共{age_info.get('total_days', 0)}天)\n", 'info')
        self.result_text.insert(tk.END, "\n", 'info')
        
        self.result_text.insert(tk.END, "刑事责任判断\n", 'info')
        self.result_text.insert(tk.END, f"   年龄：{criminal.get('age', 0):.1f}周岁\n", 'info')
        
        liability = criminal.get('criminal_liability')
        if liability == True:
            self.result_text.insert(tk.END, f"   结论：{criminal.get('reason', '')}\n", 'success')
        elif liability == '需最高检核准':
            self.result_text.insert(tk.END, f"   结论：{criminal.get('reason', '')}\n", 'warning')
        else:
            self.result_text.insert(tk.END, f"   结论：{criminal.get('reason', '')}\n", 'warning')
        self.result_text.insert(tk.END, f"   依据：{criminal.get('law_ref', '')}\n", 'law')
        self.result_text.insert(tk.END, "\n", 'info')
        
        self.result_text.insert(tk.END, "行政责任判断\n", 'info')
        self.result_text.insert(tk.END, f"   年龄：{admin.get('age', 0):.1f}周岁\n", 'info')
        
        if admin.get('admin_liability'):
            self.result_text.insert(tk.END, f"   行政处罚：可以给予行政处罚\n", 'success')
        else:
            self.result_text.insert(tk.END, f"   行政处罚：不予处罚\n", 'warning')
        
        if admin.get('can_detention'):
            self.result_text.insert(tk.END, f"   拘留执行：可以执行行政拘留\n", 'warning')
        else:
            self.result_text.insert(tk.END, f"   拘留执行：不执行行政拘留\n", 'info')
        
        self.result_text.insert(tk.END, f"   说明：{admin.get('reason', '')}\n", 'law')
        self.result_text.insert(tk.END, f"   依据：{admin.get('law_ref', '')}\n", 'law')
        self.result_text.insert(tk.END, "\n", 'info')
        
        if suggestions:
            self.result_text.insert(tk.END, "综合建议\n", 'highlight')
            for suggestion in suggestions:
                self.result_text.insert(tk.END, f"   {suggestion}\n", 'info')
        
        self.result_text.see(tk.END)
    
    def show_error(self, error_msg):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"错误：{error_msg}", 'warning')
    
    def clear(self):
        self.result_text.delete(1.0, tk.END)


# ==================== 年龄计算对话框 ====================

class AgeCalculatorDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("年龄计算与处罚适用判断")
        self.dialog.geometry("820x820")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        icon_path = get_icon_path()
        if icon_path:
            try:
                self.dialog.iconbitmap(icon_path)
            except:
                pass
        
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="年龄计算与处罚适用判断", 
                  font=('Microsoft YaHei', 16, 'bold')).pack(pady=(0, 5))
        ttk.Label(main_frame, text="依据《刑法》第17条（2021年修正）和《治安管理处罚法》第23、24条（2026年修订）", 
                  font=('Microsoft YaHei', 9), foreground='#666666').pack(pady=(0, 15))
        
        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text="输入信息", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        birth_frame = ttk.Frame(input_frame)
        birth_frame.pack(fill=tk.X, pady=3)
        ttk.Label(birth_frame, text="出生日期：", font=('Microsoft YaHei', 10)).pack(side=tk.LEFT, padx=(0, 10))
        self.birth_picker = DatePicker(birth_frame, "", initial_date=date(2010, 1, 1))
        self.birth_picker.pack(side=tk.LEFT)
        
        crime_frame = ttk.Frame(input_frame)
        crime_frame.pack(fill=tk.X, pady=3)
        ttk.Label(crime_frame, text="犯罪日期：", font=('Microsoft YaHei', 10)).pack(side=tk.LEFT, padx=(0, 10))
        self.crime_picker = DatePicker(crime_frame, "", initial_date=date.today())
        self.crime_picker.pack(side=tk.LEFT)
        
        # 选项设置
        option_frame = tk.LabelFrame(input_frame, text="选项设置（请根据案件实际情况勾选）", 
                                     font=('Microsoft YaHei', 10, 'bold'), bg='#f0f0f0', fg='#003399')
        option_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 选项1
        self.serious_crime_var = tk.BooleanVar(value=False)
        cb1_frame = tk.Frame(option_frame, bg='#f0f0f0')
        cb1_frame.pack(anchor=tk.W, pady=3, fill=tk.X)
        cb1 = tk.Checkbutton(cb1_frame, 
            text="涉嫌《刑法》第17条第2款规定的八类严重暴力犯罪", 
            variable=self.serious_crime_var,
            font=('Microsoft YaHei', 10),
            bg='#f0f0f0',
            activebackground='#f0f0f0',
            selectcolor='#f0f0f0')
        cb1.pack(side=tk.LEFT)
        self.serious_crime_status = tk.Label(cb1_frame, text="□", font=('Microsoft YaHei', 12), bg='#f0f0f0')
        self.serious_crime_status.pack(side=tk.RIGHT, padx=(10, 0))
        def update_status1():
            if self.serious_crime_var.get():
                self.serious_crime_status.config(text="☑", fg='#006600')
            else:
                self.serious_crime_status.config(text="□", fg='#666666')
        cb1.config(command=update_status1)
        update_status1()
        
        tk.Label(option_frame, 
            text="注：故意杀人、故意伤害致人重伤/死亡、强奸、抢劫、贩卖毒品、放火、爆炸、投放危险物质", 
            font=('Microsoft YaHei', 8), fg='#666666', bg='#f0f0f0').pack(anchor=tk.W, padx=(25, 0), pady=(0, 2))
        tk.Label(option_frame, 
            text="出处：《刑法》第17条第2款（2021年修正）", 
            font=('Microsoft YaHei', 8), fg='#888888', bg='#f0f0f0').pack(anchor=tk.W, padx=(25, 0), pady=(0, 5))
        
        # 选项2
        self.first_offense_var = tk.BooleanVar(value=True)
        cb2_frame = tk.Frame(option_frame, bg='#f0f0f0')
        cb2_frame.pack(anchor=tk.W, pady=3, fill=tk.X)
        cb2 = tk.Checkbutton(cb2_frame, 
            text="系初次违反治安管理（《治安管理处罚法》第24条）", 
            variable=self.first_offense_var,
            font=('Microsoft YaHei', 10),
            bg='#f0f0f0',
            activebackground='#f0f0f0',
            selectcolor='#f0f0f0')
        cb2.pack(side=tk.LEFT)
        self.first_offense_status = tk.Label(cb2_frame, text="☑", font=('Microsoft YaHei', 12), bg='#f0f0f0', fg='#006600')
        self.first_offense_status.pack(side=tk.RIGHT, padx=(10, 0))
        def update_status2():
            if self.first_offense_var.get():
                self.first_offense_status.config(text="☑", fg='#006600')
            else:
                self.first_offense_status.config(text="□", fg='#666666')
        cb2.config(command=update_status2)
        update_status2()
        
        tk.Label(option_frame, 
            text="注：初次违法是指此前未因违反治安管理受过行政处罚", 
            font=('Microsoft YaHei', 8), fg='#666666', bg='#f0f0f0').pack(anchor=tk.W, padx=(25, 0), pady=(0, 2))
        tk.Label(option_frame, 
            text="出处：《治安管理处罚法》第24条（2026年修订）", 
            font=('Microsoft YaHei', 8), fg='#888888', bg='#f0f0f0').pack(anchor=tk.W, padx=(25, 0), pady=(0, 5))
        
        # 选项3
        self.serious_circumstance_var = tk.BooleanVar(value=False)
        cb3_frame = tk.Frame(option_frame, bg='#f0f0f0')
        cb3_frame.pack(anchor=tk.W, pady=3, fill=tk.X)
        cb3 = tk.Checkbutton(cb3_frame, 
            text="情节严重、影响恶劣（《治安管理处罚法》第24条但书）", 
            variable=self.serious_circumstance_var,
            font=('Microsoft YaHei', 10),
            bg='#f0f0f0',
            activebackground='#f0f0f0',
            selectcolor='#f0f0f0')
        cb3.pack(side=tk.LEFT)
        self.serious_circumstance_status = tk.Label(cb3_frame, text="□", font=('Microsoft YaHei', 12), bg='#f0f0f0')
        self.serious_circumstance_status.pack(side=tk.RIGHT, padx=(10, 0))
        def update_status3():
            if self.serious_circumstance_var.get():
                self.serious_circumstance_status.config(text="☑", fg='#006600')
            else:
                self.serious_circumstance_status.config(text="□", fg='#666666')
        cb3.config(command=update_status3)
        update_status3()
        
        tk.Label(option_frame, 
            text="注：未成年人初次违法本应不执行拘留，但情节严重、影响恶劣的除外", 
            font=('Microsoft YaHei', 8), fg='#666666', bg='#f0f0f0').pack(anchor=tk.W, padx=(25, 0), pady=(0, 2))
        tk.Label(option_frame, 
            text="出处：《治安管理处罚法》第24条但书（2026年修订）", 
            font=('Microsoft YaHei', 8), fg='#888888', bg='#f0f0f0').pack(anchor=tk.W, padx=(25, 0), pady=(0, 5))
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="计算年龄并判断", command=self.calculate).pack(side=tk.LEFT, expand=True, padx=(0, 5))
        ttk.Button(btn_frame, text="清空", command=self.clear).pack(side=tk.LEFT, expand=True, padx=(5, 0))
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy).pack(side=tk.LEFT, expand=True, padx=(5, 0))
        
        # 结果区域
        self.result_frame = AgeResultFrame(main_frame)
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(info_frame, 
            text="提示：出生日期可回溯至1900年，支持2010年后出生的未成年人年龄判断",
            font=('Microsoft YaHei', 9), foreground='#0066cc').pack()
    
    def calculate(self):
        try:
            birth_date = self.birth_picker.get_date()
            crime_date = self.crime_picker.get_date()
            
            if birth_date > crime_date:
                self.result_frame.show_error("出生日期不能晚于犯罪日期！")
                return
            
            serious_crime = self.serious_crime_var.get()
            first_offense = self.first_offense_var.get()
            serious_circumstance = self.serious_circumstance_var.get()
            
            result = AgeCalculator.comprehensive_judgment(
                birth_date, crime_date,
                serious_crime, first_offense, serious_circumstance
            )
            
            self.result_frame.show_result(result)
            
        except Exception as e:
            self.result_frame.show_error(f"计算错误：{str(e)}")
    
    def clear(self):
        self.result_frame.clear()
        self.birth_picker.set_today()
        self.crime_picker.set_today()
        self.serious_crime_var.set(False)
        self.first_offense_var.set(True)
        self.serious_circumstance_var.set(False)


# ==================== 结果展示框架 ====================

class ResultFrame(ttk.LabelFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, text="计算结果（含法律依据）", **kwargs)
        self.result_text = tk.Text(self, height=14, width=55, font=('Microsoft YaHei', 10), wrap=tk.WORD,
                                   relief=tk.FLAT, bg='#f0f8ff')
        self.result_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        self.result_text.tag_configure('title', font=('Microsoft YaHei', 13, 'bold'), foreground='#003399')
        self.result_text.tag_configure('info', font=('Microsoft YaHei', 10), foreground='#006600')
        self.result_text.tag_configure('date', font=('Microsoft YaHei', 11, 'bold'), foreground='#cc0000')
        self.result_text.tag_configure('warning', font=('Microsoft YaHei', 10), foreground='#cc6600')
        self.result_text.tag_configure('desc', font=('Microsoft YaHei', 10), foreground='#333333')
        self.result_text.tag_configure('law', font=('Microsoft YaHei', 10, 'bold'), foreground='#8B0000')
        self.result_text.tag_configure('law_text', font=('Microsoft YaHei', 9), foreground='#444444')

    def show_result(self, result_dict):
        self.result_text.delete(1.0, tk.END)
        start = result_dict['start']
        end = result_dict['end']
        days = result_dict['days']
        name = result_dict['name']
        description = result_dict.get('description', '')
        law_info = result_dict.get('law_info', {})

        self.result_text.insert(tk.END, f"{name}\n", 'title')
        self.result_text.insert(tk.END, "-" * 45 + "\n", 'info')
        self.result_text.insert(tk.END, f"起始日期：", 'info')
        self.result_text.insert(tk.END, f"{start.strftime('%Y年%m月%d日')}\n", 'date')
        self.result_text.insert(tk.END, f"截止日期：", 'info')
        self.result_text.insert(tk.END, f"{end.strftime('%Y年%m月%d日')}\n", 'date')
        self.result_text.insert(tk.END, f"期限天数：", 'info')
        if days > 0:
            self.result_text.insert(tk.END, f"{days} 天\n", 'date')
        else:
            self.result_text.insert(tk.END, f"不足1天（以小时计）\n", 'warning')

        today = date.today()
        if end >= today:
            self.result_text.insert(tk.END, f"距离截止：{ (end - today).days } 天\n", 'warning')
        else:
            self.result_text.insert(tk.END, f"已过期：{ (today - end).days } 天\n", 'warning')

        if description:
            self.result_text.insert(tk.END, f"\n{description}\n", 'desc')

        if law_info:
            self.result_text.insert(tk.END, "\n" + "=" * 45 + "\n", 'info')
            self.result_text.insert(tk.END, f"法律依据\n", 'law')
            self.result_text.insert(tk.END, f"来源：{law_info.get('source', '')}\n", 'law_text')
            self.result_text.insert(tk.END, f"条文：{law_info.get('article', '')}\n", 'law_text')

        self.result_text.see(tk.END)

    def show_error(self, error_msg):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"错误：{error_msg}", 'info')

    def clear(self):
        self.result_text.delete(1.0, tk.END)


# ==================== 主界面 ====================

class CaseDateCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("公安机关办案日期计算器 v3.5")
        self.root.geometry("1100x920")
        self.root.resizable(True, True)
        
        icon_path = get_icon_path()
        if icon_path:
            try:
                self.root.iconbitmap(icon_path)
            except:
                pass
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Microsoft YaHei', 18, 'bold'), foreground='#003399')
        style.configure('Calc.TButton', font=('Microsoft YaHei', 12, 'bold'))
        style.configure('Age.TButton', font=('Microsoft YaHei', 11, 'bold'), foreground='#006600')

        self.main_frame = ttk.Frame(root, padding="15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(title_frame, text="公安机关办案日期计算器 v3.5", style='Title.TLabel').pack()
        ttk.Label(title_frame, text="依据2026年新修订《治安管理处罚法》| 新增年龄判断（支持2010年后出生）", 
                  font=('Microsoft YaHei', 10), foreground='#666666').pack()
        ttk.Separator(self.main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(toolbar, text="年龄计算与处罚判断", command=self.open_age_calculator,
                   style='Age.TButton').pack(side=tk.LEFT)

        self.paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.paned)
        self.paned.add(self.left_frame, weight=1)
        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.right_frame, weight=1)

        self.create_status_bar()
        self.create_result_frame()
        self.create_input_frame()
        self.calculate()

    def open_age_calculator(self):
        AgeCalculatorDialog(self.root)

    def create_status_bar(self):
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Separator(self.main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 5))
        
        contact_label = ttk.Label(self.status_frame, 
            text="如有需要更正或添加部分，请微信联系：19557500223", 
            font=('Microsoft YaHei', 9), foreground='#0066cc')
        contact_label.pack(side=tk.LEFT)
        
        right_frame = ttk.Frame(self.status_frame)
        right_frame.pack(side=tk.RIGHT)
        self.status_label = ttk.Label(right_frame, text="就绪", font=('Microsoft YaHei', 9))
        self.status_label.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(right_frame, text=f"{date.today().strftime('%Y年%m月%d日')}",
                  font=('Microsoft YaHei', 9), foreground='#666666').pack(side=tk.LEFT)

    def create_input_frame(self):
        case_frame = ttk.LabelFrame(self.left_frame, text="案件类型", padding="10")
        case_frame.pack(fill=tk.X, pady=(0, 10))
        self.case_type_var = tk.StringVar(value="行政案件")
        for i, case_type in enumerate(["行政案件", "刑事案件"]):
            rb = ttk.Radiobutton(case_frame, text=case_type, variable=self.case_type_var,
                                 value=case_type, command=self.on_case_type_change)
            rb.grid(row=0, column=i, padx=20, pady=5, sticky=tk.W)

        period_frame = ttk.LabelFrame(self.left_frame, text="期限类型", padding="10")
        period_frame.pack(fill=tk.X, pady=(0, 10))
        self.period_var = tk.StringVar()
        self.period_combo = ttk.Combobox(period_frame, textvariable=self.period_var,
                                         state='readonly', font=('Microsoft YaHei', 10))
        self.period_combo.pack(fill=tk.X, padx=5)
        self.period_combo.bind('<<ComboboxSelected>>', self.on_period_change)

        date_frame = ttk.LabelFrame(self.left_frame, text="日期设置", padding="10")
        date_frame.pack(fill=tk.X, pady=(0, 10))
        self.date_picker = DatePicker(date_frame, "起始日期：")
        self.date_picker.pack(pady=5)

        self.option_frame = ttk.LabelFrame(self.left_frame, text="选项设置", padding="10")
        self.option_frame.pack(fill=tk.X, pady=(0, 10))
        self.option_var = tk.StringVar(value="一般")
        self.option_combo = ttk.Combobox(self.option_frame, textvariable=self.option_var,
                                         state='readonly', font=('Microsoft YaHei', 10))
        self.option_combo.pack(fill=tk.X, padx=5)
        self.option_combo.bind('<<ComboboxSelected>>', self.on_option_change)

        btn_frame = ttk.Frame(self.left_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="计算期限", command=self.calculate,
                   style='Calc.TButton').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        ttk.Button(btn_frame, text="清空", command=self.clear_all,
                   style='Calc.TButton').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

        self.init_period_options()

    def create_result_frame(self):
        self.result_frame = ResultFrame(self.right_frame)
        self.result_frame.pack(fill=tk.BOTH, expand=True)
        quick_frame = ttk.LabelFrame(self.right_frame, text="快捷操作", padding="10")
        quick_frame.pack(fill=tk.X, pady=(10, 0))
        btn_frame = ttk.Frame(quick_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="复制结果", command=self.copy_result).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="保存记录", command=self.save_record).pack(side=tk.LEFT, padx=2)

    def init_period_options(self):
        self.admin_options = [
            ("继续盘问", "admin_continuing_interrogation"),
            ("案件移送", "admin_case_transfer"),
            ("回避决定", "admin_recusal_decision"),
            ("快速办理", "admin_quick_case"),
            ("处罚决定送达", "admin_serving_decision"),
            ("公告送达", "admin_public_notice"),
            ("传唤询问查证", "admin_subpoena_examination"),
            ("鉴定意见送达", "admin_appraisal_serving"),
            ("申请重新鉴定", "admin_re_appraisal_application"),
            ("先行登记保存", "admin_preserve_evidence"),
            ("扣押查封", "admin_seizure_period"),
            ("听证申请", "admin_hearing_application"),
            ("听证受理", "admin_hearing_acceptance"),
            ("听证通知", "admin_hearing_notice"),
            ("听证举行", "admin_hearing_hold"),
            ("治安案件办理", "admin_case_handling_period"),
            ("外国人拘留审查", "admin_foreigner_detention"),
            ("外国人限制活动范围", "admin_foreigner_restriction"),
            ("从重处罚追溯", "admin_enhanced_punishment"),
            ("未成年人拘留执行", "admin_minor_execution"),
        ]
        self.criminal_options = [
            ("拘传/传唤", "criminal_summons"),
            ("取保候审", "criminal_bail"),
            ("监视居住", "criminal_residential_surveillance"),
            ("拘留提请批捕", "criminal_detention_period"),
            ("审查批准逮捕", "criminal_review_arrest"),
            ("不批捕复议", "criminal_arrest_reconsideration"),
            ("不批捕复核", "criminal_arrest_review"),
            ("侦查羁押(2个月)", "criminal_detention_after_arrest"),
            ("侦查羁押延长(+1个月)", "criminal_detention_extend1"),
            ("侦查羁押再延长(+2个月)", "criminal_detention_extend2"),
            ("侦查羁押最终延长(+2个月)", "criminal_detention_extend3"),
            ("审查起诉", "criminal_prosecution_review"),
            ("法律援助转交", "criminal_legal_aid_transfer"),
            ("法律援助通知", "criminal_legal_aid_notice"),
            ("律师会见安排", "criminal_lawyer_meeting"),
        ]
        self.period_methods = {
            "admin_continuing_interrogation": CaseDateCalculator.admin_continuing_interrogation,
            "admin_case_transfer": CaseDateCalculator.admin_case_transfer,
            "admin_recusal_decision": CaseDateCalculator.admin_recusal_decision,
            "admin_quick_case": CaseDateCalculator.admin_quick_case,
            "admin_serving_decision": CaseDateCalculator.admin_serving_decision,
            "admin_public_notice": CaseDateCalculator.admin_public_notice,
            "admin_subpoena_examination": CaseDateCalculator.admin_subpoena_examination,
            "admin_appraisal_serving": CaseDateCalculator.admin_appraisal_serving,
            "admin_re_appraisal_application": CaseDateCalculator.admin_re_appraisal_application,
            "admin_preserve_evidence": CaseDateCalculator.admin_preserve_evidence,
            "admin_seizure_period": CaseDateCalculator.admin_seizure_period,
            "admin_hearing_application": CaseDateCalculator.admin_hearing_application,
            "admin_hearing_acceptance": CaseDateCalculator.admin_hearing_acceptance,
            "admin_hearing_notice": CaseDateCalculator.admin_hearing_notice,
            "admin_hearing_hold": CaseDateCalculator.admin_hearing_hold,
            "admin_case_handling_period": CaseDateCalculator.admin_case_handling_period,
            "admin_foreigner_detention": CaseDateCalculator.admin_foreigner_detention,
            "admin_foreigner_restriction": CaseDateCalculator.admin_foreigner_restriction,
            "admin_enhanced_punishment": CaseDateCalculator.admin_enhanced_punishment,
            "admin_minor_execution": CaseDateCalculator.admin_minor_execution,
            "criminal_summons": CaseDateCalculator.criminal_summons,
            "criminal_bail": CaseDateCalculator.criminal_bail,
            "criminal_residential_surveillance": CaseDateCalculator.criminal_residential_surveillance,
            "criminal_detention_period": CaseDateCalculator.criminal_detention_period,
            "criminal_review_arrest": CaseDateCalculator.criminal_review_arrest,
            "criminal_arrest_reconsideration": CaseDateCalculator.criminal_arrest_reconsideration,
            "criminal_arrest_review": CaseDateCalculator.criminal_arrest_review,
            "criminal_detention_after_arrest": CaseDateCalculator.criminal_detention_after_arrest,
            "criminal_detention_extend1": CaseDateCalculator.criminal_detention_extend1,
            "criminal_detention_extend2": CaseDateCalculator.criminal_detention_extend2,
            "criminal_detention_extend3": CaseDateCalculator.criminal_detention_extend3,
            "criminal_prosecution_review": CaseDateCalculator.criminal_prosecution_review,
            "criminal_legal_aid_transfer": CaseDateCalculator.criminal_legal_aid_transfer,
            "criminal_legal_aid_notice": CaseDateCalculator.criminal_legal_aid_notice,
            "criminal_lawyer_meeting": CaseDateCalculator.criminal_lawyer_meeting,
        }
        self.option_configs = {
            "admin_continuing_interrogation": {
                "label": "盘问类型：",
                "options": ["一般（12小时）", "延长（24小时）", "最大（48小时）"],
                "values": ["general", "extend", "max"]
            },
            "admin_serving_decision": {
                "label": "送达类型：",
                "options": ["治安处罚（2日）", "其他处罚（7日）"],
                "values": [True, False]
            },
            "admin_subpoena_examination": {
                "label": "询问类型（2026新法）：",
                "options": ["一般（8小时）", "人数众多/身份不明（12小时）", "可能拘留（24小时）"],
                "values": ["general", "multi_person", "may_detention"]
            },
            "admin_seizure_period": {
                "label": "案件类型：",
                "options": ["一般（30日）", "重大复杂（60日）"],
                "values": [False, True]
            },
            "admin_case_handling_period": {
                "label": "办案期限（2026新法）：",
                "options": ["一般（30日）", "第一次延长（60日）", "第二次延长（90日，最长）"],
                "values": [0, 1, 2]
            },
            "criminal_summons": {
                "label": "案件类型：",
                "options": ["一般（12小时）", "特别重大（24小时）"],
                "values": [False, True]
            },
            "criminal_detention_period": {
                "label": "拘留类型：",
                "options": ["一般（3日）", "延长（7日）", "流窜作案（30日）"],
                "values": ["general", "extend", "max"]
            },
            "criminal_prosecution_review": {
                "label": "审查类型：",
                "options": ["一般（1个月）", "重大复杂（延长15日）"],
                "values": [False, True]
            },
        }
        self.on_case_type_change()

    def on_case_type_change(self):
        case_type = self.case_type_var.get()
        options = self.admin_options if case_type == "行政案件" else self.criminal_options
        self.period_combo['values'] = [opt[0] for opt in options]
        self.period_combo.set(options[0][0])
        self.on_period_change()

    def on_period_change(self, event=None):
        period_name = self.period_var.get()
        case_type = self.case_type_var.get()
        options = self.admin_options if case_type == "行政案件" else self.criminal_options
        period_key = next((k for n, k in options if n == period_name), None)
        if period_key and period_key in self.option_configs:
            config = self.option_configs[period_key]
            self.option_frame.configure(text=config['label'])
            self.option_combo['values'] = config['options']
            self.option_var.set(config['options'][0])
            self.option_combo.pack(fill=tk.X, padx=5)
        else:
            self.option_combo.pack_forget()
        self.calculate()

    def on_option_change(self, event=None):
        self.calculate()

    def calculate(self):
        try:
            start_date = self.date_picker.get_date()
            period_name = self.period_var.get()
            case_type = self.case_type_var.get()
            options = self.admin_options if case_type == "行政案件" else self.criminal_options
            period_key = next((k for n, k in options if n == period_name), None)
            if not period_key:
                self.result_frame.show_error("请选择有效的期限类型")
                return

            option_value = self.option_var.get()
            config = self.option_configs.get(period_key)
            if config and option_value in config['options']:
                idx = config['options'].index(option_value)
                option_value = config['values'][idx]

            method = self.period_methods.get(period_key)
            if method:
                result = method(start_date, option_value)
                if result:
                    self.result_frame.show_result(result)
                    self.status_label.config(text="计算完成", foreground='#006600')
                else:
                    self.result_frame.show_error("计算失败")
            else:
                self.result_frame.show_error("未找到计算方法")
        except Exception as e:
            self.result_frame.show_error(f"错误：{str(e)}")
            self.status_label.config(text=f"错误：{str(e)}", foreground='#cc0000')

    def clear_all(self):
        self.result_frame.clear()
        self.status_label.config(text="已清空", foreground='#666666')

    def copy_result(self):
        text = self.result_frame.result_text.get(1.0, tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_label.config(text="已复制", foreground='#006600')
            messagebox.showinfo("提示", "结果已复制到剪贴板")

    def save_record(self):
        text = self.result_frame.result_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("提示", "没有可保存的内容")
            return
        save_dir = Path.home() / "Documents" / "办案日期计算记录"
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = save_dir / f"计算记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
            f.write(f"\n\n保存时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        self.status_label.config(text=f"已保存", foreground='#006600')
        messagebox.showinfo("保存成功", f"记录已保存到：\n{filename}")


def main():
    root = tk.Tk()
    app = CaseDateCalculatorGUI(root)
    root.update_idletasks()
    w, h = root.winfo_width(), root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f'{w}x{h}+{x}+{y}')
    root.mainloop()


if __name__ == "__main__":
    main()