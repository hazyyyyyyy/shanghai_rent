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
    
    def __init__(self, show_browser=False):
        return
    # 初始化浏览器对象，保证小量级爬取不会遇到滑块登录
    # 这里仍然没有使用ip代理池，后期添加功能
    def InitialBrowser(self, show_browser=False):
        # chrome_options 初始化选项
        chrome_options = webdriver.ChromeOptions()
        # 设置浏览器初始 位置x,y & 宽高x,y
        #chrome_options.add_argument(f'--window-position={217},{172}')
        chrome_options.add_argument(f'--window-size={1200},{1000}')
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
    
    def scrape_a_house(self, bro, h):
        '''
        bro: 浏览器对象
        h: 这个房子的WebElement对象
        '''
        this_house_info = {}
        bro.implicitly_wait(3)
        scraper.close_ad(bro)
        
        while True:
            try:
                h.click()
                break
            except Exception as e:
                print('打开房子界面出错:',e)
                scraper.close_ad(bro)
        
        handles = bro.window_handles
        bro.switch_to.window(handles[1])        
        scraper.close_ad(bro)
        
        #房名
        this_name = bro.find_element_by_xpath('/html/body/div[3]/div[1]/div[3]/p').text
        this_house_info['name'] = this_name
        '''
        右侧列表
        '''
        #租金
        this_price = bro.find_element_by_xpath('//div[@id="aside"]/div[1]').text
        this_house_info['price'] = this_price
        
        #tag
        this_tags = []
        tags_elem = bro.find_elements_by_xpath('//div[@id="aside"]/p/i')
        for i in tags_elem:
            this_tags.append(i.text)
        this_house_info['tags'] = this_tags
        
        '''
        下方基本信息列表
        '''
        #基本信息
        this_basic_info = []
        basic_info_elem = bro.find_elements_by_xpath('//div[@id="info"]/ul[1]/li')
        for i in basic_info_elem:
            this_basic_info.append(i.text)
        basic_info_elem1 = bro.find_elements_by_xpath('//div[@id="info"]/ul[2]/li')
        for i in basic_info_elem1:
            this_basic_info.append(i.text)
        this_house_info['basic_info'] = this_basic_info
        
        #配套设施
        this_facilities = []
        # this_facility_availability= []
        fac = bro.find_elements_by_xpath('/html/body/div[3]/div[1]/div[3]/div[3]/div[2]/ul/li')
        for f in fac:
            this_facility_availability = f.get_attribute('class')
            this_facility = f.text
            if 'facility_no' in this_facility_availability:
                pass
            else:
                this_facilities.append(this_facility)
        this_house_info['facility'] = this_facilities
        
        return this_house_info        

    
    def scrape_a_page(self, link):
        bro = self.InitialBrowser(show_browser=True)
        bro.get(link)
        # 进入地铁tab
        dt_tab = bro.find_element_by_xpath('//div[@id="filter"]/ul[1]/li[2]/a')
        dt_tab.click()
        
        # 点击9号线
        line9 = bro.find_element_by_xpath('//div[@id="filter"]/ul[3]/li[13]/a')
        line9.click()       
        
        ## 遍历地铁站
        stations = {}
        stations_elem = bro.find_elements_by_xpath('//div[@id="filter"]/ul[4]/li/a')
        for i in range(1, len(stations_elem)):
            print(i)
            stations_elem = bro.find_elements_by_xpath('//div[@id="filter"]/ul[4]/li/a')
            station = stations_elem[i]
            this_station = station.text
            station.click()
            # for i in range(1,len(stations_elem)): # 第0个是不限地铁站
            #     station = stations_elem[i]
            #     stations.append(station.text)
            #     station.click()
            
            #限定整租
            full = bro.find_element_by_xpath('//div[@id="filter"]/ul[5]/li[3]/a')
            full.click()
            
            #按价格排序
            sorting = bro.find_element_by_xpath('//ul[@id="contentList"]/li[3]/a')
            sorting.click()
            
            #取得房源链接列表
            houses = bro.find_elements_by_xpath('//div[@id="content"]/div[1]/div[1]/div/div/p[1]/a')
            hs = []
            scraper.close_ad(bro)
            
            for i in range(0, len(houses)):
                h = houses[i]
                this_house_info = self.scrape_a_house(bro, h)
                hs.append(this_house_info)
                
                bro.implicitly_wait(5)
                bro.close()
                handles = bro.window_handles
                bro.switch_to.window(handles[0])        
            
            stations[this_station] = hs
        return stations
    
    @staticmethod
    def close_ad(bro):
        #尝试关闭广告
        try:
            ad_button = bro.find_element_by_xpath('/html/body/div[3]/div[3]/div/div[2]/i')
            ad_button.click()
        except Exception as e:
            print(e)
            pass
        return



if __name__ == '__main__':
    pc = scraper()
    stations = pc.scrape_a_page('https://sh.lianjia.com/zufang/')
    
    
    # pc = scraper()
    # bro = pc.InitialBrowser(show_browser=True)
    # bro.get('https://sh.lianjia.com/zufang/')
    # # 进入地铁tab
    # dt_tab = bro.find_element_by_xpath('//div[@id="filter"]/ul[1]/li[2]/a')
    # dt_tab.click()
    
    # # 点击9号线
    # line9 = bro.find_element_by_xpath('//div[@id="filter"]/ul[3]/li[13]/a')
    # line9.click()
    
    # ## 测试第一个地铁站
    # stations = []
    # stations_elem = bro.find_elements_by_xpath('//div[@id="filter"]/ul[4]/li/a')
    # station = stations_elem[1]
    # stations.append(station.text)
    # station.click()
    # # for i in range(1,len(stations_elem)): # 第0个是不限地铁站
    # #     station = stations_elem[i]
    # #     stations.append(station.text)
    # #     station.click()
    
    # #限定整租
    # full = bro.find_element_by_xpath('//div[@id="filter"]/ul[5]/li[3]/a')
    # full.click()
    
    # #按价格排序
    # sorting = bro.find_element_by_xpath('//ul[@id="contentList"]/li[3]/a')
    # sorting.click()
    
    # #取得房源链接列表
    # houses = bro.find_elements_by_xpath('//div[@id="content"]/div[1]/div[1]/div/div/p[1]/a')
    # hs = []
    # scraper.close_ad()
    
    # for i in range(0, len(houses)):        
    #     this_house_info = {}        
    #     h = houses[i]
    #     bro.implicitly_wait(3)
    #     scraper.close_ad()
        
    #     while True:
    #         try:
    #             h.click()
    #             break
    #         except Exception as e:
    #             print('打开房子界面出错:',e)
    #             scraper.close_ad()
        
    #     handles = bro.window_handles
    #     bro.switch_to.window(handles[1])        
    #     scraper.close_ad()
        
    #     #房名
    #     this_name = bro.find_element_by_xpath('/html/body/div[3]/div[1]/div[3]/p').text
    #     this_house_info['name'] = this_name
    #     '''
    #     右侧列表
    #     '''
    #     #租金
    #     this_price = bro.find_element_by_xpath('//div[@id="aside"]/div[1]').text
    #     this_house_info['price'] = this_price
        
    #     #tag
    #     this_tags = []
    #     tags_elem = bro.find_elements_by_xpath('//div[@id="aside"]/p/i')
    #     for i in tags_elem:
    #         this_tags.append(i.text)
    #     this_house_info['tags'] = this_tags
        
    #     '''
    #     下方基本信息列表
    #     '''
    #     #基本信息
    #     this_basic_info = []
    #     basic_info_elem = bro.find_elements_by_xpath('//div[@id="info"]/ul[1]/li')
    #     for i in basic_info_elem:
    #         this_basic_info.append(i.text)
    #     basic_info_elem1 = bro.find_elements_by_xpath('//div[@id="info"]/ul[2]/li')
    #     for i in basic_info_elem1:
    #         this_basic_info.append(i.text)
    #     this_house_info['basic_info'] = this_basic_info
        
    #     #配套设施
    #     this_facilities = []
    #     # this_facility_availability= []
    #     fac = bro.find_elements_by_xpath('/html/body/div[3]/div[1]/div[3]/div[3]/div[2]/ul/li')
    #     for f in fac:
    #         this_facility_availability = f.get_attribute('class')
    #         this_facility = f.text
    #         if 'facility_no' in this_facility_availability:
    #             pass
    #         else:
    #             this_facilities.append(this_facility)
    #     this_house_info['facility'] = this_facilities
        
    #     hs.append(this_house_info)
        
    #     bro.implicitly_wait(5)
    #     bro.close()
    #     handles = bro.window_handles
    #     bro.switch_to.window(handles[0])
        

    
    












