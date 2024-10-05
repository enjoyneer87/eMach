# JplotReader library import sample
#
# Copyright (C) 2019 JSOL Corporation

import ctypes
import os
import sys

pythonPath = os.path.split(sys.executable)[0]
os.add_dll_directory(os.path.split(pythonPath)[0])

JplotReader = ctypes.CDLL("JplotReader.dll")

JplotReader.jplotOpen.argtypes = [ctypes.c_char_p]
JplotReader.jplotOpen.restype = ctypes.c_void_p
JplotReader.jplotClose.argtypes = [ctypes.c_void_p]
JplotReader.jplotClose.restype = None

JplotReader.jplotCountNodes.argtypes = [ctypes.c_void_p]
JplotReader.jplotCountNodes.restype = ctypes.c_int
JplotReader.jplotStartPopNode.argtypes = [ctypes.c_void_p]
JplotReader.jplotStartPopNode.restype = None
JplotReader.jplotPopNode.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
JplotReader.jplotPopNode.restype = None
JplotReader.jplotEndPopNode.argtypes = [ctypes.c_void_p]
JplotReader.jplotEndPopNode.restype = None

JplotReader.jplotCountElements.argtypes = [ctypes.c_void_p]
JplotReader.jplotCountElements.restype = ctypes.c_int
JplotReader.jplotStartPopElementCenter.argtypes = [ctypes.c_void_p]
JplotReader.jplotStartPopElementCenter.restype = None
JplotReader.jplotPopElementCenter.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
JplotReader.jplotPopElementCenter.restype = None
JplotReader.jplotEndPopElementCenter.argtypes = [ctypes.c_void_p]
JplotReader.jplotEndPopElementCenter.restype = None

JplotReader.jplotStartPopNodalDisplacement.argtypes = [ctypes.c_void_p, ctypes.c_int]
JplotReader.jplotStartPopNodalDisplacement.restype = None
JplotReader.jplotPopNodalDisplacement.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
JplotReader.jplotPopNodalDisplacement.restype = None
JplotReader.jplotEndPopNodalDisplacement.argtypes = [ctypes.c_void_p]
JplotReader.jplotEndPopNodalDisplacement.restype = None
JplotReader.jplotCountNodalDisplacements.argtypes = [ctypes.c_void_p]
JplotReader.jplotCountNodalDisplacements.restype = ctypes.c_int

JplotReader.jplotStartPopElementCenterDisplacements.argtypes = [ctypes.c_void_p, ctypes.c_int]
JplotReader.jplotStartPopElementCenterDisplacements.restype = None
JplotReader.jplotPopElementCenterDisplacement.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
JplotReader.jplotPopElementCenterDisplacement.restype = None
JplotReader.jplotEndPopElementCenterDisplacement.argtypes = [ctypes.c_void_p]
JplotReader.jplotEndPopElementCenterDisplacement.restype = None
JplotReader.jplotCountElementCenterDisplacements.argtypes = [ctypes.c_void_p]
JplotReader.jplotCountElementCenterDisplacements.restype = ctypes.c_int

JplotReader.jplotCountComponents.argtypes = [ctypes.c_void_p]
JplotReader.jplotCountComponents.restype = ctypes.c_int
JplotReader.jplotCreateComponentReader.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
JplotReader.jplotCreateComponentReader.restype = ctypes.c_void_p
JplotReader.jplotDeleteComponentReader.argtypes = [ctypes.c_void_p]
JplotReader.jplotDeleteComponentReader.restype = None
JplotReader.jplotStartPopComponent.argtypes = [ctypes.c_void_p]
JplotReader.jplotStartPopComponent.restype = None
JplotReader.jplotPopComponent.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.c_double * 6]
JplotReader.jplotPopComponent.restype = None
JplotReader.jplotEndPopComponent.argtypes = [ctypes.c_void_p]
JplotReader.jplotEndPopComponent.restype = None
JplotReader.jplotComponentDimension.argtypes = [ctypes.c_void_p]
JplotReader.jplotComponentDimension.restype = ctypes.c_int

JplotReader.jplotCountParts.argtypes = [ctypes.c_void_p]
JplotReader.jplotCountParts.restype = ctypes.c_int
JplotReader.jplotGetPartIdTitle.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_char),ctypes.c_int]
JplotReader.jplotGetPartIdTitle.restype = None