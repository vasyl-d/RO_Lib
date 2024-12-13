
''' async lib '''
import urllib.parse
import math
import urllib
import asyncio
import aiohttp
import re

RO_PATH = "https://api.remonline.app/"

Tread_limit  = 25
Timeout_sec=aiohttp.ClientTimeout(total=1000)
Api_page_size = 50
# 

class POST_exception(Exception):
    pass

class PUT_exception(Exception):
    pass

class GET_exception(Exception):
    pass

def process_name(name:str):
    return re.sub("(\s+|\t+|\n+)", " ", name.strip())

class RO():
    """only with asyncio"""
    def __init__(self, API_KEY):
        self.API_KEY = API_KEY 
        self.connector = aiohttp.TCPConnector(limit_per_host=Tread_limit)
        self.session = None
        self.TOKEN = None

    async def __aenter__(self):
        self.loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(connector=self.connector, loop=self.loop, timeout=Timeout_sec)
        self.TOKEN = await self.get_token()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    def __repr__(self) -> str:
        return self.TOKEN
    
    async def get_url(self, url):
        async with self.session.get(url) as response:
            data = await response.json()
            if not data.get("success"):
                if data:
                    raise GET_exception(data.get("message"))
                else:
                    response.raise_for_status()
            return data
            
    async def post_url(self, resource, obj = {}):
        '''dont forget to stringify custom_fields json'''
        url = f"{RO_PATH}{resource}?token={self.TOKEN}"
        # payload = json.dumps(obj)
        payload = obj
        headers = {
                "accept": "application/json",
                "content-type": "application/json"
            }
        async with self.session.post(url, json=payload, headers=headers) as response:
            data = await response.json()
            if not data.get("success"):
                if data:
                    raise GET_exception(data.get("message"))
                else:
                    response.raise_for_status()
            return data
            
    async def put_url(self, resource, obj = {}):
        '''dont forget to stringify custom_fields json'''
        url = f"{RO_PATH}{resource}?token={self.TOKEN}"
        # payload = json.dumps(obj)
        payload = obj
        headers = {
                "accept": "application/json",
                "content-type": "application/json"
            }

        async with self.session.put(url, headers=headers, json=payload) as response:
            data = await response.json()
            if not data.get("success"):
                if data:
                    raise GET_exception(data.get("message"))
                else:
                    response.raise_for_status()
            return data
            
    async def get_token(self):
        url = f"{RO_PATH}token/new?api_key={self.API_KEY}"
        data = await self.get_url(url)
        return data.get('token')
      
    async def make_full_get_request(self, url):
        '''for async return value'''
        url = f"{url}&page={1}"
        data = await self.get_url(url)
        count = int(data.get('count', 0))
        retData = data.get("data")
        totalpages = math.ceil(count/Api_page_size) + 1 
        tasks = (asyncio.create_task(self.get_url(f"{url}&page={i}")) for i in range(2, totalpages))
        responses = await asyncio.gather(*tasks, return_exceptions=True)       
        # responses = await asyncio.as_completed(tasks,timeout=Timeout_sec)       
        for el in responses:
            if type(el) in {dict}:
                retData.extend(el.get("data"))
        return retData

    async def get_client(self, name:str="", phone:str=""):
        '''search client by name and phone numbers, return id of first searched'''
        phone = "&phones=".join(phone.split(','))
        name = f"&names[]={name}" if name else ""
        url = f"{RO_PATH}clients/?token={self.TOKEN}{name}&phones[]={phone}"
        try:
            data = await self.get_url(url)
            client_list = data.get("data")
            return client_list[0].get('id') if client_list else None
        except Exception as error:
            raise error
    
    async def get_emploees(self):
        '''return dict or name:id of emplyees'''
        url = f"{RO_PATH}employees/?token={self.TOKEN}"
        try:
            data = await self.make_full_get_request(url)
            rows:list = data.get('data')
            res = dict()
            for row in rows:
                s = f"{row.get('last_name')} {row.get('first_name')}"
                res[s] = row.get('id')
            return res
        except Exception as error:
            print(error)
     
    async def get_orders(self, order_filter:dict={}):
        '''return orders dict using filter'''
        filter_str = ''
        for key, val in order_filter.items():
            filter_str += f"&{key}={urllib.parse.quote_plus(','.join(val),  safe='', encoding=None, errors=None)}" if type(val) == list else  f"&{key}={urllib.parse.quote_plus(val)}"
        url = f"{RO_PATH}order/?token={self.TOKEN}{filter_str}"
        Res = await self.make_full_get_request(url)
        return Res
    
    async def get_clients(self, clients_filter:dict={}):
        '''return orders dict using filter'''
        filter_str = ''
        for key, val in clients_filter.items():
            filter_str += f"&{key}={urllib.parse.quote_plus(','.join(val),  safe='', encoding=None, errors=None)}" if type(val) == list else  f"&{key}={urllib.parse.quote_plus(val)}"
        url = f"{RO_PATH}clients/?token={self.TOKEN}{filter_str}"
        Res = await self.make_full_get_request(url)
        return Res

        
    async def make_full_post_request(self, resource, obj_list):
        '''for async return value'''
        retData = []
        try:
            count = len(obj_list)
            if count >= 1:
                tasks = (asyncio.create_task(self.post_url(resource, el)) for el in obj_list)
                responses = await asyncio.gather(*tasks, return_exceptions=True)       
                # responses = await asyncio.as_completed(tasks,timeout=Timeout_sec)       
                for el in responses:
                    if type(el) in {dict}:
                        retData.extend(el.get("data"))
                    else:
                        retData.append(str(el))
                return retData
        except Exception as error:
            print(error)
        return retData
        
    async def make_full_put_clients(self, obj_list):
        '''for thread return value'''
        retData = []
        try:
            count = len(obj_list)
            if count >= 1:
                tasks = (asyncio.create_task(self.put_url('clients', el)) for el in obj_list)
                responses = await asyncio.gather(*tasks, return_exceptions=True)       
                # responses = await asyncio.as_completed(tasks,timeout=Timeout_sec)       
                for el in responses:
                    if type(el) in {dict}:
                        retData.extend(el.get("data"))
                return retData
        except Exception as error:
            print(error)
        return retData