import streamlit as st
import requests
import pandas as pd

# 设置网页标题
st.title("Solana 钱包交易查询")

# 输入钱包地址
wallet_address = st.text_input("请输入 Solana 钱包地址：", "")
if not wallet_address:
    st.warning("请输入钱包地址")
else:
    try:
        # 获取账户余额
        response = requests.post("https://api.mainnet-beta.solana.com", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [wallet_address]
        })
        response.raise_for_status()  # 检查请求是否成功
        balance_data = response.json()
        if 'result' not in balance_data:
            raise ValueError("API 返回的数据中没有 'result' 键")
        balance = balance_data['result']['value'] / 1_000_000_000  # 将 lamports 转换为 SOL
        st.write(f"当前钱包余额：{balance} SOL")
        
        # 获取交易记录
        response = requests.post("https://api.mainnet-beta.solana.com", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getConfirmedSignaturesForAddress2",
            "params": [wallet_address]
        })
        response.raise_for_status()  # 检查请求是否成功
        transactions_data = response.json()
        if 'result' not in transactions_data:
            raise ValueError("API 返回的数据中没有 'result' 键")
        transactions = transactions_data['result']
        
        # 解析交易记录
        transaction_list = []
        for tx in transactions:
            tx_details_response = requests.post("https://api.mainnet-beta.solana.com", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getConfirmedTransaction",
                "params": [tx['signature']]
            })
            tx_details_response.raise_for_status()  # 检查请求是否成功
            tx_details_data = tx_details_response.json()
            if 'result' not in tx_details_data:
                raise ValueError("API 返回的数据中没有 'result' 键")
            tx_details = tx_details_data['result']
            
            # 提取交易信息
            tx_type = "未知"
            tx_amount = 0.0
            other_address = "未知"
            tx_time = "未知"
            tx_balance = "未知"
            
            # 这里简化处理，实际应用中需要更复杂的逻辑来解析交易类型和金额
            # 以下为示例数据，实际应从交易数据中解析得到
            if tx_details['transaction']['message']['accountKeys'][0] == wallet_address:
                tx_type = "转入"
            else:
                tx_type = "转出"
            tx_amount = 0.01  # 示例金额
            other_address = tx_details['transaction']['message']['accountKeys'][1] if len(tx_details['transaction']['message']['accountKeys']) > 1 else "未知"
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
    
    except requests.exceptions.RequestException as e:
        st.error(f"网络请求出错：{e}")
    except ValueError as e:
        st.error(f"数据解析错误：{e}")
    except Exception as e:
        st.error(f"查询出错：{e}")
