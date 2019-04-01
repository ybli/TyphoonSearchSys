from datetime import datetime

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import APIView

from mongoengine import *

from TyphoonSystem import settings
from .views_base import BaseView
import json

# 引入mongoengine
# import mongoengine

from .models import Point, GeoTyphoonRealData
from .serializers import *
from .middle_models import *
from common import dateCommon


# Create your views here.

class PointInfoView(APIView):
    '''

    '''

    def get(self, request):
        bbxlist = Point.objects.all()
        # Point.objects.
        # json_data=BBXInfoSerializer(bbxlist,many=True)
        # return Response(serialize('json',bbxlist))
        return Response("")
        # pass


class TyphoonRealDataView(APIView):
    def get(self, request):
        code = request.GET.get("code", settings.default_typhoon_code)
        # 根据台风的code获取该台风的气象数据
        # code="MERBOK"
        # 1：使用djongo的实现
        # realtime_list=GeoTyphoonRealData.objects.filter(code=code)

        # 2：使用mongoengine的实现
        realtime_list = GeoTyphoonRealData.objects(code=code)
        json_data = GeoTyphoonRealDataSerializer(realtime_list, many=True).data

        return Response(json_data)


class FilterByMonth(BaseView):
    '''
        根据起始月份进行查询（或改成起止日期）
    '''

    def get(self, request):
        code = request.GET.get("code", settings.default_typhoon_code)
        month = int(request.GET.get("month", "1"))
        list = self.getTyphoonList(code=code, month=month)
        json_data = GeoTyphoonRealDataSerializer(list, many=True).data
        return Response(json_data)
        # pass

    def getTyphoonList(self, *args, **kwargs):
        '''
            根据code以及month查询台风路径信息
        :param args:
        :param kwargs:
        :return:
        '''
        code = kwargs.get('code', "")
        month = kwargs.get('month', datetime.now().month)
        # TODO [*]此处存在的问题不能使用django的xxx__month的方式直接按照月份去过滤
        # return GeoTyphoonRealData.objects.filter(code=code,date__month=6)
        return GeoTyphoonRealData.objects.filter(code=code, date__lte=datetime.now())


class FilterByYear(BaseView):
    '''
        根据年份进行查询
    '''

    def get(self, request):
        # TODO [-]优先完成此部分
        code = request.GET.get('code')
        year = request.GET.get('year', datetime.now().year)
        list = self.getTyphoonList(year=year, code=code)
        json_data = GeoTyphoonRealDataSerializer(list, many=True).data
        return Response(json_data)

    def getTyphoonList(self, *args, **kwargs):
        '''
            根据code以及month查询台风路径信息
        :param args:
        :param kwargs:
        :return:
        '''
        code = kwargs.get('code', "")
        year = kwargs.get('year')
        # 获取起止日期
        start, end = dateCommon.getYearDateRange(year)
        # TODO [-]此处改为使用mongoengine的方式进行查询
        return GeoTyphoonRealData.objects(date__lte=end) if code == "" else GeoTyphoonRealData.objects(code=code,
                                                                                                       date__lte=end)
        # return GeoTyphoonRealData.objects.filter(code=code,date__lte=end,date__gte=start)
        # return GeoTyphoonRealData.objects(code=code, date__lte=end)
        # return GeoTyphoonRealData.objects.filter(code=code, date__gte=start)


class FilterByRange(BaseView):
    '''
        根据经纬度[lat,lon]以及range 返回在指定范围内的台风编号
    '''

    def get(self, request):
        # TODO [-]优先完成此部分 对于第一种传输组的方式
        # latlon=request.GET.get('latlon')
        # TODO 注意python3开始，map返回的是一个迭代器，不是list，需要手动转一下
        # latlons=list(map(lambda x:float(x),latlon.split(',')))
        # TODO [-] 使用此种方式接收

        latlons = request.GET.getlist('latlon[]')
        # 处理后的latlong=[lat,lon]
        latlons = list(map(lambda x: float(x), latlons))

        range = int(request.GET.get('range'))
        # 获取去重后的code list
        codes = self.getTyphoonList(latlon=latlons, range=range)
        # TODO [*] 19-04-01根据code list，获取该code对应的code以及startdate
        # list_data = [GeoTyphoonRealData.objects(code=code)[:1].code
                     # for code in codes]

        # list_data = []
        # for code in codes:
        #     list_data.append(TyphoonModel(GeoTyphoonRealData.objects(code=code)[0].code,GeoTyphoonRealData.objects(code=code)[0].date))

        #
        # 使用列表推导
        list_data = [
            TyphoonModel(GeoTyphoonRealData.objects(code=code)[0].code,GeoTyphoonRealData.objects(code=code)[0].date)
            for code in codes]
        json_data = TyphoonModelSerializer(list_data, many=True).data
        return Response(json_data, status=status.HTTP_200_OK)

    def getTyphoonList(self, *args, **kwargs):
        '''
            根据code以及month查询台风路径信息
        :param args:
        :param kwargs:
        :return:
        '''
        latlon = kwargs.get('latlon')
        range = kwargs.get('range')

        return GeoTyphoonRealData.objects(latlon__near=latlon[::-1], latlon__max_distance=range).distinct('code')
