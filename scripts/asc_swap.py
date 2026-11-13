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
vid='692c236c-3075-42f2-b5a4-350ea0994f91'; OLD='e340d690-c113-4165-9f2d-a1448323dc0b'
bs=api('GET',f'/v1/builds?filter[app]={APP}&sort=-uploadedDate&limit=3')['data']
for b in bs: L('B',b['attributes']['version'],b['attributes']['processingState'])
nb=bs[0]
if nb['attributes']['version']!='20' or nb['attributes']['processingState']!='VALID':
    L('NOT_READY'); sys.exit()
x=api('PATCH',f'/v1/reviewSubmissions/{OLD}',{'data':{'type':'reviewSubmissions','id':OLD,'attributes':{'canceled':True}}})
L('CANCEL',json.dumps((x or {}).get('data',{}).get('attributes'))[:200] if x else 'fail')
for i in range(10):
    r=api('GET',f'/v1/reviewSubmissions/{OLD}',quiet=True)
    st=r['data']['attributes']['state'] if r else '?'
    if st in ('COMPLETE','CANCELING')==False: pass
    if st=='COMPLETE': break
    time.sleep(5)
L('OLD_STATE',st)
api('PATCH',f'/v1/appStoreVersions/{vid}/relationships/build',{'data':{'type':'builds','id':nb['id']}})
rs=api('POST','/v1/reviewSubmissions',{'data':{'type':'reviewSubmissions','attributes':{'platform':'IOS'},'relationships':{'app':{'data':{'type':'apps','id':APP}}}}})
sid=rs['data']['id']
api('POST','/v1/reviewSubmissionItems',{'data':{'type':'reviewSubmissionItems','relationships':{'reviewSubmission':{'data':{'type':'reviewSubmissions','id':sid}},'appStoreVersion':{'data':{'type':'appStoreVersions','id':vid}}}}})
x=api('PATCH',f'/v1/reviewSubmissions/{sid}',{'data':{'type':'reviewSubmissions','id':sid,'attributes':{'submitted':True}}})
L('RESULT',json.dumps((x or {}).get('data',{}).get('attributes'))[:200] if x else 'fail')
v=api('GET',f'/v1/appStoreVersions/{vid}')['data']['attributes']; L('VERSION',v['appStoreState'],v['releaseType'])
