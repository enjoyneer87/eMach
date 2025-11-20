import ctypes
import scipy.io as sio
from JplotReader import JplotReader
import os
import re

def main(jplot_file_path, totalSteps, postkey_id):
    # Open JplotReader for the given path
    reader = JplotReader.jplotOpen(jplot_file_path.encode('utf-8'))

    if reader is None:
        print(f"Cannot open file: {jplot_file_path}")
        return
    
    data = {}
    
    # Read nodes
    data['nodes'] = readNodes(reader)

    # Read element centers
    data['element_centers'] = readElementCenters(reader)

    # Read nodal displacements
    data['nodal_displacements'] = readNodalDisplacements(reader)

    # Read element center displacements
    data['element_center_displacements'] = readElementCenterDisplacements(reader)
    
    # Read component data for each step
    for stepIndex in range(1, totalSteps+1):
        if postkey_id == 16001:
            data[f'MagB_{stepIndex}'] = readComponentData(reader, postkey_id, stepIndex)
        elif postkey_id == 11005:
            data[f'MagA_{stepIndex}'] = readComponentData(reader, postkey_id, stepIndex) # 11005 is the key for magnetic vector potential A

    # Close JplotReader when finished
    JplotReader.jplotClose(reader)

    # Extract Case number and load name from the file path
    case_match = re.search(r"\\(Case\d+)", jplot_file_path)
    case_name = case_match.group(1)  # Extract the 'Case1', 'Case2', etc.

    # Extract the folder before "Case" to get the load name
    load_name_match = re.search(r"\\([^\\]+)\\Case\d+", jplot_file_path)
    if load_name_match:
        load_name = load_name_match.group(1)  # Folder name just before "Case"
    else:
        load_name = "UnknownLoad"  # Default name if extraction fails

    # Create the output file name using the extracted parts
    
    if postkey_id  == 16001:
         output_file_name = f"{load_name}_{case_name}_MagB.mat"
    elif postkey_id == 11005:
        output_file_name = f"{load_name}_{case_name}_MagA.mat"

    # Save all data to .mat file with the new name
    sio.savemat(output_file_name, data)

    print(f"Data saved to {output_file_name}")
return data,
# def getPartInfo(reader):
#     NumPart=JplotReader.jplotCountParts(reader)
#     PartStruct=[]
#     for i in range(NumPart):
#         index = ctypes.c_int()
#         id = ctypes.c_int()
#         name = ctypes.c_char_p()
#         size =ctypes.c_int()
#         JplotReader.jplotGetPartIdTitle(reader, index, id,  name, size)
#         PartStruct.append([index.value, id.value, name.value, size.value])
#     return PartStruct

def readNodes(reader):
    nodeCount = JplotReader.jplotCountNodes(reader)
    nodes = []

    JplotReader.jplotStartPopNode(reader)
    for i in range(nodeCount):
        id = ctypes.c_int()
        x = ctypes.c_double()
        y = ctypes.c_double()
        z = ctypes.c_double()
        JplotReader.jplotPopNode(reader, id, x, y, z)
        nodes.append([id.value, x.value, y.value, z.value])

    JplotReader.jplotEndPopNode(reader)
    return nodes

def readElementCenters(reader):
    elementCount = JplotReader.jplotCountElements(reader)
    element_centers = []

    JplotReader.jplotStartPopElementCenter(reader)
    for i in range(elementCount):
        id = ctypes.c_int()
        partId = ctypes.c_int()
        eleType = ctypes.c_int()
        x = ctypes.c_double()
        y = ctypes.c_double()
        z = ctypes.c_double()
        area = ctypes.c_double()
        JplotReader.jplotPopElementCenter(reader, id, partId, eleType, x, y, z, area)
        element_centers.append([id.value, partId.value, eleType.value, x.value, y.value, z.value, area.value])

    JplotReader.jplotEndPopElementCenter(reader)
    return element_centers

def readNodalDisplacements(reader):
    step = 1
    displacementCount = JplotReader.jplotCountNodalDisplacements(reader, step)
    nodal_displacements = []

    JplotReader.jplotStartPopNodalDisplacement(reader, step)
    for i in range(displacementCount):
        id = ctypes.c_int()
        dx = ctypes.c_double()
        dy = ctypes.c_double()
        dz = ctypes.c_double()
        JplotReader.jplotPopNodalDisplacement(reader, id, dx, dy, dz)
        nodal_displacements.append([id.value, dx.value, dy.value, dz.value])

    JplotReader.jplotEndPopNodalDisplacement(reader)
    return nodal_displacements

def readElementCenterDisplacements(reader):
    step = 1
    displacementCount = JplotReader.jplotCountElementCenterDisplacements(reader, step)
    element_center_displacements = []

    JplotReader.jplotStartPopElementCenterDisplacements(reader, step)
    for i in range(displacementCount):
        id = ctypes.c_int()
        dx = ctypes.c_double()
        dy = ctypes.c_double()
        dz = ctypes.c_double()
        JplotReader.jplotPopElementCenterDisplacement(reader, id, dx, dy, dz)
        element_center_displacements.append([id.value, dx.value, dy.value, dz.value])

    JplotReader.jplotEndPopElementCenterDisplacement(reader)
    return element_center_displacements

def readComponentData(reader, postkey_id,step):

    # magneticFluxDensity = 16001 # Component key to read

    # componentReader = JplotReader.jplotCreateComponentReader(reader, step, magneticFluxDensity) # Create component reader object

    componentReader = JplotReader.jplotCreateComponentReader(reader, step, postkey_id)
    if componentReader is None:
        return []
    
    componentCount = JplotReader.jplotCountComponents(componentReader)
    component_data = []

    JplotReader.jplotStartPopComponent(componentReader)
    for i in range(componentCount):
        id = ctypes.c_int()
        values = (ctypes.c_double * 3)()
        JplotReader.jplotPopComponent(componentReader, id, values)
        component_data.append([id.value, values[0], values[1], values[2]])
    
    JplotReader.jplotEndPopComponent(componentReader)
    JplotReader.jplotDeleteComponentReader(componentReader)
    return component_data

# 예시로 main 함수 호출
# main("path_to_your_jplot_file.jplot", 16001)  # 주석 처리된 예시, 실제 사용 시 주석 해제