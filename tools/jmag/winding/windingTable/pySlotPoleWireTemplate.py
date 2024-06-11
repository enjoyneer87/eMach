#---------------------------------------------------------------------
#Name: pySlotPoleWireTemplate.py
#Menu-en: 
#Type: Python
#Create: November 01, 2023 JSOL Corporation
#Comment-en: 
#---------------------------------------------------------------------
# -*- coding: utf-8 -*-
from win32com import client
app=client.dynamic.Dispatch('designer.Application.222')
# app = designer.GetApplication()
app.Show
#app.SetCurrentStudy(u"Test1")

Study=app.GetModel(0).GetStudy(0)
Study.IsValid
Study.GetName()
#Study.GetWindingRegion(u"Coil").SetSlots(48)
#Study.GetWindingRegion(u"Coil").SetPoles(8)
# app.GetModel(u"devModellerwithConductor_59").GetStudy(u"Test1")
# app.GetModel(u"devModellerwithConductor_59").GetStudy(u"Test1")
Study.GetWindingRegion(u"HairPinWave").SetSlots(u"Slots")
Study.GetWindingRegion(u"HairPinWave").SetPoles(u"Poles")
