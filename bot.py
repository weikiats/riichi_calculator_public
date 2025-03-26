import logging

from telegram import (
    ReplyKeyboardMarkup, 
    ReplyKeyboardRemove, 
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

END = ConversationHandler.END
SELECT_SESSION_ACTION, GAME_RECORDS, END_SESSION, \
ROUND_RECORDS, MODE, PLAYERS, POINTS_VALUE, SELECT_GAME_ACTION, DELETE_ROUND, FINISH_GAME, FINAL_POINTS, \
ADD_ROUND_RESULT, ADD_ROUND_WINNER, ADD_ROUND_HAN, ADD_ROUND_FU, ADD_ROUND_LOSER, ADD_ROUND_NAGASHI, ADD_ROUND_TENPAI, ADD_ROUND_RIICHI, \
ADD_ROUND_CHOMBO, ADD_ROUND_CHOMBO_POINTS, CHOMBO_PENALTY, \
DRAFT_ROUND, DRAFT_ROUND_TEXT, RESULT, WINNER, HAN, FU, LOSER, NAGASHI_MANGAN, IN_TENPAI, DECLARED_RIICHI, POINT_RECORDS, PREV_GAME_TRACKERS, \
CURRENT_WIND, CURRENT_DEALER, CURRENT_DEALER_CONSEC, CURRENT_RIICHI, CURRENT_HONBA, \
TSUMO, RON, DEALER, NONDEALER = range(43)

winds = ["East", "South", "West", "North"]
select_session_options_keyboard = ReplyKeyboardMarkup([
    ["Start new game"],
    ["End session"]
])
select_game_options_keyboard = ReplyKeyboardMarkup([
    ["Add round", "Delete last round"],
    ["Show game history", "Finish game"]
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data[GAME_RECORDS] = []
    await update.message.reply_text("\U0001F004 Welcome to Riichi Calculator \U0001F004")
    text = "Here are some helpful tips:\n\n" +\
        "1. All chat members can simultaneously interact with me\n" +\
        "2. <u>Reply</u> to my message to trigger an action when I specifically mention \"Reply with...\". " +\
            "Make use of the custom keyboard provided whenever possible\n" +\
        "3. <u>Use the same name</u> for players playing in multiple games so that I can consolidate scores correctly at the end of the session\n" +\
        "4. Player names are set to lower case by default\n" +\
        "5. Use the command /stop to stop the bot in an emergency. This will clear <u>all</u> existing Riichi data, so use with caution"
    await update.message.reply_text(text, parse_mode="HTML")
    await update.message.reply_text("Reply with next action", reply_markup=select_session_options_keyboard)

    return SELECT_SESSION_ACTION

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data.clear()
    await update.message.reply_text("Bot stopped", reply_markup=ReplyKeyboardRemove())

    return END

async def start_new_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data[ROUND_RECORDS] = []
    context.chat_data[CURRENT_WIND] = context.chat_data[CURRENT_DEALER] = context.chat_data[CURRENT_DEALER_CONSEC] = \
        context.chat_data[CURRENT_RIICHI] = context.chat_data[CURRENT_HONBA] = 0
    keyboard = ReplyKeyboardMarkup([["4P"]], one_time_keyboard=True)
    await update.message.reply_text("Reply with 4P", reply_markup=keyboard)
    
    return MODE

async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data[MODE] = update.message.text
    context.chat_data[PLAYERS] = []
    await update.message.reply_text(f"Reply with East player name", reply_markup=ReplyKeyboardRemove())

    return PLAYERS

async def players(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    total = int(context.chat_data[MODE][:1])
    context.chat_data[PLAYERS].append(update.message.text.lower())
    curr = len(context.chat_data[PLAYERS])

    if curr != total:
        await update.message.reply_text(f"Reply with {winds[curr]} player name")

        return PLAYERS

    else:
        await update.message.reply_text(f"Reply with how much 1000 points is worth in $ (e.g. 2, 1, 0.5)")

        return POINTS_VALUE
    
async def points_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data[POINTS_VALUE] = round(float(update.message.text), 2)
    text = f"Mode: <u>{context.chat_data[MODE]}</u>\n\n"
    for i, player in enumerate(context.chat_data[PLAYERS]):
        text += f"{winds[i]}: <u>{player}</u>\n"
    text += f"\n1000 points: <u>${context.chat_data[POINTS_VALUE]:.2f}</u>\n\n"
    text += "Reply with next action"
    await update.message.reply_text(text, reply_markup=select_game_options_keyboard, parse_mode="HTML")
    
    return SELECT_GAME_ACTION

async def add_round(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data[DRAFT_ROUND] = {}
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Tsumo", callback_data="Tsumo"),
            InlineKeyboardButton(text="Ron", callback_data="Ron"),
        ],
        [
            InlineKeyboardButton(text="Draw", callback_data="Draw"),
            InlineKeyboardButton(text="Chombo", callback_data="Chombo"),
        ],
        [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
    ])
    await update.message.reply_text(text="Round result?", reply_markup=keyboard)
    
    return ADD_ROUND_RESULT

async def add_round_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()

    context.chat_data[DRAFT_ROUND][RESULT] = input
    text = context.chat_data[DRAFT_ROUND][DRAFT_ROUND_TEXT] = f"Round result: <u>{input}</u>"
    buttons = []
    for i, player in enumerate(context.chat_data[PLAYERS]):
        buttons.append(InlineKeyboardButton(text=player, callback_data=i))

    if input == "Tsumo" or input == "Ron":
        text += "\n\nWho won?"
        keyboard = InlineKeyboardMarkup([
            buttons,
            [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
        ])
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

        return ADD_ROUND_WINNER

    elif input == "Draw":
        text += "\n\nWho Nagashi Mangan?"
        keyboard = InlineKeyboardMarkup([
            buttons,
            [InlineKeyboardButton(text="None", callback_data="None")],
            [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
        ])
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

        return ADD_ROUND_NAGASHI

    elif input == "Chombo":
        text += "\n\nWho Chombo?"
        keyboard = InlineKeyboardMarkup([
            buttons,
            [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
        ])
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

        return ADD_ROUND_CHOMBO
    
    else: #cancel

        return await handle_add_round_cancel(update, context)
    
async def add_round_winner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()
    round = context.chat_data[DRAFT_ROUND]

    if WINNER not in round:
        round[WINNER] = []

    if input != "Cancel":

        if input != "None":
            round[DRAFT_ROUND_TEXT] += f"\nWinner: <u>{context.chat_data[PLAYERS][int(input)]}</u>"
            round[WINNER].append({int(input): {HAN: 0, FU: 0}})
            text = round[DRAFT_ROUND_TEXT] + "\n\nHow many Han?"
            buttons = [
                [
                    InlineKeyboardButton(text="1", callback_data="1"),
                    InlineKeyboardButton(text="2", callback_data="2"),
                    InlineKeyboardButton(text="3", callback_data="3"),
                    InlineKeyboardButton(text="4", callback_data="4"),
                ],
                [
                    InlineKeyboardButton(text="5", callback_data="5"),
                    InlineKeyboardButton(text="6-7", callback_data="6"),
                ],
                [
                    InlineKeyboardButton(text="8-10", callback_data="8"),
                    InlineKeyboardButton(text="11-12", callback_data="11"),
                ],
                [
                    InlineKeyboardButton(text=">=13", callback_data="13")
                ],
                [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

            return ADD_ROUND_HAN
            
        else:
            text = round[DRAFT_ROUND_TEXT] + "\n\nWho lost?"
            w = [list(winner.keys())[0] for winner in round[WINNER]]
            buttons = []
            for i, player in enumerate(context.chat_data[PLAYERS]):
                if i not in w:
                    buttons.append(InlineKeyboardButton(text=player, callback_data=i))
            keyboard = InlineKeyboardMarkup([
                buttons,
                [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
            ])
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

            return ADD_ROUND_LOSER
        
    else:

        return await handle_add_round_cancel(update, context)
    
async def add_round_han(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()
    round = context.chat_data[DRAFT_ROUND]

    if input != "Cancel":
        last_winner = round[WINNER][-1]
        last_winner_key = list(last_winner.keys())[0]
        round[WINNER][-1][last_winner_key][HAN] = int(input)

        if int(input) in [1, 2, 3, 4]:
            text = round[DRAFT_ROUND_TEXT] + f" (Han: {get_han_name(int(input))}\n\nHow many Fu?"
            buttons = [
                InlineKeyboardButton(text="20", callback_data="20"),
                InlineKeyboardButton(text="25", callback_data="25"),
                InlineKeyboardButton(text="30", callback_data="30")
            ]
            
            if int(input) == 1:
                buttons = buttons[2:]
            
            elif round[RESULT] == "Ron":
                buttons = buttons[1:]

            buttons = [buttons]

            if int(input) == 4:
                buttons.append([InlineKeyboardButton(text=">=40 (Mangan)", callback_data="Mangan")])

            else:
                buttons.append([
                    InlineKeyboardButton(text="40", callback_data="40"),
                    InlineKeyboardButton(text="50", callback_data="50"),
                    InlineKeyboardButton(text="60", callback_data="60"),
                ])

                if int(input) == 3:
                    buttons.append([InlineKeyboardButton(text="70 (Mangan)", callback_data="Mangan")])

                else:
                    buttons.append([InlineKeyboardButton(text="70", callback_data="70")])

            buttons.append([InlineKeyboardButton(text="Cancel", callback_data="Cancel")])
            keyboard = InlineKeyboardMarkup(buttons)
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

            return ADD_ROUND_FU

        else:
            round[DRAFT_ROUND_TEXT] += f" (Han: <u>{get_han_name(int(input))}</u>)"

            return await helper_han_fu(update, context)

    else:
        
        return await handle_add_round_cancel(update, context)
    
def get_han_name(i):
    match i:
        case 5:
            return "Mangan"
        case 6:
            return "Haneman"
        case 8:
            return "Baiman"
        case 11:
            return "Sanbaiman"
        case 13:
            return "Yakuman"
        case _:
            return f"{i}"
        
async def add_round_fu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()
    round = context.chat_data[DRAFT_ROUND]

    if input != "Cancel":
        last_winner = round[WINNER][-1]
        last_winner_key = list(last_winner.keys())[0]
        
        if input == "Mangan":
            round[DRAFT_ROUND_TEXT] += f" (Han: <u>{get_han_name(5)}</u>)"
            round[WINNER][-1][last_winner_key][HAN] = 5
            
        else:
            round[DRAFT_ROUND_TEXT] += f" (Han: <u>{round[WINNER][-1][last_winner_key][HAN]}</u>, " +\
                f"Fu: <u>{int(input)}</u>)"
            round[WINNER][-1][last_winner_key][FU] = int(input)

        return await helper_han_fu(update, context)
    
    else:
        
        return await handle_add_round_cancel(update, context)
        
async def helper_han_fu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    round = context.chat_data[DRAFT_ROUND]
    check = len(context.chat_data[PLAYERS]) - 1 == len(round[WINNER])
    w = [list(winner.keys())[0] for winner in round[WINNER]]

    if round[RESULT] == "Tsumo" or check:
        
        if check:
            l = next(pos for pos in range(len(context.chat_data[PLAYERS])) if pos not in w)
            round[LOSER] = l
            round[DRAFT_ROUND_TEXT] += f"\nLoser: <u>{context.chat_data[PLAYERS][l]}</u>"

        text = round[DRAFT_ROUND_TEXT] + "\n\nWho declared Riichi?"
        buttons = []
        for i, player in enumerate(context.chat_data[PLAYERS]):
            buttons.append(InlineKeyboardButton(text=player, callback_data=i))
        keyboard = InlineKeyboardMarkup([
            buttons,
            [InlineKeyboardButton(text="None", callback_data="None")],
            [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
        ])
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

        return ADD_ROUND_RIICHI

    else:
        text = round[DRAFT_ROUND_TEXT] + "\n\nWho else won?"
        buttons = []
        for i, player in enumerate(context.chat_data[PLAYERS]):
            if i not in w:
                buttons.append(InlineKeyboardButton(text=player, callback_data=i))
        keyboard = InlineKeyboardMarkup([
            buttons,
            [InlineKeyboardButton(text="None", callback_data="None")],
            [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
        ])
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

        return ADD_ROUND_WINNER
    
async def add_round_loser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()
    round = context.chat_data[DRAFT_ROUND]

    if input != "Cancel":

        round[DRAFT_ROUND_TEXT] += f"\nLoser: <u>{context.chat_data[PLAYERS][int(input)]}</u>"
        round[LOSER] = int(input)
        text = round[DRAFT_ROUND_TEXT] + "\n\nWho declared Riichi?"
        buttons = []
        for i, player in enumerate(context.chat_data[PLAYERS]):
            buttons.append(InlineKeyboardButton(text=player, callback_data=i))
        keyboard = InlineKeyboardMarkup([
            buttons,
            [InlineKeyboardButton(text="None", callback_data="None")],
            [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
        ])
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

        return ADD_ROUND_RIICHI
    
    else:
        
        return await handle_add_round_cancel(update, context)
    
async def add_round_nagashi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # nagashi mangan implemented here is considered a bonus payment, not a proper win
    # payment is not affected by honba / existing riichi
    # winds will move if dealer is not in tenpai, even if dealer nagashi mangan
    # any successful nagashi mangan will cancel out regular tenpai settlements 
    # (https://riichi.wiki/Nagashi_mangan)
    input = update.callback_query.data
    await update.callback_query.answer()
    round = context.chat_data[DRAFT_ROUND]

    if NAGASHI_MANGAN not in round:
        round[NAGASHI_MANGAN] = []

    if input != "Cancel":

        if input != "None":
            round[NAGASHI_MANGAN].append(int(input))
        
            if len(round[NAGASHI_MANGAN]) == len(context.chat_data[PLAYERS]):
                round[DRAFT_ROUND_TEXT] += helper_nagashi_text(context)
                text = round[DRAFT_ROUND_TEXT] + "\n\nWho in Tenpai?"
                keyboard = helper_nagashi_button(context, False, True)
                await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
                
                return ADD_ROUND_TENPAI
            
            else:
                text = round[DRAFT_ROUND_TEXT] + helper_nagashi_text(context) +\
                    "\n\nWho else Nagashi Mangan?"
                keyboard = helper_nagashi_button(context, True, True)
                await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

                return ADD_ROUND_NAGASHI
        
        else:
            if round[NAGASHI_MANGAN]:
                round[DRAFT_ROUND_TEXT] += helper_nagashi_text(context)
            text = round[DRAFT_ROUND_TEXT] + "\n\nWho in Tenpai?"
            keyboard = helper_nagashi_button(context, False, True)
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

            return ADD_ROUND_TENPAI
    
    else:
        
        return await handle_add_round_cancel(update, context)

def helper_nagashi_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    text = ", ".join([context.chat_data[PLAYERS][i] for i in context.chat_data[DRAFT_ROUND][NAGASHI_MANGAN]]) \
        if context.chat_data[DRAFT_ROUND][NAGASHI_MANGAN] else "None"
    return f"\nNagashi Mangan: <u>{text}</u>"

def helper_nagashi_button(context: ContextTypes.DEFAULT_TYPE, remove_nagashi_players: bool, has_none: bool):
    players = []
    for i, player in enumerate(context.chat_data[PLAYERS]):
        if not remove_nagashi_players or i not in context.chat_data[DRAFT_ROUND][NAGASHI_MANGAN]:
            players.append(InlineKeyboardButton(text=player, callback_data=i))
    buttons = [players]

    if has_none:
        buttons.append([InlineKeyboardButton(text="None", callback_data="None")])

    buttons.append([InlineKeyboardButton(text="Cancel", callback_data="Cancel")])

    return InlineKeyboardMarkup(buttons)

async def add_round_tenpai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()
    round = context.chat_data[DRAFT_ROUND]

    if IN_TENPAI not in round:
        round[IN_TENPAI] = []

    if input != "Cancel":

        if input != "None":
            round[IN_TENPAI].append(int(input))
        
            if len(round[IN_TENPAI]) == len(context.chat_data[PLAYERS]):
                round[DRAFT_ROUND_TEXT] += helper_tenpai_text(context)
                text = round[DRAFT_ROUND_TEXT] + "\n\nWho declared Riichi?"
                keyboard = helper_tenpai_button(context, False, True)
                await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
                
                return ADD_ROUND_RIICHI
            
            else:
                text = round[DRAFT_ROUND_TEXT] + helper_tenpai_text(context) +\
                    "\n\nWho else in Tenpai?"
                keyboard = helper_tenpai_button(context, True, True)
                await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

                return ADD_ROUND_TENPAI
        
        else:
            round[DRAFT_ROUND_TEXT] += helper_tenpai_text(context)
            text = round[DRAFT_ROUND_TEXT] + "\n\nWho declared Riichi?"
            keyboard = helper_tenpai_button(context, False, True)
            await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

            return ADD_ROUND_RIICHI
    
    else:
        
        return await handle_add_round_cancel(update, context)
    
def helper_tenpai_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    text = ", ".join([context.chat_data[PLAYERS][i] for i in context.chat_data[DRAFT_ROUND][IN_TENPAI]]) \
        if context.chat_data[DRAFT_ROUND][IN_TENPAI] else "None"
    return f"\nIn Tenpai: <u>{text}</u>"

def helper_tenpai_button(context: ContextTypes.DEFAULT_TYPE, remove_tenpai_players: bool, has_none: bool):
    players = []
    for i, player in enumerate(context.chat_data[PLAYERS]):
        if not remove_tenpai_players or i not in context.chat_data[DRAFT_ROUND][IN_TENPAI]:
            players.append(InlineKeyboardButton(text=player, callback_data=i))
    buttons = [players]

    if has_none:
        buttons.append([InlineKeyboardButton(text="None", callback_data="None")])

    buttons.append([InlineKeyboardButton(text="Cancel", callback_data="Cancel")])

    return InlineKeyboardMarkup(buttons)

async def add_round_riichi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()
    round = context.chat_data[DRAFT_ROUND]
    
    if DECLARED_RIICHI not in round:
        round[DECLARED_RIICHI] = []

    if input != "Cancel":
        
        if input != "None":            
            round[DECLARED_RIICHI].append(int(input))
            
            if len(round[DECLARED_RIICHI]) == len(context.chat_data[PLAYERS]):
                round[DRAFT_ROUND_TEXT] += helper_riichi_text(context)

                return await add_game_finish(update, context)

            else:
                text = round[DRAFT_ROUND_TEXT] + helper_riichi_text(context) +\
                    "\n\nWho else declared Riichi?"
                buttons = []
                for i, player in enumerate(context.chat_data[PLAYERS]):
                    if i not in round[DECLARED_RIICHI]:
                        buttons.append(InlineKeyboardButton(text=player, callback_data=i))
                keyboard = InlineKeyboardMarkup([
                    buttons,
                    [InlineKeyboardButton(text="None", callback_data="None")],
                    [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
                ])
                await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

                return ADD_ROUND_RIICHI
        
        else:
            round[DRAFT_ROUND_TEXT] += helper_riichi_text(context)
            
            return await add_game_finish(update, context)
    
    else:
        
        return await handle_add_round_cancel(update, context)
    
def helper_riichi_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    text = ", ".join([context.chat_data[PLAYERS][i] for i in context.chat_data[DRAFT_ROUND][DECLARED_RIICHI]]) \
        if context.chat_data[DRAFT_ROUND][DECLARED_RIICHI] else "None"
    return f"\nDeclared Riichi: <u>{text}</u>"

async def add_game_finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    round = context.chat_data[DRAFT_ROUND]

    if context.chat_data[MODE] == '4P':
        round[POINT_RECORDS] = helper_finish_points_4p(context)

    else:
        # revisit for 3P
        print()

    round[PREV_GAME_TRACKERS] = {
        CURRENT_WIND: context.chat_data[CURRENT_WIND],
        CURRENT_DEALER: context.chat_data[CURRENT_DEALER],
        CURRENT_DEALER_CONSEC: context.chat_data[CURRENT_DEALER_CONSEC],
        CURRENT_RIICHI: context.chat_data[CURRENT_RIICHI],
        CURRENT_HONBA: context.chat_data[CURRENT_HONBA]
    }

    context.chat_data[ROUND_RECORDS].append(round)
    curr = helper_curr_wind_dealer_text(context) if round[RESULT] != "Chombo" else "Chombo"

    if round[RESULT] == "Draw":
        
        if round[DECLARED_RIICHI]:
            context.chat_data[CURRENT_RIICHI] = len(round[DECLARED_RIICHI])

        context.chat_data[CURRENT_HONBA] += 1

        if context.chat_data[CURRENT_DEALER] in round[IN_TENPAI]:
            context.chat_data[CURRENT_DEALER_CONSEC] += 1

        else:
            context.chat_data[CURRENT_DEALER] += 1
            context.chat_data[CURRENT_DEALER_CONSEC] = 0

            if context.chat_data[CURRENT_DEALER] == 4:
                context.chat_data[CURRENT_WIND] += 1
                context.chat_data[CURRENT_DEALER] = 0

    elif round[RESULT] == "Tsumo" or round[RESULT] == "Ron": # Tsumo or Ron
        context.chat_data[CURRENT_RIICHI] = 0
        winners = [list(winner.keys())[0] for winner in round[WINNER]]
        
        if context.chat_data[CURRENT_DEALER] in winners:
            context.chat_data[CURRENT_HONBA] += 1
            context.chat_data[CURRENT_DEALER_CONSEC] += 1

        else:
            context.chat_data[CURRENT_DEALER] += 1
            context.chat_data[CURRENT_DEALER_CONSEC] = 0
            context.chat_data[CURRENT_HONBA] = 0
            
            if context.chat_data[CURRENT_DEALER] == 4:
                context.chat_data[CURRENT_WIND] += 1
                context.chat_data[CURRENT_DEALER] = 0
    
    # large red circle = \U0001F534
    # black square button = \U0001F532
    if context.chat_data[CURRENT_RIICHI] or context.chat_data[CURRENT_HONBA]:
        counter = ""

        if context.chat_data[CURRENT_RIICHI]:
            counter += "\U0001F534 " * context.chat_data[CURRENT_RIICHI]

        if context.chat_data[CURRENT_HONBA]:
            counter += "\U0001F532 " * context.chat_data[CURRENT_HONBA]

    else:
        counter = "None"
    
    score = helper_finish_points_text(context)
    round[DRAFT_ROUND_TEXT] = f"<b>{curr}</b>\n\n" +\
        f"{round[DRAFT_ROUND_TEXT]}\n" +\
        f"Counters: {counter}\n\n" +\
        f"{score}"
    await update.callback_query.edit_message_text(text=round[DRAFT_ROUND_TEXT], reply_markup=None, parse_mode="HTML")
    await update.callback_query.message.reply_text(text="Reply with next action", reply_markup=select_game_options_keyboard)
    
    return SELECT_GAME_ACTION

def helper_finish_points_4p(context: ContextTypes.DEFAULT_TYPE):
    round = context.chat_data[DRAFT_ROUND]
    players = context.chat_data[PLAYERS]

    # tally points via table
    data = {i: 0 for i in range(len(players))}
    
    if round[RESULT] == "Draw":
        player_count = len(players)
        nagashi_count = len(round[NAGASHI_MANGAN])
        tenpai_count = len(round[IN_TENPAI])

        if nagashi_count not in [0, player_count]:
            for nagashi_player in round[NAGASHI_MANGAN]:
                data[nagashi_player] += 12000 if nagashi_player == context.chat_data[CURRENT_DEALER] else 8000
                for p, player in enumerate(players):
                    if p != nagashi_player:
                        data[p] -= 4000 if nagashi_player == context.chat_data[CURRENT_DEALER] or p == context.chat_data[CURRENT_DEALER] else 2000

        elif tenpai_count not in [0, player_count] and nagashi_count == 0:
            points_tenpai = 3000 // tenpai_count
            points_non_tenpai = -3000 // (player_count - tenpai_count)
            for i in data:
                data[i] += points_tenpai if i in round[IN_TENPAI] else points_non_tenpai

        for i in round[DECLARED_RIICHI]:
            data[i] -= 1000

    elif round[RESULT] == "Chombo":

        if round[CHOMBO_PENALTY] != 0:
            for i in data:
                if i == round[LOSER]:
                    data[i] = -round[CHOMBO_PENALTY]

                elif context.chat_data[CURRENT_DEALER] == round[LOSER]:
                    data[i] = round[CHOMBO_PENALTY] // 3

                elif i == context.chat_data[CURRENT_DEALER]:
                    data[i] = round[CHOMBO_PENALTY] // 2

                else:
                    data[i] = round[CHOMBO_PENALTY] // 4

    else: # Tsumo or Ron
        round_result = TSUMO if round[RESULT] == "Tsumo" else RON

        # standard points
        for winner in round[WINNER]:
            i = list(winner.keys())[0]
            han_fu = winner[i]
            dealer_result = DEALER if i == context.chat_data[CURRENT_DEALER] else NONDEALER
            points = points_data[han_fu[HAN]][round_result][dealer_result] if han_fu[HAN] >= 5 \
                else points_data[han_fu[HAN]][han_fu[FU]][round_result][dealer_result]

            if round_result == TSUMO:
                others = list(data.keys())
                others.remove(i)

                if dealer_result == DEALER:
                    data[i] = points * 3
                    for i in others:
                        data[i] -= points

                else: # Tsumo by non-dealer
                    nd, d = points[0], points[1]
                    data[i] = nd * 2 + d
                    data[context.chat_data[CURRENT_DEALER]] -= d
                    others.remove(context.chat_data[CURRENT_DEALER])
                    for i in others:
                        data[i] -= nd
                
            else: # Ron
                data[i] = points
                data[round[LOSER]] -= points

        winner_count = len(round[WINNER])

        # existing/new riichi bonus
        bonus_riichi = context.chat_data[CURRENT_RIICHI] * 1000 + len(round[DECLARED_RIICHI]) * 1000

        if bonus_riichi:
            
            winners = []
            for winner in round[WINNER]:
                i = list(winner.keys())[0]
                winners.append(i)
                data[i] += bonus_riichi // winner_count

            if len(round[DECLARED_RIICHI]):
                for i in round[DECLARED_RIICHI]:
                    data[i] -= 1000

        # honba bonus
        bonus_honba = context.chat_data[CURRENT_HONBA] * 300

        if bonus_honba:

            if round_result == TSUMO:
                i = list(round[WINNER][0].keys())[0]
                data[i] += bonus_honba
                for p, player in enumerate(players):
                    if p != i:
                        data[p] -= bonus_honba // 3

            else:
                for winner in round[WINNER]:
                    i = list(winner.keys())[0]
                    data[i] += bonus_honba
                data[round[LOSER]] -= bonus_honba * winner_count

    return data

points_data = {
    13: {
        TSUMO: {
            DEALER: 16000, 
            NONDEALER: [8000, 16000]
        }, 
        RON: {
            DEALER: 48000, 
            NONDEALER: 32000
        }},
    11: {
        TSUMO: {
            DEALER: 12000, 
            NONDEALER: [6000, 12000]
        },
        RON: {
            DEALER: 36000, 
            NONDEALER: 24000
        }},
    8: {
        TSUMO: {
            DEALER: 8000, 
            NONDEALER: [4000, 8000]
        },
        RON: {
            DEALER: 24000, 
            NONDEALER: 16000
        }},
    6: {
        TSUMO: {
            DEALER: 6000, 
            NONDEALER: [3000, 6000]
        },
        RON: {
            DEALER: 18000, 
            NONDEALER: 12000
        }},
    5: {
        TSUMO: {
            DEALER: 4000, 
            NONDEALER: [2000, 4000]
        },
        RON: {
            DEALER: 12000, 
            NONDEALER: 8000
        }},
    4: {
        20: {
            TSUMO: {
                DEALER: 2600,
                NONDEALER: [1300, 2600]
            },
            RON: {
                DEALER: 0,
                NONDEALER: 0
            }
        },
        25: {
            TSUMO: {
                DEALER: 3200,
                NONDEALER: [1600, 3200]
            },
            RON: {
                DEALER: 9600,
                NONDEALER: 6400
            }
        },
        30: {
            TSUMO: {
                DEALER: 3900,
                NONDEALER: [2000, 3900]
            },
            RON: {
                DEALER: 11600,
                NONDEALER: 7700
            }
        }
    },
    3: {
        20: {
            TSUMO: {
                DEALER: 1300,
                NONDEALER: [700, 1300]
            },
            RON: {
                DEALER: 0,
                NONDEALER: 0
            }
        },
        25: {
            TSUMO: {
                DEALER: 1600,
                NONDEALER: [800, 1600]
            },
            RON: {
                DEALER: 4800,
                NONDEALER: 3200
            }
        },
        30: {
            TSUMO: {
                DEALER: 2000,
                NONDEALER: [1000, 2000]
            },
            RON: {
                DEALER: 5800,
                NONDEALER: 3900
            }
        },
        40: {
            TSUMO: {
                DEALER: 2600,
                NONDEALER: [1300, 2600]
            },
            RON: {
                DEALER: 7700,
                NONDEALER: 5200
            }
        },
        50: {
            TSUMO: {
                DEALER: 3200,
                NONDEALER: [1600, 3200]
            },
            RON: {
                DEALER: 9600,
                NONDEALER: 6400
            }
        },
        60: {
            TSUMO: {
                DEALER: 3900,
                NONDEALER: [2000, 3900]
            },
            RON: {
                DEALER: 11600,
                NONDEALER: 7700
            }
        }
    },
    2: {
        20: {
            TSUMO: {
                DEALER: 700,
                NONDEALER: [400, 700]
            },
            RON: {
                DEALER: 0,
                NONDEALER: 0
            }
        },
        25: {
            TSUMO: {
                DEALER: 800,
                NONDEALER: [400, 800]
            },
            RON: {
                DEALER: 2400,
                NONDEALER: 1600
            }
        },
        30: {
            TSUMO: {
                DEALER: 1000,
                NONDEALER: [500, 1000]
            },
            RON: {
                DEALER: 2900,
                NONDEALER: 2000
            }
        },
        40: {
            TSUMO: {
                DEALER: 1300,
                NONDEALER: [700, 1300]
            },
            RON: {
                DEALER: 3900,
                NONDEALER: 2600
            }
        },
        50: {
            TSUMO: {
                DEALER: 1600,
                NONDEALER: [800, 1600]
            },
            RON: {
                DEALER: 4800,
                NONDEALER: 3200
            }
        },
        60: {
            TSUMO: {
                DEALER: 2000,
                NONDEALER: [1000, 2000]
            },
            RON: {
                DEALER: 5800,
                NONDEALER: 3900
            }
        },
        70: {
            TSUMO: {
                DEALER: 2300,
                NONDEALER: [1200, 2300]
            },
            RON: {
                DEALER: 6800,
                NONDEALER: 4500
            }
        }
    },
    1: {
        30: {
            TSUMO: {
                DEALER: 500,
                NONDEALER: [300, 500]
            },
            RON: {
                DEALER: 1500,
                NONDEALER: 1000
            }
        },
        40: {
            TSUMO: {
                DEALER: 700,
                NONDEALER: [400, 700]
            },
            RON: {
                DEALER: 2000,
                NONDEALER: 1300
            }
        },
        50: {
            TSUMO: {
                DEALER: 800,
                NONDEALER: [400, 800]
            },
            RON: {
                DEALER: 2400,
                NONDEALER: 1600
            }
        },
        60: {
            TSUMO: {
                DEALER: 1000,
                NONDEALER: [500, 1000]
            },
            RON: {
                DEALER: 2900,
                NONDEALER: 2000
            }
        },
        70: {
            TSUMO: {
                DEALER: 1200,
                NONDEALER: [600, 1200]
            },
            RON: {
                DEALER: 3400,
                NONDEALER: 2300
            }
        }
    }
}

def helper_curr_wind_dealer_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    return f"{winds[context.chat_data[CURRENT_WIND]]} {str(context.chat_data[CURRENT_DEALER] + 1)}" +\
        f"{f"-{context.chat_data[CURRENT_DEALER_CONSEC]}" if context.chat_data[CURRENT_DEALER_CONSEC] else ""}"

def helper_finish_points_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    points = helper_finish_points(context)
    last_point_records = context.chat_data[ROUND_RECORDS][-1][POINT_RECORDS]
    text = "<b>Current points</b>\n\n"
    for i, p in enumerate(points):
        text += f"{context.chat_data[PLAYERS][i]}: {p} ({last_point_records[i]})\n"
    text = text[:-1]
    
    return text

def helper_finish_points(context: ContextTypes.DEFAULT_TYPE) -> str:
    points = [0] * len(context.chat_data[PLAYERS])

    for round in context.chat_data[ROUND_RECORDS]:
        point_records = round[POINT_RECORDS]
        for i, p in point_records.items():
            points[i] += p

    return points

async def add_round_chombo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()
    round = context.chat_data[DRAFT_ROUND]

    if input != "Cancel":
        round[DRAFT_ROUND_TEXT] += f"\nChombo: <u>{context.chat_data[PLAYERS][int(input)]}</u>"
        round[LOSER] = int(input)
        text = round[DRAFT_ROUND_TEXT] + "\n\nHow many points to penalise?"
        if context.chat_data[CURRENT_DEALER] == round[LOSER]:
            big, small = 12000, 6000
        else:
            big, small = 8000, 4000
        buttons = [
            [
                InlineKeyboardButton(text=f"{big}", callback_data=f"{big}"),
                InlineKeyboardButton(text=f"{small}", callback_data=f"{small}"),
                InlineKeyboardButton(text="0", callback_data="0"),
            ],
            [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")

        return ADD_ROUND_CHOMBO_POINTS

    else:
        
        return await handle_add_round_cancel(update, context)

async def add_round_chombo_points(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()
    round = context.chat_data[DRAFT_ROUND]

    if input != "Cancel":
        round[DRAFT_ROUND_TEXT] += f"\nPenalty: <u>{int(input)}</u>"
        round[CHOMBO_PENALTY] = int(input)

        return await add_game_finish(update, context)

    else:
        
        return await handle_add_round_cancel(update, context)

async def handle_add_round_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    del context.chat_data[DRAFT_ROUND]
    await update.callback_query.delete_message()

    return SELECT_GAME_ACTION

async def delete_last_round(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    if context.chat_data[ROUND_RECORDS]:
        text = context.chat_data[ROUND_RECORDS][-1][DRAFT_ROUND_TEXT] +\
            "\n\nDelete this round?"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Delete", callback_data="Delete")],
            [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
        ])
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")

        return DELETE_ROUND

    else:
        await update.message.reply_text("There are no round records to delete from. Reply with next action", 
            reply_markup=select_game_options_keyboard)

        return SELECT_GAME_ACTION
    
async def delete_last_round_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()

    if input == "Delete":
        prev = context.chat_data[ROUND_RECORDS][-1]
        trackers = prev[PREV_GAME_TRACKERS]
        context.chat_data[CURRENT_WIND] = trackers[CURRENT_WIND]
        context.chat_data[CURRENT_DEALER] = trackers[CURRENT_DEALER]
        context.chat_data[CURRENT_DEALER_CONSEC] = trackers[CURRENT_DEALER_CONSEC]
        context.chat_data[CURRENT_RIICHI] = trackers[CURRENT_RIICHI]
        context.chat_data[CURRENT_HONBA] = trackers[CURRENT_HONBA]
        curr = helper_curr_wind_dealer_text(context) if prev[RESULT] != "Chombo" else "Chombo"
        text = f"Round ({curr}) deleted"
        context.chat_data[ROUND_RECORDS].pop()

        await update.callback_query.edit_message_text(text=text, reply_markup=None)
        await update.callback_query.message.reply_text(text="Reply with next action", reply_markup=select_game_options_keyboard)

    # cancel
    else:
        await update.callback_query.delete_message()
        
    return SELECT_GAME_ACTION

async def show_game_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    if context.chat_data[GAME_RECORDS]:
        text = ""
        for i, game in enumerate(context.chat_data[GAME_RECORDS]):
            text += f"<b>Game {i+1}</b>\n\n"
            for i, player in enumerate(game[PLAYERS]):
                text += f"{player}: {game[FINAL_POINTS][i]}\n"
            text += f"\n1000 points: ${game[POINTS_VALUE]:.2f}\n\n"
        text += "Reply with next action"

    else:
        text = "There are no games recorded. Reply with next action"

    await update.message.reply_text(text, reply_markup=select_game_options_keyboard, parse_mode="HTML")

    return SELECT_GAME_ACTION

async def finish_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    if context.chat_data[ROUND_RECORDS]:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Finish", callback_data="Finish")],
            [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
        ])
        await update.message.reply_text("Finish the game?", reply_markup=keyboard)

        return FINISH_GAME

    else:
        await update.message.reply_text("There are no rounds recorded. Reply with next action", reply_markup=select_game_options_keyboard)

        return SELECT_GAME_ACTION
    
async def finish_game_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()

    if input == "Finish":
        points = helper_finish_points(context)
        sorted_points = sorted(points, reverse=True)
        winner_points = sorted_points[0]
        winner_count = 1
        riichi_transfer = 0

        if context.chat_data[CURRENT_RIICHI]:
            # stupid edge case
            if sorted_points[0] == sorted_points[1]:
                winner_count += 1
                if sorted_points[0] == sorted_points[2]:
                    winner_count += 1
            riichi_transfer = context.chat_data[CURRENT_RIICHI] * 1000 // winner_count

            for i, p in enumerate(points):
                if p == winner_points:
                    points[i] += riichi_transfer
        
        context.chat_data[GAME_RECORDS].append({
            PLAYERS: context.chat_data[PLAYERS],
            FINAL_POINTS: points,
            POINTS_VALUE: context.chat_data[POINTS_VALUE]
        })

        text = ""
        game_count = len(context.chat_data[GAME_RECORDS])
        for i, game in enumerate(context.chat_data[GAME_RECORDS][::-1]):
            text += f"<b>Game {game_count-i} - Final points</b>\n\n"
            for j, player in enumerate(game[PLAYERS]):
                text += f"{player}: {game[FINAL_POINTS][j]}\n"
            text += f"\n1000 points: ${game[POINTS_VALUE]:.2f}\n\n"
        text = text[:-2]        

        await update.callback_query.edit_message_text(text=text, reply_markup=None, parse_mode="HTML")
        await update.callback_query.message.reply_text(text="Reply with next action", reply_markup=select_session_options_keyboard)

        return SELECT_SESSION_ACTION
    
    # cancel
    else:
        await update.callback_query.delete_message()
        
        return SELECT_GAME_ACTION
    
async def end_session(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    if context.chat_data[GAME_RECORDS]:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="End", callback_data="End")],
            [InlineKeyboardButton(text="Cancel", callback_data="Cancel")]
        ])
        await update.message.reply_text("End the session?", reply_markup=keyboard)

        return END_SESSION

    else:
        await update.message.reply_text("There are no games recorded. Reply with next action", reply_markup=select_session_options_keyboard)

        return SELECT_SESSION_ACTION
    
async def end_session_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input = update.callback_query.data
    await update.callback_query.answer()

    if input == "End":
        data = {}
        for game in context.chat_data[GAME_RECORDS]:
            for i, player in enumerate(game[PLAYERS]):
                if player in data:
                    data[player] += round(game[FINAL_POINTS][i] * game[POINTS_VALUE] / 1000, 2)
                else:
                    data[player] = round(game[FINAL_POINTS][i] * game[POINTS_VALUE] / 1000, 2)

        text = "<b>Overall calculation</b>\n\n"
        data_sorted = sorted(data.items(), key=lambda item: item[1])
        for player, amount in data_sorted:
            text += f"{player}: {amount:.2f}\n"
        text += "\n"

        start = 0
        end = len(data_sorted) - 1
        while start < end:
            diff = round(data_sorted[start][1] + data_sorted[end][1], 2)
            if diff > 0:
                text += f"{data_sorted[start][0]} pay {data_sorted[end][0]} ${abs(data_sorted[start][1]):.2f}\n"
                start += 1
                data_sorted[end] = (data_sorted[end][0], diff)
            elif diff < 0:
                text += f"{data_sorted[start][0]} pay {data_sorted[end][0]} ${data_sorted[end][1]:.2f}\n"
                end -= 1
                data_sorted[start] = (data_sorted[start][0], diff)
            else:
                text += f"{data_sorted[start][0]} pay {data_sorted[end][0]} ${abs(data_sorted[start][1]):.2f}\n"
                start += 1
                end -= 1

        await update.callback_query.edit_message_text(text=text, reply_markup=None, parse_mode="HTML")
        await update.callback_query.message.reply_text(text="Bot stopped", reply_markup=ReplyKeyboardRemove())

        return END
    
    # cancel
    else:
        await update.callback_query.delete_message()
        
        return SELECT_GAME_ACTION

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("").build()

    add_round_conv = ConversationHandler(
        entry_points = [MessageHandler(filters.Regex("^Add round$"), add_round)],
        states = {
            ADD_ROUND_RESULT: [CallbackQueryHandler(add_round_result)],
            ADD_ROUND_WINNER: [CallbackQueryHandler(add_round_winner)],
            ADD_ROUND_HAN: [CallbackQueryHandler(add_round_han)],
            ADD_ROUND_FU: [CallbackQueryHandler(add_round_fu)],
            ADD_ROUND_LOSER: [CallbackQueryHandler(add_round_loser)],
            ADD_ROUND_NAGASHI: [CallbackQueryHandler(add_round_nagashi)],
            ADD_ROUND_TENPAI: [CallbackQueryHandler(add_round_tenpai)],
            ADD_ROUND_RIICHI: [CallbackQueryHandler(add_round_riichi)],
            ADD_ROUND_CHOMBO: [CallbackQueryHandler(add_round_chombo)],
            ADD_ROUND_CHOMBO_POINTS: [CallbackQueryHandler(add_round_chombo_points)]
        },
        fallbacks = [CommandHandler("stop", stop)],
        map_to_parent = {
            SELECT_GAME_ACTION: SELECT_GAME_ACTION,
            END: END
        },
        per_user = False
    )

    delete_last_round_conv = ConversationHandler(
        entry_points = [MessageHandler(filters.Regex("^Delete last round$"), delete_last_round)],
        states = {
            DELETE_ROUND: [CallbackQueryHandler(delete_last_round_confirm)]
        },
        fallbacks = [CommandHandler("stop", stop)],
        map_to_parent = {
            SELECT_GAME_ACTION: SELECT_GAME_ACTION,
            END: END
        },
        per_user = False
    )

    finish_game_conv = ConversationHandler(
        entry_points = [MessageHandler(filters.Regex("^Finish game$"), finish_game)],
        states = {
            FINISH_GAME: [CallbackQueryHandler(finish_game_confirm)]
        },
        fallbacks = [CommandHandler("stop", stop)],
        map_to_parent = {
            SELECT_GAME_ACTION: SELECT_GAME_ACTION,
            SELECT_SESSION_ACTION: SELECT_SESSION_ACTION,
            END: END
        },
        per_user = False
    )

    select_game_action_handlers = [
        add_round_conv,
        delete_last_round_conv,
        MessageHandler(filters.Regex("^Show game history$"), show_game_history),
        finish_game_conv,
    ]
    
    start_new_game_conv = ConversationHandler(
        entry_points = [MessageHandler(filters.Regex("^Start new game$"), start_new_game)],
        states = {
            MODE : [MessageHandler(filters.Regex("^4P$"), mode), CommandHandler("help", help)],
            PLAYERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, players)],
            POINTS_VALUE: [MessageHandler(filters.Regex(r"^\d+(\.\d+)?$"), points_value)],
            SELECT_GAME_ACTION: select_game_action_handlers,
        },
        fallbacks = [CommandHandler("stop", stop)],
        map_to_parent = {
            SELECT_SESSION_ACTION: SELECT_SESSION_ACTION,
            END: END
        },
        per_user = False
    )

    end_session_conv = ConversationHandler(
        entry_points = [MessageHandler(filters.Regex("^End session$"), end_session)],
        states = {
            END_SESSION: [CallbackQueryHandler(end_session_confirm)]
        },
        fallbacks = [CommandHandler("stop", stop)],
        map_to_parent = {
            SELECT_SESSION_ACTION: SELECT_SESSION_ACTION,
            END: END
        },
        per_user = False
    )

    select_session_action_handlers = [
        start_new_game_conv,
        end_session_conv,
    ]
    
    conv_handler = ConversationHandler(
        entry_points = [CommandHandler("start", start)],
        states = {
            SELECT_SESSION_ACTION: select_session_action_handlers,
            END: [CommandHandler("start", start)]
        },
        fallbacks = [CommandHandler("stop", stop)],
        per_user = False
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
