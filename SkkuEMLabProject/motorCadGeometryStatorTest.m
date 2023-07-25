% motorCadGeometryStatorTest - Test script for motorCadGeometryStator class
classdef motorCadGeometryStatorTest < matlab.unittest.TestCase

    properties
        statorObj
    end

    methods (TestMethodSetup)
        function createMotorcadGeometryStatorObject(testCase)
            % Define the input parameters
            pStatorSlots = 24;
            iStatorOD = 100;
            iSlotCornerRadius = 5;
            pToothTipDepth = 10;
            pToothTipAngle = 30;
            iActiveLength = 200;
            iSplitRatio = 0.4;
            iDepthSlotRatio = 0.5;
            pMinThicknessBackIron = 5;
            iYtoT = 0.2;
            iSlotOpRatio = 0.7;

            % Create an instance of motorCadGeometryStator
            testCase.statorObj = motorCadGeometryStator(pStatorSlots, iStatorOD, iSlotCornerRadius, pToothTipDepth, pToothTipAngle, iActiveLength, iSplitRatio, iDepthSlotRatio, pMinThicknessBackIron, iYtoT, iSlotOpRatio);
        end
    end

    methods (Test)
        function testProperties(testCase)
            % Test the properties of the statorObj
            testCase.verifyEqual(testCase.statorObj.slotNumber, 24);
            testCase.verifyEqual(testCase.statorObj.housingDia, 140);
            testCase.verifyEqual(testCase.statorObj.statorLamDia, 100);
            testCase.verifyEqual(testCase.statorObj.slotCornerRadius, 5);
            testCase.verifyEqual(testCase.statorObj.toothTipDepth, 10);
            testCase.verifyEqual(testCase.statorObj.toothTipAngle, 30);
            testCase.verifyEqual(testCase.statorObj.activeVolume, 1.4e-4, 'AbsTol', 1e-6);
            testCase.verifyEqual(testCase.statorObj.ratioBore, 0.4);
            testCase.verifyEqual(testCase.statorObj.ratioSlotDepthParallelTooth, 0.5);
            testCase.verifyEqual(testCase.statorObj.minBackIronThickness, 5);
            testCase.verifyEqual(testCase.statorObj.ratioToothWidth, 0.0112, 'AbsTol', 1e-6);
            testCase.verifyEqual(testCase.statorObj.ratioSlotOpeningParallelTooth, 0.7);
        end
    end
end
