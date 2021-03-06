# -*- coding: utf-8 -*-
from datetime import datetime
import random
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.template import loader, Context
from xml.etree import ElementTree as ET
from imgtest import imgtest
import time
import hashlib
from menu import MenuManager
from models import Hotel,Comment,ApInfo, Complaintext
import json
import requests
APPID = 'wxe840f265a71f11b8'
APPSECRET = '050bb9529cf251aa4d0c1f7a2565554d'

@csrf_exempt
def WeChat(request):
  #这里我当时写成了防止跨站请求伪造，其实不是这样的，恰恰相反。因为django默认是开启了csrf防护中间件的
  #所以这里使用@csrf_exempt是单独为这个函数去掉这个防护功能。
  if request.method == "GET":

    #下面这四个参数是在接入时，微信的服务器发送过来的参数
    signature = request.GET.get('signature', None)
    timestamp = request.GET.get('timestamp', None)
    nonce = request.GET.get('nonce', None)
    echostr = request.GET.get('echostr', None)

    #这个token是我们自己来定义的，并且这个要填写在开发文档中的Token的位置
    token = 'bdcloud'

    #把token，timestamp, nonce放在一个序列中，并且按字符排序
    hashlist = [token, timestamp, nonce]
    hashlist.sort()

    #将上面的序列合成一个字符串
    hashstr = ''.join([s for s in hashlist])

    #通过python标准库中的sha1加密算法，处理上面的字符串，形成新的字符串。
    hashstr = hashlib.sha1(hashstr).hexdigest()

    #把我们生成的字符串和微信服务器发送过来的字符串比较，
    #如果相同，就把服务器发过来的echostr字符串返回去
    if hashstr == signature:
      return HttpResponse(echostr)
  if request.method == "POST":
     # print "######## wechat post method ##########"
      str_xml = request.body
      xml = ET.fromstring(str_xml)
      msgType=xml.find("MsgType").text
      toUser=xml.find("FromUserName").text
      fromUser=xml.find("ToUserName").text
      nowtime = str(int(time.time()))    
      if msgType == 'event':
           Event=xml.find("Event").text
           if Event == 'CLICK':
               EventKey=xml.find("EventKey").text
               if EventKey == 'XM_WIFI':
                  t = loader.get_template('home/tuwen.xml')
                  c = Context({'toUser': toUser, 'fromUser': fromUser,'nowtime': nowtime,
                               'title1': '锡林浩特WIFI热点分布图', 'description1':'功能开发中，敬请期待。',
                               'picurl1':'http://121.40.58.147/static/images/map-1.jpg',
                               'url1':'http://licong.iok.la:35148/home/text',
                               'title2': '锡林浩特智慧旅游城市项目计划', 'description2':'功能开发中，敬请期待。',
                               'picurl2':'http://121.40.58.147/static/images/1111.jpg',
                               'url2':'http://licong.iok.la:35148/home/guihua',
                               'title3': '智慧锡林浩特简介', 'description4':'功能开发中，敬请期待。',
                               'picurl3':'http://121.40.58.147/static/images/1113.jpg',
                               'url3':'http://licong.iok.la:35148/home/xlht'
                               })
                  return HttpResponse(t.render(c))
           elif Event == 'subscribe':
                content = '终于等到你，感谢您的关注。'
           else:
                content = ''
      elif msgType == 'image':
          try:
            picurl = xml.find('PicUrl').text
            datas = imgtest(picurl)
            content =  '图中人物性别为'+datas[0]+'\n'+'年龄为'+datas[1]
          except:
            content =  '识别失败，换张图片试试吧'
      else:
            content = chat( xml.find("Content").text)
      
      #加载text.xml模板
      t = loader.get_template('home/text.xml')
      #将我们的数据组成Context用来render模板。
      c = Context({'toUser': toUser, 'fromUser': fromUser,
                   'nowtime': nowtime, 'content': content})
      #print t.render(c)
      return HttpResponse(t.render(c))
     
def createmenu(request):
    wx = MenuManager()
    accessToken = wx.getAccessToken(request)
    wx.createMenu(accessToken)
    return HttpResponse("创建成功")

def delmenu(request):
    wx = MenuManager()
    accessToken = wx.getAccessToken(request)
    wx.delMenu(accessToken)
    return HttpResponse("删除成功")

def getmenu(request):
    wx = MenuManager()
    accessToken = wx.getAccessToken(request)
    respstr = wx.getMenu(accessToken)
    print "respstr:",respstr
    return HttpResponse(respstr)

def municipalhall(request):
    return render(request,'home/municipalhall.html')

def wechatmatrix(request):
    return render(request,'home/wechatmatrix.html')

def getuserinfo(code):
    '''
     获得用户的昵称等信息
    :param request:
    :return:
    '''

    access_token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    cont = {}
    cont["appid"] = APPID
    cont["secret"] = APPSECRET
    cont["code"] = code
    cont["grant_type"] = "authorization_code"
    cont["srtnoc"] =  random.random()

    response = requests.get(access_token_url,params=cont)

    print "response:",response.text

    retparm = eval(response.text)
    print "retparm:",retparm
    openid = retparm["openid"]
    refresh_token = retparm["refresh_token"]
    access_token = checktoken(retparm["access_token"],openid,refresh_token)
    scope = retparm["scope"]
    userparams_url = "https://api.weixin.qq.com/sns/userinfo?access_token="+access_token+"&openid="+openid+"&lang=zh_CN"
    userinfo = requests.get(userparams_url)
    userinfo.encoding = 'utf-8'
    print "用户信息：",userinfo.text
    return eval(userinfo.text)
@csrf_exempt
def canyindetail(request):
    if request.method == "GET":
        code = request.GET.get('code')
        parms = request.GET.get('id')
        hostid = parms.split("$")[1]
        pos = parms.split("$")[0]
        print code,"id:",hostid
        print "pos",pos

        context = {}
        try:
            useinfo = getuserinfo(code)

            print "用户信息：",useinfo["nickname"]
            print "用户信息：",useinfo["headimgurl"]
            context["nickname"] = useinfo["nickname"]
            context["useinfo"] = useinfo
        except:
            print "useinfo error"

        commentlist = Comment.objects.filter(hotel_id=hostid)
        commentinfo = []
        if commentlist:
            for comm in commentlist:
                temodict = {}
                temodict["comment"] = comm
                if comm.img:
                    imgurllist = comm.img.encode('utf-8').split(';')
                    imgurllist.pop()
                    temodict["imgurllist"] = imgurllist
                else:
                    temodict["imgurllist"] = []
                commentinfo.append(temodict)

        hotel = Hotel.objects.filter(id=hostid)
        if hotel:
            context["hotelpoint"] = hotel[0].avr_score
            context["hotel"] = hotel[0]
        context["commentlist"] = commentlist
        context["commentlistlen"] = len(commentlist)
        context["item_list"] = [1,2,3,4]
        context["hostid"] = hostid
        context["commentinfo"] = commentinfo
        context["personpos"] = pos


        numpoint = []
        for temp in ['10000','11000','11100','11110','11111']:
            if len(commentlist) != 0:
                numpoint.append(float('%.2f' %(float(getnumforpoint(hostid,temp))/len(commentlist)))*100)
            else:
                numpoint.append(0)
            print "getnumforpoint(temp):",getnumforpoint(hostid,temp)
        context["numpoint"] = numpoint

        return render(request,'home/detail.html',context)
    if request.method == "POST":
        print "I am POST "
        hostid = request.POST.get("hostid")
        useinfo = request.POST.get("useinfo")
        nickname = request.POST.get("nickname")
        personpos = request.POST.get("personpos")
        point = request.POST.get("inputpoint")[:1]
        if not point:
            point = 5
        commenttext = request.POST.get("commenttext")
        images = request.FILES.getlist('commentimg')
        imagesurl = ''
        for f in images:
             url = './static/comm_images/'+'COMMENT' + genOrderNum() + f.name
             imagesurl += "../../."+url+";"
             destination = open(url,'wb+')
             for chunk in f.chunks():
                  destination.write(chunk)
             destination.close()
        print imagesurl,"point,",point
        comment = Comment()
        comment.username = nickname
        if eval(useinfo)["headimgurl"]:
            comment.headimgurl = str(eval(useinfo)["headimgurl"]).replace("\\","")
        comment.socre = getstr(point)
        comment.comment = commenttext
        comment.img = imagesurl
        hotel = Hotel.objects.get(id=hostid)
        comment.hotel = hotel
        comment.save()
        commentlist = Comment.objects.filter(hotel_id=hostid)
        commentinfo = []
        if commentlist:
            for comm in commentlist:
                temodict = {}
                temodict["comment"] = comm
                if comm.img:
                    imgurllist = comm.img.encode('utf-8').split(';')
                    imgurllist.pop()
                    temodict["imgurllist"] = imgurllist
                else:
                    temodict["imgurllist"] = []
                commentinfo.append(temodict)

        sumpoint = 0
        for temp in ['10000','11000','11100','11110','11111']:
            sumpoint += getpoint(temp)*getnumforpoint(hostid,temp)
        hotel.avr_score = float('%.2f'%(sumpoint/float(len(commentlist))))
        hotel.save()
        #传到前端的数据  评论
        context = {}
        hotel = Hotel.objects.filter(id=hostid)
        if hotel:
             context["hotel"] = hotel[0]
        context["commentlist"] = commentlist
        context["commentlistlen"] = len(commentlist)
        context["nickname"] = eval(useinfo)["nickname"]
        context["useinfo"] = useinfo
        context["hostid"] = hostid
        context["commentinfo"] = commentinfo
        context["personpos"] = personpos

        numpoint = []
        sumpoint = 0
        for temp in ['10000','11000','11100','11110','11111']:
            if len(commentlist) != 0:
                numpoint.append(float('%.2f' %(float(getnumforpoint(hostid,temp))/len(commentlist)))*100)
            else:
                numpoint.append(0)
            print "getnumforpoint(temp):",getnumforpoint(hostid,temp)
        if hotel:
            context["hotelpoint"] = hotel[0].avr_score
        context["numpoint"] = numpoint

        return render(request,'home/detail.html',context)

def getnumforpoint(hostid,strpoint):
     commentlist = Comment.objects.filter(hotel__id=hostid,socre=strpoint)
     return len(commentlist)

def genOrderNum():
    _now = datetime.utcnow()
    seq = [
        '{0:04}'.format(_now.year),
        '{0:02}'.format(_now.month),
        '{0:02}'.format(_now.day),
        '{0:02}'.format(_now.hour),
        '{0:02}'.format(_now.minute),
        '{0:02}'.format(_now.second),
        '{0:06}'.format(_now.microsecond)]
    return ''.join(seq)

def getstr(point):
    point = int(point)
    strpoint0 = "00000"
    strpoint1 = "11111"
    strpoint = strpoint1[0:point]+strpoint0[point:5]
    return strpoint

def getpoint(str):
    point = 0
    for temp in str:
        point += int(temp)
    return point


def checktoken(token,openid,refresh_token):
    chekouturl = "https://api.weixin.qq.com/sns/auth?access_token="+token+"&openid="+openid
    result = requests.get(chekouturl)
    if eval(result.text)["errcode"] == 0:
        print "token有效"
        return token
    else:
        refurl = "https://api.weixin.qq.com/sns/oauth2/refresh_token?appid="+APPID+"&grant_type="+refresh_token+"&refresh_token=REFRESH_TOKEN"
        respon = requests.post(refurl)
        if eval(respon.text).has_key('access_token'):
            return eval(respon.text)["access_token"]

def canyin(request):
    hotels_info=[]
    order = request.GET.get('order','0')
    alist = request.GET.get('alist','null')
    id_distance = request.GET.get('id_distance','null')
    print "alist:",alist,"id_distance:",id_distance
    order = str(order)
    print "order:",order,type(order)
    context={}
    if order == '0':
        hotels=Hotel.objects.all().order_by('-avr_score')
    elif order == '2':
        localpointlng = request.GET.get('localpointlng')
        localpointlat = request.GET.get('localpointlat')
        context["localpointlng"]=localpointlng
        context["localpointlat"]=localpointlat
        hotelslist = []
        newlist = eval('['+id_distance+']')
        print newlist,type(newlist)
        for templi in newlist:
            hotelslist.append(Hotel.objects.get(id=int(templi)))
        hotels = hotelslist
    else:
        hotels=Hotel.objects.all().order_by('avr_score')
    for hotel in hotels:
        tmp_info={}
        tmp_info["posi"]=[]
        tmp_info["name"]=""
        tmp_info["id"]=None
        tmp_info["score"]=None
        tmp_info["name"]=hotel.name.encode('utf-8')
        tmp_info["address"]=hotel.address.encode('utf-8')
        tmp_info["avr_score"]=float(hotel.avr_score)
        commentlist = Comment.objects.filter(hotel=hotel)
        context["commentlen"] = len(commentlist)
        tmp_info["id"]=int(hotel.id)
        tmp_posi=[]
        tmp_posi.append(hotel.lng)
        tmp_posi.append(hotel.lat)
        tmp_info["posi"]=tmp_posi
        hotelimg = hotel.img.encode('utf-8').split(';')
        if hotel.img != '':
            # print "有图片"
            tmp_info["img"] = hotelimg[0]
        else:
            # print "无图片"
            tmp_info["img"] = '../../../static/comm_images/COMMENT20170428051333849860玉石.jpg'
        # print "6666666666",tmp_info["img"]
        comment = Comment.objects.filter(hotel=hotel)
        tmp_info["commentlen"] = comment.count()
        hotels_info.append(tmp_info)


    # print hotels_info,type(hotels_info)
    context["hotels_info"]=json.dumps(hotels_info)
    context["hotels_title"]=hotels_info
    return render(request,'home/canyin.html',context)
@csrf_exempt
def addhotelimg(request):
    if request.method == "GET":
        hotellist = Hotel.objects.all()
        context = {}
        context["hotellist"] = hotellist
        return render(request,'home/addhotelimg.html',context)
    if request.method == "POST":
        hotelid = request.POST.get('hotelid')
        images = request.FILES.getlist('hotelimg')
        imagesurl = ''
        for f in images:
             url = './static/hotel_images/'+ 'HOTEL' + genOrderNum() + f.name
             imagesurl += "../../."+url
             destination = open(url,'wb+')
             for chunk in f.chunks():
                  destination.write(chunk)
             destination.close()
        hotel = Hotel.objects.filter(id=hotelid)
        print 'hotelid:',hotelid,'hotel:',hotel
        if hotel:
            hotel[0].img=imagesurl
            hotel[0].save()
            print "图片已保存"
        hotellist = Hotel.objects.all()
        context = {}
        context["hotellist"] = hotellist
        return render(request,'home/addhotelimg.html',context)

def text(request):
    return render(request,'home/detail.html')

def charge(request):
    return render(request,'home/charge.html')

def guihua(request):
    return render(request,'home/guihua.html')

def xlht(request):
    return render(request,'home/xlht.html')

def star(request):
    return render(request,'home/star.html')

def complain(request):
    return render(request,'home/complain.html')

def jinqu(request):
    return render(request,'home/jinqu.html')

def wenticanyin(request):
    hotelslist = Hotel.objects.filter(id__lt=7)
    context = {}
    context["hotels_title"] = hotelslist
    return render(request,'home/wenticanyin.html',context)

@csrf_exempt
def complaintext(request):
    if request.method == "GET":
        hotelid = request.GET.get('hotelid')
        nickname = request.GET.get('nickname')
        print hotelid,nickname
        context = {}
        context["hotelid"] = hotelid
        context["nickname"] = nickname

        return render(request,'home/complaintext.html',context)
    if request.method == "POST":
        hotelid = request.POST.get('hotelid')
        nickname = request.POST.get('nickname')
        text = request.POST.get('text')
        print hotelid,nickname,text
        complain = Complaintext()
        complain.hotelid = hotelid
        complain.username = nickname
        complain.complaintext = text
        complain.save()
        result = {}
        result['res'] = 1
        return JsonResponse(result)

def chat(msg):
    import sys
    reload(sys)
    sys.setdefaultencoding('utf8')
    url = 'http://www.tuling123.com/openapi/api'
    con = '''{"key":"0767b07223a94eb299c7657b9b2b5c72","info":"%s"}'''%(msg)
    print con
    response = requests.post(url,data = con.encode('utf-8'))
    print response.text
    return eval(response.text)["text"]

def showAps(request):
    ap_list=[]
    aps=ApInfo.objects.all()
    print aps
    for ap in aps:
        tmp=[]
        tmp.append(ap.lng)
        tmp.append(ap.lat)
        ap_list.append(tmp)
        print tmp
    context={}
    context["apInfo"]=json.dumps(ap_list)
    return  render(request,'home/apmap.html',context)

def line(request):
    personpos = request.GET.get('personpos')
    lng = request.GET.get('lng')
    lat = request.GET.get('lat')
    print personpos,lng,lat
    cont = {}
    cont["personpos"] = personpos
    cont["lng"] = lng
    cont["lat"] = lat
    context = {}
    context["parm"] = json.dumps(cont)
    return render(request,'home/line.html',context)