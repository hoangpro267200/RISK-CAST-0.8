import os
skip={'node_modules','venv','dist','.git','__pycache__','.cursor','terminals'}
exts={'.png','.jpg','.jpeg','.gif','.svg','.ico','.woff','.woff2','.ttf','.otf','.wasm','.map','.mp4','.mov','.zip','.json','lock'}
total=0
for dp,dns,fns in os.walk('.'):
    dns[:] = [d for d in dns if d not in skip and not d.startswith('.') ]
    for f in fns:
        if any(f.endswith(e) for e in exts):
            continue
        p=os.path.join(dp,f)
        try:
            with open(p,'rb') as fh:
                total += sum(1 for _ in fh)
        except Exception:
            pass
print(total)
