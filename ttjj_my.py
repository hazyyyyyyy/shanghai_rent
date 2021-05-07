# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 12:21:22 2021

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
    
    # 等待函数
    def wait(self, wait_time):
        start_time = time.time()
        time.sleep(abs(round(random.normalvariate(wait_time,0.5),2)))
        end_time = time.time()
        print('强行等待了{}秒'.format(round(end_time-start_time),2))
    
    # 爬取总函数
    def run_crawl(self):
        # 创建Df存储结果
        man_basic = pd.DataFrame(columns=['company','manager','work_year', 'fund_scale', 'ari_annual_gr', 'geo_annual_gr'])
        man_fund_stock = pd.DataFrame(columns=['company','manager','fund','stock','ratio'])
    
        # 初始化
        bro = self.InitialBrowser()
        # 进入首页
        bro.get('http://fund.eastmoney.com/manager/#dt14;mcreturnjson;ftall;pn50;pi1;scabbname;stasc')
        # 点击按照现任基金最佳回报获取数据
        bro.find_element_by_xpath('//a[@id="bestProfit"]').click()
        bro.implicitly_wait(4)
        # 收集公司名
        companys = []
        comps = bro.find_elements_by_xpath('//table[@id="datalist"]/tbody/tr/td[3]/a')
        for c in comps:
            companys.append(c.text)
        print(companys)
    
        work_years = []
        fund_scales = []
        wy = bro.find_elements_by_xpath('//table[@id="datalist"]/tbody/tr/td[5]')
        fs = bro.find_elements_by_xpath('//table[@id="datalist"]/tbody/tr/td[6]')
        for w in wy:
            work_years.append(w.text)
        for f in fs:
            fund_scales.append(f.text)
        # 收集姓名，为点击进入新页面的接口
        names = bro.find_elements_by_xpath('//table[@id="datalist"]/tbody/tr/td[2]/a')
    
        # 开始逐层收集信息
        for i in tqdm(range(0, len(names))):
            n = names[i]
            name = n.text
            company = companys[i]
            # v1.1新增
            work_year = work_years[i]
            fund_scale = fund_scales[i]
            # 打印姓名和对应的公司名称
            print(name,company)
            n.click()
            bro.implicitly_wait(4)
            # 切换到新窗口
            handles = bro.window_handles
            bro.switch_to.window(handles[1]) #当前位于基金经理页面
            bro.implicitly_wait(3)
            # 获取每个基金的名字
            funds = bro.find_elements_by_xpath('//div[@class="content_out"]/div[2]/table/tbody/tr/td[2]/a')
            fund_names = []
            for f in funds:
                fund_names.append(f.text)
                print(f.text)
            # for i in range(len(funds)):
            #     # 缺双gr
            #     man_basic.loc[len(man_basic)] = {'company':company, 'manager':name, 'work_year':work_year, 'fund_scale':fund_scale} #, 'fund':fund_names[i]}     
    
            # 逐基金获取数据
            this_man_funds = {}
            for i in range(len(funds)):
                f = funds[i]
                f_name = f.text
                link = f.get_attribute('href')
                annual_grs, stock_data = self.crawl_fund(link)
                this_fund_data = [annual_grs, stock_data]
                this_man_funds[f_name] = this_fund_data
            
            # 求算术平均，几何平均，提取股票数据
            all_funds_annual_grs = []
            #all_funds_stocks = []
            for key in this_man_funds.keys():
                this_fund_data = this_man_funds[key]
                this_fund_annual_grs = this_fund_data[0]
                this_fund_stock = this_fund_data[1]
                all_funds_annual_grs.append(this_fund_annual_grs)
                if type(this_fund_stock)!=np.float: # 股票不是nan
                    for s in range(0, this_fund_stock.shape[0]):
                        this_stock_name = this_fund_stock.index[s]
                        this_stock_ratio = this_fund_stock[this_stock_name]
                        man_fund_stock.loc[len(man_fund_stock)] = \
                            {'company':company, 'manager':name, 'fund':str(key), \
                             'stock':this_stock_name, 'ratio':this_stock_ratio}
                else:
                    print('----------------------')
                    print('该基金无股票数据', 'manager', name, '; fund', str(key))
                    print('----------------------')
                    man_fund_stock.loc[len(man_fund_stock)] = \
                        {'company':company, 'manager':name, 'fund':str(key), \
                         'stock':np.nan, 'ratio':np.nan}
    
            ari_annual_gr, geo_annual_gr = self.cal_annual_gr(all_funds_annual_grs)
            man_basic.loc[len(man_basic)] =\
                {'company':company, 'manager':name, 'work_year':work_year, 'fund_scale':fund_scale, \
                 'ari_annual_gr':ari_annual_gr, 'geo_annual_gr':geo_annual_gr}    
        
            bro.close()
            bro.switch_to.window(handles[0])
            #wait(3)
        return man_basic, man_fund_stock

    # 爬取基金数据
    def crawl_fund(self, url):
        '''
            return：年化增长df， 股票持仓df
        '''
        bro = self.InitialBrowser()
        bro.get(url)
        bro.implicitly_wait(3)  
        '''
        爬取股票持仓部分
        '''
        stocks = bro.find_elements_by_xpath('//div[@class="fund_item quotationItem_DataTable popTab"][1]/div[2]/ul/li[1]/div[1]/table/tbody/tr/td[1]/a')[:10]
        stock_name = []
        for s in stocks:
            stock_name.append(s.text)
        ratios = bro.find_elements_by_xpath('//div[@class="fund_item quotationItem_DataTable popTab"][1]/div[2]/ul/li[1]/div[1]/table/tbody/tr/td[2]')[:10]
        ratio_num = []
        for r in ratios:
            ratio_num.append(r.text)
        if len(stock_name)==len(ratio_num) and len(stock_name)>0:
            stock_data = pd.Series(ratio_num, index=stock_name)
        else:
            stock_data = np.nan
        '''
        爬取年化部分
        '''
        # 首先要点出tabbutton, 这里不知道为啥find不能调用click
        # show_annual_gr = bro.find_elements_by_xpath('//div[@id="IncreaseAmount"]/div[1]/div[3]')
        # show_annual_gr[0].click()
        bro.execute_script('document.querySelector("#IncreaseAmount > div.item_title.hd > div:nth-child(3) > h3 > a").click()')
        # 然后再逐行取值
        years = bro.find_elements_by_xpath('//div[@id="IncreaseAmount"]/div[2]/ul/li[3]/table/tbody/tr/th/div')
        years_elem = []
        for i in range(0, len(years)):
            years_elem.append(years[i].text)
        
        annual_grs = pd.DataFrame(columns=years_elem)
        annuals = bro.find_elements_by_xpath('//div[@id="IncreaseAmount"]/div[2]/ul/li[3]/table/tbody/tr/td/div')
        this_line = []
        for i in range(0, len(annuals)):
            a_value = annuals[i]
            if i!=0 and i%len(annual_grs.columns)==0: #完成了一行，填表并重洗this_line
                annual_grs.loc[len(annual_grs)] = this_line
                this_line = []
                this_line.append(a_value.text)
            else:    
                this_line.append(a_value.text)
        annual_grs.drop('', axis=1, inplace=True)
        annual_grs.index = ['growth', 'average', 'hs300', 'rank_in_same_kind']
        annual_grs.rename(lambda x:int(x[:4]), axis=1, inplace=True) # 去除'年度'两个字
        annual_grs.iloc[0,:] = annual_grs.iloc[0,:].apply(lambda x:self.percent_2_decimal(x))
        bro.close()
        return annual_grs, stock_data
    
    # 百分数转小数函数
    def percent_2_decimal(self, x):
        if '--' in x:
            return np.nan
        else:
            return float(x.strip('%'))/100
    
    # 求算术平均，几何平均年化函数
    def cal_annual_gr(self, list_of_annuals):
        '''
            return: ari_annual_gr, geo_annual_gr
        '''
        growth_list = []
        for i in range(0, len(list_of_annuals)):
            growth_list.append(list_of_annuals[i].iloc[0,:])
            annual_grs = pd.concat(growth_list, axis=1)
            annual_grs = annual_grs.sort_index(ascending=False)
        annual_grs.dropna(axis=0, how='all', inplace=True) #去除全nan行
        
        if len(list_of_annuals)>=1: # 有至少一个基金      
            # 算术年化
            ari_annual_gr = 0
            for i in range(0, annual_grs.shape[0]):
                num_nan = np.sum(annual_grs.iloc[i,:].isna())
                ari_annual_gr += np.sum(annual_grs.iloc[i,:])/(annual_grs.shape[1]-num_nan)
                #print(annual_grs.index[i], np.sum(annual_grs.iloc[i,:]), annual_grs.shape[1]-num_nan)
            ari_annual_gr /= annual_grs.shape[0]
            # 几何年化
            geo_annual_gr = 1
            for i in range(0, annual_grs.shape[0]):
                num_nan = np.sum(annual_grs.iloc[i,:].isna())
                this_year_ave_gr = np.sum(annual_grs.iloc[i,:])/(annual_grs.shape[1]-num_nan)
                #print(annual_grs.index[i], np.sum(annual_grs.iloc[i,:]), annual_grs.shape[1]-num_nan)
                geo_annual_gr *= (1+this_year_ave_gr)
            geo_annual_gr = math.pow(geo_annual_gr, 1/annual_grs.shape[0])-1       
            return ari_annual_gr, geo_annual_gr
        else:
           return 0, 0


if __name__ == '__main__':
    start = time.time()
    pc = scraper()
    man_basic, man_fund_stock = pc.run_crawl()
    print(man_basic.head(50))
    print(man_fund_stock.head(50))
    #df.to_csv('ttjj_1.csv',encoding='gbk')
    man_basic.to_csv('man_basic.csv', encoding='gbk')
    man_fund_stock.to_csv('man_fund_stock.csv', encoding='gbk')
    end = time.time()
    print("耗时:",end-start)
    
    
   
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
