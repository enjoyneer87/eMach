function MagnetName=setMagnetNamePerLayer(NewLayerTable,app,LayerName)
Model=app.GetCurrentModel;
appView=app.View();
MagnetName={'MagnetOuter','MagnetInner'};
LayerNumbers=height(NewLayerTable);
if nargin>2
MagnetName=LayerName;
end
    if LayerNumbers<3
        for LayerIndex=1:height(NewLayerTable)
            InnnerMagnetTable=NewLayerTable.MagnetTable{LayerIndex};
            selMagnetInner=Model.CreateSelection();
            for partIndex=1:height(InnnerMagnetTable.partIndex)
                selMagnetInner.SelectPart(InnnerMagnetTable.partIndex(partIndex))
                curSel=appView.GetCurrentSelection;
                a=curSel.GetPart(partIndex-1);
                a.SetName(MagnetName{LayerIndex});
            end
            selMagnetInner.Clear
            curSel.Clear          
        end
    elseif LayerNumbers>2
        if  LayerNumbers==length(MagnetName)
            for LayerIndex=1:height(NewLayerTable)
                InnnerMagnetTable=NewLayerTable.MagnetTable{LayerIndex};
                selMagnetInner=Model.CreateSelection();
                for partIndex=1:height(InnnerMagnetTable.partIndex)
                    selMagnetInner.SelectPart(InnnerMagnetTable.partIndex(partIndex))
                    curSel=appView.GetCurrentSelection;
                    a=curSel.GetPart(partIndex-1);
                    a.SetName(MagnetName{LayerIndex});
                end
            selMagnetInner.Clear
            curSel.Clear 
            end
        elseif length(MagnetName)<LayerNumbers
            % 입력받은 이름이 없거나 Layer테이블보다 짧으면
            % MangetName만들기
            for LayerIndex=1:height(NewLayerTable)
                MagnetName=['MangetLayer',num2str(LayerIndex)];
                InnnerMagnetTable=NewLayerTable.MagnetTable{LayerIndex};
                selMagnetInner=Model.CreateSelection();
                for partIndex=1:height(InnnerMagnetTable.partIndex)
                    selMagnetInner.SelectPart(InnnerMagnetTable.partIndex(partIndex))
                    curSel=appView.GetCurrentSelection;
                    a=curSel.GetPart(partIndex-1);
                    a.SetName(MagnetName);
                end
            selMagnetInner.Clear
            curSel.Clear 
            end
        end
    end
end


