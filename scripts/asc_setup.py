import os,sys,time,json,csv,hashlib,base64,jwt,requests
APP='6826431094'
kid=os.environ['ASC_KEY_ID'];iss=os.environ['ASC_ISSUER_ID']
p8=base64.b64decode(os.environ['ASC_KEY_P8_BASE64']).decode()
def tok(): return jwt.encode({'iss':iss,'exp':int(time.time())+1100,'aud':'appstoreconnect-v1'},p8,algorithm='ES256',headers={'kid':kid})
B='https://api.appstoreconnect.apple.com'
log=[]
def L(*a):
    s=' '.join(str(x) for x in a);print(s,flush=True);log.append(s)
def api(m,path,body=None,ok=(200,201,204),quiet=False):
    for i in range(3):
        r=requests.request(m,B+path if path.startswith('/') else path,headers={'Authorization':'Bearer '+tok(),'Content-Type':'application/json'},data=json.dumps(body) if body is not None else None,timeout=60)
        if r.status_code in ok: return r.json() if r.content else {}
        if r.status_code>=500: time.sleep(3);continue
        break
    if not quiet: L('ERR',m,path,r.status_code,r.text[:600])
    return None
def upload(res_path,rtype,fpath,patch_path):
    data=open(fpath,'rb').read()
    # reservation passed in res
    return data
def do_upload(created,fpath,patch_path,rtype):
    data=open(fpath,'rb').read()
    ops=created['data']['attributes']['uploadOperations']
    for o in ops:
        h={x['name']:x['value'] for x in o['requestHeaders']}
        chunk=data[o['offset']:o['offset']+o['length']]
        r=requests.request(o['method'],o['url'],headers=h,data=chunk,timeout=120)
        if r.status_code>=300: L('UPLOAD ERR',r.status_code,r.text[:200]);return False
    return api('PATCH',patch_path+'/'+created['data']['id'],{'data':{'type':rtype,'id':created['data']['id'],'attributes':{'uploaded':True,'sourceFileChecksum':hashlib.md5(data).hexdigest()}}}) is not None

import traceback
sys.excepthook=lambda t,v,tb:L('EXC',''.join(traceback.format_exception(t,v,tb))[-1500:])
what=sys.argv[1] if len(sys.argv)>1 else 'all'

# ---------- Game Center ----------
if what in('all','gc'):
    gd=api('GET',f'/v1/apps/{APP}/gameCenterDetail',quiet=True)
    if not gd:
        gd=api('POST','/v1/gameCenterDetails',{'data':{'type':'gameCenterDetails','attributes':{},'relationships':{'app':{'data':{'type':'apps','id':APP}}}}})
    gid=gd['data']['id'];L('GC detail',gid)
    ex=api('GET',f'/v1/gameCenterDetails/{gid}/gameCenterAchievements?limit=200&fields[gameCenterAchievements]=vendorIdentifier')
    have={a['attributes']['vendorIdentifier']:a['id'] for a in (ex or {}).get('data',[])}
    rows=list(csv.DictReader(open('asc/ach.csv',encoding='utf-8-sig')))
    for r in rows:
        key=r['Chave'];vid='rodix.'+key
        if vid in have: aid=have[vid];L('exists',vid)
        else:
            c=api('POST','/v1/gameCenterAchievements',{'data':{'type':'gameCenterAchievements','attributes':{'referenceName':r['Nome (en)'][:60]+' ('+key+')'[:0],'vendorIdentifier':vid,'points':int(r['Pontos']),'showBeforeEarned':True,'repeatable':False},'relationships':{'gameCenterDetail':{'data':{'type':'gameCenterDetails','id':gid}}}}})
            if not c: continue
            aid=c['data']['id'];L('created',vid)
        locs=api('GET',f'/v1/gameCenterAchievements/{aid}/localizations',quiet=True) or {'data':[]}
        lh={l['attributes']['locale']:l['id'] for l in locs['data']}
        for loc,n,d in (('pt-BR',r['Nome (pt-BR)'],r['Descrição (pt-BR)']),('en-US',r['Nome (en)'],r['Descrição (en)'])):
            if loc in lh: lid=lh[loc]; continue
            lc=api('POST','/v1/gameCenterAchievementLocalizations',{'data':{'type':'gameCenterAchievementLocalizations','attributes':{'locale':loc,'name':n[:30],'beforeEarnedDescription':d[:255],'afterEarnedDescription':d[:255]},'relationships':{'gameCenterAchievement':{'data':{'type':'gameCenterAchievements','id':aid}}}}})
            if not lc: continue
            lid=lc['data']['id']
            fp='asc/icons/'+r['Arquivo do ícone']
            if loc=='en-US' or True:
                pass
            lh[loc]=lid
        # icon on first localization only needed per locale
        for loc,lid in lh.items():
            im=api('GET',f'/v1/gameCenterAchievementLocalizations/{lid}/gameCenterAchievementImage',quiet=True)
            if im and im.get('data'): continue
            fp='asc/icons/'+r['Arquivo do ícone']
            cr=api('POST','/v1/gameCenterAchievementImages',{'data':{'type':'gameCenterAchievementImages','attributes':{'fileName':os.path.basename(fp),'fileSize':os.path.getsize(fp)},'relationships':{'gameCenterAchievementLocalization':{'data':{'type':'gameCenterAchievementLocalizations','id':lid}}}}})
            if cr and do_upload(cr,fp,'/v1/gameCenterAchievementImages','gameCenterAchievementImages'): pass
    L('GC done')

# ---------- IAP ----------
PACKS=[('rodix_coins_200','Mini',200,'1.29'),('rodix_coins_900','Básico',900,'4.99'),('rodix_coins_2350','Médio',2350,'11.99'),('rodix_coins_6500','Grande',6500,'22.99'),('rodix_coins_12000','Supremo',12000,'39.99')]
if what in('all','iap'):
    ex=api('GET',f'/v1/apps/{APP}/inAppPurchasesV2?limit=200')
    have={i['attributes']['productId']:i['id'] for i in (ex or {}).get('data',[])}
    for pid,nm,coins,price in PACKS:
        cn=f'{coins:,}'.replace(',','.')
        if pid in have: iid=have[pid];L('exists',pid)
        else:
            c=api('POST','/v2/inAppPurchases',{'data':{'type':'inAppPurchases','attributes':{'name':f'{cn} Coins - Pacote {nm}','productId':pid,'inAppPurchaseType':'CONSUMABLE','reviewNote':'Consumable pack of in-game currency (Rodix Coins). Open Menu > Loja (Shop) > Pacotes de Coins.','familySharable':False},'relationships':{'app':{'data':{'type':'apps','id':APP}}}}})
            if not c: continue
            iid=c['data']['id'];L('created',pid)
        locs=api('GET',f'/v2/inAppPurchases/{iid}/inAppPurchaseLocalizations',quiet=True) or {'data':[]}
        lh={l['attributes']['locale'] for l in locs['data']}
        for loc,n,d in (('pt-BR',f'{cn} Rodix Coins',f'Pacote {nm}: {cn} Rodix Coins para usar na loja do jogo.'),('en-US',f'{cn} Rodix Coins',f'{nm} pack: {cn} Rodix Coins to spend in the in-game shop.')):
            if loc in lh: continue
            api('POST','/v1/inAppPurchaseLocalizations',{'data':{'type':'inAppPurchaseLocalizations','attributes':{'locale':loc,'name':n,'description':d[:45] if False else d},'relationships':{'inAppPurchaseV2':{'data':{'type':'inAppPurchases','id':iid}}}}})
        # price
        sch=api('GET',f'/v2/inAppPurchases/{iid}/iapPriceSchedule',quiet=True)
        if not (sch and sch.get('data')):
            pts=[];url=f'/v2/inAppPurchases/{iid}/pricePoints?filter[territory]=BRA&limit=200'
            while url:
                j=api('GET',url);
                if not j:break
                pts+=j['data'];url=j.get('links',{}).get('next')
            m=[p for p in pts if abs(float(p['attributes']['customerPrice'])-float(price))<0.001]
            if not m: L('no price point',pid,price);
            else:
                api('POST','/v1/inAppPurchasePriceSchedules',{'data':{'type':'inAppPurchasePriceSchedules','relationships':{'inAppPurchase':{'data':{'type':'inAppPurchases','id':iid}},'baseTerritory':{'data':{'type':'territories','id':'BRA'}},'manualPrices':{'data':[{'type':'inAppPurchasePrices','id':'${p1}'}]}}},'included':[{'type':'inAppPurchasePrices','id':'${p1}','attributes':{'startDate':None},'relationships':{'inAppPurchasePricePoint':{'data':{'type':'inAppPurchasePricePoints','id':m[0]['id']}}}}]})
        # availability: all territories
        av=api('GET',f'/v2/inAppPurchases/{iid}/inAppPurchaseAvailability',quiet=True)
        if not (av and av.get('data')):
            terr=[];url='/v1/territories?limit=200'
            while url:
                j=api('GET',url)
                if not j:break
                terr+=[t['id'] for t in j['data']];url=j.get('links',{}).get('next')
            api('POST','/v1/inAppPurchaseAvailabilities',{'data':{'type':'inAppPurchaseAvailabilities','attributes':{'availableInNewTerritories':True},'relationships':{'inAppPurchase':{'data':{'type':'inAppPurchases','id':iid}},'availableTerritories':{'data':[{'type':'territories','id':t} for t in terr]}}}})
        # review screenshot
        rs=api('GET',f'/v2/inAppPurchases/{iid}/appStoreReviewScreenshot',quiet=True)
        if not (rs and rs.get('data')):
            fp='asc/iap_review.png'
            cr=api('POST','/v1/inAppPurchaseAppStoreReviewScreenshots',{'data':{'type':'inAppPurchaseAppStoreReviewScreenshots','attributes':{'fileName':'shop.png','fileSize':os.path.getsize(fp)},'relationships':{'inAppPurchaseV2':{'data':{'type':'inAppPurchases','id':iid}}}}})
            if cr: do_upload(cr,fp,'/v1/inAppPurchaseAppStoreReviewScreenshots','inAppPurchaseAppStoreReviewScreenshots')
        st=api('GET',f'/v2/inAppPurchases/{iid}?fields[inAppPurchases]=state',quiet=True)
        L(pid,'state',st and st['data']['attributes']['state'])
    L('IAP done')

