from enum import Enum

class ProxyType(Enum):
    pass

class ProxySwitchAlgo(Enum):
    BRUTE_FORCE = 1

class ProxySwitcher:
    
    __used_proxies = 0
    def __init__(self, proxies_list: list = None, proxy_switch_algo: ProxySwitchAlgo = ProxySwitchAlgo.BRUTE_FORCE) -> None:
        self.proxies_list = proxies_list
        self.proxy_switch_algo = proxy_switch_algo
        self.__proxy_algos_map = {
            ProxySwitchAlgo.BRUTE_FORCE: self.__choose_proxy_brute_force
        }

    @staticmethod
    def proxy_type(proxy_url: str):
        pass

    def __choose_proxy_brute_force(self):
        if self.proxies_list is None or len(self.proxies_list) == 0:
            return None
        if self.__used_proxies == len(self.proxies_list):
            self.__used_proxies = 0
        self.__used_proxies += 1
        return self.proxies_list[self.__used_proxies - 1]
    
    def choose_proxy(self):
        return self.__proxy_algos_map[self.proxy_switch_algo]()