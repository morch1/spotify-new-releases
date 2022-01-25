import hjson
import services
import sqlite3
import os
import pytz
from commands import COMMANDS
from config import Config
from apscheduler.schedulers.background import BlockingScheduler
from datetime import datetime


def main():
    if os.getenv('DEBUG', 0):
        import debugpy
        debugpy.listen(("0.0.0.0", 3000))
        debugpy.wait_for_client()
        print('Attached!')

    with open('/etc/spotify-utils.hjson', 'r', encoding='utf-8') as cf:
        config = hjson.load(cf)

    scheduler = BlockingScheduler(timezone=pytz.timezone(config.get('timezone', 'UTC')))

    for schedule in config['schedules']:
        
        def do_tasks(schedule=schedule):
            print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] running schedule {schedule["name"]}')

            db = sqlite3.connect('/var/lib/spotify-utils/db.sqlite3')

            lastfm = services.LastFM(db, **config.get('lastfm', {}))
            join = services.Join(**config.get('join', {}))
            spotify = services.Spotify(db, **config['spotify'])
            configObj = Config(db, spotify, lastfm, join)

            for task in schedule['tasks']:
                args = task.get('args', dict())
                print(f'> {task["cmd"]}', ' '.join(f'{arg}={value}' for arg, value in args.items()))
                comment = task.get('comment', None)
                if comment:
                    print(f'    {comment}')
                COMMANDS[task['cmd']](configObj, **args)
            
            db.close()
            print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] finished running schedule {schedule["name"]}')

        cron = schedule['cron']
        scheduler.add_job(do_tasks, 'cron', **cron)

    try:
        scheduler.start()
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    main()
