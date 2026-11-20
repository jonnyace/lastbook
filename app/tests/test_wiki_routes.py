"""Actual Chat card -> parse -> wiki -> load -> saved/revisited route; layout only is stubbed."""
import html.parser,json,shutil,subprocess,unittest
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[2]
NODE=shutil.which('node')
HARNESS=r'''
const fs=require('fs'), app=fs.readFileSync(process.argv[1],'utf8'), chat=fs.readFileSync(process.argv[2],'utf8');
const inputs=JSON.parse(process.argv[3]);
const esc=eval(app.split('\n').find(x=>/^const esc\s*=/.test(x)).replace('const esc =',''));
const fileUrl=x=>x,ico=x=>'',clock=x=>String(x);
let hash='#/ask';const here=()=>hash;
const parse=new Function('here',app.slice(app.indexOf('function parse()'),app.indexOf('// The sidebar row'))+';return parse;')(here);
const cards=new Function('esc','fileUrl','ico','clock','here',chat.slice(chat.indexOf('  function srcHref('),chat.indexOf('  /* markdown-lite'))+';return srcCards;')(esc,fileUrl,ico,clock,here);
const wikiCode=app.slice(app.indexOf('async function wiki('),app.indexOf('// The address an encyclopedia'));
const decodeHTML=x=>x.replaceAll('&amp;','&').replaceAll('&quot;','"').replaceAll('&#39;',"'").replaceAll('&lt;','<').replaceAll('&gt;','>');
(async()=>{
 const output=[];
 for(const article of inputs){
  hash='#/ask';let replaced=null,remembered=null,load=null,firstSaved=null,lastSaved=null;
  const titleEl={textContent:''},toolbar={textContent:''},saved={innerHTML:''};
  const frame={isConnected:false,contentDocument:null,contentWindow:null,addEventListener:(n,f)=>{if(n==='load')load=f}};
  const main={innerHTML:'',classList:{toggle(){}}};
  const $=s=>({'#wframe':frame,'#wtitle':titleEl,'#wsave':saved,'#tbTitle':toolbar,'#wopen':null}[s]);
  const saveButton=i=>{firstSaved??=i;lastSaved=i;return ''};
  const history={replaceState:(a,b,url)=>{replaced=url;hash=url}};
  const fn=new Function('setTitle','zimLabel','zimMain','main','$','backButton','saveButton','esc','IN_WINDOW','window','scrolls','current','performance','history','remember','lookOf','tidyArticle','requestAnimationFrame','setTimeout',wikiCode+';return wiki;');
  const wiki=fn(t=>{titleEl.textContent=t},x=>x,()=>Promise.resolve('/zim/demo.zim/index'),main,$,()=>'',saveButton,esc,true,{}, {},'#test',{now:()=>0},history,i=>{remembered=i},()=>{},()=>null,()=>{},()=>{});
  try{
   const row={kind:'zim',key:'S1',title:article,zim:'zim/demo.zim/'+article,path:'zim/demo.zim/'+article.split('/').map(encodeURIComponent).join('/')};
   const card=cards([row],false);hash=decodeHTML(card.match(/href="([^"]+)"/)[1]);
   const parsed=parse();await wiki(parsed.parts.slice(1).join('/'),parsed.q.get('from'),null);
   const iframe=main.innerHTML.match(/<iframe[^>]+src="([^"]+)"/)[0]+'>',framePath=decodeHTML(iframe.match(/src="([^"]+)"/)[1]);
   const own={textContent:article.replaceAll('_',' '),getBoundingClientRect:()=>({bottom:10}),style:{setProperty(){}}};
   frame.contentDocument={title:own.textContent,getElementById:()=>({}),querySelector:()=>own};frame.contentWindow={location:{pathname:framePath},scrollY:0};
   await load();const again=parse();
   output.push({article,card,iframe,title:titleEl.textContent,framePath,firstSaved,lastSaved,remembered,replaced,revisited:again.parts.slice(1).join('/'),from:again.q.get('from')});
  }catch(e){output.push({article,error:e.name+': '+e.message})}
 }
 console.log(JSON.stringify(output));
})().catch(e=>{console.error(e);process.exit(1)});
'''
class Tags(html.parser.HTMLParser):
 def __init__(self):super().__init__();self.tags=[]
 def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))
@unittest.skipUnless(NODE,'needs Node')
class WikiRoutes(unittest.TestCase):
 def test_encoded_card_reader_and_revisit(self):
  articles=['Why?','100%_Juice','X"onmouseover="review','Literal%2FName','Folder/Why?','A&B#C']
  r=subprocess.run([NODE,'-e',HARNESS,str(ROOT/'web/app.js'),str(ROOT/'web/chat.js'),json.dumps(articles)],capture_output=True,text=True,check=True)
  for row in json.loads(r.stdout):
   with self.subTest(article=row['article']):
    self.assertNotIn('error',row,row)
    a=row['article'];expected='demo.zim/'+a
    self.assertEqual(row['revisited'],expected);self.assertEqual(row['title'],a.replace('_',' '));self.assertEqual(row['from'],'#/ask')
    self.assertEqual(row['firstSaved']['href'],row['lastSaved']['href']);self.assertEqual(row['remembered']['href'],row['lastSaved']['href'])
    self.assertEqual(row['replaced'],row['lastSaved']['href']+'?from=%23%2Fask')
    self.assertEqual(unquote(row['framePath']),'/zim/'+expected)
    tags=Tags();tags.feed(row['card']+row['iframe'])
    self.assertEqual(set(next(a for n,a in tags.tags if n=='a')),{'class','href','id'})
    self.assertEqual(set(next(a for n,a in tags.tags if n=='iframe')),{'class','id','title','src'})
 def test_malformed_encodings_are_not_silently_reinterpreted(self):
  app=(ROOT/'web/app.js').read_text();parse=app[app.index('function parse()'):app.index('// The sidebar row')]
  script='const here=()=>process.argv[1];'+parse+';try{parse();process.stdout.write("accepted")}catch(e){process.stdout.write(e.name)}'
  for route in ('#/wiki/demo.zim/bad%','#/wiki/demo.zim/%GG','#/wiki/demo.zim/%C0%AF'):
   with self.subTest(route=route):
    r=subprocess.run([NODE,'-e',script,route],capture_output=True,text=True,check=True);self.assertEqual(r.stdout,'URIError')
if __name__=='__main__':unittest.main()
