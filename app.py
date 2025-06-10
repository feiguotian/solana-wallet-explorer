import streamlit as st
import requests
import pandas as pd
from solana.rpc.api import Client
from solana.publickey import PublicKey

# 连接到 Solana 主网
solana_client = Client("https://api.mainnet-beta.solana.com")

# 设置网页标题
st.title("Solana 钱包交易查询")

# 输入钱包地址
wallet_address = st.text_input("请输入 Solana 钱包地址：", "")
if not wallet_address:
    st.warning("请输入钱包地址")
else:
    try:
        # 获取账户信息
        public_key = PublicKey(wallet_address)
        
        # 获取账户余额（以 SOL 为单位）
        balance_info = solana_client.get_balance(public_key)
        balance = balance_info['result']['value'] / 1_000_000_000  # 将 lamports 转换为 SOL
        
        # 显示余额
        st.write(f"当前钱包余额：{balance} SOL")
        
        # 获取交易记录
        transactions = solana_client.get_confirmed_signatures_for_address2(public_key)
        
        # 解析交易记录
        transaction_list = []
        for tx in transactions['result']:
            tx_details = solana_client.get_confirmed_transaction(tx['signature'])
            tx_data = tx_details['result']['transaction']
            
            # 提取交易信息
            tx_type = "未知"
            tx_amount = 0.0
            other_address = "未知"
            tx_time = "未知"
            tx_balance = "未知"
            
            # 这里简化处理，实际应用中需要更复杂的逻辑来解析交易类型和金额
            # 以下为示例数据，实际应从交易数据中解析得到
            tx_type = "转入" if tx_data['message']['accountKeys'][0] == str(public_key) else "转出"
            tx_amount = 0.01  # 示例金额
            other_address = tx_data['message']['accountKeys'][1] if len(tx_data['message']['accountKeys']) > 1 else "未知"
            tx_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")  # 示例时间
            
            # 添加到交易列表
            transaction_list.append({
                "时间": tx_time,
                "类型": tx_type,
                "金额 (SOL)": tx_amount,
                "对方地址": other_address,
                "交易后余额 (SOL)": tx_balance  # 示例余额
            })
        
        # 显示交易记录
        if transaction_list:
            df = pd.DataFrame(transaction_list)
            st.write("交易记录：")
            st.dataframe(df)
        else:
            st.info("未找到交易记录")
    
    except Exception as e:
        st.error(f"查询出错：{e}")
