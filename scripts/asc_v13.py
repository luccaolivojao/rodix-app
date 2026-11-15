import os,sys,time,json,csv,hashlib,base64,jwt,requests
APP='6826431094'
kid=os.environ['ASC_KEY_ID'];iss=os.environ['ASC_ISSUER_ID']
raw=os.environ['ASC_KEY_P8_BASE64']
if 'BEGIN' in raw: p8=raw
else:
    d=base64.b64decode(raw)
    if b'BEGIN' in d: p8=d.decode()
    else:
        b=base64.b64encode(d).decode(); p8='-----BEGIN PRIVATE KEY-----\n'+'\n'.join(b[i:i+64] for i in range(0,len(b),64))+'\n-----END PRIVATE KEY-----\n'
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
    if not quiet: L('ERR',m,path,r.status_code,' '.join(r.text.split())[:350])
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
    return api('PATCH',patch_path+'/'+created['data']['id'],{'data':{'type':rtype,'id':created['data']['id'],'attributes':({'uploaded':True} if rtype=='gameCenterAchievementImages' else {'uploaded':True,'sourceFileChecksum':hashlib.md5(data).hexdigest()})}}) is not None


import traceback
sys.excepthook=lambda t,v,tb:L('EXC',''.join(traceback.format_exception(t,v,tb))[-1500:])
MODE=os.environ.get('MODE','inspect')
VS='1.3'; MINB=25
WN='Árbitros novos em campo, com três uniformes (amarelo, verde e rosa) e um visual diferente a cada partida. Torcida nas arquibancadas e atrás dos gols. Modo Técnico: comande um clube, escale o time direto no campo, cuide das transferências e da diretoria. Pedidos de autógrafo bem menos frequentes. Rodix Social com imagens novas e mais textos traduzidos.'
vs=api('GET',f'/v1/apps/{APP}/appStoreVersions?limit=10')['data']
for v in vs: L('V',v['id'],v['attributes']['versionString'],v['attributes']['appStoreState'],v['attributes'].get('releaseType'))
cur=next((v for v in vs if v['attributes']['versionString']==VS),None)
bs=api('GET',f'/v1/builds?filter[app]={APP}&sort=-uploadedDate&limit=5')['data']
for b in bs: L('B',b['id'],b['attributes']['version'],b['attributes']['processingState'],b['attributes'].get('usesNonExemptEncryption'))
subs=api('GET',f'/v1/apps/{APP}/reviewSubmissions?limit=10')['data']
for s in subs: L('S',s['id'],s['attributes']['state'])
if MODE=='go':
    good=[b for b in bs if b['attributes']['processingState']=='VALID' and not b['attributes'].get('expired') and int(b['attributes']['version'])>=MINB]
    if not good: L('NOT_READY'); sys.exit()
    nb=good[0]; L('USING_BUILD',nb['attributes']['version'])
    for sb in subs:
        if sb['attributes']['state'] in ('WAITING_FOR_REVIEW','UNRESOLVED_ISSUES'):
            api('PATCH',f"/v1/reviewSubmissions/{sb['id']}",{'data':{'type':'reviewSubmissions','id':sb['id'],'attributes':{'canceled':True}}}); L('CANCELED',sb['id'])
            for _ in range(20):
                time.sleep(6); st=api('GET',f"/v1/reviewSubmissions/{sb['id']}")['data']['attributes']['state']
                if st not in ('WAITING_FOR_REVIEW','CANCELING'): break
            L('SUB_STATE',st)
    subs=api('GET',f'/v1/apps/{APP}/reviewSubmissions?limit=10')['data']
    if not cur:
        cur=api('POST','/v1/appStoreVersions',{'data':{'type':'appStoreVersions','attributes':{'platform':'IOS','versionString':VS,'releaseType':'AFTER_APPROVAL'},'relationships':{'app':{'data':{'type':'apps','id':APP}}}}})['data']
    vid=cur['id']; L('USING_VERSION',vid)
    if nb['attributes'].get('usesNonExemptEncryption') is None:
        api('PATCH',f'/v1/builds/{nb["id"]}',{'data':{'type':'builds','id':nb['id'],'attributes':{'usesNonExemptEncryption':False}}})
    api('PATCH',f'/v1/appStoreVersions/{vid}/relationships/build',{'data':{'type':'builds','id':nb['id']}})
    api('PATCH',f'/v1/appStoreVersions/{vid}',{'data':{'type':'appStoreVersions','id':vid,'attributes':{'releaseType':'AFTER_APPROVAL'}}})
    ls=api('GET',f'/v1/appStoreVersions/{vid}/appStoreVersionLocalizations')['data']
    for l in ls:
        api('PATCH',f'/v1/appStoreVersionLocalizations/{l["id"]}',{'data':{'type':'appStoreVersionLocalizations','id':l['id'],'attributes':{'whatsNew':WN}}})
        L('WHATSNEW',l['attributes']['locale'])
    op=next((s for s in subs if s['attributes']['state']=='READY_FOR_REVIEW'),None)
    if op: sid=op['id']; L('REUSE_SUB',sid)
    else: sid=api('POST','/v1/reviewSubmissions',{'data':{'type':'reviewSubmissions','attributes':{'platform':'IOS'},'relationships':{'app':{'data':{'type':'apps','id':APP}}}}})['data']['id']
    it=api('POST','/v1/reviewSubmissionItems',{'data':{'type':'reviewSubmissionItems','relationships':{'reviewSubmission':{'data':{'type':'reviewSubmissions','id':sid}},'appStoreVersion':{'data':{'type':'appStoreVersions','id':vid}}}}})
    L('ITEM','ok' if it else 'fail')
    x=api('PATCH',f'/v1/reviewSubmissions/{sid}',{'data':{'type':'reviewSubmissions','id':sid,'attributes':{'submitted':True}}})
    L('RESULT',json.dumps((x or {}).get('data',{}).get('attributes'))[:300] if x else 'fail')
    v=api('GET',f'/v1/appStoreVersions/{vid}')['data']['attributes']; L('VERSION',v['versionString'],v['appStoreState'],v['releaseType'])
