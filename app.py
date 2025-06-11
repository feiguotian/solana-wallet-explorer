import streamlit as st
import requests
import pandas as pd

# 设置 Helius API 端点和你的 API 密钥
HELIOUS_MAINNET = "https://mainnet.helius-rpc.com/"
API_KEY = "ccf35c43-496e-4514-b595-1039601450f2"  # 替换为你的 API 密钥

st.title("Solana 钱包交易查询")

wallet_address = st.text_input("请输入 Solana 钱包地址：", "")
if not wallet_address:
    st.warning("请输入钱包地址")
else:
    try:
        # 获取账户余额
        balance_response = requests.post(
            HELIOUS_MAINNET,
            params={"api-key": API_KEY},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [wallet_address]
            }
        )
        balance_response.raise_for_status()
        balance_data = balance_response.json()
        if 'result' not in balance_data:
            st.error("数据解析错误：API 返回的数据中没有 'result' 键")
        else:
            balance = balance_data['result']['value'] / 1_000_000_000
            st.write(f"当前钱包余额：{balance} SOL")
            
            # 获取交易记录
            transactions_response = requests.post(
                HELIOUS_MAINNET,
                params={"api-key": API_KEY},
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSignaturesForAddress",
                    "params": [wallet_address]
                }
            )
            transactions_response.raise_for_status()
            transactions_data = transactions_response.json()
            if 'result' not in transactions_data:
                st.error("数据解析错误：API 返回的数据中没有 'result' 键")
            else:
                transactions = transactions_data['result']
                transaction_list = []
                for tx in transactions:
                    tx_details_response = requests.post(
                        HELIOUS_MAINNET,
                        params={"api-key": API_KEY},
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getTransaction",
                            "params": [tx['signature']]
                        }
                    )
                    tx_details_response.raise_for_status()
                    tx_details_data = tx_details_response.json()
                    if 'result' not in tx_details_data:
                        st.error("数据解析错误：API 返回的数据中没有 'result' 键")
                        break
                    tx_details = tx_details_data['result']
                    tx_type = "未知"
                    tx_amount = 0.0
                    other_address = "未知"
                    tx_time = "未知"
                    tx_balance = "未知"
                    if tx_details['transaction']['message']['accountKeys'][0] == wallet_address:
                        tx_type = "转入"
                    else:
                        tx_type = "转出"
                    tx_amount = 0.01
                    other_address = tx_details['transaction']['message']['accountKeys'][1] if len(tx_details['transaction']['message']['accountKeys']) > 1 else "未知"
                    tx_time = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    transaction_list.append({
                        "时间": tx_time,
                        "类型": tx_type,
                        "金额 (SOL)": tx_amount,
                        "对方地址": other_address,
                        "交易后余额 (SOL)": tx_balance
                    })
                else:
                    if transaction_list:
                        df = pd.DataFrame(transaction_list)
                        st.write("交易记录：")
                        st.dataframe(df)
                    else:
                        st.info("未找到交易记录")
    except requests.exceptions.RequestException as e:
        st.error(f"网络请求出错：{e}")
    except KeyError as e:
        st.error(f"数据解析错误：缺失键 {e}")
    except Exception as e:
        st.error(f"查询出错：{e}")
