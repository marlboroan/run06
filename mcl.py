import json
import math
import random
import re
from time import sleep
import onetimepass as otp
import requests
import log

CR = None
NR = None


class CL:
    REGISTER_SUCCESS = 1
    REGISTER_FAIL_VALIDATE_WRONG = 2
    REGISTER_FAIL_INVCODE_WRONG = 3
    REGISTER_FAIL_UNAME_UNAV = 4
    REGISTER_FAIL_UNKNOWN = 5
    BANK_TYPE_DINGQI = 2
    VAL_CODE_RETRY_TIMES = 3
    BANK_TYPE_HUOQI = 1
    SESSION = requests.session()
    BANK_ACTION_SAVE = 'save'
    BANK_ACTION_DRAW = 'draw'
    CL_JSON = "./cl_json.json"
    KEY_UNAMES = "unames"
    KEY_EMAIL = "email"
    KEY_PASSWORD = "password"
    KEY_ALL = "all"
    HOST = 'https://www.t66y.com/'
    LOGIN_URL = HOST + 'login.php'
    JQ_URL = HOST + "thread0806.php?fid=7&search=today"
    XSD_URL = HOST + "thread0806.php?fid=8&search=today"
    GQ_URL = HOST + "thread0806.php?fid=16&search=today"
    POST_URL = HOST + 'post.php?'
    INDEX_URL = HOST + 'index.php'
    PROFILE_URL = HOST + 'profile.php'
    BANK_URL = HOST + 'hack.php?H_name=bank&'
    REGIS_URL = HOST + "register.php"
    PM_URL = HOST + "message.php?action=write&touid="
    DEFAULT_SECRET = 'SECRET'
    HEADERS = {
        'Host': 't66y.com',
        'Proxy-Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Safari: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Safari/513.23'
    }

    has_news = False
    __session = requests.Session()
    __login_times = 1
    __last_atc_content = ""
    __headers = HEADERS

    def __init__(self, uname, upass, secret=DEFAULT_SECRET, headers=None):
        # log.d("uname = %s, upass = %s,secrct = %s", uname, upass, secret)
        if headers is not None:
            self.__headers.update(headers)
        if secret == CL.DEFAULT_SECRET or len(secret) < len(CL.DEFAULT_SECRET):
            log.i('use cookies')
            self.__session.cookies['227c9_winduser'] = uname
            if headers is None:
                t = {'User-Agent': upass}
                self.__headers.update(t)
        else:
            log.i('use pass')
            self._uname = uname
            self._upass = upass
            self._secret = secret
            while not self.login() and self.__login_times < 5:
                self.__login_times = self.__login_times + 1

    def login(self):
        sleep(2)
        log.d('login times = ' + str(self.__login_times))
        data = {
            'pwuser': self._uname.encode('gb2312'),
            'pwpwd': self._upass,
            'hideid': '0',
            'cktime': '0',
            'forward': self.HOST + 'post.php?',
            'jumpurl': self.HOST + 'post.php?',
            'step': '2'
        }
        res = CL.cl_decode(self.__session.post(self.LOGIN_URL, headers=self.__headers, data=data))
        status = False
        if res.find('登录尝试次数过多') != -1:
            log.w('too much try times')
            input_times = 0
            while not self.input_vercode() and input_times < 3:
                input_times = input_times + 1
        elif res.find('賬號已開啟兩步驗證') != -1:
            status = self.login_with_two_step()
        elif res.find('密碼輸入錯誤') != -1 or res.find('密碼錯誤') != -1:
            raise Exception('login :pass wrong')
        elif res.find('您已經順利登錄') != -1:
            status = True
        else:
            log.e(CL.get_prompt(res))
        # log.d("login " + str_(status))
        return status

    def login_with_two_step(self):
        sleep(2)
        status = False
        retry_times = 0
        while retry_times < 3:
            my_token = otp.get_totp(self._secret)
            data = {
                'step': '2',
                'cktime': '0',
                'oneCode': str(my_token)
            }
            res = CL.cl_decode(self.__session.post(self.LOGIN_URL, headers=self.__headers, data=data))
            need_break = True
            if res.find('您已經順利登錄') != -1:
                status = True
            elif res.find("密匙驗證失敗") != -1:
                need_break = False
                sleep(62)
            else:
                log.e(CL.get_prompt(res))
            if need_break:
                break
        log.d(str(status))
        return status

    def input_vercode(self):
        sleep(2)
        vercode = self.get_code()
        data = {
            'validate': vercode
        }
        res = CL.cl_decode(self.__session.post(self.LOGIN_URL, data=data, headers=self.__headers))
        return res.find('驗證碼不正確') == -1

    def is_login(self):
        sleep(2)
        res = CL.cl_decode(self.__session.get(self.INDEX_URL, headers=self.__headers))
        # log.d(res)
        uname = "$"
        search = re.search('font-weight:bold\">(.*)</span>', res)
        if search:
            uname = search.group(1)
        is_login = res.find('login.php?action=quit') != -1
        uname = uname[0] + " "
        log.d(uname + str(is_login))
        return is_login

    def init_date(self):
        sleep(2)
        res = CL.cl_decode(self.__session.get(self.INDEX_URL, headers=self.__headers))
        # log.d(res)
        pat_info = r'您的等級.*?>(.*?)<.*?' \
                   r'您的IP : (.*?)<.*?' \
                   r'威望: ([0-9]+).*?' \
                   r'金錢: ([0-9]+).*?' \
                   r'貢獻: ([0-9]+).*?' \
                   r'共發表帖子: ([0-9]+)'
        v = 103
        g = 0
        search = re.search(pat_info, res)
        if search:
            v = int(search.group(3))
            g = int(search.group(5))
        self.jifen = math.ceil(v + 0.02 * g)
        log.d("积分 %s", self.jifen)
        sleep(2)
        res = CL.cl_decode(self.__session.get(self.PROFILE_URL, headers=self.__headers))
        pro_detail_url = re.findall(r'profile.php\?action=show&uid=\d{1,9}', res)[0]
        pro_detail_url = self.HOST + pro_detail_url
        self._pro_detail_url = pro_detail_url
        # log.d('pro_detail_url = '+pro_detail_url)
        self.init_links()

    def init_links(self):
        sleep(2)
        res = CL.cl_decode(self.__session.get(self.JQ_URL, headers=self.__headers))
        jq_links = self.get_legal_links(res, 10)
        log.d('jq_links = ' + str(len(jq_links)))
        sleep(2)
        res = CL.cl_decode(self.__session.get(self.XSD_URL, headers=self.__headers))
        xsd_links = self.get_legal_links(res, 10)
        random.shuffle(xsd_links)
        xsd_links = xsd_links[0:10]
        log.d('xsd_links = ' + str(len(xsd_links)))
        sleep(2)
        res = CL.cl_decode(self.__session.get(self.GQ_URL, headers=self.__headers))
        gq_links = self.get_legal_links(res, 3)
        random.shuffle(gq_links)
        gq_links = gq_links[0:20]
        log.d('gq_links = ' + str(len(gq_links)))
        all_links = jq_links + xsd_links + gq_links
        log.d("all_links = " + str(len(all_links)))
        random.shuffle(all_links)
        self._all_links = all_links

    def browse(self):
        sleep(2)
        status = False
        try:
            one_link = self.get_one_link()
            self._oneLink = one_link
            group = one_link.split("/")
            tid = group[len(group) - 1].replace(".html", "")
            fid = group[len(group) - 2]
            one_link = self.HOST + one_link
            res = CL.cl_decode(self.__session.get(url=one_link, headers=self.__headers))
            self._atc_title = self.get_atc_title(res)
            self._atc_content = self.get_atc_content()
            while self.__last_atc_content == self._atc_content:
                log.d('browse atc_content same as last')
                self._atc_content = self.get_atc_content()
            self._fid = fid
            self._tid = tid
            log.d('browse fid = ' + str(fid) + ',tid = ' + str(tid))
            status = True
        except Exception as err:
            log.e('Exception = ' + str(err))
        return status

    def get_one_link(self):
        m = random.randint(0, len(self._all_links) - 1)
        one_link = self._all_links[m]
        log.d('getOneLink = ' + one_link)
        return one_link

    def get_atc_content(self):
        reply = ['感谢分享。', '感谢分享', '感谢分享', '谢谢分享', '多谢分享']
        if self.jifen < 99:
            reply.append('1024')
        reply_content = reply[random.randint(0, len(reply) - 1)]
        log.d(str(reply_content))
        return reply_content.encode('gb2312')

    def post_reply(self):
        sleep(2)
        data = {
            'atc_usesign': '1',
            'atc_convert': '1',
            'atc_autourl': '1',
            'atc_title': self._atc_title,
            'atc_content': self._atc_content,
            'step': '2',
            'action': 'reply',
            'fid': self._fid,
            'tid': self._tid,
            'atc_attachment': 'none',
            'pid': '',
            'article': '',
            'touid': '',
            'verify': 'verify'
        }
        # log.d("url = %s,data = %s,heads = %s", self.POST_URL, data, self.__headers)
        res = CL.cl_decode(self.__session.post(url=self.POST_URL, data=data, headers=self.__headers))
        if res.find('發貼完畢點擊') != -1:
            status = '回复成功'
            self.__last_atc_content = self._atc_content
            self._all_links.remove(self._oneLink)
        elif res.find('所屬的用戶組') != -1:
            status = '今日已达上限'
        elif res.find('1024秒內不能') != -1:
            status = '1024限制'
        elif res.find('尚未開啟兩步驗證') != -1:
            status = '未開啟兩步驗證'
        else:
            status = CL.get_prompt(res)
        return status

    def get_today_reply_times(self):
        sleep(2)
        res = CL.cl_decode(self.__session.get(self._pro_detail_url, headers=self.__headers))
        # log.d(res)
        self.has_news = res.find('您有新私信, 請注意查收') != -1
        today_reply_times = 10
        search = re.search(r'今日(\d{1,5})篇', res)
        if search:
            today_reply_times = int(search.group(1))
        log.d(today_reply_times)
        return today_reply_times

    def bank(self, money_number, action=BANK_ACTION_SAVE, btype=BANK_TYPE_HUOQI):
        sleep(12)
        data = {
            'action': action,
            'btype': btype
        }
        if action == CL.BANK_ACTION_DRAW:
            data['drawmoney'] = money_number
        elif action == CL.BANK_ACTION_SAVE:
            data['savemoney'] = money_number
        else:
            log.e("no action")
            return False
        res = CL.cl_decode(self.__session.post(self.BANK_URL, data=data, headers=self.__headers))
        # log.d(res)
        btype = "H" if btype == CL.BANK_TYPE_HUOQI else "D"
        log.d('bank:type %s, action %s', btype, action)
        result = res.find('完成') != -1
        if not result:
            log.e("bank fail %s", CL.get_prompt(res))
        else:
            log.d("bank Success!")
        return result

    def close_session(self):
        self.__session.close()

    def is_uid_available(self, uid, default=False):
        sleep(random.randint(2, 6))
        url = self.PM_URL + str(uid)
        result = default
        try:
            res = CL.cl_decode(self.__session.get(url=url, headers=self.__headers))
            result = res.find("ws23dfr") != -1
        except Exception as err:
            log.e(err)
        return result

    def get_cur_av_uid(self, start_uid=555555, end_uid=666666):
        global NR
        if NR is None:
            NR = __import__("noticer")
        if start_uid == 555555:
            start_uid = int(NR.opera_data()) - 1
            log.d("from database start_uid %s", start_uid)
        if self.is_uid_available(start_uid):
            log.d("start uid available,return.%s", start_uid)
            return start_uid
        if end_uid <= start_uid:
            end_uid = start_uid + 100
        end_times = 1
        while not self.is_uid_available(end_uid) and end_times <= 10:
            end_uid = 100 * end_times * end_times + end_uid
            end_times = end_times + 1
            log.d("end_uid not available %s,times %s", end_uid, end_times)
        curr_uid = start_uid + min(73, math.floor((end_uid - start_uid) / 2))
        while start_uid <= curr_uid < end_uid:
            log.d("start %s ,curr_uid %s, end %s", start_uid, curr_uid, end_uid)
            curr_av = self.is_uid_available(curr_uid)
            last_one_av = self.is_uid_available(curr_uid - 1)
            if curr_av and not last_one_av:
                NR.opera_data(value=curr_uid, optype="set")
                break
            if curr_av:
                end_uid = curr_uid
                curr_uid = curr_uid - math.ceil((curr_uid - start_uid) / 2)
            else:
                start_uid = curr_uid
                curr_uid = curr_uid + math.ceil((end_uid - curr_uid) / 2)
        return curr_uid

    def get_code(self):
        return CL.get_code_static(self.__session)

    @staticmethod
    def get_atc_title(res):
        pat = r'<h4>(.*)</h4>'
        atc_title = 'Re:'
        search = re.search(pat, res)
        if not search:
            index = res.find(r'article=0">編輯') + 45
            log.d(res[index:index + 50])
        else:
            atc_title = atc_title + search.group(1)
        log.d(atc_title)
        return atc_title

    @staticmethod
    def cl_decode(res):
        return res.text.encode('iso-8859-1').decode('gbk', 'ignore')

    @staticmethod
    def get_code_static(session=SESSION):
        global CR
        if CR is None:
            CR = __import__("captchaer")
        code = random.uniform(0, 1)
        code = round(code, 16)
        vercode_url = CL.HOST + 'require/codeimg.php?' + str(code)
        res = session.get(vercode_url, headers=CL.__headers)
        vercode = CR.get_code(res.content)
        # log.d("code = %s", vercode)
        return vercode

    @staticmethod
    def get_legal_links(res, legal_start_index):
        legal_start_index = max(3, legal_start_index)
        pat = r'htm_data/\w+/\w+/\w+.html'
        pt_index = res.find("普通主題")
        tm_index = res.rfind("Top-marks")
        index = max(pt_index, tm_index)
        # log.d("pt_index = " + str_(pt_index) +",tm_index = " + str_(tm_index))
        if index != -1:
            res = res[index:len(res)]
            legal_start_index = 0
        links = re.findall(pat, res)
        links = links[legal_start_index:len(links)]
        return links

    @staticmethod
    def get_prop(res, prop):
        value = None
        pat = '<input type_=\"hidden\".*' + prop + r'.*\/>'
        search = re.findall(pat, res)
        if len(search) > 0:
            search = re.search(r'value=\"(.*)\"', search[0])
            if search:
                value = search.group(1)
        log.d(prop + " = " + value)
        return value

    @staticmethod
    def save_config(dict_):
        log.d("save dict_ %s", dict_)
        with open(CL.CL_JSON, 'w', encoding='utf-8') as fw:
            json.dump(dict_, fw, ensure_ascii=False)

    @staticmethod
    def get_config_by_key(key=KEY_ALL, default=""):
        value = default
        try:
            with open(CL.CL_JSON, 'r', encoding='utf-8') as fr:
                load = json.load(fr)
                value = load if key == CL.KEY_ALL else load.get(key, default)
        except Exception as e:
            dict_ = {
                CL.KEY_UNAMES: [""],
                CL.KEY_PASSWORD: "",
                CL.KEY_EMAIL: ""
            }
            CL.save_config(dict_)
            log.e("Exception %s", e)
        return value

    @staticmethod
    def update_config():
        unames = CL.get_config_by_key(CL.KEY_UNAMES)
        if not unames or len(unames) < 1:
            log.e("unames has nothing")
        else:
            for uname in unames[:]:
                if not CL.is_uname_available(uname, True):
                    unames.remove(uname)
        log.d("get all %s", CL.get_config_by_key())
        password = CL.get_config_by_key(CL.KEY_PASSWORD)
        email = CL.get_config_by_key(CL.KEY_EMAIL)
        dict_ = {
            CL.KEY_UNAMES: unames,
            CL.KEY_PASSWORD: password,
            CL.KEY_EMAIL: email
        }
        CL.save_config(dict_)

    @staticmethod
    def register(invate_code, uname="", password="", email="", validate=""):
        unames = CL.get_config_by_key(CL.KEY_UNAMES)
        uname = unames[random.randint(0, len(unames) - 1)] if not uname and unames else uname
        password = password if password else CL.get_config_by_key(CL.KEY_PASSWORD)
        email = email if email else CL.get_config_by_key(CL.KEY_EMAIL)
        if not (uname and password and email):
            log.e("please check cl_json or args,name or pass or email isn't exist")
            return False
        return CL.real_register(invate_code, uname, password, email, validate) == CL.REGISTER_SUCCESS

    @staticmethod
    def real_register(invate_code, uname, password, email, validate=""):
        log.d("uname = %s,email = %s,password = %s,invate_code = %s,validate = %s",
              uname, email, password, invate_code, validate)
        status = CL.REGISTER_FAIL_UNKNOWN
        times = 0

        while status != CL.REGISTER_SUCCESS:
            times = times + 1
            log.d("try times %s", times)
            validate = validate if validate else CL.get_code_static()
            data = {
                'regname': uname.encode('gb2312'),
                'regpwd': password,
                "regpwdrepeat": password,
                "regemail": email,
                "invcode": invate_code,
                "validate": validate,
                "forward": "",
                'step': '2'
            }
            res = CL.cl_decode(CL.SESSION.post(CL.REGIS_URL, headers=CL.__headers, data=data))
            need_break = True
            if res.find('恭喜您') != -1:
                status = CL.REGISTER_SUCCESS
            elif res.find('驗證碼不正確') != -1:
                log.w("register :驗證碼不正確")
                need_break = times >= CL.VAL_CODE_RETRY_TIMES
                validate = None
                status = CL.REGISTER_FAIL_VALIDATE_WRONG
            elif res.find('邀請碼錯誤') != -1:
                log.e("register :邀請碼錯誤")
                status = CL.REGISTER_FAIL_INVCODE_WRONG
            elif res.find("此用戶名已經被註冊") != -1:
                log.e("此用戶名已經被註冊")
                status = CL.REGISTER_FAIL_UNAME_UNAV
            else:
                log.e(CL.get_prompt(res))
                status = CL.REGISTER_FAIL_UNKNOWN

            if status == CL.REGISTER_SUCCESS:
                log.i("register success ! uname = %s,email = %s,password = %s,invate_code = %s",
                      uname, email, password, invate_code)
                CL.update_config()
            if need_break:
                break
        return status == CL.REGISTER_SUCCESS

    @staticmethod
    def get_prompt(res):
        prompt_position = res.find("提示信息")
        if prompt_position != -1:
            res = res[prompt_position:prompt_position + 150]
        else:
            res = res[1332:] if len(res) > 1332 else res
        return res

    @staticmethod
    def is_uname_available(uname, default=False):
        sleep(2)
        status = default
        if not (uname and len(uname) > 1):
            log.e("uname %s length less than 1", uname)
            return status
        val_code_times = 0
        while val_code_times < CL.VAL_CODE_RETRY_TIMES:
            validate = CL.get_code_static()
            data = {
                'username': uname.encode('gb2312'),
                "validate": validate,
                "action": "regnameck"
            }
            res = CL.cl_decode(CL.SESSION.post(CL.REGIS_URL, headers=CL.__headers, data=data))
            pat = r"parent.retmsg\('(\d)'\)"
            result = re.search(pat, res)
            msg_index = int(result.group(1)) if result else 3
            status = msg_index == 4
            if msg_index == 5:
                val_code_times = val_code_times + 1
                continue
            break
        log.d("uname = " + uname + ", available = " + str(status))
        return status
