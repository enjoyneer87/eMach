import nbformat
nb = nbformat.read(r"D:\KDH\gitEmach\eMach\mlxperPJT\pyMotorGeo_v1.ipynb", as_version=4)
print(f"Cells: {len(nb.cells)}")
print(f"Kernel: {nb.metadata.get('kernelspec',{}).get('display_name','?')}")
errs = nbformat.validate(nb)
print("nbformat valid" if errs is None else f"Errors: {errs}")
