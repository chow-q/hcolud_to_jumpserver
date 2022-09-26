# coding: utf-8

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkecs.v2 import *
import json,re,requests


#获取jsmp运维频台的token
def get_token(jms_url, username, password):
  url = jms_url + '/api/v1/authentication/auth/'
  query_args = {
    "username": username,
    "password": password
  }
  response = requests.post(url, data=query_args)
  return json.loads(response.text)['token']

#获取token的UUID
def get_uuid(jms_url, token):
  url = jms_url + '/api/v1/users/users/'
  headers = {
    "Authorization": 'Bearer ' + token,
    'X-JMS-ORG': '00******02'
  }
  response = requests.get(url, headers=headers)
  return (json.loads(response.text))


#创建主机资产
def add_host(jms_url,token,name,ip):
  url = jms_url + '/api/v1/assets/assets/'
  headers = {
    "Authorization": 'Bearer ' + token,
    "X-JMS-ORG": "0000000002",
    "Content-Type": "application/json",
    "accept": "application/json"
  }
  post_dict = {
    "hostname": name,
    "ip": ip,
    "platform": "Linux",
    "protocol": "ssh",
    "port":22,
    "is_active": "true",
    "admin_user": "58***********ff",
    "nodes": ["7***********b"]
  }

  response = requests.post(url,headers=headers,data=json.dumps(post_dict))
  print(response.text)


#jump运维平台列出化为云主机资产，通过node 参数决定显示那个分组
def list_host(jms_url, token,node):

  url = jms_url + '/api/v1/assets/assets/'
  headers = {
    "Authorization": 'Bearer ' + token,
    "X-JMS-ORG": "00002",
    "Content-Type": "application/json",
    "accept": "application/json"
  }
  #请求携带华为云id分组
  post_dict = {
    "node": node
  }
  response = requests.get(url, headers=headers,params=post_dict)
  response_list = response.json()

  #获取jusmp 的资产的id，ip
  for host in response_list:
    id = host['id']
    ip = host['ip']
    host_dict[ip] = id


#删除jump华为分组的主机
def del_host(jms_url,token,host_uuid):
  url = jms_url + '/api/v1/assets/assets/' + host_uuid + '/'

  headers = {
    "Authorization": 'Bearer ' + token,
    "X-JMS-ORG": "00000002",
    "Content-Type": "application/json",
    "accept": "application/json"
  }
  response = requests.delete(url, headers=headers)
  print(response.text)


if __name__ == "__main__":

  # 获取华为云登录信息
  ak = ""
  sk = ""

  # jsmp平台登录信息
  jms_url = 'http://1.1.1.1'
  username = ''
  password = ''

  #node 参数为jump运维平台华为云分组的id，只过滤出华为云的分组的主机列表
  node = "7*************b"


  #华为云请求sdk
  credentials = BasicCredentials(ak, sk) \

  client = EcsClient.new_builder() \
      .with_credentials(credentials) \
      .with_region(EcsRegion.value_of("cn-south-1")) \
      .build()

  try:
        request = NovaListServersDetailsRequest()
        response = client.nova_list_servers_details(request)
#        print(response)
  except exceptions.ClientRequestException as e:
        print(e.status_code)
        print(e.request_id)
        print(e.error_code)
        print(e.error_msg)

  #将得到华为云资产清单的response 转成字符串，再转换成 json格式
  response_str = str(response)
  response_josn = json.loads(response_str)

  #登录jsmp平台
  token = get_token(jms_url, username, password)

  #获取用户信息
  # id = get_uuid(jms_url, token)

  #获取jusmp 资产清单信息
  host_dict = {}
  list_host(jms_url,token,node)

#  print(host_dict)
#同步华为云主机到jsmp。
#原则：以华为云为准，jsmp上多的删除，少的添加。

  #遍历华为云服务器列表写入一个字典（需要华为云vpc的id才能获取到IP）
  hcolud_dict = {}
  for host in response_josn['servers']:
      name = host['name']
      ip = host["addresses"]["7****************a"][0]["addr"]
      #得到以ip为key，服务器名称为value的字典
      hcolud_dict[ip] = name

  #获取jsmp比华为云多的主机
  for hc_host in hcolud_dict:
    if hc_host in host_dict:
      #对比主机，获取jsmp比华为云多的主机
      del host_dict[hc_host]
    else:
      #华为云主机不在jsmp,则添加主机到jsmp
      add_host(jms_url, token,hcolud_dict[hc_host],hc_host)

  #删除，jump有，而华为云没有的服务主机
  for host_uuid in host_dict:
    del_host(jms_url,token,host_dict[host_uuid])
