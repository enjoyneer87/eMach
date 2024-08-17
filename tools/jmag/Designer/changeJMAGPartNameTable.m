function changeJMAGPartNameTable(ConductorPartTable,app)
appView=app.View();
Model=app.GetCurrentModel;
sel=Model.CreateSelection();

  for partIndex=1:height(ConductorPartTable)

                    sel.SelectPart(ConductorPartTable.partIndex(partIndex))
                    curSel=appView.GetCurrentSelection;
                    PartName=ConductorPartTable.Name(partIndex);
                    isPart=curSel.GetPart(0);
                    isPart.SetName(PartName{:});   
                    curSel.Clear
  end
sel.Clear

end