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
VS='1.1'
WN='Novas seleções (Indonésia e mais 15 países), personalização de cabelo e notícias com jornais e capas de hat-trick. Melhorias gerais.'
vs=api('GET',f'/v1/apps/{APP}/appStoreVersions?limit=10')['data']
for v in vs: L('V',v['id'],v['attributes']['versionString'],v['attributes']['appStoreState'])
cur=next((v for v in vs if v['attributes']['versionString']==VS),None)
live=next((v for v in vs if v['attributes']['appStoreState']=='READY_FOR_SALE'),None)
bs=api('GET',f'/v1/builds?filter[app]={APP}&sort=-uploadedDate&limit=5')['data']
for b in bs: L('B',b['id'],b['attributes']['version'],b['attributes']['processingState'],b['attributes'].get('usesNonExemptEncryption'))
if MODE=='go':
    if not cur:
        cur=api('POST','/v1/appStoreVersions',{'data':{'type':'appStoreVersions','attributes':{'platform':'IOS','versionString':VS,'releaseType':'MANUAL'},'relationships':{'app':{'data':{'type':'apps','id':APP}}}}})['data']
    vid=cur['id']; L('USING_VERSION',vid)
    good=[b for b in bs if b['attributes']['processingState']=='VALID' and not b['attributes'].get('expired')]
    nb=good[0]; L('USING_BUILD',nb['attributes']['version'])
    if nb['attributes'].get('usesNonExemptEncryption') is None:
        api('PATCH',f'/v1/builds/{nb["id"]}',{'data':{'type':'builds','id':nb['id'],'attributes':{'usesNonExemptEncryption':False}}})
    api('PATCH',f'/v1/appStoreVersions/{vid}/relationships/build',{'data':{'type':'builds','id':nb['id']}})
    ls=api('GET',f'/v1/appStoreVersions/{vid}/appStoreVersionLocalizations')['data']
    for l in ls:
        api('PATCH',f'/v1/appStoreVersionLocalizations/{l["id"]}',{'data':{'type':'appStoreVersionLocalizations','id':l['id'],'attributes':{'whatsNew':WN}}})
        L('WHATSNEW',l['attributes']['locale'])
    rd=api('GET',f'/v1/appStoreVersions/{vid}/appStoreReviewDetail',quiet=True)
    L('REVIEWDETAIL',bool(rd and rd.get('data')))
    rs=api('POST','/v1/reviewSubmissions',{'data':{'type':'reviewSubmissions','attributes':{'platform':'IOS'},'relationships':{'app':{'data':{'type':'apps','id':APP}}}}})
    sid=rs['data']['id']
    api('POST','/v1/reviewSubmissionItems',{'data':{'type':'reviewSubmissionItems','relationships':{'reviewSubmission':{'data':{'type':'reviewSubmissions','id':sid}},'appStoreVersion':{'data':{'type':'appStoreVersions','id':vid}}}}})
    x=api('PATCH',f'/v1/reviewSubmissions/{sid}',{'data':{'type':'reviewSubmissions','id':sid,'attributes':{'submitted':True}}})
    L('RESULT',json.dumps(x)[:300] if x else 'fail')
