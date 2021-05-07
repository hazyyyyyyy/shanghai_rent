# -*- coding: utf-8 -*-
"""
Created on Fri May  7 18:56:04 2021

@author: Stan
"""

from selenium import webdriver
from selenium.webdriver import ChromeOptions
import time
from selenium.webdriver import ActionChains
import random
import tqdm
import pandas as pd 
import numpy as np
import math
from tqdm import tqdm

class scraper:
    def __init__(self):
        return
    # 初始化浏览器对象，保证小量级爬取不会遇到滑块登录
    # 这里仍然没有使用ip代理池，后期添加功能
    def InitialBrowser(self, show_browser=False):
        # chrome_options 初始化选项
        chrome_options = webdriver.ChromeOptions()
        # 设置浏览器初始 位置x,y & 宽高x,y
        #chrome_options.add_argument(f'--window-position={217},{172}')
        #chrome_options.add_argument(f'--window-size={1200},{1000}')
        # 关闭自动测试状态显示 // 会导致浏览器报：请停用开发者模式
        # window.navigator.webdriver还是返回True,当返回undefined时应该才可行。
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
        # 关闭开发者模式
        chrome_options.add_experimental_option("useAutomationExtension", False)
        # 禁止图片加载
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # chrome_options.add_experimental_option("prefs", prefs)
        # 设置中文
        chrome_options.add_argument('lang=zh_CN.UTF-8')
        # 更换头部
        chrome_options.add_argument('user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"')
    	# 是否隐藏浏览器
        if show_browser==False:
            chrome_options.add_argument('--headless')
    	# 部署项目在linux时，其驱动会要求这个参数
    	# chrome_options.add_argument('--no-sandbox')
        # 创建浏览器对象
        # chrome_options.add_argument("--proxy-server=http://114.103.81.101：8888")
        driver = webdriver.Chrome(options=chrome_options)
        # 设置执行js代码转换模式
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """Object.defineProperty(navigator, 'webdriver', {get: () => undefined})""",
        })
        return driver




if __name__ == '__main__':
    pc = scraper()
    bro = pc.InitialBrowser(show_browser=True)
    bro.get('https://sh.lianjia.com/zufang/')
    # 进入地铁tab
    dt_tab = bro.find_element_by_xpath('//div[@id="filter"]/ul[1]/li[2]/a')
    dt_tab.click()
    # 
    

















