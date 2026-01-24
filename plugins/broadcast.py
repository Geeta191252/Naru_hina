import datetime
import time
import os
import asyncio
from logging_helper import LOGGER
from pyrogram import Client, filters, enums
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong
from pyrogram.errors import FloodWait
from database.users_chats_db import db
from info import ADMINS
from utils import users_broadcast, groups_broadcast, temp, get_readable_time, clear_junk, junk_group
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

lock = asyncio.Lock()

@Client.on_callback_query(filters.regex(r'^broadcast_cancel'))
async def broadcast_cancel(bot, query):
    _, target = query.data.split("#", 1)
    if target == 'users':
        temp.B_USERS_CANCEL = True
        await query.message.edit("🛑 ᴛʀʏɪɴɢ ᴛᴏ ᴄᴀɴᴄᴇʟ ᴜꜱᴇʀꜱ ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...")
    elif target == 'groups':
        temp.B_GROUPS_CANCEL = True
        await query.message.edit("🛑 ᴛʀʏɪɴɢ ᴛᴏ ᴄᴀɴᴄᴇʟ ɢʀᴏᴜᴘꜱ ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...")

broadcast_cache = {}

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast_users(bot, message):
    if lock.locked():
        return await message.reply("⚠️ Another broadcast is in progress. Please wait...")

    total_users = await db.total_users_count()
    broadcast_cache[message.from_user.id] = {
        "message": message.reply_to_message
    }

    await message.reply(
        f"<b>📊 Total Users: {total_users}</b>\n\n"
        f"<b>📌 Do you want to pin this message?</b>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Pin", callback_data="bcast_pin#yes"),
             InlineKeyboardButton("❌ No Pin", callback_data="bcast_pin#no")]
        ])
    )

@Client.on_callback_query(filters.regex(r'^bcast_pin#'))
async def broadcast_pin_select(bot, query):
    user_id = query.from_user.id
    if user_id not in ADMINS:
        return await query.answer("❌ Not authorized!", show_alert=True)

    if user_id not in broadcast_cache:
        return await query.answer("❌ Session expired. Use /broadcast again.", show_alert=True)

    if lock.locked():
        return await query.answer("⚠️ Another broadcast in progress!", show_alert=True)

    _, pin_choice = query.data.split("#", 1)
    is_pin = pin_choice == "yes"
    cached = broadcast_cache.pop(user_id)
    b_msg = cached["message"]

    await query.message.delete()
    silentxbotz_status_msg = await bot.send_message(
        query.message.chat.id,
        f"📤 <b>Starting broadcast...</b>\n⏸️ Ping paused"
    )

    success = blocked = deleted = failed = done = 0
    start_time = time.time()
    cancelled = False

    temp.BROADCAST_RUNNING = True

    try:
        async with lock:
            all_users = []
            try:
                users_cursor = await db.get_all_users()
                async for user in users_cursor:
                    try:
                        all_users.append(int(user["id"]))
                    except:
                        pass
            except:
                pass

            total_users = len(all_users) if all_users else 1

            for uid in all_users:
                if temp.B_USERS_CANCEL:
                    temp.B_USERS_CANCEL = False
                    cancelled = True
                    break

                try:
                    _, result = await asyncio.wait_for(
                        users_broadcast(uid, b_msg, is_pin),
                        timeout=8
                    )
                    if result == "Success":
                        success += 1
                    elif result == "Blocked":
                        blocked += 1
                    elif result == "Deleted":
                        deleted += 1
                    else:
                        failed += 1
                except:
                    failed += 1

                done += 1

                if done % 100 == 0:
                    elapsed = get_readable_time(time.time() - start_time)
                    try:
                        await asyncio.wait_for(
                            silentxbotz_status_msg.edit(
                                f"📣 <b>Broadcast Progress:</b>\n\n"
                                f"👥 Total: <code>{total_users}</code>\n"
                                f"✅ Done: <code>{done}</code>\n"
                                f"📬 Success: <code>{success}</code>\n"
                                f"⛔ Blocked: <code>{blocked}</code>\n"
                                f"🗑️ Deleted: <code>{deleted}</code>\n"
                                f"⏱️ Time: {elapsed}",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("❌ CANCEL", callback_data="broadcast_cancel#users")]
                                ])
                            ),
                            timeout=5
                        )
                    except:
                        pass
    except Exception as e:
        LOGGER.error(f"Broadcast outer error: {e}")
    finally:
        temp.BROADCAST_RUNNING = False

    elapsed = get_readable_time(time.time() - start_time)
    final_status = (
        f"{'❌ <b>Broadcast Cancelled.</b>' if cancelled else '✅ <b>Broadcast Completed.</b>'}\n\n"
        f"🕒 Time: {elapsed}\n"
        f"👥 Total: <code>{total_users}</code>\n"
        f"📬 Success: <code>{success}</code>\n"
        f"⛔ Blocked: <code>{blocked}</code>\n"
        f"🗑️ Deleted: <code>{deleted}</code>\n"
        f"❌ Failed: <code>{failed}</code>"
    )
    try:
        await silentxbotz_status_msg.edit(final_status)
    except:
        pass


grp_broadcast_cache = {}

@Client.on_message(filters.command("grp_broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast_group(bot, message):
    if lock.locked():
        return await message.reply("⚠️ Another broadcast is in progress. Please wait...")
    b_msg = message.reply_to_message
    grp_broadcast_cache[message.from_user.id] = {
        "message": b_msg,
        "chat_id": message.chat.id
    }
    await message.reply(
        "<b>📢 Group Broadcast</b>\n\nDo you want to pin this message in groups?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📌 Yes, Pin it", callback_data="grp_bcast_pin#yes"),
             InlineKeyboardButton("❌ No", callback_data="grp_bcast_pin#no")]
        ])
    )

@Client.on_callback_query(filters.regex(r'^grp_bcast_pin'))
async def grp_broadcast_pin_callback(bot, query):
    user_id = query.from_user.id
    if user_id not in ADMINS:
        return await query.answer("❌ You are not authorized!", show_alert=True)
    if user_id not in grp_broadcast_cache:
        return await query.answer("❌ Session expired. Please use /grp_broadcast again.", show_alert=True)

    _, choice = query.data.split("#", 1)
    is_pin = choice == "yes"
    cached = grp_broadcast_cache.pop(user_id)
    b_msg = cached["message"]

    await query.message.delete()
    chats = await db.get_all_chats()
    total_chats = await db.total_chat_count()
    silentxbotz_status_msg = await bot.send_message(cached["chat_id"], "📤 <b>Broadcasting your message to groups...</b>")
    start_time = time.time()
    done = success = failed = skipped = 0
    cancelled = False

    async with lock:
        async for chat in chats:
            if temp.B_GROUPS_CANCEL:
                temp.B_GROUPS_CANCEL = False
                cancelled = True
                break

            chat_id = int(chat["id"])
            try:
                result = await asyncio.wait_for(
                    groups_broadcast(chat_id, b_msg, is_pin),
                    timeout=10
                )
                if result == "Success":
                    success += 1
                else:
                    failed += 1
            except:
                failed += 1

            done += 1

            if done % 20 == 0:
                elapsed = get_readable_time(time.time() - start_time)
                try:
                    await silentxbotz_status_msg.edit(
                        f"📣 <b>Group Broadcast Progress:</b>\n\n"
                        f"👥 Total: <code>{total_chats}</code>\n"
                        f"✅ Done: <code>{done}</code>\n"
                        f"📬 Success: <code>{success}</code>\n"
                        f"❌ Failed: <code>{failed}</code>\n"
                        f"⏱️ Time: {elapsed}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("❌ CANCEL", callback_data="broadcast_cancel#groups")]
                        ])
                    )
                except:
                    pass

    elapsed = get_readable_time(time.time() - start_time)
    final_status = (
        f"{'❌ <b>Broadcast Cancelled.</b>' if cancelled else '✅ <b>Group Broadcast Completed.</b>'}\n\n"
        f"🕒 Time: {elapsed}\n"
        f"👥 Total: <code>{total_chats}</code>\n"
        f"📬 Success: <code>{success}</code>\n"
        f"❌ Failed: <code>{failed}</code>"
    )
    try:
        await silentxbotz_status_msg.edit(final_status)
    except:
        pass


@Client.on_message(filters.command("clear_junk") & filters.user(ADMINS))
async def clear_junk_command(bot, message):
    sts = await message.reply("Clearing junk users...")
    junk = await clear_junk()
    await sts.edit(f"Cleared {junk} junk users!")


@Client.on_message(filters.command("junk_group") & filters.user(ADMINS) & filters.reply)
async def junk_group_command(bot, message):
    sts = await message.reply("Broadcasting to junk group...")
    b_msg = message.reply_to_message
    total = await junk_group(message.chat.id, b_msg)
    await sts.edit(f"Broadcasted to {total} junk users!")
