import aiohttp
import asyncio
import numpy as np
from bs4 import BeautifulSoup
import re



class EbayScrapper:
    __base_url ="https://www.ebay.com/sch/i.html?_nkw=<keyword>&_ddo=1&_ipg=100&_pgn=<number>"
    __used_proxies = 0
    def __init__(self, max_coroutines: int = 10, proxies_list: list = None,
                 max_proxies_per_host = 5,
                 refresh_rate: float = 0.5, use_own_ip: bool = True, 
                 shipping_cost: bool = True) -> None:
        self.max_coroutines = max_coroutines
        self.proxies_list = proxies_list
        self.refresh_rate = refresh_rate
        self.max_proxies_per_host = max_proxies_per_host
        if self.proxies_list and use_own_ip:
            self.proxies_list.insert(0, None)
        self.shipping_cost = shipping_cost
    
    @staticmethod
    def ebay_get_product_price(product_element) -> float:
        product_price = product_element.find("span", class_="s-item__price")
        if product_price is not None:
            product_price = str(product_price.text)
            if "to" in product_price:
                prices = product_price.split(" to ")
                prices[0] = float(prices[0].replace(",", "").replace("$", ""))
                prices[1] = float(prices[1].replace(",", "").replace("$", ""))
                return (prices[0] + prices[1]) / 2 
            return float(product_price.replace(",", "").replace("$", ""))
    @staticmethod
    def ebay_get_product_shipping_price(product_element):
        shipping_price = product_element.find('span', class_='s-item__shipping s-item__logisticsCost')
        if shipping_price is not None:
            shipping_cost = re.search(r"\+\$", shipping_price.text)
            if shipping_cost is not None:
                shipping_cost = shipping_price.text[shipping_cost.span()[1]:]
                shipping_cost = shipping_cost.replace(",", "")
                leftover_string = re.search(r"\s", shipping_cost)
                shipping_cost = shipping_cost[:leftover_string.span()[1]]
                return float(shipping_cost)
        return 0.0
    @staticmethod
    def ebay_get_product_url(product_element) -> str:
        product_url = product_element.find("a", class_="s-item__link")
        if product_url is not None:
            return product_url.get("href")

    def choose_proxy(self):
        if self.proxies_list is None or len(self.proxies_list) == 0:
            return None
        if self.__used_proxies == len(self.proxies_list):
            self.__used_proxies = 0
        self.__used_proxies += 1
        return self.proxies_list[self.__used_proxies - 1]
    
    
    def parse_url(self, keyword: str):
        return self.__base_url.replace("<keyword>", keyword)   

    async def __ebay_get_products_generator(self, product_url: str, proxy: str = None):
        connector = None
        if proxy is not None:
            connector = aiohttp.TCPConnector(ssl=False, limit_per_host=self.max_proxies_per_host, limit=self.max_coroutines)
        page = 1
        items_found = True
        items_ammount = 0
        while items_found:
            current_url = product_url.replace("<number>", str(page))
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(current_url)  as response:
                    if response.status == 200:
                        response_text = await response.text()
                        
                        soup = BeautifulSoup(response_text)
                        if page == 1:
                            items_ammount = soup.find("h1", class_="srp-controls__count-heading")
                            items_ammount = soup.find("span", class_="BOLD")
                            items_ammount = items_ammount.text
                            items_ammount = items_ammount.replace(",", "")
                            items_ammount = int(items_ammount)
                        items = soup.find_all('div', class_='s-item__info clearfix')
                        if len(items) == 0 or items_ammount == 0:
                            items_found = False
                        i = 0
                        for item in items:
                            i += 1
                            try:
                                if items_ammount == 0:
                                    break
                                item_price = self.ebay_get_product_price(item)
                                if self.shipping_cost:
                                    shipping_cost = self.ebay_get_product_shipping_price(item)
                                    item_price += shipping_cost
                                if item_price is not None:
                                    item_url = self.ebay_get_product_url(item)
                                    if "https://ebay.com/itm/123456" not in item_url:
                                        item_url = item_url.split("?")[0]
                                        data =  {"item_price": item_price, "item_url": item_url}
                                        items_ammount -= 1
                                        yield data
                            except Exception as e:
                                pass
                page += 1
                await asyncio.sleep(self.refresh_rate)

    async def ebay_get_products_generator(self, product_name, proxy:str = None):
        product_url = self.parse_url(product_name)
        async for product_info in self.__ebay_get_products_generator(product_url, proxy):
            yield product_info