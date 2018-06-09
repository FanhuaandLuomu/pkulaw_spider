#coding:utf-8
import socket
socket.setdefaulttimeout(60)
import requests
import urllib2
# import cchardet
import os,time
from lxml import etree
import threading
import re
import random

# filenames=os.listdir('.')
# count=0
# for fname in filenames:
# 	if fname.startswith('gid_log'):
# 		count+=1

# gid_path='gid_log_%d' %(count)

# 1、2步分开运行要注意gid_path
# gid_path='gid_log_12'

def get_html(url):  #得到网页源码
	headers = {
	    "Accept-Language": "zh-CN,zh;q=0.8", 
	    "Accept-Encoding": "gzip, deflate, sdch", 
	    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", 
	    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36", 
	    "Host": "www.pkulaw.cn", 
	    "Cookie": "ASP.NET_SessionId=cl2tkn0phvk0ozzzkevfnj0w; CheckIPAuto=0; CheckIPDate=2018-06-09 20:56:18; CookieId=cl2tkn0phvk0ozzzkevfnj0w; Hm_lvt_58c470ff9657d300e66c7f33590e53a8=1528548975; Hm_lpvt_58c470ff9657d300e66c7f33590e53a8=1528549306; bdyh_record=1970324891788741%2C1970324891779934%2C1970324891786271%2C1970324891781214%2C1970324891781391%2C1970324891813384%2C1970324891813401%2C1970324891828997%2C1970324891829101%2C1970324891829114%2C1970324891828717%2C1970324891828807%2C1970324891828821%2C1970324891829381%2C1970324891829411%2C1970324848225657%2C1970324891817924%2C1970324848198841%2C1970324891848364%2C1970324891840137%2C", 
	    "Upgrade-Insecure-Requests": "1", 
	    "Proxy-Connection": "keep-alive"
	}
	html=requests.get(url,headers=headers).text
	return html

def write2file(content,filename):  # 将爬取的文书写入文件保存
	try:
		f=open(filename,'w')
	except Exception,e:
		filename=filename.split(u'、')[0]+'_error_filename.txt'
		f=open(filename,'w')
	f.write(content.encode('utf-8'))
	f.close()

 #下载ihref对应的文书
def load_one_wenshu(gid,title): 
	ex_href='http://www.pkulaw.cn/case/FullText/_getFulltext?library=pfnl&gid=#gid#&loginSucc=0'
	href=ex_href.replace('#gid#',gid)
	html=get_html(href)
	page=etree.HTML(html)
	content=page.xpath('body')[0].xpath('string(.)').strip()
	write2file(content,filepath+os.sep+title+'.txt')

def load_one_page_wenshu(gid_list,titles):  # 多线程抓取多个href的文书
	# threads=[]   # 尝试多线程加速 失败 访问频繁 出现验证码 封ip
	# for i in range(len(gid_list)):
	# 	gid,title=gid_list[i],titles[i]
	# 	threads.append(threading.Thread(target=load_one_wenshu,args=(gid,title,)))
	# for t in threads:
	# 	t.start()
	# t.join()  # 阻塞

	for i in range(len(gid_list)):  # 顺序爬取 时间过长 一个月大概需要20~30h
		load_one_wenshu(gid_list[i],titles[i])
		# time.sleep(0.1)

# 保存案件标题和id至文件
def save_gids(pageIndex,gid_list,titles):
	fpath=gid_path
	if not os.path.exists(fpath):
		os.mkdir(fpath)
	f=open(fpath+os.sep+str(pageIndex)+'.txt','w')
	for i in range(len(gid_list)):
		f.write('%s\t%s\n' %(titles[i].encode('utf-8'),gid_list[i]))
	f.close()

#得到一页上所有的文书名称和案件id并保存
def get_one_page_all_href(href,pageIndex):
	html=get_html(href.replace('#pageIndex#',str(pageIndex)))
	# time.sleep(random.random())
	page=etree.HTML(html)
	items=page.xpath('//dl[@class="contentList"]/dd/a')
	print len(items)
	gid_list=[]
	titles=[]
	for item in items:
		ihref=item.attrib['href']
		# title=item.text.strip()
		title=item.xpath('string(.)').strip()
		# if u'、' in title:
		# 	title=title.split(u'、')[1]
		gid=re.findall(r'_(.*?).html',ihref)[0]
		if gid not in gid_list:
			gid_list.append(gid)
			titles.append(title)
	# print len(set(titles))
	print 'page:%d has %d different case.' %(pageIndex,len(gid_list))
	# load_one_page_wenshu(gid_list,titles)
	save_gids(pageIndex,gid_list,titles)

# 获取当前log文件的所有title和id
def get_titles_gids(filename):
	gid_list=[]
	titles=[]
	f=open(filename,'r')
	for line in f:
		pieces=line.strip().split('\t')
		title,gid=pieces[0],pieces[1]
		title=title.replace('?','')
		# print cchardet.detect(title)
		gid_list.append(gid)
		titles.append(title.decode('utf-8'))
	return gid_list,titles

def load_one_page_from_gid_log(filename):  # 从下载好的gid中开始下载文书
	gid_list,titles=get_titles_gids(filename)   # 得到 gid_list 和 titles
	f=open('href_error_log.txt','a')
	for i in range(len(gid_list)):
		try:
			load_one_wenshu(gid_list[i],titles[i])
			print '%s-%d load success..' %(filename,i+1)
		except Exception,e:   # 若该项抓取出错 记录至error_log.txt
			print '%s-%d load failed...' %(filename,i+1),e
			f.write('%s-%d:\t%s\t%s\n' %(filename,i+1,titles[i].encode('utf-8'),gid_list[i]))
			f.flush()
			time.sleep(1)
	f.close()

#得到目标日期范围内的数据页数pageNum
def getPageNum(href):
	html=get_html(href.replace('#pageIndex#','0'))
	page=etree.HTML(html)
	pageNum=page.xpath('//*[@id="toppager"]/span/span[2]')
	if pageNum!=None:
		pageNum=int(pageNum[0].xpath('string(.)').strip())
	else:
		pageNum=50
	print 'pageNum:',pageNum
	return pageNum

def main():
	# PageSize=1000&Pager.PageIndex=0   
	# Start"%3A"2016.09.24"%2C"End"%3A"2016.10.13"%7D
	# href为查询案例与裁判文书的 链接  可设置页大小 页码  起始结束日期
	href='http://www.pkulaw.cn/case/Search/Record?Menu=CASE\
		&IsFullTextSearch=False&MatchType=Exact&Keywords=#keyword#\
		&OrderByIndex=0&GroupByIndex=0&ShowType=1\
		&ClassCodeKey=#classcode1#%2C%2C#classcode3#&OrderByIndex=0&GroupByIndex=0\
		&ShowType=0&ClassCodeKey=#classcode1#%2C%2C#classcode3#&Library=PFNL\
		&FilterItems.CourtGrade=&FilterItems.TrialStep=\
		&FilterItems.DocumentAttr=&FilterItems.TrialStepCount=\
		&FilterItems.LastInstanceDate=%7B"Start"%3A"#start_date#"%2C"End"%3A"#end_date#"%7D\
		&FilterItems.CriminalPunish=&FilterItems.SutraCase=\
		&FilterItems.CaseGistMark=&FilterItems.ForeignCase=&GroupIndex=\
		&GroupValue=&TitleKeywords=&FullTextKeywords=\
		&Pager.PageSize=1000&Pager.PageIndex=#pageIndex#&X-Requested-With=XMLHttpRequest'
	global filepath
	# filepath='2017-12_15-1_19'  # 日期修改 href中也要修改

	# filepath='2017_01_01-2017_09_01'

	print 'input date info (eg:2017_01_01-2017_09_01):'
	filepath=raw_input(">").strip()

	start_date,end_date=filepath.split('-')

	start_date=start_date.replace('_','.')
	end_date=end_date.replace('_','.')

	print 'start_date:',start_date
	print 'end_date:',end_date

	# classcode1='007'

	print 'input classcode1(an you):(eg:007)'
	classcode1=raw_input(">").strip()

	href=href.replace('#start_date#',start_date).replace('#end_date#',end_date).replace('#classcode1#',classcode1)

	print 'input classcode3(fa yuan):(eg:01)'
	classcode3=raw_input(">").strip()

	href=href.replace('#classcode3#',classcode3)

	# keyword=u'离婚'
	print 'input keyword:'
	keyword=raw_input('>').decode('GB18030').strip()
	href=href.replace('#keyword#',keyword)

	# print href

	# filepath='tmp'

	filepath=filepath+'+'+classcode1+'+'+classcode3+'+'+keyword

	if not os.path.exists(filepath):
		os.mkdir(filepath)

	global gid_path
	gid_path=filepath+'_log'

	pageNum=getPageNum(href)  # 得到所有案件页数
	print pageNum
	
	
	# 第一步 下载hrefs 和 titles
	for i in range(pageNum):   # 页数要修改
		get_one_page_all_href(href,i)
	
	
	'''
	# t0=time.time()
	# threads=[]   # 多线程
	# for i in range(459):
	# 	threads.append(threading.Thread(target=get_one_page_all_href,args=(href,i,)))
	# for t in threads:
	# 	t.start()
	# t.join()
	# print 'load %s cost:%.2f' %(filepath,time.time()-t0)
	'''
	
	
	
	# 第二步 根据gid文件下载相应的文书
	for i in range(pageNum):
		f=open('page_error_log.txt','a')
		try:
			fname=gid_path+os.sep+str(i)+'.txt'
			load_one_page_from_gid_log(fname)  #从gid_log中取title和id 下载相关文书
			print '%s load success...' %(fname)
		except Exception,e:
			print '%s load failed...' %(fname),e
			f.write('%s' %(fname))
			f.flush()
			time.sleep(10)  # 休眠10s
		f.close()
	
	

if __name__ == '__main__':
	main()
