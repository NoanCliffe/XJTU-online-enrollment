from hashlib import md5
import requests
import time
import logging
from bs4 import BeautifulSoup

class XJTULogin:
    
    class LoginError(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    def __init__(self,username:str|int,pswd:str,encrypted=False,debug=False) -> None:
        '''创建登录句柄
        Parameters:
            username:任何用于统一认证的用户名
            pswd:统一认证平台密码，默认情况下为明文
            encrypted:密码是否已加密，加密遵循RSA-PKCS#1 v1.5方式，密钥为https://login.xjtu.edu.cn/cas/jwt/publicKey
            debug:是否打印调试信息
        '''
        self.logger=logging
        self.debug=debug
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        self.webClient=requests.session()
        self.webClient.headers['User-Agent']='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        self.username=str(username)
        self.fingerprint=str(md5(f"{username}{pswd}@XJTULogin".encode()).hexdigest())
        if not encrypted:
            import base64
            try:
                from Crypto.PublicKey import RSA
                from Crypto.Cipher import PKCS1_v1_5
            except ModuleNotFoundError as e:
                raise Exception('Crypto module not found, please run "pip install pycryptodome" or encrypt your password manually and set encrypted=True')
            try:
                res=self.webClient.get('https://login.xjtu.edu.cn/cas/jwt/publicKey')
                if res.status_code != 200:
                    self.logger.warning('Failed to fetch public key for encryption, status code: %s, using cached public key...', res.status_code)
                    pub_key=RSA.import_key('-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2u2v/bjSIVsaxCBBxkjWf7LpmsjuhFJUJE7MYTn9hBcDXlK4smgtNoMqmGz4ztg5t1h+h0fqrJT3WkdoLV/FKC8OwElTe+p+YLqA6/PgmGtsffcQmAW0eye5NygiWM+B0tO69ML6jNLpAWAvXwod5kr/k7qsM1DGTux+e7bjdFz/IA8vOZx3IlGHnX+RE/uBJUwPXHnLPw5pQSwkWwfpPwxMrgzwik6htqRHF2c7Z+pJToXbrIJWD5nmRiU6jzgu8ncLqbMb3WNOKSodcEnlUpTH/ApH56IOJHWpq3mxJL9DaUaWzjziR93wjlyvR1K4VM7TLqD35CVZQaoE5FWgZwIDAQAB\n-----END PUBLIC KEY-----')
                else:
                    pub_key=RSA.import_key(res.text)
            except requests.RequestException as e:
                self.logger.warning('Failed to fetch public key for encryption: %s, using cached public key...', e)
                pub_key=RSA.import_key('-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2u2v/bjSIVsaxCBBxkjWf7LpmsjuhFJUJE7MYTn9hBcDXlK4smgtNoMqmGz4ztg5t1h+h0fqrJT3WkdoLV/FKC8OwElTe+p+YLqA6/PgmGtsffcQmAW0eye5NygiWM+B0tO69ML6jNLpAWAvXwod5kr/k7qsM1DGTux+e7bjdFz/IA8vOZx3IlGHnX+RE/uBJUwPXHnLPw5pQSwkWwfpPwxMrgzwik6htqRHF2c7Z+pJToXbrIJWD5nmRiU6jzgu8ncLqbMb3WNOKSodcEnlUpTH/ApH56IOJHWpq3mxJL9DaUaWzjziR93wjlyvR1K4VM7TLqD35CVZQaoE5FWgZwIDAQAB\n-----END PUBLIC KEY-----')
            handle = PKCS1_v1_5.new(pub_key)
            pwen = handle.encrypt(pswd.encode())
            self.pswdEncryptd = '__RSA__' + base64.b64encode(pwen).decode()
        else:
            self.pswdEncryptd=pswd

    def __check_mfa_phone(self,code):
        self.logger.debug('Checking MFA phone from code: %s', code)
        parmas={'state':code}
        res=self.webClient.get('https://login.xjtu.edu.cn/cas/mfa/initByType/securephone',params=parmas)
        self.logger.debug('MFA phone check response: %s', res.text)
        if res.status_code!=200:
            self.logger.debug('MFA phone check http error, response code: %s', res.status_code)
            raise self.LoginError('MFA phone check failed, code {}'.format(res.status_code))
        if res.json()['code']!=0:
            self.logger.debug('MFA phone check api error, response raw: %s', res.text)
            raise self.LoginError('MFA phone check failed, {}'.format(res.json()['data']))
        return res.json()['data']

    def __send_mfa_sms(self,gid):
        self.logger.debug('Sending MFA SMS to gid: %s', gid)
        res=self.webClient.post('https://login.xjtu.edu.cn/attest/api/guard/securephone/send',json={'gid':gid})
        self.logger.debug('MFA SMS send response: %s', res.text)
        if res.status_code!=200:
            self.logger.debug('MFA SMS send http error, response code: %s', res.status_code)
            raise self.LoginError('MFA SMS send failed, code {}'.format(res.status_code))
        if res.json()['code']!=0:
            self.logger.debug('MFA SMS send api error, response raw: %s', res.text)
            raise self.LoginError('MFA SMS send failed, {}'.format(res.json()['message']))
        
    def __verfy_mfa_sms(self,sms_code,gid):
        if not sms_code or sms_code=='':
            self.logger.debug('No SMS code provided, will resend SMS.')
            print('检测到空验证码，等待重新发送短信验证码...')
            for i in range(60,0,-1):
                print(f'\r重新发送倒计时: {i} 秒',end='\r',flush=True)
                time.sleep(1)
            print('\n')
            return False,False
        self.logger.debug('Verifying MFA SMS with id: %s and sms_code: %s', gid, sms_code)
        res=self.webClient.post('https://login.xjtu.edu.cn/attest/api/guard/securephone/valid',json={'code':sms_code,'gid':gid})
        self.logger.debug('MFA SMS verify response: %s', res.text)
        if res.status_code!=200:
            self.logger.debug('MFA SMS verify http error, response code: %s', res.status_code)
            raise self.LoginError('MFA SMS verify failed, code {}'.format(res.status_code))
        if res.json()['code']!=0:
            self.logger.debug('MFA SMS verify api error, response raw: %s', res.text)
            raise self.LoginError('MFA SMS verify failed, {}'.format(res.json()['data']['message']))
        if res.json()['data']['status'] == 3:
            self.logger.debug('MFA SMS verify failed, invalid SMS code.')
            print('验证码错误，请重新输入。')
            return True,True
        elif res.json()['data']['status'] == 2:
            self.logger.debug('MFA SMS verify successed.')
            print('验证成功')
            return True,False
        else:
            self.logger.debug('MFA SMS verify failed, unknown status: %s', res.json()['data']['status'])
            raise self.LoginError('MFA SMS verify failed, unknown status {}'.format(res.json()['data']['status']))

    def login(self,orgURL,identity=None,consistent_fingerprint=None):
        '''登录
        Parameters:
            orgURL:原平台的登陆地址，类似于"https://login.xjtu.edu.cn/cas/login?service=..."(新版原生)或"http://org.xjtu.edu.cn/openplatform/oauth/authorize?appId=..."(旧版org兼容跳转)
            identity:该统一认证账户有多个身份情况下，指定身份(学工号)***暂未实现***
            consistent_fingerprint:如果需要保持一致的浏览器追踪指纹，请提供一个一致的指纹字符串(小写32位十六进制字符串)，否则会根据学号密码自动生成一个新的指纹
        Returns:
            str:为统一认证平台返回的重定向url，请根据平台的登录逻辑处理
        '''
        if identity is not None:
            self.logger.error('Identity parameter is not implemented yet, if you have multiple identities, please report it to the developer to help implement this feature.')
            raise NotImplementedError('Identity parameter is not implemented yet')
        if orgURL.startswith('http://'):
            orgURL = orgURL.replace('http://','https://',1)
        if not (orgURL.startswith('https://login.xjtu.edu.cn') or orgURL.startswith('https://org.xjtu.edu.cn')):
            self.logger.error('Invalid orgURL, must start with "https://login.xjtu.edu.cn" or "https://org.xjtu.edu.cn",see Parameters for details.')
            raise ValueError('Invalid orgURL')
        res=self.webClient.get(orgURL)
        call_back_url=res.url
        self.logger.debug('login callback URL: %s', call_back_url)
        page = BeautifulSoup(res.text, 'html.parser')
        forms=page.find_all("form")
        login_data={}
        for form in forms:
            if form.get('id')!='fm1':
                continue
            for tag in form.find_all('input'):
                login_data[tag.get('name')]=tag.get('value',default='')
                if tag.get('v-model')=='passwordLoginUsername':
                    login_data[tag.get('name')]=self.username
                elif tag.get('v-model')=='passwordLoginPassword':
                    login_data[tag.get('name')]=self.pswdEncryptd
            login_data['fpVisitorId']=consistent_fingerprint or self.fingerprint
            login_data.pop('rememberMe', None) #不删报错
        self.logger.debug('login data:{}'.format(login_data))
        self.logger.debug('Checking MFA status...')
        res=self.webClient.post('https://login.xjtu.edu.cn/cas/mfa/detect',data={'username':self.username,'password':self.pswdEncryptd,'fpVisitorId':login_data['fpVisitorId']})
        self.logger.debug('MFA status response:{}'.format(res.text))
        code=res.json()['data']['state']
        self.logger.debug('MFA status code:{}'.format(code))
        mfa_successed=not res.json()['data']['need']
        while not mfa_successed:
            if not res.json()['data']['mfaTypeSecurePhone']:
                raise NotImplementedError('MFA type not supported yet, you must enable phone sms MFA. If you have enabled phone sms MFA and still see this error, please report it to the developer.')
            #raise self.LoginError('MFA is required, please report it to the developer.')
            print('!!!MFA is required, please complete MFA verification first.')
            self.logger.debug('getting MFA state sms code...')
            phone_info=self.__check_mfa_phone(code)
            phone_number=phone_info['securePhone']
            print(f'SMS code will be sent to your registered phone number: {phone_number}')
            self.__send_mfa_sms(phone_info['gid'])
            sms_code_still_valid=True
            while sms_code_still_valid:
                sms_code = input('输入收到的短信验证码，留空重新获取: ').strip()
                mfa_successed,sms_code_still_valid = self.__verfy_mfa_sms(code, sms_code, phone_info['gid'])


        login_data['mfaState']=code
        res=self.webClient.post(call_back_url,data=login_data,allow_redirects=False)
        if res.status_code==401:
            raise self.LoginError('Login failed, please check your username and password')
        elif res.status_code==200:
            raise self.LoginError('Unknown error, please report it to the developer.')
        while res.status_code==302 and ('org.xjtu.edu.cn' in res.headers['Location'] or 'login.xjtu.edu.cn' in res.headers['Location']):
            res=self.webClient.get(res.headers['Location'],allow_redirects=False)
        return res.headers.get('Location', '')

    def login_old_org(self,orgURL,identity=None):
        '''登录旧版org平台(鬼知道能不能用，鬼知道有没有用)
        Parameters:
            orgURL:原平台的登陆地址
            identity:该统一认证账户有多个身份情况下，指定身份(学工号)
        Returns:
            str:为统一认证平台返回的重定向url，请根据平台的登录逻辑处理
        '''
        res = self.webClient.get(orgURL)
        logindata={"loginType":1,"username":self.username,"pwd":self.pswdEncryptd,"jcaptchaCode":""}
        res=self.webClient.post('https://org.xjtu.edu.cn/openplatform/g/admin/login',json=logindata)
        self.logger.debug('Step 1:login','request',username=self.username)
        if res.status_code!=200:
            self.logger.debug('Step 1:login','http error',response_code=res.status_code)
            raise self.LoginError('login failed, code {}'.format(res.status_code))
        if res.json()['code']!=0:
            self.logger.debug('Step 1:login','api error',response_raw=res.text)
            raise self.LoginError('login failed, {}'.format(res.json()['message']))
        self.orgToken = res.json()['data']['tokenKey']
        self.orgMemberID = res.json()['data']['orgInfo']['memberId']
        self.orgState = res.json()['data']['state']
        self.logger.debug('Step 1:login','response',orgToken=self.orgToken,orgMemberID=self.orgMemberID,state=self.orgState,raw=res.json())
        self.webClient.cookies['memberId']=str(self.orgMemberID)
        self.webClient.cookies['open_Platform_User']=self.orgToken
        self.webClient.cookies['state']=self.orgState
        res = self.webClient.post('https://org.xjtu.edu.cn/openplatform/g/admin/getUserIdentity',data={'memberId':self.orgMemberID})
        if res.status_code!=200:
            self.logger.debug('Step 2: get user id','http error',response_code=res.status_code)
            raise self.LoginError('failed to get user Identity, code{}'.format(res.status_code))
        elif res.json()['code']!=0:
            self.logger.debug('Step 2: get user id','api error',response_raw=res.text)
            raise self.LoginError('failed to get user Identity, {}'.format(res.json()['message']))
        identitys=res.json()['data']
        self.logger.debug('Step 2: get user id','response',identitys=identitys,response_raw=res.json())
        if len(identitys)>1:
            
            ChosenIdentity=None
            if not identity:
                identity=self.username
            self.logger.debug('Step 3: choose identity','requests',identitys=len(identitys),given_identity=identity)
            for id in identitys:
                if id['personNo']==str(identity):
                    ChosenIdentity=id
                    break
            if not ChosenIdentity:
                self.logger.debug('Step 3: choose identity','error',identitys=identitys,given_identity=identity)
                raise self.LoginError('no match indentity found. Please use student ID to login or specify identity')
        else:
            ChosenIdentity=identitys[0]
            self.logger.debug('Step 3: choose identity','response',ChosenIdentity=ChosenIdentity)
        redirparam={"userType":ChosenIdentity['userType'],'personNo':ChosenIdentity['personNo'],"_":str(int(time.time()*1000))}
        res = self.webClient.get('https://org.xjtu.edu.cn/openplatform/oauth/auth/getRedirectUrl',params=redirparam)
        if res.status_code!=200:
            self.logger.debug('Step 4: get redirect URL','http error',response_code=res.status_code)
            raise self.LoginError('Failed to get redirect URL, code {}'.format(res.status_code))
        if res.json()['code']!=0:
            self.logger.debug('Step 4: get redirect URL','api error',response_raw=res.text)
            raise self.LoginError('Failed to get redirect URL, {}'.format(res.json()['message']))
        redirURL=res.json()['data']
        self.logger.debug('Step 4: get redirect URL','response',redirect_URL=redirURL,response_raw=res.json())
        return redirURL