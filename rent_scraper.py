# -*- coding: utf-8 -*-
"""
Created on Fri May  7 18:56:04 2021

@author: Stan
"""

from selenium import webdriver
from selenium.webdriver import ChromeOptions
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
import random
import tqdm
import pandas as pd 
import numpy as np
import math
from tqdm import tqdm
import pickle

class scraper:
    
    def __init__(self):
        return
    # 初始化浏览器对象，保证小量级爬取不会遇到滑块登录
    # 这里仍然没有使用ip代理池，后期添加功能
    def InitialBrowser(self, show_browser=False):
        # chrome_options 初始化选项
        chrome_options = webdriver.ChromeOptions()
        # 设置浏览器初始 位置x,y & 宽高x,y
        chrome_options.add_argument(f'--window-position={-6},{0}')
        chrome_options.add_argument(f'--window-size={1980},{1080}')
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
        driver.maximize_window()
        return driver
    
    def scrape_a_house(self, bro, h):
        '''
        bro: 浏览器对象
        h: 这个房子的WebElement对象
        '''
        this_house_info = {}
        this_house_info['link'] = bro.current_url
        bro.implicitly_wait(3)
        scraper.close_ad(bro)
        
        while True:
            try:
                h.click()
                handles = bro.window_handles
                bro.switch_to.window(handles[1])        
                scraper.close_ad(bro)
                break
            except Exception as e:
                print('打开房子界面出错，尝试关闭广告...\n',e)
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
        this_house_info['facilities'] = this_facilities
        
        return this_house_info        

    
    def scrape_a_line(self, bro):
        
        ## 遍历地铁站
        stations = {}
        stations_elem = bro.find_elements_by_xpath('//div[@id="filter"]/ul[4]/li/a')
        for i in tqdm(range(1, len(stations_elem))):
            stations_elem = bro.find_elements_by_xpath('//div[@id="filter"]/ul[4]/li/a') #为防止StaleElementError
            station = stations_elem[i]
            this_station = station.text            
            print(this_station)
            station.click()
                        
            #取得房源链接列表
            houses = bro.find_elements_by_xpath('//div[@id="content"]/div[1]/div[1]/div/div/p[1]/a')
            hs = []
            scraper.close_ad(bro)
            
            for i in range(0, len(houses)):
                h = houses[i]
                this_house_info = self.scrape_a_house(bro, h)
                hs.append(this_house_info)
                
                bro.implicitly_wait(3)
                bro.close()
                handles = bro.window_handles
                bro.switch_to.window(handles[0])
            
            stations[this_station] = hs
        return stations
    
    def scrape_a_page(self, link, show_browser=True):
        bro = self.InitialBrowser(show_browser=show_browser)
        bro.get(link)
        scraper.close_ad(bro)
        
        #限定整租
        full = bro.find_element_by_xpath('//div[@id="filter"]/ul[5]/li[3]/a')
        full.click()
        
        #按价格排序
        sorting = bro.find_element_by_xpath('//ul[@id="contentList"]/li[3]/a')
        sorting.click()
        
        # 进入地铁tab
        dt_tab = bro.find_element_by_xpath('//div[@id="filter"]/ul[1]/li[2]/a')
        dt_tab.click()
        
        # 地铁站
        lines = {}
        lines_elem = bro.find_elements_by_xpath('//div[@id="filter"]/ul[3]/li/a')
        for i in range(1, len(lines_elem)): #第0个是不限地铁站
            lines_elem = bro.find_elements_by_xpath('//div[@id="filter"]/ul[3]/li/a') # 为防止StaleElementError
            this_line = lines_elem[i]
            this_line_name = this_line.text
            print('开始爬取地铁线路：', this_line_name)
            this_line.click()
            this_line_info = self.scrape_a_line(bro)
            lines[this_line_name] = this_line_info
            print('完成地铁线路：', this_line_name, '的爬取，执行存储pickle')
            pickle.dump(this_line_info, open(this_line_name+'.p', 'wb'))
            print('完成pickle存储')
            
        pickle.dump(lines, open('lines.p', 'wb'))
        return lines
    
    @staticmethod
    def close_ad(bro):
        #尝试关闭广告
        try:
            ad_button = bro.find_element_by_xpath('/html/body/div[3]/div[3]/div/div[2]/i')
            ad_button.click()
        except Exception as e:
            #print(e)
            pass
        return


class beike(scraper):
    
    '''
    重写父类爬房子方法
    '''
    def scrape_a_house(self, bro, h):
        '''
        bro: 浏览器对象
        h: 这个房子的WebElement对象
        '''
        this_house_info = {}
        this_house_info['link'] = bro.current_url
        bro.implicitly_wait(3)
        scraper.close_ad(bro)
        
        #如果两次次关闭广告失败，可能是被中介信息挡住了
        while True:
            try:
                h.click()
                handles = bro.window_handles
                bro.switch_to.window(handles[1])        
                scraper.close_ad(bro)
                break
            except Exception as e:
                print('打开房子界面出错，尝试下滚页面并关闭广告...\n',e)
                #ActionChains(bro).move_to_element(h).perform()
                #bro.execute_script("return arguments[0].scrollIntoView(0, document.documentElement.scrollHeight-10);", h)
                bro.execute_script("window.scrollTo(0, 400)") 
                scraper.close_ad(bro)                         
        
        try: 
            '''
            这是单一房子的界面，如果是公寓的话会找不到元素，从而执行 except
            '''
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
            this_house_info['facilities'] = this_facilities
            
        except Exception:
            
            '''
            进入except模块的话，这个应该是个公寓界面
            '''
            #租金
            this_price = bro.find_element_by_xpath('//div[@id="layoutInfo"]/div[2]/div[5]/div[2]/div[1]/p[2]/span[1]').text
            this_house_info['price'] = this_price
            
            #配套设施
            this_facilities = []
            fac = bro.find_elements_by_xpath('//div[@id="layoutInfo"]/div[2]/div[5]/div[2]/div[3]/div[2]/ul/li')
            for f in fac:
                this_facilities.append(f.text)
                #print('配套设施--', f.text)
            this_house_info['facilities'] = this_facilities    
            
            #把当前户型的popup关掉后爬取公寓设施
            this_apartment_facilities = []
            bro.find_element_by_xpath('//div[@id="layoutInfo"]/div[2]/div[4]').click()
            
            fac = bro.find_elements_by_xpath('//div[@id="facility"]/ul/li')
            for i in range(0, len(fac)):    
                f = fac[i]
                this_facility_availability = f.get_attribute('class')
                this_facility = f.text
                if 'hide' in this_facility_availability:
                    pass
                else:
                    this_apartment_facilities.append(this_facility)
            #print(this_apartment_facilities)
            this_house_info['apartment_facilities'] = this_apartment_facilities
            
        return this_house_info    
            
    def scrape_a_line(self, bro):
        
        ## 遍历地铁站
        stations = {}
        stations_elem = bro.find_elements_by_xpath('//div[@id="filter"]/ul[4]/li/a')
        for i in tqdm(range(1, len(stations_elem))):
            stations_elem = bro.find_elements_by_xpath('//div[@id="filter"]/ul[4]/li/a') #为防止StaleElementError
            station = stations_elem[i]
            this_station = station.text            
            print(this_station)
            station.click()
                        
            #取得房源链接列表
            houses = bro.find_elements_by_xpath('//div[@id="content"]/div[1]/div[1]/div/a[1]')
            houses_name = bro.find_elements_by_xpath('//div[@id="content"]/div[1]/div[1]/div/div/p[1]/a')
            hs = []
            scraper.close_ad(bro)
            
            for i in range(0, len(houses)):
                h = houses[i]
                
                #-------以下为公寓界面下才有用的变量，用于在外部爬取：房名,tags
                h_name = houses_name[i].text
                h_tags_elems = bro.find_elements_by_xpath('//div[@id="content"]/div[1]/div[1]/div[%s]/div/p[3]/i'%(str(i)))
                h_tags = []
                for tag in h_tags_elems:
                    h_tags.append(tag.text)
                #-------以上为公寓界面下才有用的变量，用于在外部爬取：房名,tags
                
                this_house_info = self.scrape_a_house(bro, h)                
                
                if 'name' not in list(this_house_info.keys()): # 如果是公寓界面
                    this_house_info['name'] = h_name
                    this_house_info['tags'] = h_tags
                    
                hs.append(this_house_info)
                
                bro.implicitly_wait(3)
                bro.close()
                handles = bro.window_handles
                bro.switch_to.window(handles[0])        
            
            stations[this_station] = hs
        return stations
    



if __name__ == '__main__':
    # pc = scraper()
    # stations = pc.scrape_a_page('https://sh.lianjia.com/zufang/', show_browser=True)

    bk = beike()
    bk_stations = bk.scrape_a_page('https://sh.zu.ke.com/zufang', show_browser=True)
     
    
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
        

    
    












