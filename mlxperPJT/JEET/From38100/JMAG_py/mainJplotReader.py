import ctypes
import scipy.io as sio
from JplotReader import JplotReader
import os
import re


def main(jplot_file_path,startStep, totalSteps, postkey_id):
    """
    Main function to read component data from JplotReader and save to a .mat file.
    
    :param jplot_file_path: Path to the Jplot file (also used to find the corresponding .mat file for partID filtering)
    :param startSteps: Starting step to read
    :param totalSteps: Last step to read
    :param postkey_id: Postkey ID to read
    """
    
    # Open JplotReader for the given path
    reader = JplotReader.jplotOpen(jplot_file_path.encode('utf-8'))
    if reader is None:
        print(f"Cannot open file: {jplot_file_path}")
        return


    # 데이터를 저장할 딕셔너리 생성
    data = {}

    # Read nodes
    data['nodes'] = readNodes(reader)

    # Read element centers
    element_centers=[]
    element_centers= readElementCenters(reader)
    data['element_centers'] = element_centers
    # 전역적으로 element_ids_set을 초기화 (한 번만 설정)
    # initialize_filtered_ids(element_centers, part_ids)
    if postkey_id == 16001 or postkey_id == 19501:    
        JmagPJTPath, PartIDmat_file_path=getJmagPJTPathAndMatPath(jplot_file_path,'PartID')
        # .mat 파일 경로 생성
        try:
            # .mat 파일에서 partID 목록 읽어오기
            mat_data = sio.loadmat(PartIDmat_file_path)
            part_ids = mat_data['partID'].flatten()  # partIDs를 1D로 변환 (ndarray)
        except Exception as e:
            print(f"Error loading .mat file: {e}")
            return
        filtered_ids = filterElementCentersByPartID(element_centers, part_ids)
        filtered_ids_set = set(filtered_ids)  # set으로 변환하여 검색 최적화
    elif postkey_id == 11005:
         JmagPJTPath, NODEIDmat_file_path=getJmagPJTPathAndMatPath(jplot_file_path,'NodeID')
         try:
               # .mat 파일에서 partID 목록 읽어오기
               mat_data = sio.loadmat(NODEIDmat_file_path)
               NodeIDs= mat_data['NodeID'].flatten()  # partIDs를 1D로 변환 (ndarray)
         except Exception as e:
               print(f"Error loading .mat file: {e}")
               return
         filtered_ids_set = set(NodeIDs)  # set으로 변환하여 검색 최적화

    # Read nodal displacements
    data['nodal_displacements'] = readNodalDisplacements(reader)

    # Read element center displacements
    data['element_center_displacements'] = readElementCenterDisplacements(reader)
    
    # 각 단계에 대한 컴포넌트 데이터 읽기
    for stepIndex in range(startStep, totalSteps + 1):
        if postkey_id == 16001 or postkey_id == 19501:
            data[f'MagB_{stepIndex}'] = readComponentData(reader, postkey_id, stepIndex,filtered_ids_set)
        elif postkey_id == 11005:
            data[f'MagA_{stepIndex}'] = readComponentData(reader, postkey_id, stepIndex,filtered_ids_set)
        # elif postkey_id == 19501:
        #     data[f'MagB_{stepIndex}'] = readComponentData(reader, postkey_id, stepIndex,filtered_ids_set)
    
    # JplotReader 닫기
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

    
    if postkey_id  == 16001:
         output_file_name = f"{load_name}_{case_name}_MagB.mat"
    elif postkey_id == 11005:
        output_file_name = f"{load_name}_{case_name}_MagA.mat"
    elif postkey_id == 19501:
        output_file_name = f"{load_name}_{case_name}_MagB.mat"
    # 결과 데이터를 .mat 파일로 저장
    sio.savemat(output_file_name, data)
    print(f"Data saved to {output_file_name}")

    
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
        id = ctypes.c_int()    # element ID
        partId = ctypes.c_int()  # part ID
        eleType = ctypes.c_int()
        x = ctypes.c_double()
        y = ctypes.c_double()
        z = ctypes.c_double()
        area = ctypes.c_double()
        JplotReader.jplotPopElementCenter(reader, id, partId, eleType, x, y, z, area)
        element_centers.append([id.value, partId.value, eleType.value, x.value, y.value, z.value, area.value])

    JplotReader.jplotEndPopElementCenter(reader)
    return element_centers


def getJmagPJTPathAndMatPath(JmagResultPath,type2Find):
    """
    주어진 JmagResultPath에서 .jproj 파일 경로 및 .mat 파일 경로 생성
    :param JmagResultPath: JMAG 시뮬레이션 결과 경로
    :return: JmagPJTPath (jproj 파일 경로), mat_file_path (mat 파일 경로)
    """
    # JmagResultName 추출
    JmagResultName = os.path.basename(JmagResultPath)  # 경로에서 파일명 추출
    
    # 확장자 ".jfiles" 이전의 경로 추출
    JmagResultDIR = re.sub(r'\.jfiles.*$', '', JmagResultPath)  # ".jfiles" 이전 부분만 추출
    
    # .jproj 파일 경로 생성
    JmagPJTDIR, JmagPJTName = os.path.split(JmagResultDIR)  # 디렉토리 및 이름 분리
    JmagPJTPath = os.path.join(JmagPJTDIR, f"{JmagPJTName}.jproj")  # .jproj 파일 경로 생성
    
    # 동일한 구조의 .mat 파일 경로 생성
    mat_file_path = os.path.join(JmagPJTDIR, f"{JmagPJTName}{type2Find}.mat")  # .mat 파일 경로 생성
    
    return JmagPJTPath, mat_file_path


def filterElementCentersByPartID(element_centers, part_ids):
    """
    요소의 element_centers에서 partID가 주어진 목록에 포함된 요소들만 필터링합니다.
    
    :param element_centers: 요소 정보가 담긴 리스트
    :param part_ids: 필터링할 partID 목록 (numpy array)
    :return: 필터링된 요소 ID 목록
    """
    filtered_ids = []
    
    for center in element_centers:
        part_id = center[1]  # center[1]이 partID를 의미함
        if part_id in part_ids:  # part_ids에 포함된 partID만 필터링
            filtered_ids.append(center[0])  # 해당 요소의 element ID 추가
            
    return filtered_ids



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



def getPartInfo(jplot_file_path):
    reader = JplotReader.jplotOpen(jplot_file_path.encode('utf-8'))
    NumPart=JplotReader.jplotCountParts(reader)
    PartStruct=[]
    for i in range(NumPart):
        index = ctypes.c_int()
        id = ctypes.c_int()
        name = ctypes.c_char_p()
        size =ctypes.c_int()
        JplotReader.jplotGetPartIdTitle(reader, index, id,  name, size)
        PartStruct.append([index.value, id.value, name.value, size.value])
    return PartStruct 


# def initialize_filtered_ids(element_centers, part_ids):
#     """
#     전역적으로 filtered_ids_set을 한 번만 정의하고 이후 재사용
#     :param element_centers: 요소 정보가 담긴 리스트
#     :param part_ids: 필터링할 partID 목록
#     """
#     global filtered_ids_set
#     if 'filtered_ids_set' not in globals() or filtered_ids_set is None:
#         # part_ids에 기반하여 element_centers를 필터링
#         filtered_ids = filterElementCentersByPartID(element_centers, part_ids)
#         filtered_ids_set = set(filtered_ids)  # set으로 변환하여 검색 최적화
#     return filtered_ids_set


def readComponentData(reader, postkey_id, step, filtered_ids_set):
    # componentReader 생성
    componentReader = JplotReader.jplotCreateComponentReader(reader, step, postkey_id)
    if componentReader is None:
        return []

    componentCount = JplotReader.jplotCountComponents(componentReader)

    component_data = []
    JplotReader.jplotStartPopComponent(componentReader)

    for i in range(componentCount):
        id = ctypes.c_int()
        values = (ctypes.c_double * 6)()
        JplotReader.jplotPopComponent(componentReader, id, values)
        # element_ids_set을 사용한 필터링
        if id.value in filtered_ids_set:
            if postkey_id == 19501:
                component_data.append([id.value, values[0], values[1], values[2], values[3], values[4], values[5]])
            else:
                component_data.append([id.value, values[0], values[1], values[2]])

    # 종료 및 삭제
    JplotReader.jplotEndPopComponent(componentReader)
    JplotReader.jplotDeleteComponentReader(componentReader)
    
    return component_data
# def readComponentData(reader, postkey_id, step, element_ids):
#     """
#     reader: JplotReader 구조체 포인터
#     postkey_id: 읽을 컴포넌트의 key ID
#     step: 데이터를 읽을 단계
#     element_ids: 필터링된 element ID 목록
#     """
    
#     # componentReader 생성
#     componentReader = JplotReader.jplotCreateComponentReader(reader, step, postkey_id)
#     if componentReader is None:
#         return []

#     # 컴포넌트 카운트 및 물리값 차원 확인
#     componentCount = JplotReader.jplotCountComponents(componentReader)
#     # physicalvalueDim = JplotReader.jplotComponentDimension(componentReader)

#     component_data = []
#     JplotReader.jplotStartPopComponent(componentReader)

#     for i in range(componentCount):
#         # 컴포넌트 데이터 가져오기
#         id = ctypes.c_int()
#         values = (ctypes.c_double * 6)()

#         # 컴포넌트 데이터 가져오기
#         JplotReader.jplotPopComponent(componentReader, id, values)

#         # 해당 id가 필터링된 element_ids에 포함되어 있는지 확인
#         if id.value in element_ids:
#             if postkey_id == 19501:
#                 component_data.append([id.value, values[0], values[1], values[2], values[3], values[4], values[5]])
#             else:
#                 component_data.append([id.value, values[0], values[1], values[2]])

#     # 종료 및 삭제
#     JplotReader.jplotEndPopComponent(componentReader)
#     JplotReader.jplotDeleteComponentReader(componentReader)
    
#     return component_data