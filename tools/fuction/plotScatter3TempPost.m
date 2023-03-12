function [refTempMotorcad calcTempMotorcad refTempMotorcadPost] = plotScatter3TempPost(refFile, flag, file_name)

    global phasemesh currentmesh;
    
    % Create MotorcadData object and set paths and file names
    refTempMotorcad = MotorcadData(12);
    refTempMotorcad.motorcadMotPath = 'Z:\Thesis\Optislang_Motorcad\Validation';
    refTempMotorcad.motocadLabPath = strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
    refTempMotorcad.proj_path = refTempMotorcad.motorcadMotPath;
    refTempMotorcad.file_path = refTempMotorcad.proj_path;
    refTempMotorcad.matfileFindList = what(refTempMotorcad.motocadLabPath);
    refTempMotorcad.file_name = refFile;
    refTempMotorcad.refFile = refFile;

    % Load ModelParameters_MotorLAB
    refTempMotorcad.ModelParameters_MotorLAB;
    
    % Calculate raw psi data
    refTempMotorcad = refTempMotorcad.rawPsiDataPost();
    
    % Create ResultMotorcadLabData object and set temperatures and model parameters
    % Load reference file if provided and create MotorcadData object
    if nargin > 2
        calcTempMotorcad = MotorcadData(12);
        calcTempMotorcad.motorcadMotPath = refTempMotorcad.motorcadMotPath;
        calcTempMotorcad.motocadLabPath = refTempMotorcad.motocadLabPath;
        calcTempMotorcad.proj_path = calcTempMotorcad.motorcadMotPath;
        calcTempMotorcad.file_path = calcTempMotorcad.proj_path;
        calcTempMotorcad.matfileFindList = what(calcTempMotorcad.motocadLabPath);
        calcTempMotorcad.file_name = file_name;
        calcTempMotorcad.refFile = refTempMotorcad.file_name;
        calcTempMotorcad.ModelParameters_MotorLAB;
        calcTempMotorcad = calcTempMotorcad.rawPsiDataPost();

        refTempMotorcadPost = ResultMotorcadLabData(refTempMotorcad);
        refTempMotorcadPost.postMagnet_Temperature = refTempMotorcad.Magnet_Temperature+50;
        refTempMotorcadPost.postArmatureConductor_Temperature = refTempMotorcad.ArmatureConductor_Temperature+50;
        
%             % Calculate flux ratio
%         refTempMotorcadPost.psiDTempRatio = ((calcTempMotorcad.ModelParameters_MotorLAB.PsiDModel_Lab./refTempMotorcad.ModelParameters_MotorLAB.PsiDModel_Lab)/100-1)/50;
%         refTempMotorcadPost.psiQTempRatio = ((calcTempMotorcad.ModelParameters_MotorLAB.PsiQModel_Lab./refTempMotorcad.ModelParameters_MotorLAB.PsiQModel_Lab)/100-1)/50;
        refTempMotorcadPost.psiDTempRatio = ((refTempMotorcad.ModelParameters_MotorLAB.PsiDModel_Lab./calcTempMotorcad.ModelParameters_MotorLAB.PsiDModel_Lab)/100-1)/50;
        refTempMotorcadPost.psiQTempRatio = ((refTempMotorcad.ModelParameters_MotorLAB.PsiQModel_Lab./calcTempMotorcad.ModelParameters_MotorLAB.PsiQModel_Lab)/100-1)/50;
      

        refTempMotorcadPost = refTempMotorcadPost.tempCorrectedModelParameters_MotorLAB(-0.1594);

%         1+refTempMotorcad.ModelParameters_MotorLAB.PsiDModel_Lab
%         refTempMotorcadPost.psiQTempRatio=(refTempMotorcad.ModelParameters_MotorLAB.PsiQModel_Lab/refTempMotorcad.ModelParameters_MotorLAB.PsiQModel_Lab-1)/Temp1-Tempref)
    end

%% Plot 

if flag == 0
    for i = 1:size(currentmesh, 1)
        scatter3(phasemesh(i,:)', currentmesh(i,:)', refTempMotorcad.ModelParameters_MotorLAB.PsiDModel_Lab(i,:)', ...
        'DisplayName', strcat('i=',num2str(currentmesh(i,1)),'@Temp',num2str(refTempMotorcad.Magnet_Temperature)), ...
        'Marker', 'o', 'MarkerEdgeColor', 'k');
        hold on
    end
elseif flag == 1 & nargin > 2
%     for i = 1:size(currentmesh, 1)
        figure(1)

        scatter3(reshape(phasemesh, [], 1), reshape(currentmesh, [], 1), reshape(refTempMotorcad.ModelParameters_MotorLAB.PsiDModel_Lab, [], 1), ...
            'DisplayName', strcat('@Ref Temp',num2str(refTempMotorcad.Magnet_Temperature)), ...
            'Marker', 'o', 'MarkerEdgeColor', 'k');
        hold on
        scatter3(reshape(phasemesh, [], 1), reshape(currentmesh, [], 1), reshape(calcTempMotorcad.ModelParameters_MotorLAB.PsiDModel_Lab, [], 1), ...
            'DisplayName', strcat('@Temp',num2str(calcTempMotorcad.Magnet_Temperature)), ...
            'Marker', 'x', 'MarkerEdgeColor','blue')
        hold on
        scatter3(reshape(phasemesh, [], 1), reshape(currentmesh, [], 1), reshape(refTempMotorcadPost.postModelParameters_MotorLAB.PsiDModel_Lab, [], 1), ...
            'DisplayName', strcat('PostCalc@Temp',num2str(refTempMotorcadPost.postMagnet_Temperature)), ...
            'Marker', 'hexagram', 'MarkerEdgeColor', 'r');
        legend('show')

        figure(2)
        scatter3(reshape(phasemesh, [], 1), reshape(currentmesh, [], 1), reshape(refTempMotorcad.ModelParameters_MotorLAB.PsiQModel_Lab, [], 1), ...
            'DisplayName', strcat('@Ref Temp',num2str(refTempMotorcad.Magnet_Temperature)), ...
            'Marker', 'o', 'MarkerEdgeColor', 'k');
        hold on
        scatter3(reshape(phasemesh, [], 1), reshape(currentmesh, [], 1), reshape(calcTempMotorcad.ModelParameters_MotorLAB.PsiQModel_Lab, [], 1), ...
            'DisplayName', strcat('@Temp',num2str(calcTempMotorcad.Magnet_Temperature)), ...
            'Marker', 'x', 'MarkerEdgeColor','blue')
        hold on
        scatter3(reshape(phasemesh, [], 1), reshape(currentmesh, [], 1), reshape(refTempMotorcadPost.postModelParameters_MotorLAB.PsiQModel_Lab, [], 1), ...
            'DisplayName', strcat('PostCalc@Temp',num2str(refTempMotorcadPost.postMagnet_Temperature)), ...
            'Marker', 'hexagram', 'MarkerEdgeColor', 'r');

% end
end
% colorbar  % cdata에 대한 컬러맵 출력
    legend('show')
    xlabel('Phase')
    ylabel('Current')
    zlabel('')
end