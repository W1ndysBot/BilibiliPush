# script/BilibiliPush/main.py

import logging
import os
import sys
import re
import json
import requests

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import *
from app.api import *
from app.switch import load_switch, save_switch


# 数据存储路径，实际开发时，请将BilibiliPush替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "BilibiliPush",
)


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "BilibiliPush")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "BilibiliPush", status)


# 处理元事件，用于启动时确保数据目录存在
async def handle_BilibiliPush_meta_event(websocket):
    os.makedirs(DATA_DIR, exist_ok=True)


# 处理开关状态
async def toggle_function_status(websocket, group_id, message_id, authorized):
    if not authorized:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]❌❌❌你没有权限对BilibiliPush功能进行操作,请联系管理员。",
        )
        return

    if load_function_status(group_id):
        save_function_status(group_id, False)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]🚫🚫🚫BilibiliPush功能已关闭",
        )
    else:
        save_function_status(group_id, True)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]✅✅✅BilibiliPush功能已开启",
        )


# 加载直播订阅文件
def load_live_subscription(group_id):
    file_path = os.path.join(DATA_DIR, f"{group_id}_live_subscription.json")
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        subscriptions = json.load(f)
    return subscriptions


# 保存直播订阅文件
def save_live_subscription(group_id, bilibili_UID):
    file_path = os.path.join(DATA_DIR, f"{group_id}_live_subscription.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            subscriptions = json.load(f)
    else:
        subscriptions = []

    if bilibili_UID not in subscriptions:
        subscriptions.append(bilibili_UID)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(subscriptions, f, ensure_ascii=False, indent=4)


# 加载动态订阅文件
def load_dynamic_subscription(group_id):
    file_path = os.path.join(DATA_DIR, f"{group_id}_dynamic_subscription.json")
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        subscriptions = json.load(f)
    return subscriptions


# 保存动态订阅文件
def save_dynamic_subscription(group_id, bilibili_UID):
    file_path = os.path.join(DATA_DIR, f"{group_id}_dynamic_subscription.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            subscriptions = json.load(f)
    else:
        subscriptions = []

    if bilibili_UID not in subscriptions:
        subscriptions.append(bilibili_UID)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(subscriptions, f, ensure_ascii=False, indent=4)


# 添加直播订阅
async def add_live_subscription(websocket, group_id, message_id, raw_message):
    try:
        match = re.match(r"^订阅直播.*?(\d+)$", raw_message)
        if match:
            bilibili_UID = match.group(1)
        else:
            return
        # 检查是否已订阅
        if bilibili_UID in load_live_subscription(group_id):
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]本群已订阅UID为{bilibili_UID}的主播",
            )
            return
        # 添加订阅
        save_live_subscription(group_id, bilibili_UID)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]已订阅UID为{bilibili_UID}的主播",
        )
    except Exception as e:
        logging.error(f"添加直播订阅失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]添加直播订阅失败，错误信息：{e}",
        )


# 取消直播订阅
async def delete_live_subscription(websocket, group_id, message_id, raw_message):
    try:
        match = re.match(r"^取消订阅直播.*?(\d+)$", raw_message)
        if match:
            bilibili_UID = match.group(1)
        else:
            return
        # 检查是否已订阅
        if bilibili_UID not in load_live_subscription(group_id):
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]本群未订阅UID为{bilibili_UID}的主播",
            )
            return
        # 删除订阅
        subscriptions = load_live_subscription(group_id)
        subscriptions.remove(bilibili_UID)
        with open(
            os.path.join(DATA_DIR, f"{group_id}_live_subscription.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(subscriptions, f, ensure_ascii=False, indent=4)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]已取消订阅UID为{bilibili_UID}的主播",
        )
    except Exception as e:
        logging.error(f"删除直播订阅失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]删除直播订阅失败，错误信息：{e}",
        )


# 添加动态订阅
async def add_dynamic_subscription(websocket, group_id, message_id, raw_message):
    try:
        match = re.match(r"^订阅动态.*?(\d+)$", raw_message)
        if match:
            bilibili_UID = match.group(1)
        else:
            return
        # 检查是否已订阅
        if bilibili_UID in load_dynamic_subscription(group_id):
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]本群已订阅UID为{bilibili_UID}的动态",
            )
            return
        # 添加订阅
        save_dynamic_subscription(group_id, bilibili_UID)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]已订阅UID为{bilibili_UID}的动态",
        )
    except Exception as e:
        logging.error(f"添加动态订阅失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]添加动态订阅失败，错误信息：{e}",
        )


# 取消动态订阅
async def delete_dynamic_subscription(websocket, group_id, message_id, raw_message):
    try:
        match = re.match(r"^取消订阅动态.*?(\d+)$", raw_message)
        if match:
            bilibili_UID = match.group(1)
        else:
            return
        # 检查是否已订阅
        if bilibili_UID not in load_dynamic_subscription(group_id):
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]本群未订阅UID为{bilibili_UID}的动态",
            )
            return
        # 删除订阅
        subscriptions = load_dynamic_subscription(group_id)
        subscriptions.remove(bilibili_UID)
        with open(
            os.path.join(DATA_DIR, f"{group_id}_dynamic_subscription.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(subscriptions, f, ensure_ascii=False, indent=4)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]已取消订阅UID为{bilibili_UID}的动态",
        )
    except Exception as e:
        logging.error(f"删除动态订阅失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]删除动态订阅失败，错误信息：{e}",
        )


async def get_login_qr(websocket, group_id, message_id, raw_message):
    """
    获取登录二维码
    """
    try:
        match = re.match(r"^请求登录$", raw_message)
        if match:
            # 发送请求获取二维码和秘钥
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(
                "https://passport.bilibili.com/x/passport-login/web/qrcode/generate",
                headers=headers,
            )
            if response.status_code == 200:
                data = response.json()
                if data["code"] == 0:
                    qr_url = data["data"]["url"]
                    qrcode_key = data["data"]["qrcode_key"]

                    # 发送二维码URL给用户
                    await send_group_msg(
                        websocket,
                        group_id,
                        f"[CQ:reply,id={message_id}]请复制下面地址粘贴到哔哩哔哩客户端确认登录，确认登录后请在群里发送【确认登录】\n\n{qr_url}",
                    )

                    # 保存扫码登录秘钥到本地文件
                    with open(
                        os.path.join(DATA_DIR, "qrcode_key.txt"), "w", encoding="utf-8"
                    ) as f:
                        f.write(qrcode_key)
                else:
                    logging.error(f"获取二维码失败: {data['message']}")
            else:
                logging.error(f"请求二维码失败，状态码: {response.status_code}")
    except Exception as e:
        logging.error(f"获取登录二维码失败: {e}")


async def scan_login(websocket, group_id, message_id, raw_message):
    """
    扫码登录
    """
    try:
        match = re.match(r"^确认登录$", raw_message)
        if match:
            # 读取之前保存的 qrcode_key
            with open(
                os.path.join(DATA_DIR, "qrcode_key.txt"), "r", encoding="utf-8"
            ) as f:
                qrcode_key = f.read().strip()

            # 轮询二维码状态
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://passport.bilibili.com/login",
            }
            response = requests.get(
                "https://passport.bilibili.com/x/passport-login/web/qrcode/poll",
                params={"qrcode_key": qrcode_key},
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                if data["code"] == 0:
                    poll_data = data["data"]
                    if poll_data["code"] == 0:
                        # 登录成功，提取并保存 SESSDATA
                        cookies = response.cookies.get_dict()
                        sessdata = cookies.get("SESSDATA", "")

                        with open(
                            os.path.join(DATA_DIR, "sessdata.txt"),
                            "w",
                            encoding="utf-8",
                        ) as f:
                            f.write(sessdata)
                        await send_group_msg(
                            websocket,
                            group_id,
                            f"[CQ:reply,id={message_id}]登录成功，SESSDATA已保存。",
                        )
                    elif poll_data["code"] == 86090:
                        await send_group_msg(
                            websocket,
                            group_id,
                            f"[CQ:reply,id={message_id}]登录未确认，请在手机上确认。",
                        )
                    elif poll_data["code"] == 86101:
                        await send_group_msg(
                            websocket,
                            group_id,
                            f"[CQ:reply,id={message_id}]检测到链接未授权，请发送【请求登录】重新获取。",
                        )
                    elif poll_data["code"] == 86038:
                        await send_group_msg(
                            websocket,
                            group_id,
                            f"[CQ:reply,id={message_id}]会话已失效，请发送【请求登录】重新获取。",
                        )
                else:
                    logging.error(f"扫码登录失败: {data['message']}")
            else:
                logging.error(f"请求扫码登录失败，状态码: {response.status_code}")
    except Exception as e:
        logging.error(f"扫码登录失败: {e}")


# 群消息处理函数
async def handle_BilibiliPush_group_message(websocket, msg):
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
            await add_live_subscription(websocket, group_id, message_id, raw_message)
            await add_dynamic_subscription(websocket, group_id, message_id, raw_message)
            await delete_live_subscription(websocket, group_id, message_id, raw_message)
            await delete_dynamic_subscription(
                websocket, group_id, message_id, raw_message
            )
            await get_login_qr(websocket, group_id, message_id, raw_message)
            await scan_login(websocket, group_id, message_id, raw_message)
            # 查询订阅
            if raw_message == "查询订阅":
                await query_subscriptions(websocket, group_id, message_id)
                return
    except Exception as e:
        logging.error(f"处理BilibiliPush群消息失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]处理BilibiliPush群消息失败，错误信息："
            + str(e),
        )
        return


async def check_live_and_dynamic(websocket):
    """
    定时检查直播有无变化
    """
    await check_live(websocket)
    await check_dynamic(websocket)


def get_previous_live_status(group_id, UID):
    """
    获取上一次的直播状态
    """
    file_path = os.path.join(DATA_DIR, f"{group_id}_live_status.json")
    if not os.path.exists(file_path):
        # 初始化文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        return 0  # 默认状态为0，表示未开播
    with open(file_path, "r", encoding="utf-8") as f:
        subscriptions = json.load(f)
    return subscriptions.get(UID, 0)


def save_live_status(group_id, UID, live_status):
    """
    保存直播状态
    """
    file_path = os.path.join(DATA_DIR, f"{group_id}_live_status.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            subscriptions = json.load(f)
    else:
        subscriptions = {}

    subscriptions[UID] = live_status

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(subscriptions, f, ensure_ascii=False, indent=4)


def save_user_name_mapping(UID, user_name):
    """
    保存UID和用户名的映射到本地文件
    """
    file_path = os.path.join(DATA_DIR, "uid_name_mapping.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            uid_name_mapping = json.load(f)
    else:
        uid_name_mapping = {}

    uid_name_mapping[UID] = user_name

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(uid_name_mapping, f, ensure_ascii=False, indent=4)


def get_user_name(UID):
    """
    获取主播名字，优先从本地文件读取，如果没有则通过API获取
    """
    file_path = os.path.join(DATA_DIR, "uid_name_mapping.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            uid_name_mapping = json.load(f)
    else:
        uid_name_mapping = {}

    if UID in uid_name_mapping:
        return uid_name_mapping[UID]

    # 如果本地没有，使用API获取
    user_info_url = (
        f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={UID}"
    )
    # 获取cookie
    with open(os.path.join(DATA_DIR, "sessdata.txt"), "r", encoding="utf-8") as f:
        sessdata = f.read().strip()
    headers = {
        "Cookie": f"SESSDATA={sessdata}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    try:
        user_response = requests.get(user_info_url, headers=headers)
        if user_response.status_code == 200:
            user_data = user_response.json()

            if "data" in user_data and "items" in user_data["data"]:
                user_name = user_data["data"]["items"][0]["modules"]["module_author"][
                    "name"
                ]
                # 使用新的函数保存映射
                save_user_name_mapping(UID, user_name)
                return user_name
            else:
                logging.error("API响应中缺少预期的'data'或'items'字段")
        else:
            logging.error(f"请求用户信息失败，状态码: {user_response.status_code}")
    except Exception as e:
        logging.error(f"获取用户信息时发生异常: {e}")

    return "未知用户"


# 修改 query_subscriptions 函数
async def query_subscriptions(websocket, group_id, message_id):
    """
    查询已订阅的直播和动态
    """
    try:
        # 查询直播订阅
        live_subscriptions = load_live_subscription(group_id)
        live_message = (
            f"群【{group_id}】已订阅直播如下\n"
            + "\n".join(
                [f"{get_user_name(uid)} (UID: {uid})" for uid in live_subscriptions]
            )
            if live_subscriptions
            else f"群【{group_id}】没有已订阅的直播"
        )

        # 查询动态订阅
        dynamic_subscriptions = load_dynamic_subscription(group_id)
        dynamic_message = (
            f"群【{group_id}】已订阅动态如下\n"
            + "\n".join(
                [f"{get_user_name(uid)} (UID: {uid})" for uid in dynamic_subscriptions]
            )
            if dynamic_subscriptions
            else f"群【{group_id}】没有已订阅的动态"
        )

        # 发送查询结果
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]{live_message}\n\n{dynamic_message}",
        )

    except Exception as e:
        logging.error(f"查询订阅失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]查询订阅失败，错误信息：{e}",
        )


# 修改 check_live 函数
async def check_live(websocket):
    """
    定时检查直播有无变化
    """
    try:
        # 获取所有有数据的群，检查文件结尾是否是live_subscription.json
        files = os.listdir(DATA_DIR)
        groups = []
        for file in files:
            if file.endswith("_live_subscription.json"):
                group_id = file.split("_")[0]
                if group_id not in groups:
                    groups.append(group_id)

        # 对于每个群检查是否开启
        for group_id in groups:
            if load_function_status(group_id):
                subscriptions = load_live_subscription(group_id)
                for UID in subscriptions:
                    # 获取UID的直播信息
                    url = f"https://api.live.bilibili.com/room/v1/Room/getRoomInfoOld?mid={UID}"
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    }
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        liveStatus = data.get("data").get("liveStatus")
                        PreviousStatus = get_previous_live_status(group_id, UID)
                        if liveStatus != PreviousStatus:
                            save_live_status(group_id, UID, liveStatus)
                            user_name = get_user_name(UID)
                            # 保存映射
                            save_user_name_mapping(UID, user_name)
                            if liveStatus == 1:
                                # 在直播状态为1时代表开播
                                title = data["data"]["title"]
                                url = data["data"]["url"]
                                cover = data["data"]["cover"]
                                online = data["data"]["online"]
                                await send_group_msg(
                                    websocket,
                                    group_id,
                                    f"UID为【{UID}】的主播【{user_name}】开播了\n"
                                    f"标题: {title}\n"
                                    f"观看人数: {online}\n"
                                    f"直播地址: {url}\n"
                                    f"[CQ:image,file={cover}]",
                                )
                            elif liveStatus == 0:
                                await send_group_msg(
                                    websocket,
                                    group_id,
                                    f"UID为【{UID}】的主播【{user_name}】关播了",
                                )
    except Exception as e:
        logging.error(f"定时检查直播有无变化失败: {e}")


def is_new_dynamic(group_id, UID, dynamic_id):
    """
    检查是否是新动态
    """
    file_path = os.path.join(DATA_DIR, f"{group_id}_dynamic_status.json")
    if not os.path.exists(file_path):
        # 初始化文件并保存最新动态ID
        with open(file_path, "w", encoding="utf-8") as f:
            subscriptions = {UID: [dynamic_id]}
            json.dump(subscriptions, f, ensure_ascii=False, indent=4)
        return False  # 初始化时不视为新动态
    with open(file_path, "r", encoding="utf-8") as f:
        subscriptions = json.load(f)
    return dynamic_id not in subscriptions.get(UID, [])


def save_latest_dynamic_id(group_id, UID, dynamic_id):
    """
    保存最新动态id
    """
    file_path = os.path.join(DATA_DIR, f"{group_id}_dynamic_status.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            subscriptions = json.load(f)
    else:
        subscriptions = {}

    if UID not in subscriptions:
        subscriptions[UID] = []

    subscriptions[UID].append(dynamic_id)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(subscriptions, f, ensure_ascii=False, indent=4)


async def check_dynamic(websocket):
    """
    定时检查有无新动态
    """
    try:
        # 获取所有有数据的群，检查文件结尾是否是dynamic_subscription.json
        files = os.listdir(DATA_DIR)
        groups = []
        for file in files:
            if file.endswith("_dynamic_subscription.json"):
                group_id = file.split("_")[0]
                if group_id not in groups:
                    groups.append(group_id)

        # 对于每个群检查是否开启
        for group_id in groups:
            if load_function_status(group_id):
                subscriptions = load_dynamic_subscription(group_id)
                for UID in subscriptions:
                    url = f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space?host_mid={UID}"
                    # 获取cookie
                    with open(
                        os.path.join(DATA_DIR, "sessdata.txt"), "r", encoding="utf-8"
                    ) as f:
                        sessdata = f.read().strip()
                    headers = {
                        "Cookie": f"SESSDATA={sessdata}",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    }
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        # 检查是否返回错误代码 -352
                        if data["code"] == -352:
                            logging.warning(f"请求被限制: {data['message']}")
                            await send_group_msg(
                                websocket,
                                group_id,
                                f"监控用户动态的请求被限制，可能是由于访问cookie过期。请发送【请求登录】进行登录以更新cookie后重试。",
                            )
                            return  # 退出循环，不再进行接下来的扫描
                        # 提取最近一次动态的信息
                        if (
                            data["code"] == 0
                            and "data" in data
                            and "items" in data["data"]
                            and data["data"]["items"]  # 确保 items 列表不为空
                        ):
                            latest_dynamic = data["data"]["items"][0]
                            dynamic_id = latest_dynamic["id_str"]
                            if is_new_dynamic(group_id, UID, dynamic_id):
                                save_latest_dynamic_id(group_id, UID, dynamic_id)
                                author_name = latest_dynamic["modules"][
                                    "module_author"
                                ]["name"]
                                pub_time = latest_dynamic["modules"]["module_author"][
                                    "pub_time"
                                ]
                                dynamic_type = latest_dynamic["type"]
                                dynamic_url = latest_dynamic["modules"][
                                    "module_author"
                                ]["jump_url"]

                                # 处理不同类型的动态
                                if "desc" in latest_dynamic["modules"]["module_dynamic"]:
                                    dynamic_text = latest_dynamic["modules"]["module_dynamic"]["desc"]["text"]
                                else:
                                    dynamic_text = "未能解析动态内容"

                                # 构建基础消息模板
                                message = (
                                    f"UID:【{UID}】发布了新动态:\n"
                                    f"作者: {author_name}\n"
                                    f"发布时间: {pub_time}\n"
                                    f"动态内容: {dynamic_text}\n"
                                    f"动态类型: {dynamic_type}\n"
                                    f"动态地址: {dynamic_url}"
                                )

                                # 根据动态类型添加额外内容
                                if dynamic_type == "DYNAMIC_TYPE_DRAW":
                                    # 图片动态
                                    if "items" in latest_dynamic["modules"]["module_dynamic"]["major"]["draw"]:
                                        images = latest_dynamic["modules"]["module_dynamic"]["major"]["draw"]["items"]
                                        for img in images:
                                            message += f"\n[CQ:image,file={img['src']}]"

                                elif dynamic_type == "DYNAMIC_TYPE_AV":
                                    # 视频动态
                                    video_info = latest_dynamic["modules"]["module_dynamic"]["major"]["archive"]
                                    video_title = video_info["title"]
                                    video_desc = video_info.get("desc", "")
                                    video_url = video_info["jump_url"]
                                    video_cover = video_info["cover"]
                                    
                                    message = (
                                        f"UID:【{UID}】投稿了新视频:\n"
                                        f"作者: {author_name}\n" 
                                        f"发布时间: {pub_time}\n"
                                        f"视频标题: {video_title}\n"
                                        f"视频描述: {video_desc}\n"
                                        f"视频地址: {video_url}\n"
                                        f"[CQ:image,file={video_cover}]"
                                    )
                                    
                                elif dynamic_type == "DYNAMIC_TYPE_FORWARD":
                                    # 转发动态
                                    if "orig" in latest_dynamic:
                                        orig_type = latest_dynamic["orig"]["type"]
                                        message += f"\n转发自: {orig_type}"
                                        
                                        # 处理原动态内容
                                        if "major" in latest_dynamic["orig"]["modules"]["module_dynamic"]:
                                            orig_major = latest_dynamic["orig"]["modules"]["module_dynamic"]["major"]
                                            if orig_major["type"] == "MAJOR_TYPE_DRAW":
                                                # 原动态为图片
                                                orig_images = orig_major["draw"]["items"]
                                                for img in orig_images:
                                                    message += f"\n[CQ:image,file={img['src']}]"
                                            elif orig_major["type"] == "MAJOR_TYPE_ARCHIVE":
                                                # 原动态为视频
                                                message += f"\n原视频封面: [CQ:image,file={orig_major['archive']['cover']}]"

                                else:
                                    # 其他类型动态
                                    if "desc" in latest_dynamic["modules"]["module_dynamic"]:
                                        dynamic_text = latest_dynamic["modules"]["module_dynamic"]["desc"]["text"]
                                    else:
                                        dynamic_text = "未能解析动态内容"
                                        
                                    message = (
                                        f"UID:【{UID}】发布了新动态:\n"
                                        f"作者: {author_name}\n"
                                        f"发布时间: {pub_time}\n"
                                        f"动态内容: {dynamic_text}\n"
                                        f"动态类型: {dynamic_type}\n"
                                        f"动态地址: {dynamic_url}"
                                    )

                                # 发送消息
                                await send_group_msg(websocket, group_id, message)
    except Exception as e:
        logging.error(f"定时检查有无新动态失败: {e}")
