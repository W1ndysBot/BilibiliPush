# script/BilibilliPush/main.py

import logging
import os
import sys
import re
import json

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import *
from app.api import *
from app.switch import load_switch, save_switch


# 数据存储路径，实际开发时，请将BilibilliPush替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "BilibilliPush",
)


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "BilibilliPush")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "BilibilliPush", status)


# 处理元事件，用于启动时确保数据目录存在
async def handle_BilibilliPush_meta_event(websocket, msg):
    os.makedirs(DATA_DIR, exist_ok=True)


# 处理开关状态
async def toggle_function_status(websocket, group_id, message_id, authorized):
    if not authorized:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]❌❌❌你没有权限对BilibilliPush功能进行操作,请联系管理员。",
        )
        return

    if load_function_status(group_id):
        save_function_status(group_id, False)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]🚫🚫🚫BilibilliPush功能已关闭",
        )
    else:
        save_function_status(group_id, True)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]✅✅✅BilibilliPush功能已开启",
        )


# 加载直播订阅文件
def load_live_subscription(group_id, user_id):
    file_path = os.path.join(DATA_DIR, f"{group_id}_live.json")
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        subscriptions = json.load(f)
    return subscriptions.get(user_id, [])


# 保存直播订阅文件
def save_live_subscription(group_id, user_id, bilibili_uid):
    file_path = os.path.join(DATA_DIR, f"{group_id}_live.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            subscriptions = json.load(f)
    else:
        subscriptions = {}

    if user_id not in subscriptions:
        subscriptions[user_id] = []

    if bilibili_uid not in subscriptions[user_id]:
        subscriptions[user_id].append(bilibili_uid)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(subscriptions, f, ensure_ascii=False, indent=4)


# 加载动态订阅文件
def load_dynamic_subscription(group_id, user_id):
    file_path = os.path.join(DATA_DIR, f"{group_id}_dynamic.json")
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        subscriptions = json.load(f)
    return subscriptions.get(user_id, [])


# 保存动态订阅文件
def save_dynamic_subscription(group_id, user_id, bilibili_uid):
    file_path = os.path.join(DATA_DIR, f"{group_id}_dynamic.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            subscriptions = json.load(f)
    else:
        subscriptions = {}

    if user_id not in subscriptions:
        subscriptions[user_id] = []

    if bilibili_uid not in subscriptions[user_id]:
        subscriptions[user_id].append(bilibili_uid)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(subscriptions, f, ensure_ascii=False, indent=4)


# 添加直播订阅
async def add_live_subscription(websocket, group_id, user_id, message_id, raw_message):
    try:
        match = re.match(r"^订阅直播(\d+)$", raw_message)
        if match:
            bilibili_uid = match.group(1)
        else:
            return
        # 检查是否已订阅
        if bilibili_uid in load_live_subscription(group_id, user_id):
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]你已订阅uid为{bilibili_uid}的主播",
            )
            return
        # 添加订阅
        save_live_subscription(group_id, user_id, bilibili_uid)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]已订阅uid为{bilibili_uid}的主播",
        )
    except Exception as e:
        logging.error(f"添加直播订阅失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]添加直播订阅失败，错误信息：{e}",
        )


# 取消直播订阅
async def delete_live_subscription(
    websocket, group_id, user_id, message_id, raw_message
):
    try:
        match = re.match(r"^取消订阅直播(\d+)$", raw_message)
        if match:
            bilibili_uid = match.group(1)
        else:
            return
        # 检查是否已订阅
        if bilibili_uid not in load_live_subscription(group_id, user_id):
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]你未订阅uid为{bilibili_uid}的主播",
            )
            return
        # 删除订阅
        save_live_subscription(group_id, user_id, bilibili_uid)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]已取消订阅uid为{bilibili_uid}的主播",
        )

    except Exception as e:
        logging.error(f"删除直播订阅失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]删除直播订阅失败，错误信息：{e}",
        )


# 添加动态订阅
async def add_dynamic_subscription(
    websocket, group_id, user_id, message_id, raw_message
):
    try:
        match = re.match(r"^订阅动态(\d+)$", raw_message)
        if match:
            bilibili_uid = match.group(1)
        else:
            return
        # 检查是否已订阅
        if bilibili_uid in load_dynamic_subscription(group_id, user_id):
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]你已订阅uid为{bilibili_uid}的动态",
            )
            return
        # 添加订阅
        save_dynamic_subscription(group_id, user_id, bilibili_uid)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]已订阅uid为{bilibili_uid}的动态",
        )
    except Exception as e:
        logging.error(f"添加动态订阅失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]添加动态订阅失败，错误信息：{e}",
        )


# 取消动态订阅
async def delete_dynamic_subscription(
    websocket, group_id, user_id, message_id, raw_message
):
    try:
        match = re.match(r"^取消订阅动态(\d+)$", raw_message)
        if match:
            bilibili_uid = match.group(1)
        else:
            return

        # 检查是否已订阅
        if bilibili_uid not in load_dynamic_subscription(group_id, user_id):
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]你未订阅uid为{bilibili_uid}的动态",
            )
            return
        # 删除订阅
        save_dynamic_subscription(group_id, user_id, bilibili_uid)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]已取消订阅uid为{bilibili_uid}的动态",
        )
    except Exception as e:
        logging.error(f"删除动态订阅失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]删除动态订阅失败，错误信息：{e}",
        )


# 群消息处理函数
async def handle_BilibilliPush_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))
        authorized = user_id in owner_id

        # 开关
        if raw_message == "bilipush":
            await toggle_function_status(websocket, group_id, message_id, authorized)
            return
        # 检查是否开启
        if load_function_status(group_id):
            await add_live_subscription(
                websocket, group_id, user_id, message_id, raw_message
            )
            await add_dynamic_subscription(
                websocket, group_id, user_id, message_id, raw_message
            )
            await delete_live_subscription(
                websocket, group_id, user_id, message_id, raw_message
            )
            await delete_dynamic_subscription(
                websocket, group_id, user_id, message_id, raw_message
            )
    except Exception as e:
        logging.error(f"处理BilibilliPush群消息失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]处理BilibilliPush群消息失败，错误信息："
            + str(e),
        )
        return


# 定时检查直播和动态
async def check_live_and_dynamic():
    pass
