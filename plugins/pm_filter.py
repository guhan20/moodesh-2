# Kanged From @TroJanZheX
import asyncio
import re
import ast
from datetime import datetime
import pytz
from time import time
import random
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import ADMINS, AUTH_CHANNEL, AUTH_USERS, CUSTOM_FILE_CAPTION, AUTH_GROUPS, DELETE_TIME, P_TTI_SHOW_OFF, IMDB, REDIRECT_TO, \
    SINGLE_BUTTON, SPELL_CHECK_REPLY, IMDB_TEMPLATE, START_IMAGE_URL, redirected_env
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto,InputMediaDocument,InputMediaVideo,InputMediaAnimation,InputMediaAudio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

#########################################################################################


START_TIME = datetime.utcnow()
START_TIME_ISO = START_TIME.replace(microsecond=0).isoformat()
TIME_DURATION_UNITS = (
    ("Week", 60 * 60 * 24 * 7),
    ("Day", 60 ** 2 * 24),
    ("hour", 60 ** 2),
    ("Min", 60),
    ("Sec", 1),
)


async def _human_time_duration(seconds):
    if seconds == 0:
        return "inf"
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append("{} {}{}".format(amount, unit, "" if amount == 1 else ""))
    return " | ".join(parts)

#################################################################################################

BUTTONS = {}
SPELL_CHECK = {}
PICS = ['https://telegra.ph/file/a6a7d35e3221b630bea60.jpg', 'https://telegra.ph/file/665e3464f841a56f31bb0.jpg', 'https://telegra.ph/file/f3f4d581b9d52c4485126.jpg', 'https://telegra.ph/file/b6d8bfff766da9a4f4f2d.jpg', 'https://telegra.ph/file/1d5643e5ab65add8e796e.jpg', 'https://telegra.ph/file/972ccfb9abf61ab61a47d.jpg',]


@Client.on_message((filters.group | filters.private) & filters.text & filters.incoming)
async def give_filter(client, message):
    k = await manual_filters(client, message)
    if k == False:
        await auto_filter(client, message)


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(f"അല്ലയോ {query.from_user.first_name} അങ്ങുന്നേ.. സ്വന്തമായി മൂവി REQUEST ചെയ്താലും 😕\n\n ʀᴇǫᴜᴇsᴛ  ʏᴏᴜʀ ᴏᴡɴ ғɪʟᴇ , ᴅᴏɴ'ᴛ ᴄʟɪᴄᴋ ᴏᴛʜᴇʀs ʀᴇǫᴜᴇsᴛᴇᴅ ғɪʟᴇs. 🤦‍♂️", show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer(f"അല്ലയോ {query.from_user.first_name} അങ്ങുന്നേ.. സ്വന്തമായി മൂവി REQUEST ചെയ്താലും 😕\n\n ʀᴇǫᴜᴇsᴛ  ʏᴏᴜʀ ᴏᴡɴ ғɪʟᴇ , ᴅᴏɴ'ᴛ ᴄʟɪᴄᴋ ᴏᴛʜᴇʀs ʀᴇǫᴜᴇsᴛᴇᴅ ғɪʟᴇs. 🤦‍♂️", show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    settings = await get_settings(query.message.chat.id)
    pre = 'Chat' if settings['redirect_to'] == 'Chat' else 'files'

    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"▫️ {get_size(file.file_size)} ▸ {file.file_name}", callback_data=f'{pre}#{file.file_id}#{query.from_user.id}'
                )
            ] 
            for file in files
        ]
    else:
        btn = [        
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}", callback_data=f'{pre}#{file.file_id}#{query.from_user.id}'
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'{pre}_#{file.file_id}#{query.from_user.id}',
                )
            ] 
            for file in files
        ]

    btn.insert(0, 
        [ 
            InlineKeyboardButton(f'ᴍᴏᴠɪᴇs', 'movie'),
            InlineKeyboardButton(f'sᴇʀɪᴇs', 'series'),
            InlineKeyboardButton(f'ɪɴғᴏ', 'test')
        ]
    )

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append([
           InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"), 
           InlineKeyboardButton(f"{round(int(offset)/10)+1} - {round(total/10)}", callback_data="pages"),
           InlineKeyboardButton("ᴅᴇʟᴇᴛᴇ", callback_data=f"close_data"),
        ])
    elif off_set is None:
        btn.append([
           InlineKeyboardButton("ᴘᴀɢᴇꜱ", callback_data=f"pages"),
           InlineKeyboardButton(f"{round(int(offset)/10)+1} - {round(total/10)}", callback_data="pages"), 
           InlineKeyboardButton("ɴᴇxᴛ", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"{round(int(offset)/10)+1} - {round(total/10)}", callback_data="pages"),
                InlineKeyboardButton("ɴᴇxᴛ", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer("𝖲𝗐𝖺𝗇𝗍𝗁𝖺𝗆𝖺𝗒𝗂 𝖲𝖾𝖺𝗋𝖼𝗁 𝖢𝗁𝖾𝗒𝖺𝖽𝖺 𝖬𝗈𝗐𝗇𝖾", show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movies = SPELL_CHECK.get(query.message.reply_to_message.message_id)
    if not movies:
        return await query.answer("𝖱𝖾𝗊𝗎𝖾𝗌𝗍 𝖠𝗀𝖺𝗂𝗇 𝖣𝗎𝖽𝖾, 𝖥𝗂𝗅𝖾 𝖫𝗂𝗇𝗄 𝖾𝗑𝗉𝗂𝗋𝖾𝖽.", show_alert=True)
    movie = movies[(int(movie_))]
    await query.answer('𝖭𝗃𝖺𝗇 𝖬𝗈𝗏𝗂𝖾 𝗈𝗇𝗇 𝖳𝗁𝖺𝗉𝗉𝖺𝗍𝖾 𝖻𝗋𝗈...')
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:
            k = await query.message.edit('This Movie Not Found In DataBase')
            await asyncio.sleep(10)
            await k.delete()


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
        await query.message.reply_to_message.delete()
         
    
    if query.data == "notalert_ml":
        await query.answer("താങ്കൾ ഉദ്ദേശിച്ച മൂവി / സീരീസ് ഇതല്ല എങ്കിൽ  ഗൂഗിളിൽ പോയി കറക്റ്റ് സ്പെല്ലിങ് കണ്ടുപിടിച്ചു അതുപോലെ എവിടെ കൊടുക്ക്", show_alert=True)
    
    elif query.data == "rpclose":
        await query.message.delete()
      
    elif query.data == "movie":

        await query.answer("""⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯
ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇsᴛ ғᴏʀᴍᴀᴛ 
⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯
ɢᴏ ᴛᴏ ɢᴏᴏɢʟᴇ ➠ ᴛʏᴘᴇ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ➠ ᴄᴏᴘʏ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ➠ ᴘᴀsᴛ ᴛʜɪs ɢʀᴏᴜᴘ 

ᴇxᴀᴍᴘʟᴇ : ᴀᴡᴀᴋᴇ  ᴏʀ  ᴀᴡᴀᴋᴇ 2021

🚯 ᴅᴏɴᴛ ᴜsᴇ ➠ ':(!,./)

© ᴄɪɴɪᴍᴀᴀᴅʜᴏʟᴏᴋᴀᴍ""", show_alert=True)
         
    elif query.data == "series": 
        await query.answer("""⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯
sᴇʀɪᴇs ʀᴇǫᴜᴇsᴛ ғᴏʀᴍᴀᴛ 
⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯

ɢᴏ ᴛᴏ ɢᴏᴏɢʟᴇ ➠ ᴛʏᴘᴇ sᴇʀɪᴇs ɴᴀᴍᴇ ➠ ᴄᴏᴘʏ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ➠ ᴘᴀsᴛ ᴛʜɪs ɢʀᴏᴜᴘ 
Dark or Dark S01E01

🚯 ᴅᴏɴᴛ ᴜsᴇ ➠ ':(!,./)

© ᴄɪɴɪᴍᴀᴀᴅʜᴏʟᴏᴋᴀᴍ""", show_alert=True)
         
    elif query.data == "test": 
        await query.answer("""⚠ Information ⚠
        
After 30 minutes this message will be automatically deleted

If you do not see the requested movie / series file, look at the next page

© ᴄɪɴɪᴍᴀᴀᴅʜᴏʟᴏᴋᴀᴍ""", show_alert=True)
 
    elif query.data == "notalert_en": 
        await query.answer("If this is not the movie / series you are looking for then just go to Google and find the correct spelling and give it a try.", show_alert=True)
         
    elif query.data == "whyjoin": 
        await query.answer("അഥവാ ഗ്രൂപ്പ് കോപ്പിറൈറ് കിട്ടി പോയാൽ .. പുതിയ ഗ്രൂപ്പ് തുടങ്ങുമ്പോൾ ഇപ്പോൾ ജോയിൻ ആകുന്ന Channel വഴി ആയിരിക്കും അറിയിക്കുന്നത് 🤥", show_alert=True)
         
    elif query.data == "pm": 
        await query.answer("""📵 𝘾𝙤𝙣𝙩𝙖𝙘𝙩 𝙉𝙤𝙩 𝘼𝙡𝙡𝙤𝙬𝙚𝙙  
        
- Section B206 - Spam + Ban ⚠️
- Section Y8R6 - Spam + Report 🉐

🗽 ʙʏ  ◉‿◉  ɢ ⁷⁷ ɢᴢ""", show_alert=True)

    elif query.data == "Seen": 
        await query.answer("""⛔ ഇവിടെ നിന്ന് ഫയൽ ഡൗൺലോഡ് ചെയ്യരുത്.  

➡️ എവിടെയെങ്കിലും ഫോർവേഡ് ചെയ്ത ശേഷം ഡൗൺലോഡ് ചെയ്യുക. 

✅ അല്ലെങ്കിൽ BOT PM ബട്ടണിൽ ക്ലിക്ക് ചെയ്യുക""", show_alert=True)
        
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer('Piracy Is Crime')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('Piracy Is Crime')

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('𝗌𝖺𝗇𝗍𝗁𝗈𝗌𝗁𝖺𝗆 𝖺𝗅𝗅𝖾')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == "creator") or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == "private":
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in ["group", "supergroup"]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == "creator") or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("That's not for you!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode="md"
        )
        return await query.answer('Piracy Is Crime')
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode="md")
        return await query.answer('Piracy Is Crime')
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode="md"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode="md"
            )
        return await query.answer('Piracy Is Crime')
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode="md"
            )
        return await query.answer('Piracy Is Crime')
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('Piracy Is Crime')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        ident, file_id, rid = query.data.split("#")

        if int(rid) not in [query.from_user.id, 0]:
            return await query.answer(f"അല്ലയോ {query.from_user.first_name} അങ്ങുന്നേ.. സ്വന്തമായി മൂവി REQUEST ചെയ്താലും 😁\n\n ʀᴇǫᴜᴇsᴛ  ʏᴏᴜʀ ᴏᴡɴ ғɪʟᴇ , ᴅᴏɴ'ᴛ ᴄʟɪᴄᴋ ᴏᴛʜᴇʀs ʀᴇǫᴜᴇsᴛᴇᴅ ғɪʟᴇs. 🤦‍♂️", show_alert=True)

        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)                                                      
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            elif settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False 
                )
                await query.answer('𝖨 𝗁𝖺𝗏𝖾 𝗌𝖾𝗇𝖽 𝗒𝗈𝗎 𝖿𝗂𝗅𝖾𝗌 𝖯𝖾𝗋𝗌𝗈𝗇𝖺𝗅𝗒 , 𝖢𝗁𝖾𝖼𝗄 𝗆𝗒 𝗉𝗆', show_alert=True)
        except UserIsBlocked:
            await query.answer('Unblock the bot mahn !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    
    elif query.data.startswith("Chat"):
        ident, file_id, rid = query.data.split("#")

        if int(rid) not in [query.from_user.id, 0]:
            return await query.answer(f"മോനെ {query.from_user.first_name} ഇത്‌ നിനക്കുള്ളതല്ല 🤭\n\n {query.message.reply_to_message.from_user.first_name} ന്റെ റിക്യുസ്റ്റ് ആണ് ഇത് 🙂\n\nRequest your own 🥰\n\n© Cinimaadholokam", show_alert=True)

        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        mention = query.from_user.mention
        f_caption = files.caption
        present = datetime.now(tz=pytz.timezone("Asia/Kolkata"))
        time = present.strftime("%I:%M:%S %p")
        date = present.strftime("%d-%B-%Y")
        day = present.strftime("%A")
        utc = present.strftime("%z")
        current_time = datetime.utcnow()
        uptime_sec = (current_time - START_TIME).total_seconds()
        uptime = await _human_time_duration(int(uptime_sec))
        settings = await get_settings(query.message.chat.id)
        pre = 'Chat' if settings['redirect_to'] == 'botpm' else 'files'
        settings = await get_settings(query.message.chat.id)
        m = datetime.now()

        time = m.hour

        if time < 6:
            get="Gᴏᴏᴅ Mᴏʀɴɪɴɢ  🌅" 
        elif time < 12:
            get="Gᴏᴏᴅ Aғᴛᴇʀɴᴏᴏɴ ☕"
        elif time < 17:
            get="Gᴏᴏᴅ Eᴠᴀɴɪɴɢ ⛱️"
        elif time < 20: 
            get="Gᴏᴏᴅ Nɪɢʜᴛ 🌙"
        else:
            get="Gᴏᴏᴅ Nɪɢʜᴛ"

        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
            size = size
            mention = mention
        if f_caption is None:
            f_caption = f"{files.file_name}"
            size = f"{files.file_size}"
            mention = f"{query.from_user.mention}"
  
        try:
            msg = await client.send_cached_media(
                chat_id=AUTH_CHANNEL,
                file_id=file_id,
                caption=f'<b>Hai 👋 {query.from_user.mention}</b> 😍\n\n<code>{title}</code>\n\n⚠️ <i>This file will be deleted from here within 5 minute as it has copyright ... !!!</i>\n\n<i>കോപ്പിറൈറ്റ് ഉള്ളതുകൊണ്ട് ഫയൽ 5 മിനിറ്റിനുള്ളിൽ ഇവിടെനിന്നും ഡിലീറ്റ് ആകുന്നതാണ് അതുകൊണ്ട് ഇവിടെ നിന്നും മറ്റെവിടെക്കെങ്കിലും മാറ്റിയതിന് ശേഷം ഡൗൺലോഡ് ചെയ്യുക!</i>\n\n<i><b>⚡ Powered by {query.message.chat.title}</b></i>',
                protect_content=True if ident == "filep" else False,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(f'🇮🇳 ᴍᴀʟ', callback_data="seen"),
                            InlineKeyboardButton('sᴇɴᴅ ᴘᴍ', callback_data=f'{pre}#{files.file_id}#{query.from_user.id}')
                        ],                       
                        [
                            InlineKeyboardButton('ᴊᴏɪɴ ᴏᴜʀ ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ ', url="https://t.me/calinkzz")
                        ]
                    ]
                )
            )
            butt = [[InlineKeyboardButton('📥 ᴍᴏᴠɪᴇ ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ 📥 ', url = msg.link)]]
            msg1 = await query.message.reply(
                f'<b> ʜᴇʟʟᴏ {query.from_user.mention} {get}  </b> \n\n<b><i>✅ ʏᴏᴜʀ ғɪʟᴇ sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘʟᴏᴀᴅᴇᴅ ᴛᴏ ᴄʜᴀɴɴᴇʟ ᴘʟᴇᴀsᴇ ᴄʟɪᴄᴋ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ,</i></b>\n\n'           
                f'<b>📂 Fɪʟᴇ Nᴀᴍᴇ</b> : <code>{title}</code>\n\n'              
                f'<b>⚙️ Fɪʟᴇ Sɪᴢᴇ</b> : <b>{size}</b>\n\n'
                f'<b>⏰ ᴜᴘᴛɪᴍᴇ : <code>{uptime}</code></b>',
                True,
                'html',
                reply_markup=InlineKeyboardMarkup(butt))
                
           #     )
      #      )
            await query.answer(f'ʜᴇʏ {query.from_user.first_name} ʏᴏᴜʀ ғɪʟᴇ ɪs ʀᴇᴅʏ 😴\n\n𝙥𝙡𝙚𝙖𝙨𝙚 𝙘𝙡𝙞𝙘𝙠 @ 𝙗𝙪𝙩𝙩𝙤𝙣 💡\n\n𝙊𝙪𝙧 S𝙘𝙧𝙤𝙡𝙡 𝘿𝙤𝙬𝙣 ⬇️', show_alert=True)
          #  await asyncio.sleep(300) 
           # await msg1.delete()
          #  await msg.delete()
          #  del msg1, msg
        except Exception as e:
            logger.exception(e, exc_info=True)
            await query.answer(f"Encountering Issues", True)

    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("I Like Your Smartness, But Don't Be Oversmart 😒", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        mention = query.from_user.mention
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
                size = size
                mention = mention
        if f_caption is None:
            f_caption = f"{title}"
        if size is None:
            size = f"{size}"
        if mention is None:
            mention = f"{mention}"
       

        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False
        )
    elif query.data == "pages":
        await query.answer()
    elif query.data == "start":
        buttons = [[
            InlineKeyboardButton('⚡ ᴄʟɪᴄᴋ ᴛᴏ ᴄʟᴏsᴇ ᴛʜɪs ʙᴜᴛᴛᴏᴜɴs ⚡', callback_data='ccbb')
            ],[
            InlineKeyboardButton('👑 ᴏᴡɴᴇʀ', callback_data='pm'),
            InlineKeyboardButton('👥 ɢʀᴏᴜᴘ', url="https://t.me/cinimaadholokaam")
            ],[
            InlineKeyboardButton('🎬 ᴄʜᴀɴɴᴇʟ', url='https://t.me/Calinkzz'),
            InlineKeyboardButton('🔐 ᴄʟᴏsᴇ', callback_data='rpclose')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            #parse_mode='html
        )           
    elif query.data == "owner":
        buttons = [[
            InlineKeyboardButton('ᴄᴏɴᴛᴀᴄᴛ', callback_data='pm'),
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='Dback')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        file_id = 'https://telegra.ph/file/571de8942f4ac7730cbd6.jpg'
        mid =  InputMediaPhoto(file_id, caption=script.OWN_TEXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME))
        await query.edit_message_media(
            media = mid,
            #caption=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup
            #parse_mode='html'
        )
    elif query.data == "Dback":
        buttons = [[
            InlineKeyboardButton('⚡ ᴄʟɪᴄᴋ ᴛᴏ ᴄʟᴏsᴇ ᴛʜɪs ʙᴜᴛᴛᴏᴜɴs ⚡', callback_data='ccbb')
            ],[
            InlineKeyboardButton('👑 ᴏᴡɴᴇʀ', callback_data='pm'),
            InlineKeyboardButton('👥 ɢʀᴏᴜᴘ', url='https://t.me/cinimaadholokaam')
            ],[
            InlineKeyboardButton('🎬 ᴄʜᴀɴɴᴇʟ', url='https://t.me/Calinkzz'),
            InlineKeyboardButton('🔐 ᴄʟᴏsᴇ', callback_data='rpclose')
            #],[
            #InlineKeyboardButton('ꜱʀᴇᴇɴᴀᴛʜ ʙʜᴀꜱɪ ꜰɪʟᴍᴏɢʀᴀᴘʜʏ', callback_data='year')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        file_id = random.choice(PICS)
        mid =  InputMediaPhoto(file_id, caption=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME))
        await query.editMessageMedia(
            media = mid,
            chat_id=message.from_user.id,
            #caption=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup
           # parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "ccbb":
        buttons = [[
            InlineKeyboardButton('ᴄʟɪᴄᴋ ʜᴇʀᴇ ғᴏʀ ᴍᴏʀᴇ ʙᴜᴛᴛᴏᴜɴs', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            #parse_mode='html
        )
    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[
            InlineKeyboardButton('👩‍🦯 Back', callback_data='help'),
            InlineKeyboardButton('♻️', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode='html'
        )
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return await query.answer('Piracy Is Crime')

        if status == "True" or status == "Chat":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Filter Button',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Single' if settings["button"] else 'Double',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton( 'Redirect To',
                                         callback_data=f'setgs#redirect_to#{settings["redirect_to"]}#{grp_id}',),
                    InlineKeyboardButton('👤 PM' if settings["redirect_to"] == "PM" else '📄 Chat',
                                         callback_data=f'setgs#redirect_to#{settings["redirect_to"]}#{grp_id}',),
                ],
                [
                    InlineKeyboardButton('Bot PM', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["botpm"] else '❌ No',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('File Secure',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["file_secure"] else '❌ No',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('IMDB', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["imdb"] else '❌ No',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Spell Check',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["spell_check"] else '❌ No',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Welcome', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["welcome"] else '❌ No',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    elif query.data == "close_data":
        await query.message.delete()
        await query.message.reply_to_message.delete()
    try: await query.answer(f"അല്ലയോ {query.from_user.first_name} അങ്ങുന്നേ.. സ്വന്തമായി മൂവി REQUEST ചെയ്താലും 😁\n\n ʀᴇǫᴜᴇsᴛ  ʏᴏᴜʀ ᴏᴡɴ ғɪʟᴇ , ᴅᴏɴ'ᴛ ᴄʟɪᴄᴋ ᴏᴛʜᴇʀs ʀᴇǫᴜᴇsᴛᴇᴅ ғɪʟᴇs. 🤦‍♂️") 
    except: pass


async def auto_filter(client, msg: pyrogram.types.Message, spoll=False):
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if 2 < len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(msg)
                else:
                    return
        else:
            return
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    
    pre = 'filep' if settings['file_secure'] else 'file'
    pre = 'Chat' if settings['redirect_to'] == 'Chat' else pre

    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                        text=f"▫️ {get_size(file.file_size)} ▸ {file.file_name}", 
                        callback_data=f'{pre}#{file.file_id}#{msg.from_user.id if msg.from_user is not None else 0}'
                )
            ] 
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"{file.file_name}",
                    callback_data=f'{pre}#{file.file_id}#{msg.from_user.id if msg.from_user is not None else 0}',
                ),
                InlineKeyboardButton(
                    text=f"{get_size(file.file_size)}",
                    callback_data=f'{pre}_#{file.file_id}#{msg.from_user.id if msg.from_user is not None else 0}',
                )
            ]
            for file in files
        ]

    btn.insert(0, 
        [
            InlineKeyboardButton(f'ᴍᴏᴠɪᴇs', 'movie'),
            InlineKeyboardButton(f'sᴇʀɪᴇs', 'series'),
            InlineKeyboardButton(f'ɪɴғᴏ', 'test')
        ]
    )

    if offset != "":
        key = f"{message.chat.id}-{message.message_id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append([
           InlineKeyboardButton(text=f"ᴘᴀɢᴇꜱ",callback_data="pages"),
           InlineKeyboardButton(text=f"1 - {round(int(total_results)/10)}",callback_data="pages"), 
           InlineKeyboardButton(text="ɴᴇxᴛ",callback_data=f"next_{req}_{key}_{offset}")
        ])
    else:
        btn.append(
            [InlineKeyboardButton(text="ᴍᴏʀᴇ ᴘᴀɢᴇꜱ ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ",callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            mention_bot=temp.MENTION,
            mention_user=message.from_user.mention if message.from_user else message.sender_chat.title,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b>Hai 👋 {message.from_user.mention}</b> 😍\n\n<b>📁 Found ✨  Files For Your Query : {search} 👇</b> "
    if imdb and imdb.get('poster'):
        try:
            fmsg = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024],
                                      reply_markup=InlineKeyboardMarkup(btn))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            fmsg = await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
        except Exception as e:
            logger.exception(e)
            fmsg = await message.reply_photo(photo="https://telegra.ph/file/e4fa9ab229d31a779c010.jpg", caption=f"""<b>🎪 ᴛɪᴛɪʟᴇ <i>{search}</i>
                
┏ 🤴 ᴀsᴋᴇᴅ ʙʏ : <a href="tg://need_update_for_some_feature">{message.from_user.first_name}</a>
┣ ⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : [𐌑ꤌ꤯᥉꤯ꤕ ²·⁰](https://t.me/Ca_maisiebot) 
┗ 🍁 ᴄʜᴀɴɴᴇʟ : @Calinkzz

<i>★ ᴘᴏᴡᴇʀᴇᴅ ʙʏ  <a href="https://t.me/Cinimadholokam">ᴄɪɴɪᴍᴀᴀᴅʜᴏʟᴏᴋᴀᴍ</a></i></b>""", reply_markup=InlineKeyboardMarkup(btn))
    else:
        fmsg = await message.reply_photo(photo="https://telegra.ph/file/e4fa9ab229d31a779c010.jpg", caption=f"""<b>🎪 ᴛɪᴛɪʟᴇ <i>{search}</i>
                
┏ 🤴 ᴀsᴋᴇᴅ ʙʏ : <a href="tg://need_update_for_some_feature">{message.from_user.first_name}</a>
┣ ⚡ ᴘᴏᴡᴇʀᴇᴅ ʙʏ : <a href="https://t.me/Ca_maisiebot">𐌑ꤌ꤯᥉꤯ꤕ ²·⁰</a>
┗ 🍁 ᴄʜᴀɴɴᴇʟ : @Calinkzz

<i>★ ᴘᴏᴡᴇʀᴇᴅ ʙʏ  <a href="https://t.me/Cinimadholokam">ᴄɪɴɪᴍᴀᴀᴅʜᴏʟᴏᴋᴀᴍ</a></i></b>""", reply_markup=InlineKeyboardMarkup(btn))
    
    #await asyncio.sleep(DELETE_TIME)
    #await fmsg.delete()

    if spoll:
        await msg.message.delete()


async def advantage_spell_chok(msg):
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    gs_parsed = []
    if not g_s:
        k = await msg.reply("𝖨 𝖼𝖺𝗇𝗍 𝖿𝗂𝗇𝖽 𝗂𝗍 𝗂𝗇 𝗆𝗒 𝖣𝖺𝗍𝖺𝖡𝖺𝗌𝖾.")
        await asyncio.sleep(8)
        await k.delete()
        return
    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE)  # look for imdb / wiki results
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(
        r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)',
        '', i, flags=re.IGNORECASE) for i in gs]
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*",
                         re.IGNORECASE)  # match something like Watch Niram | Amazon Prime
        for mv in g_s:
            match = reg.match(mv)
            if match:
                gs_parsed.append(match.group(1))
    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    gs_parsed = list(dict.fromkeys(gs_parsed))  # removing duplicates https://stackoverflow.com/a/7961425
    if len(gs_parsed) > 3:
        gs_parsed = gs_parsed[:3]
    if gs_parsed:
        for mov in gs_parsed:
            imdb_s = await get_poster(mov.strip(), bulk=True)  # searching each keyword in imdb
            if imdb_s:
                movielist += [movie.get('title') for movie in imdb_s]
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip() for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist))  # removing duplicates
    if not movielist:
        k = await msg.reply("𝖡𝗋𝗈, 𝖢𝗁𝖾𝖼𝗄 𝗍𝗁𝖾 𝗌𝗉𝖾𝗅𝗅𝗂𝗇𝗀 𝖸𝗈𝗎 𝗁𝖺𝗏𝖾 𝗌𝖾𝗇𝖽 𝗂𝗇 𝗀𝗈𝗈𝗀𝗅𝖾. 𝖨𝖿 𝖸𝗈𝗎 𝗁𝖺𝗏𝖾 𝗋𝖾𝗊𝗎𝖾𝗌𝗍𝖾𝖽 𝖥𝗈𝗋 𝖢𝖺𝗆 𝗉𝗋𝗂𝗇𝗍 𝖸𝗈𝗎 𝗐𝗂𝗅𝗅 𝗇𝗈𝗍 𝖦𝖾𝗍 𝗂𝗍.")
        await asyncio.sleep(8)
        await k.delete()
        return
    SPELL_CHECK[msg.message_id] = movielist
    btn = [InlineKeyboardButton("🔍ɢᴏᴏɢʟᴇ🔎", url=f'https://google.com/search?q={query}')]
    await msg.reply("𝖡𝗋𝗈, 𝖢𝗁𝖾𝖼𝗄 𝗍𝗁𝖾 𝗌𝗉𝖾𝗅𝗅𝗂𝗇𝗀 𝖸𝗈𝗎 𝗁𝖺𝗏𝖾 𝗌𝖾𝗇𝖽 𝗂𝗇 𝗀𝗈𝗈𝗀𝗅𝖾. 𝖨𝖿 𝖸𝗈𝗎 𝗁𝖺𝗏𝖾 𝗋𝖾𝗊𝗎𝖾𝗌𝗍𝖾𝖽 𝖥𝗈𝗋 𝖢𝖺𝗆 𝗉𝗋𝗂𝗇𝗍 𝖸𝗈𝗎 𝗐𝗂𝗅𝗅 𝗇𝗈𝗍 𝖦𝖾𝗍 𝗂𝗍.",
                    reply_markup=InlineKeyboardMarkup(btn))

async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.message_id if message.reply_to_message else message.message_id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(group_id, reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
