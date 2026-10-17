#!/usr/bin/env python3
"""Gera www/ a partir do jogo atual (../scpc/soccer-champs.html), com fontes locais."""
import re, shutil, os, subprocess, sys
root=os.path.dirname(os.path.abspath(__file__)); os.chdir(root)
subprocess.run(['sh','build.sh'],cwd='../scpc',check=True,stdout=subprocess.DEVNULL)
game=open('../scpc/soccer-champs.html',encoding='utf-8').read()
shutil.rmtree('www/fonts',ignore_errors=True); os.makedirs('www/fonts')
spec=[('big-shoulders-display','Big Shoulders Display',[600,700,800,900]),('hanken-grotesk','Hanken Grotesk',[400,500,600,700]),('kaushan-script','Kaushan Script',[400])]
css=''
for pkg,fam,ws in spec:
    for w in ws:
        fn=f'{pkg}-latin-{w}-normal.woff2'
        shutil.copy(f'node_modules/@fontsource/{pkg}/files/{fn}',f'www/fonts/{fn}')
        css+=f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;font-display:swap;src:url(fonts/{fn}) format('woff2')}}\n"
game=re.sub(r'<link rel="preconnect"[^>]*>\n','',game)
game=re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis[^>]*>\n','<style>'+css+'</style>\n',game)
assert 'googleapis' not in game
head='<!doctype html>\n<html lang="en"><head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">\n<meta name="theme-color" content="#070d1a">\n<meta name="mobile-web-app-capable" content="yes">\n<meta name="apple-mobile-web-app-capable" content="yes">\n'
open('www/index.html','w',encoding='utf-8').write(head+game+'\n</body></html>\n')
print('ok',os.path.getsize('www/index.html'))
