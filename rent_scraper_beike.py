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

from rent_scraper import scraper

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
    # pickle.dump(stations, open('lianjia.p', 'wb'))
    
    bk = beike()
    bk_stations = bk.scrape_a_page('https://sh.zu.ke.com/zufang', all_stations=False, website_name='beike', show_browser=True)
    pickle.dump(bk_stations, open('beike.p', 'wb'))
    
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
        

    
    












