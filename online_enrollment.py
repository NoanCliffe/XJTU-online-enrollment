import os
import random
from PIL import Image
import io
import base64

from xjtulogin import XJTULogin
import requests
from urllib.parse import urlparse, parse_qs

def get_aosp_builds(ver):
    if ver == 13:
        return random.choice(["TP1A", "TQ2A", "TKQ1","TKP1","TKP2"])
    elif ver == 14:
        return random.choice(["UP1A", "UQ1A","UP1B", "UQ1A","UK2A", "UK1B"])
    elif ver == 15:
        bstr=''
        bstr+=random.choice(['A','B','C'])
        bstr+=random.choice(['P','Q','K'])
        bstr+=random.choice(['1','2','3'])
        bstr+=random.choice(['A','B'])
        return bstr
chrome_versions = [
    "121.0.6167.139",
    "121.0.6167.160",
    "121.0.6167.184",
    "121.0.6167.85",
    "122.0.6261.111",
    "122.0.6261.128",
    "122.0.6261.57",
    "122.0.6261.69",
    "122.0.6261.94",
    "123.0.6312.105",
    "123.0.6312.122",
    "123.0.6312.58",
    "123.0.6312.86",
    "124.0.6367.118",
    "124.0.6367.155",
    "124.0.6367.201",
    "124.0.6367.207",
    "124.0.6367.60",
    "124.0.6367.78",
    "124.0.6367.91",
    "125.0.6422.112",
    "125.0.6422.141",
    "125.0.6422.60",
    "125.0.6422.76",
    "126.0.6478.114",
    "126.0.6478.126",
    "126.0.6478.182",
    "126.0.6478.55",
    "126.0.6478.61",
    "127.0.6533.119",
    "127.0.6533.72",
    "127.0.6533.88",
    "127.0.6533.99",
    "128.0.6613.113",
    "128.0.6613.119",
    "128.0.6613.137",
    "128.0.6613.84",
    "129.0.6668.100",
    "129.0.6668.58",
    "129.0.6668.70",
    "129.0.6668.89",
    "130.0.6723.116",
    "130.0.6723.58",
    "130.0.6723.69",
    "130.0.6723.91",
    "131.0.6778.108",
    "131.0.6778.139",
    "131.0.6778.204",
    "131.0.6778.264",
    "131.0.6778.69",
    "131.0.6778.85",
    "132.0.6834.110",
    "132.0.6834.159",
    "132.0.6834.83",
    "133.0.6943.126",
    "133.0.6943.141",
    "133.0.6943.53",
    "133.0.6943.98",
    "134.0.6998.117",
    "134.0.6998.165",
    "134.0.6998.35",
    "134.0.6998.88",
    "135.0.7049.114",
    "135.0.7049.52",
    "135.0.7049.84",
    "135.0.7049.95",
    "136.0.7103.113",
    "136.0.7103.59",
    "136.0.7103.92",
    "137.0.7151.103",
    "137.0.7151.119",
    "137.0.7151.55",
    "137.0.7151.68",
    "138.0.7204.100",
    "138.0.7204.157",
    "138.0.7204.168",
    "138.0.7204.183",
    "138.0.7204.49",
    "138.0.7204.92",
    "139.0.7258.127",
    "139.0.7258.138",
    "139.0.7258.154",
    "139.0.7258.66",
    "140.0.7339.127",
    "140.0.7339.185",
    "140.0.7339.207",
    "140.0.7339.80",
    "141.0.7390.107",
    "141.0.7390.122",
    "141.0.7390.54",
    "141.0.7390.65",
    "141.0.7390.76",
    "142.0.7444.134",
    "142.0.7444.162",
    "142.0.7444.175",
    "142.0.7444.59",
    "143.0.7499.109",
    "143.0.7499.146",
    "143.0.7499.169",
    "143.0.7499.192",
    "143.0.7499.40",
    "144.0.7559.109",
    "144.0.7559.132",
    "144.0.7559.59",
    "144.0.7559.96",
    "145.0.7632.109",
    "145.0.7632.116",
    "145.0.7632.45",
    "145.0.7632.67",
    "145.0.7632.75"
]
hello_entrance = "https://org.xjtu.edu.cn/openplatform/oauth/authorize?responseType=code&scope=user_info&appId=755&state=1234&redirectUri=http%3A%2F%2Fhello.xjtu.edu.cn%2Fyingxin%2Flogin%2Fxjtu%2Foauth%2Fapp"

Android_version=random.randint(13, 15)

model_list=['2211133C','2304FPN6DC','23054RA19C','24101PNB7C','2509FPN0BC','25069PTEBG','25098PN5AC','25113PN0EG','I2508','V2546A','V2538','V2511','V2514','V2516A','PMC110','CPH2801','CPH2789','CPH2813','CPH2825','CPH2791','CPH2763','CPH2757']
sysBuild={13:[]}
address_list=['西安交通大学(创新港校区)','涵英楼','西安交通大学创新港校区足球场','西安交通大学空天与动力研究院','西安交通大学创新港校区学生宿舍惠园','创新港-西安交通大学自动化科学与工程研究分院']

client=requests.session()
client.headers['X-Requested-With']='com.supwisdom.xjtu'

client.headers['systemType']='yingxin_student_app'
client.headers['User-Agent']='Mozilla/5.0 (Linux; Android {}; {} Build/{}.{:0>2}{:0>2}{:0>2}.{:0>3}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{} Mobile Safari/537.36 SuperApp'.format(Android_version, random.choice(model_list), get_aosp_builds(Android_version), random.randint(24,25), random.randint(1, 12), random.randint(1, 28), random.randint(0, 99),random.choice(chrome_versions))
latitude='{:.6f}'.format(random.uniform(34.25, 34.26))
longitude='{:.6f}'.format(random.uniform(108.65, 108.67))
try:
    netid=input("输入你的NetID:")
    pswd=input("输入你的密码:")
    login_handle = XJTULogin(netid, pswd)
    redirect_url=login_handle.login(hello_entrance)
except XJTULogin.LoginError as e:
    print("登录失败:", str(e))
    input("按回车键退出...")
    exit(1)
except Exception as e:
    print("发生未知错误:", str(e))
    input("按回车键退出...")
    exit(1)

print("登录成功，重定向URL:", redirect_url)
final_response = client.get(redirect_url, allow_redirects=False)
if final_response.status_code == 302:
    final_url=final_response.headers['Location']
    parsed_url = urlparse(final_url)
    query_params = parse_qs(parsed_url.query)
    token=query_params.get('info', [None])[0]
    if not token:
        print("重定向URL中未找到token参数")
        input("按回车键退出...")
        exit(1)
    print("重定向成功，用户身份key:", token[:15]+"...")
    img_path=None
    image_data=None
    while not img_path:
        img_path=input("输入你的人脸照片路径或直接将照片文件拖放进来，然后按回车键继续:")
        if not os.path.exists(img_path):
            print("文件路径不存在，请重新输入。")
            img_path=None
        elif not os.path.isfile(img_path):
            print("输入的路径不是一个文件，请重新输入。")
            img_path=None
        elif img_path and os.path.isfile(img_path):
            try:
                img = Image.open(img_path)
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                encoded_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
                image_data = f"data:image/png;base64,{encoded_data}"
            except Exception as e:
                print("无法打开或处理图片文件，请确保文件是有效的图片格式。错误详情:", str(e))
                print("请重新输入图片路径。")
                img_path=None
    client.headers['access_token']=token
    req_headers = {
        'Referer':'http://hello.xjtu.edu.cn/yingxin-student/photo',
        'Origin':'http://hello.xjtu.edu.cn'
    }
    payload={
        'flowId':2223,
        'imageFile':image_data,
        "latitude": latitude,
        "longitude": longitude,
        "address": random.choice(address_list),
        'synAccessSource':'h5'
    }
    response=client.post("http://hello.xjtu.edu.cn/yingxin/checkIn/saveOrUpdate",json=payload,headers=req_headers)
    print("签到响应:", response.text)
    input("按回车键退出...")
