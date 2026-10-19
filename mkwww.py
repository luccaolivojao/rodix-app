#!/usr/bin/env python3
"""Gera www/index.html a partir do jogo (arquivo HTML cru). Uso: python3 mkwww.py caminho/do/jogo.html"""
import re, sys, os
root=os.path.dirname(os.path.abspath(__file__)); os.chdir(root)
game=open(sys.argv[1],encoding='utf-8').read()
spec=[('big-shoulders-display','Big Shoulders Display',[600,700,800,900]),('hanken-grotesk','Hanken Grotesk',[400,500,600,700]),('kaushan-script','Kaushan Script',[400])]
css=''
for pkg,fam,ws in spec:
    for w in ws:
        fn=f'{pkg}-latin-{w}-normal.woff2'; assert os.path.exists('www/fonts/'+fn),fn
        css+=f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;font-display:swap;src:url(fonts/{fn}) format('woff2')}}\n"
game=re.sub(r'<link rel="preconnect"[^>]*>\n','',game)
game=re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis[^>]*>\n','<style>'+css+'</style>\n',game)
assert 'googleapis' not in game
old=open('www/index.html',encoding='utf-8').read(); head=old[:old.index('<title>')]
open('www/index.html','w',encoding='utf-8').write(head+game+'\n</body></html>\n')
print('ok',os.path.getsize('www/index.html'))
