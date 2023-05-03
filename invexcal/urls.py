from django.urls import path,include
from . import views

urlpatterns = [
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
        # path('optiondup/',views.optionDup,name='optionDup'),
        path('getData/',views.getData,name='getData'),
        path('calc/',views.calculate,name='calculate'),
        path('save/',views.save,name='save'),
        # path('getVol/',views.getVol,name='getVol'),

        # path('hist/',views.valuation,name='valuation')
]