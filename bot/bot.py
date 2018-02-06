from telegram.ext import Updater, CommandHandler
import logging
import db
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt #; plt.rcdefaults()
import numpy as np

import datetime

TOKEN = os.environ.get('BOT_TOKEN', None)
if TOKEN is None:
    raise Exception('No Token!')

updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def meditate(bot, update):
    db.get_or_create_user(update.message.from_user)
    parts = update.message.text.split(' ')
    if len(parts) < 2:
        bot.send_message(chat_id=update.message.from_user.id, text="You need to specify how many minutes did you meditate!")
        return

    minutes = parts[1]
    minutes = int(minutes)
    if minutes < 5 or minutes > 1000:
        return

    try:
        db.add_timelog_to(update.message.from_user.id, minutes)
        db.increase_streak_of(update.message.from_user.id)
        bot.send_message(chat_id=update.message.from_user.id, text="You have meditated today! 🙏")
    except ValueError:
        bot.send_message(chat_id=update.message.from_user.id, text="You need to specify the minutes as a number!")

def anxiety(bot, update):
    db.get_or_create_user(update.message.from_user)
    parts = update.message.text.split(' ')
    command = parts[0]

    if len(parts) < 2:
        bot.send_message(chat_id=update.message.from_user.id, text="Please give your anxiety levels.")
        return

    value = parts[1]
    value = int(value)
    if value < 0 or value > 10:
        bot.send_message(chat_id=update.message.from_user.id, text="Please rate your anxiety between 0 (low) and 10 (high).")
        return

    try:
        db.add_to_table(command, update.message.from_user.id, value)
        bot.send_message(chat_id=update.message.from_user.id, text="Thank you for updating! 🙏")
    except ValueError:
        bot.send_message(chat_id=update.message.from_user.id, text="You need to specify the value as a number.")

def top(bot, update):
    db.get_or_create_user(update.message.from_user)
    top_users = db.get_top(5)
    line = []
    for i, user in enumerate(top_users):
        first_name = user[0]
        last_name = user[1]
        username = user[2]
        streak = user[3]

        if username:
            name_to_show = username
        else:
            name_to_show = first_name
            if last_name:
                name_to_show += f' {last_name}'

        line.append(f'{i + 1}. {name_to_show}   ({streak}🔥)')

    message = '\n'.join(line)
    bot.send_message(chat_id=update.message.chat_id, text=message)

def stats(bot, update):
    db.get_or_create_user(update.message.from_user)
    parts = update.message.text.split(' ')
    command = parts[0]
    duration = 7

    if len(parts) == 2:
        if parts[1] == 'weekly':
            duration = 7
        elif parts[1] == 'biweekly':
            duration = 14
        elif parts[1] == 'monthly':
            duration = 30
    
    if command == "meditatestats":
        generate_timelog_report_from(update.message.from_user.id, duration)
    else:
        # anxiety stats
        pass

    with open('./chart.png', 'rb') as photo:
        bot.send_photo(chat_id=update.message.chat_id, photo=photo)

def generate_timelog_report_from(id, days):
    results = db.get_anxiety(id, days - 1)

    now = datetime.datetime.now()
    past_week = {}
    for days_to_subtract in reversed(range(days)):
        d = datetime.datetime.today() - datetime.timedelta(days=days_to_subtract)
        past_week[d.day] = 0

    for result in results:
        past_week[result[1].day] = result[0]

    total = 0
    for key in past_week.keys():
        total += past_week[key]
    average = total / len(past_week.keys())

    y_pos = np.arange(len(past_week.keys()))

    plt.bar(y_pos, past_week.values(), align='center', alpha=0.5)
    plt.xticks(y_pos, past_week.keys())
    plt.ylabel('Level')
    plt.title(f'Last {days} days report. Average: {average}')
    plt.savefig('chart.png')
    plt.close()

def generate_timelog_report_from(id, days):
    results = db.get_timelog_from(id, days - 1)

    now = datetime.datetime.now()
    past_week = {}
    for days_to_subtract in reversed(range(days)):
        d = datetime.datetime.today() - datetime.timedelta(days=days_to_subtract)
        past_week[d.day] = 0

    for result in results:
        past_week[result[1].day] += result[0]

    total = 0
    for key in past_week.keys():
        total += past_week[key]

    y_pos = np.arange(len(past_week.keys()))

    plt.bar(y_pos, past_week.values(), align='center', alpha=0.5)
    plt.xticks(y_pos, past_week.keys())
    plt.ylabel('Minutes')
    plt.title(f'Last {days} days report. Total: {total} minutes')
    plt.savefig('chart.png')
    plt.close()

dispatcher.add_handler(CommandHandler('anxiety', anxiety))
dispatcher.add_handler(CommandHandler('anxietystats', stats))
dispatcher.add_handler(CommandHandler('meditate', meditate))
dispatcher.add_handler(CommandHandler('meditatestats', stats))
dispatcher.add_handler(CommandHandler('top', top))

updater.start_polling()
updater.idle()
