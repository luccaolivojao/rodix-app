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
MODE=os.environ.get('MODE','inspect')
NOTE=('Esta versao nao oferece compras dentro do app no iOS: os pacotes de Rodix Coins ficam ocultos e nao ha fluxo de compra. '
      'Os produtos de compra cadastrados nao fazem parte desta versao e nao estao enviados para analise. '
      'This version does not offer in-app purchases on iOS: Rodix Coins packs are hidden and there is no purchase flow. '
      'The In-App Purchase products are not part of this version and are not submitted for review.')
try:
    vs=api('GET',f'/v1/apps/{APP}/appStoreVersions?limit=10')
    for v in vs['data']: L('VERSION',v['id'],v['attributes']['versionString'],v['attributes']['appStoreState'])
    ver=[v for v in vs['data'] if v['attributes']['appStoreState']=='REJECTED' or v['attributes']['appVersionState']=='REJECTED'][0]; vid=ver['id']
    bs=api('GET',f'/v1/builds?filter[app]={APP}&sort=-uploadedDate&limit=5')
    for b in bs['data']: L('BUILD',b['id'],b['attributes']['version'],b['attributes']['processingState'],b['attributes']['uploadedDate'],b['attributes'].get('expired'))
    cur=api('GET',f'/v1/appStoreVersions/{vid}/build',quiet=True); L('CURRENT_BUILD',(cur or {}).get('data',{}).get('attributes',{}).get('version'))
    rs=api('GET',f'/v1/apps/{APP}/reviewSubmissions?limit=10')
    for r in rs['data']:
        its=api('GET',f'/v1/reviewSubmissions/{r["id"]}/items',quiet=True) or {'data':[]}
        L('SUBMISSION',r['id'],r['attributes']['state'],r['attributes'].get('submittedDate'),'items',[(i['id'],i['attributes'].get('state')) for i in its['data']])
    rd=api('GET',f'/v1/appStoreVersions/{vid}/appStoreReviewDetail',quiet=True)
    if rd: L('REVIEWDETAIL',rd['data']['id'],{k:(str(v)[:80] if v else v) for k,v in rd['data']['attributes'].items() if k!='demoAccountPassword'})
    if MODE=='go':
        good=[b for b in bs['data'] if b['attributes']['processingState']=='VALID' and not b['attributes'].get('expired')]
        nb=good[0]; L('USING_BUILD',nb['attributes']['version'])
        api('PATCH',f'/v1/appStoreVersions/{vid}/relationships/build',{'data':{'type':'builds','id':nb['id']}})
        if rd: api('PATCH',f'/v1/appStoreReviewDetails/{rd["data"]["id"]}',{'data':{'type':'appStoreReviewDetails','id':rd['data']['id'],'attributes':{'notes':NOTE}}})
        for r in rs['data']:
            if r['attributes']['state'] in ('UNRESOLVED_ISSUES','READY_FOR_REVIEW','WAITING_FOR_REVIEW','IN_REVIEW'):
                if r['attributes']['state']=='UNRESOLVED_ISSUES':
                    its=api('GET',f'/v1/reviewSubmissions/{r["id"]}/items',quiet=True) or {'data':[]}
                    L('RESUBMIT_EXISTING',r['id'])
                    x=api('PATCH',f'/v1/reviewSubmissions/{r["id"]}',{'data':{'type':'reviewSubmissions','id':r['id'],'attributes':{'submitted':True}}})
                    L('RESULT',json.dumps(x)[:300] if x else 'fail')
                    break
except Exception as e:
    L('EXC',repr(e))
open('/tmp/asc_log.txt','w').write('\n'.join(log)+'\nEND\n')
