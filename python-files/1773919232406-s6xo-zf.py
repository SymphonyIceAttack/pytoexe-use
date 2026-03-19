# -------------------- 优化后的核心提取逻辑 --------------------

def get_all_text_from_control(control):
    """
    遍历指定控件下的所有子节点，提取所有文本内容
    避免因为微信UI层级变化导致找不到文字
    """
    text_list = []
    # WalkControl 是 uiautomation 提供的高效遍历方法
    for c, depth in automation.WalkControl(control, includeTop=True):
        if c.ControlType == automation.ControlType.TextControl and c.Name:
            text_list.append(c.Name.strip())
    # 将提取到的所有文本用回车拼接，方便后续正则处理
    return "\n".join(text_list)

def parse_payment_info(text_block):
    """
    从完整的文本块中利用正则精准提取所需数据
    """
    info = {
        'amount': '',
        'amountAll': '',
        'sender': '',
        'timestamp': ''
    }
    
    # 1. 提取收款金额 (兼容 "收款金额￥10.00" 和 "收款金额\n￥10.00")
    amount_match = re.search(r'收款金额.*?￥\s*([\d.]+)', text_block, re.S)
    if amount_match:
        info['amount'] = amount_match.group(1)
        
    # 2. 提取来自/付款人
    sender_match = re.search(r'来自\s*([^\n]+)', text_block)
    if sender_match:
        info['sender'] = sender_match.group(1).strip()
        
    # 3. 提取到账时间
    time_match = re.search(r'到账时间[:：]?\s*([\d\-:\s]+)', text_block)
    if time_match:
        info['timestamp'] = time_match.group(1).strip()
        
    # 4. 提取总计/汇总金额 (兼容 "共计￥10.00" 或 "收款金额总额￥10.00")
    total_match = re.search(r'(?:共计|总额|汇总金额).*?￥\s*([\d.]+)', text_block, re.S)
    if total_match:
        info['amountAll'] = total_match.group(1)
    elif info['amount']: 
        # 如果没抓到总额，默认和单笔金额一致
        info['amountAll'] = info['amount'] 

    return info

def process_wechat_window(wechat_window, prev_hash):
    """
    主处理窗口逻辑
    """
    if not wechat_window.Exists(0, 0):
        print("未找到微信聊天窗口，请保持窗口独立或显示...")
        return prev_hash

    try:
        # 直接定位微信聊天记录的“消息”列表
        msg_list = wechat_window.ListControl(Name='消息')
        if not msg_list.Exists(0, 0):
            return prev_hash

        # 获取消息列表里的所有子元素（每一条消息）
        children = msg_list.GetChildren()
        if not children:
            return prev_hash

        # 从最后一条消息开始往前检查最新的3条（防止因为别人发了句废话把支付消息顶上去了）
        for item in reversed(children[-3:]):
            text_block = get_all_text_from_control(item)
            
            # 判断是不是微信支付的通知
            if "微信支付" in text_block and "收款金额" in text_block:
                
                # 为这段文本生成唯一Hash，用于判断是否是新消息
                current_hash = hashlib.md5(text_block.encode('utf-8')).hexdigest()
                
                # 如果Hash变化了，说明是新的收款记录
                if current_hash != prev_hash:
                    # 提取精准数据
                    data = parse_payment_info(text_block)
                    
                    if data['amount']: # 确保金额不为空才处理
                        last_matched_info = (f"收款金额: ￥{data['amount']}, "
                                             f"来自: {data['sender']}, "
                                             f"到账时间: {data['timestamp']}, "
                                             f"收款总额: ￥{data['amountAll']}")
                        
                        # 打印日志
                        log_message("💰 监听到新的支付信息：")
                        log_message(f"▸ {last_matched_info.replace(', ', '\n▸ ')}")
                        log_message("-" * 30)
                        
                        log_message("📡 正在请求回调接口...")
                        log_message("——— 请求回调 ———")
                        
                        # 发送请求
                        threading.Thread(target=send_http_request, args=(
                            last_matched_info, 
                            data['amount'], 
                            data['amountAll'], 
                            data['sender'], 
                            data['timestamp']
                        )).start()
                        
                        return current_hash # 返回新的 Hash 记录为上一次的状态
                break # 找到了最新的支付消息就退出循环

    except Exception as e:
        print(f"解析微信窗口时发生异常: {str(e)}")
        
    return prev_hash

# --------------------------------------------------------------