# encoding=utf-8import reimport loggingimport datetimeimport requestsimport timefrom scrapy.selector import Selectorfrom scrapy.exceptions import CloseSpiderfrom sina_weibo.items import InformationItem, FollowsItemdef get_user_detail(uid, cookies, user=None):    '''通过用户id返回用户的详细信息'''    informationItems = InformationItem()    if uid is None and user is not None:        uid = user['user_id']        informationItems['fir_category'] = user['fir_category']        informationItems['sec_category'] = user['sec_category']    informationItems['user_id'] = uid    user_url = "http://weibo.cn/attgroup/opening?uid=%s" % uid    time.sleep(5)    req = requests.get(url=user_url, cookies=cookies)    if req.status_code >= 300:        logging.error(req.status_code)        logging.info(req.url)        logging.info(req.body)        if req.status_code == 302:            raise CloseSpider("访问异常: " + str(req.status_code))    selector = Selector(text=req.content)    text0 = selector.xpath('body/div[@class="u"]/div[@class="tip2"]').extract_first()    if text0:        num_tweets = re.findall(u'\u5fae\u535a\[(\d+)\]', text0)  # 微博数        num_follows = re.findall(u'\u5173\u6ce8\[(\d+)\]', text0)  # 关注数        num_fans = re.findall(u'\u7c89\u4e1d\[(\d+)\]', text0)  # 粉丝数        if num_tweets:            informationItems["num_tweets"] = int(num_tweets[0])        if num_follows:            informationItems["num_follows"] = int(num_follows[0])        if num_fans:            informationItems["num_fans"] = int(num_fans[0])        informationItems["user_id"] = uid    url_information1 = "http://weibo.cn/%s/info" % uid    response = requests.get(url_information1, cookies=cookies)    if response.status_code >= 300:        logging.error(response.status_code)        logging.info(response.url)        logging.info(response.body)        if response.status_code == 302:            raise CloseSpider("访问异常: " + str(response.status_code))    selector = Selector(text=response.content)    text1 = ";".join(selector.xpath('body/div[@class="c"]/text()').extract())  # 获取标签里的所有text()    nickname = re.findall(u'\u6635\u79f0[:|\uff1a](.*?);', text1)  # 昵称    gender = re.findall(u'\u6027\u522b[:|\uff1a](.*?);', text1)  # 性别    place = re.findall(u'\u5730\u533a[:|\uff1a](.*?);', text1)  # 地区（包括省份和城市）    signature = re.findall(u'\u7b80\u4ecb[:|\uff1a](.*?);', text1)  # 个性签名    birthday = re.findall(u'\u751f\u65e5[:|\uff1a](.*?);', text1)  # 生日    sexorientation = re.findall(u'\u6027\u53d6\u5411[:|\uff1a](.*?);', text1)  # 性取向    marriage = re.findall(u'\u611f\u60c5\u72b6\u51b5[:|\uff1a](.*?);', text1)  # 婚姻状况    url = re.findall(u'\u4e92\u8054\u7f51[:|\uff1a](.*?);', text1)  # 首页链接    if nickname:        informationItems["nickname"] = nickname[0]    if gender:        informationItems["gender"] = gender[0]    if place:        place = place[0].split(" ")        informationItems["province"] = place[0]        if len(place) > 1:            informationItems["city"] = place[1]    if signature:        informationItems["signature"] = signature[0]    if birthday:        try:            birthday = datetime.datetime.strptime(birthday[0], "%Y-%m-%d")            informationItems["birthday"] = birthday - datetime.timedelta(hours=8)        except Exception:            pass    if sexorientation:        if sexorientation[0] == gender[0]:            informationItems["sex_orientation"] = "gay"        else:            informationItems["sex_orientation"] = "Heterosexual"    if marriage:        informationItems["marriage"] = marriage[0]    if url:        informationItems["url"] = url[0]        print informationItems["nickname"]    return informationItemsdef get_uid_by_uname(uname, cookies):    '''将传入的uname转为uid'''    r = requests.get(url="http://weibo.cn/" + uname, cookies=cookies)    id = re.search(r'<a href="/(\d+)/info">', r.text)    if id:        return id.groups()[0]    return Nonedef parse_follows(uid, cookies):    """ 抓取关注 """    url_follows = "http://weibo.cn/%s/follow" % uid    followsItems = FollowsItem()    followsItems["user_id"] = uid    response = requests.get(url=url_follows, cookies=cookies)    if response.status_code >= 300:        logging.error(response.status_code)        logging.info(response.url)        logging.info(response.body)        if response.status_code == 302:            raise CloseSpider("访问异常: " + str(response.status_code))    selector = Selector(text=response.text)    # 获取关注的人的url，以便获取user_id    follows_urls = selector.xpath(u'body//table/tr/td/a[text()="关注他" or text()="关注她"]/@href').extract()    follows = []    for elem in follows_urls:        elem = re.findall('uid=(\d+)', elem)        if elem:            follows.append(elem[0])    url_next = selector.xpath(u'body//div[@class="pa" and @id="pagelist"]/form/div/a[text()="\u4e0b\u9875"]/@href').extract()    while url_next:        response = requests.get("http://weibo.cn" + url_next[0], cookies=cookies)        time.sleep(5)        selector = Selector(text=response.content)        follows_urls = selector.xpath(u'body//table/tr/td/a[text()="关注他" or text()="关注她"]/@href').extract()        for elem in follows_urls:            # 获取uid            elem = re.findall('uid=(\d+)', elem)            if elem:                # 将关注人的uid添加到结果中                follows.append(elem[0])        url_next = selector.xpath(u'body//div[@class="pa" and @id="pagelist"]/form/div/a[text()="\u4e0b\u9875"]/@href').extract()    followsItems['follows'] = follows    # 如果没有下一页即获取完毕    return followsItems