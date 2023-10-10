function LabLinkFormatNameCell=defMCADLabLinkFortCell(varargin)
    LabLinkFormatNameCell = {
    'Is',
    'Current Angle',
    'Flux Linkage D',
    'Flux Linkage Q',
    'Hysteresis Iron Loss',
    'Eddy Iron Loss',
    'Excess Iron Loss',
    'Hysteresis Iron Loss (Stator)',
    'Eddy Iron Loss (Stator)',
    'Excess Iron Loss (Stator)',
    'Hysteresis Iron Loss (Rotor)',
    'Eddy Iron Loss (Rotor)',
    'Excess Iron Loss (Rotor)',
    'Hysteresis Iron Loss (Stator Back Iron)',
    'Eddy Iron Loss (Stator Back Iron)',
    'Excess Iron Loss (Stator Back Iron)',
    'Hysteresis Iron Loss (Stator Tooth)',
    'Eddy Iron Loss (Stator Tooth)',
    'Excess Iron Loss (Stator Tooth)',
    'Hysteresis Iron Loss (Rotor Back Iron)',
    'Eddy Iron Loss (Rotor Back Iron)',
    'Excess Iron Loss (Rotor Back Iron)',
    'Hysteresis Iron Loss (Rotor Pole)',
    'Eddy Iron Loss (Rotor Pole)',
    'Excess Iron Loss (Rotor Pole)',
    'Magnet Loss',
    'Banding Loss',
    'Sleeve Loss',
    'AC Copper Loss (C1)',
    % 'AC Copper Loss (C2)',    
};
  if nargin > 0
      if ~isempty(varargin{1})
          MachineData = varargin{1};
          CuboidName=  LabLinkFormatNameCell{end};
          strIndex=strfind(CuboidName, '(C');
          lastCuboidIndex=CuboidName(strIndex+2:end-1);
          lastCuboidIndex=str2double(lastCuboidIndex);
          if isfield(MachineData,'NumberOfCuboids_LossModel_Lab')
             totalCuboidNumber=MachineData.NumberOfCuboids_LossModel_Lab;
             % totalCuboidNumber=length(convertCharTypeData2ArrayData(MachineData.ACConductorLossProportion_Lab));
          else ,isnumeric(MachineData)
             totalCuboidNumber=MachineData;
          end
         for i=lastCuboidIndex+1:totalCuboidNumber
            newVariableName = ['AC Copper Loss', ' (C', num2str(i), ')'];
            LabLinkFormatNameCell{end+1} = newVariableName;
         end
      end
  end

       


% 
% MotorCADSaturationMapFormat = {
%     'Stator Current Phase Peak',
%     'Stator Current Phase RMS',
%     'Stator Current Line Peak',
%     'Stator Current Line RMS',
%     'Voltage Phase Peak',
%     'Voltage Phase RMS',
%     'Voltage Line Peak',
%     'Voltage Line RMS',
%     'Id Peak',
%     'Id RMS',
%     'Iq Peak',
%     'Iq RMS',
%     'Vd Peak',
%     'Vd RMS',
%     'Vq Peak',
%     'Vq RMS',
%     'Flux Linkage D',
%     'Flux Linkage Q',
%     'Phase Advance',
%     'Total Loss',
%     'Stator Copper Loss',
%     'Stator Copper Loss AC',
%     'Stator Copper Loss DC',
%     'Iron Loss',
%     'Iron Loss Stator',
%     'Iron Loss Stator Back Iron',
%     'Iron Loss Stator Back Iron Hysteresis',
%     'Iron Loss Stator Back Iron Hysteresis Coefficient',
%     'Iron Loss Stator Back Iron Eddy',
%     'Iron Loss Stator Back Iron Eddy Coefficient',
%     'Iron Loss Stator Tooth',
%     'Iron Loss Stator Tooth Hysteresis',
%     'Iron Loss Stator Tooth Hysteresis Coefficient',
%     'Iron Loss Stator Tooth Eddy',
%     'Iron Loss Stator Tooth Eddy Coefficient',
%     'Iron Loss Rotor',
%     'Iron Loss Rotor Back Iron',
%     'Iron Loss Rotor Back Iron Hysteresis',
%     'Iron Loss Rotor Back Iron Hysteresis Coefficient',
%     'Iron Loss Rotor Back Iron Eddy',
%     'Iron Loss Rotor Back Iron Eddy Coefficient',
%     'Iron Loss Rotor Pole',
%     'Iron Loss Rotor Pole Hysteresis',
%     'Iron Loss Rotor Pole Hysteresis Coefficient',
%     'Iron Loss Rotor Pole Eddy',
%     'Iron Loss Rotor Pole Eddy Coefficient',
%     'Iron Loss Hysteresis',
%     'Iron Loss Hysteresis Coefficient',
%     'Iron Loss Eddy',
%     'Iron Loss Eddy Coefficient',
%     'Magnet Loss',
%     'Sleeve Loss',
%     'Banding Loss',
%     'Electromagnetic Torque',
%     'Ld',
%     'Lq',
%     'PM Flux Linkage',
%     'CurrentDensityRMS'
% };
% cellArray = cellstr(SatuMapData.varStr);
% Is                                       %- Peak phase current (A)
% Current Angle                            %           - The phase advance angle in electrical degrees in the range of 0                                      -90, where 0 is fully aligned with EMF producing no reluctance torque (electrical degrees)
% Flux Linkage D                           %            - The flux linkage in the D axis averaged over the full electrical cycle (Vs)
% Flux Linkage Q                           %            - The flux linkage in the Q axis averaged over the full electrical cycle (Vs)
% Magnet Loss                              %         - The calculated losses in the magnets at a defined reference speed (W)
% Banding Loss                             %          - The calculated losses in the rotor banding at a defined reference speed (W)
% Sleeve Loss                              %         - The calculated losses in the stator sleeve at a defined reference speed (W) 
% AC Copper Loss                           %            - the total AC copper losses in the stator winding at a defined reference speed (W)
% AC Copper Loss (Cj)                      %                 - The AC copper loss in the j'th cuboid at a defined reference speed (W)
% 
% %% 
% Hysteresis Iron Loss                     %                  - The hysteresis iron loss component of the entire motor divided by the electrical frequency. (W/Hz)
% Eddy Iron Loss                           %            - The eddy current iron loss component of the entire motor divided by the square of the electrical frequency. (W/Hz2)
% Excess Iron Loss                         %              - The excess iron loss component of the entire motor divided by the electrical frequency to the power of 3/2 (W/Hz3/2)
% Hysteresis Iron Loss (Stator)            %                           - The hysteresis iron loss component of the entire stator divided by the electrical frequency. (W/Hz)
% Eddy Iron Loss (Stator)                  %                     - The eddy current iron loss component of the entire stator divided by the square of the electrical frequency. (W/Hz2)
% Excess Iron Loss (Stator)                %                       - The excess iron loss component of the entire stator divided by the electrical frequency to the power of 3/2 (W/Hz3/2)
% Hysteresis Iron Loss (Rotor)             %                          - The hysteresis iron loss component of the entire rotor divided by the electrical frequency. (W/Hz)
% Eddy Iron Loss (Rotor)                   %                    - The eddy current iron loss component of the entire rotor divided by the square of the electrical frequency. (W/Hz2)
% Excess Iron Loss (Rotor)                 %                      - The excess iron loss component of the entire rotor divided by the electrical frequency to the power of 3/2 (W/Hz3/2)
% Hysteresis Iron Loss (Stator Back Iron)  %                                     - The hysteresis iron loss component of the stator back iron divided by the electrical frequency. (W/Hz)
% Eddy Iron Loss (Stator Back Iron)        %                               - The eddy current iron loss component of the stator back iron divided by the square of the electrical frequency. (W/Hz2)
% Excess Iron Loss (Stator Back Iron)      %                                 - The excess iron loss component of the stator back iron divided by the electrical frequency to the power of 3/2 (W/Hz3/2)
% Hysteresis Iron Loss (Stator Tooth)      %                                 - The hysteresis iron loss component of the stator tooth divided by the electrical frequency. (W/Hz)
% Eddy Iron Loss (Stator Tooth)            %                           - The eddy current iron loss component of the stator tooth divided by the square of the electrical frequency. (W/Hz2)
% Excess Iron Loss (Stator Tooth)          %                             - The excess iron loss component of the stator tooth divided by the electrical frequency to the power of 3/2 (W/Hz3/2)
% Hysteresis Iron Loss (Rotor Back Iron)   %                                    - The hysteresis iron loss component of the rotor back iron divided by the electrical frequency. (W/Hz)
% Eddy Iron Loss (Rotor Back Iron)         %                              - The eddy current iron loss component of the rotor back iron divided by the square of the electrical frequency. (W/Hz2)
% Excess Iron Loss (Rotor Back Iron)       %                                - The excess iron loss component of the rotor back iron divided by the electrical frequency to the power of 3/2 (W/Hz3/2)
% Hysteresis Iron Loss (Rotor Pole)        %                               - The hysteresis iron loss component of the rotor pole divided by the electrical frequency. (W/Hz)
% Eddy Iron Loss (Rotor Pole)              %                         - The eddy current iron loss component of the rotor pole divided by the square of the electrical frequency. (W/Hz2)
% Excess Iron Loss (Rotor Pole)            %                           - The excess iron loss component of the rotor pole divided by the electrical frequency to the power of 3/2 (W/Hz3/2)
end