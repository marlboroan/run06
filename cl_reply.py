import os
import random
from time import sleep
import log
from mcl import CL


def main():
    test = False
    uname = os.environ["UNAME"]
    upass = os.environ["UPASS"]
    secret = os.environ.get("SECRET", CL.DEFAULT_SECRET)
    secret = CL.DEFAULT_SECRET if len(secret) < len(CL.DEFAULT_SECRET) else secret

    cl = CL(uname, upass, secret)
    if cl and not cl.is_login():
        raise Exception("login fail")

    cl.init_date()
    times = 10
    try:
        times = int(os.environ["TIMES"])
    except (ValueError, KeyError) as err:
        log.d("%s %s", type(err), err)
    if cl.jifen < 100:
        today_times = cl.get_today_reply_times()
        times = 10 - today_times if times + today_times > 10 else times
        inter_times = 12
    else:
        if times == 10:
            raise Exception("Stop!")
        else:
            times = times if times < 5 else random.randint(times - 5, times + 5)
        inter_times = random.randint(13, 21)
    times = 4 if test else times
    log.d('times = %s', times)
    before_sleep_time = 2 if times <= 1 else random.randint(0, 2048)
    before_sleep_time = 3 if test else before_sleep_time
    log.d('before_sleep_time = %s', before_sleep_time)
    if before_sleep_time > 60:
        cl.close_session()
    sleep(before_sleep_time)
    has_loop_times = 0
    reply_success_times = 0
    while reply_success_times < times and has_loop_times - reply_success_times < 6:
        try:
            log.i("At %s", reply_success_times + 1)
            has_loop_times = has_loop_times + 1
            if not cl.browse():
                log.w("browse fail , next time")
                continue
            browse_time = 3 if test else random.randint(8, 63)
            log.d('browse time = %ss', browse_time)
            sleep(browse_time)
            if cl.jifen < 100:
                sleep_time = random.randint(1024, 2048)
            else:
                sleep_time = random.randint(300, 800)
            sleep_time = 2 if test else sleep_time
            au = '回复成功' if test else cl.post_reply()
            if au == "回复成功":
                log.d(au)
            else:
                log.w(au)
            log.d('sleep_time = %ss', sleep_time)
            if au == '回复成功':
                reply_success_times = reply_success_times + 1
                if reply_success_times < times:
                    cl.close_session()
                    if reply_success_times % inter_times == 0:
                        sleep_time = sleep_time if test else sleep_time + random.randint(30 * 60, 40 * 60)
                        log.w('change sleep_time :%s', sleep_time)
                    sleep(sleep_time)
            elif au == '今日已达上限':
                reply_success_times = times
            elif au == '1024限制':
                has_loop_times = has_loop_times - 1
                cl.close_session()
                sleep(sleep_time)
            elif au == '未開啟兩步驗證':
                sleep(2)
            else:
                log.e('unknown err')
                sleep(2)
        except Exception as err:
            sleep(2)
            log.ex('Exception :%s', err)
    log.i(cl.get_today_reply_times())
    cl.close_session()
    if cl.has_news:
        raise Exception("has News")


if __name__ == "__main__":
    main()
