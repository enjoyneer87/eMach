"""AF 보정 커스텀 손실 주입 → SC 'Calibrated' 효율맵 생성.

Lab48(hybrid) 사본에 Internal Custom Loss
  Stator_Copper_Loss_AC × (AF_traj(Speed) − 1)   [Electrical]
를 등록하고 동일 설정으로 Lab 효율맵을 계산한다.
AF_traj = 효율맵 궤적의 P_AC 가중 AF(speed) 5차 다항 (pipeline 예측 기반,
fit RMSE 0.047; fig15 3자 비교의 세 번째 맵).
"""
from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_MOT = r'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_Lab48.mot'
WORK_MOT = (r'D:\KangDH\Thesis\e10\SLFEA'
            r'\e10Turn6V261SLFEA_Lab48_customLoss.mot')
FORMULA_TXT = (HERE / 'map_exports' / 'e10' / 'SC'
               / 'AF_traj_poly5_formula.txt')
OUT_MAT = (HERE / 'map_exports' / 'e10' / 'effmaps'
           / 'MotorLAB_elecdata_SC_calibrated.mat')
LOSS_NAME = 'AF_traj_SC'


def main() -> None:
    import time

    import ansys.motorcad.core as pymotorcad

    formula = FORMULA_TXT.read_text(encoding='utf-8').strip()
    print(f'formula ({len(formula)} chars):\n{formula}')

    shutil.copyfile(SRC_MOT, WORK_MOT)
    print('work mot:', WORK_MOT)

    # 병렬 배치가 CPU를 점유하면 기동 핸드셰이크가 타임아웃될 수 있어 재시도
    mc = None
    for attempt in range(3):
        try:
            mc = pymotorcad.MotorCAD(enable_success_variable=False)
            break
        except Exception as exc:
            print(f'[retry {attempt + 1}/3] launch failed: {exc}',
                  flush=True)
            time.sleep(60)
    if mc is None:
        raise RuntimeError('Motor-CAD launch failed after retries')
    try:
        mc.set_variable('MessageDisplayState', 2)
        mc.load_from_file(WORK_MOT)
        assert mc.get_model_built_lab(), 'Lab model not built'

        mc.set_motorlab_context()
        # 허용 변수 확인 (Speed / Stator_Copper_Loss_AC 포함 여부)
        try:
            allowed = str(mc.get_variable('CustomLossVariablesInternal_Lab'))
            for v in ('Speed', 'Stator_Copper_Loss_AC'):
                print(f'  allowed[{v}] = {v in allowed}')
        except Exception as exc:
            print('  [warn] allowed-vars read:', exc)

        # pymotorcad 래퍼는 thermal_node=-1(미지정)을 거부하므로
        # +mcad/addLabInternalCustomLoss.m과 동일하게 원시 배열 변수로 등록
        num = int(mc.get_variable('NumCustomLossesInternal_Lab'))
        idx = num
        for i in range(num):
            nm = str(mc.get_array_variable(
                'CustomLoss_Name_Internal_Lab', i)).strip()
            if nm.lower() == LOSS_NAME.lower():
                idx = i
                print(f'replacing existing custom loss at index {i}')
                break
        if idx == num:
            mc.set_variable('NumCustomLossesInternal_Lab', num + 1)
        mc.set_array_variable('CustomLoss_Name_Internal_Lab', idx,
                              LOSS_NAME)
        mc.set_array_variable('CustomLoss_Function_Internal_Lab', idx,
                              formula)
        mc.set_array_variable('CustomLoss_Type_Internal_Lab', idx,
                              'Electrical')
        mc.set_array_variable('CustomLoss_ThermalNode_Internal_Lab', idx,
                              -1)
        rb = str(mc.get_array_variable('CustomLoss_Function_Internal_Lab',
                                       idx))
        print(f'custom loss registered idx={idx}, readback '
              f'{len(rb)} chars, match={rb.strip() == formula}')

        # 효율맵 설정 (run_lab_effmaps_fig15.py와 동일)
        mc.set_variable('EmagneticCalcType_Lab', 1)
        mc.set_variable('SpeedMin_MotorLAB', 0)
        mc.set_variable('SpeedMax_MotorLAB', 16000)
        mc.set_variable('Speedinc_MotorLAB', 500)
        mc.set_variable('CurrentSpec_MotorLAB', 1)
        mc.set_variable('Imax_RMS_MotorLAB', 920)
        mc.set_variable('Imin_MotorLAB', 0)

        print('calculating calibrated efficiency map ...', flush=True)
        mc.calculate_magnetic_lab()
        res = Path(str(mc.get_variable('ResultsPath_MotorLAB')).strip())
        src = res / 'MotorLAB_elecdata.mat'
        assert src.exists(), f'no elecdata: {src}'
        OUT_MAT.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, OUT_MAT)
        print('saved:', OUT_MAT)
        mc.save_to_file(WORK_MOT)
    finally:
        try:
            mc.quit()
        except Exception:
            pass
    print('done')


if __name__ == '__main__':
    main()
