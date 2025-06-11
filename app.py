import streamlit as st
import requests
import pandas as pd

# Helius RPC 端点
RPC_URL = "https://mainnet.helius-rpc.com/?api-key=ccf35c43-496e-4514-b595-1039601450f2"

st.title("🔍 Solana 钱包交易查询工具")

wallet_address = st.text_input("请输入 Solana 钱包地址：").strip()

if wallet_address:
    try:
        # ---------- 查询余额 ----------
        balance_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [wallet_address]
        }
        balance_response = requests.post(RPC_URL, json=balance_payload)
        balance_json = balance_response.json()

        # 错误检测
        if 'result' not in balance_json or balance_json['result'] is None:
            st.error("❌ 获取余额失败，API 无返回结果")
            st.json(balance_json)  # 输出原始结果调试用
        else:
            balance = balance_json['result']['value'] / 1_000_000_000
            st.success(f"💰 当前钱包余额：{balance:.4f} SOL")

        # ---------- 查询交易签名 ----------
        signatures_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [wallet_address, {"limit": 10}]  # 默认只查10条避免过多
        }
        sig_response = requests.post(RPC_URL, json=sig_payload := signatures_payload)
        sig_json = sig_response.json()

        if 'result' not in sig_json or sig_json['result'] is None:
            st.error("❌ 获取交易记录失败，API 无返回结果")
            st.json(sig_json)
        else:
            transactions = sig_json['result']
            if not transactions:
                st.info("该地址没有任何交易记录")
            else:
                tx_list = []
                for tx in transactions:
                    sig = tx.get("signature")
                    if not sig:
                        continue
                    
                    # ---------- 查询交易详情 ----------
                    tx_detail_payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getTransaction",
                        "params": [sig, {"encoding": "json", "commitment": "confirmed"}]
                    }
                    detail_response = requests.post(RPC_URL, json=tx_detail_payload)
                    detail_json = detail_response.json()

                    if 'result' not in detail_json or detail_json['result'] is None:
                        continue
                    
                    detail = detail_json['result']
                    tx_type = "未知"
                    amount_sol = 0.0
                    counterparty = "-"
                    timestamp = "-"
                    post_balance = "-"

                    # 处理转账信息
                    try:
                        msg = detail['transaction']['message']
                        acc_keys = msg['accountKeys']
                        instructions = msg.get("instructions", [])
                        meta = detail.get("meta", {})

                        if acc_keys and len(acc_keys) >= 2:
                            from_addr = acc_keys[0]
                            to_addr = acc_keys[1]
                            counterparty = to_addr if from_addr == wallet_address else from_addr
                            tx_type = "转出" if from_addr == wallet_address else "转入"
                        
                        if meta and 'postBalances' in meta:
                            sol = meta['postBalances'][0] / 1e9
                            post_balance = f"{sol:.4f}"

                        if 'blockTime' in detail:
                            timestamp = pd.to_datetime(detail['blockTime'], unit="s").strftime("%Y-%m-%d %H:%M:%S")

                        # 转账金额（近似值）
                        if meta and 'preBalances' in meta and 'postBalances' in meta:
                            pre = meta['preBalances'][0] / 1e9
                            post = meta['postBalances'][0] / 1e9
                            amount_sol = abs(pre - post)

                    except Exception as e:
                        st.warning(f"⚠️ 解析交易 {sig} 时出错：{e}")
                    
                    tx_list.append({
                        "时间": timestamp,
                        "类型": tx_type,
                        "金额 (SOL)": f"{amount_sol:.4f}",
                        "对方地址": counterparty,
                        "交易后余额 (SOL)": post_balance
                    })

                # 显示交易数据表格
                if tx_list:
                    df = pd.DataFrame(tx_list)
                    st.subheader("📄 最近交易记录：")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("❗ 交易解析失败，可能格式不一致或尚未完成确认。")

    except requests.exceptions.RequestException as e:
        st.error(f"🌐 网络请求出错：{e}")
    except Exception as e:
        st.error(f"❗ 程序运行时出错：{e}")
else:
    st.info("请输入有效的钱包地址以开始查询。")
