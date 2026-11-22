import http from 'node:http'
import fs from 'node:fs'
const base=new URL(process.env.LOAD_BASE_URL||'http://127.0.0.1:8081')
const count=Number(process.env.LOAD_COUNT||500)
const agent=new http.Agent({keepAlive:true,maxSockets:600})
function request(path,body,token){return new Promise((resolve,reject)=>{const started=performance.now();const data=body===undefined?null:JSON.stringify(body);const req=http.request(new URL(path,base),{agent,method:data?'POST':'GET',headers:{...(token?{Authorization:`Bearer ${token}`} : {}),...(data?{'Content-Type':'application/json','Content-Length':Buffer.byteLength(data)}:{})}},res=>{let text='';res.on('data',b=>text+=b);res.on('end',()=>resolve({status:res.statusCode,body:text?JSON.parse(text):null,ms:performance.now()-started}))});req.setTimeout(60000,()=>req.destroy(new Error('timeout')));req.on('error',reject);if(data)req.write(data);req.end()})}
try{
 const login=await request('/api/auth/login',{username:'student',password:'Demo12345!'})
 if(login.status!==200)throw new Error('专用演示负载环境未就绪')
 const token=login.body.token
 const resources=await request('/api/instruments',undefined,token)
 const instrument=resources.body[0]
 const tomorrow=new Date(Date.now()+86400000).toLocaleDateString('en-CA',{timeZone:'Asia/Shanghai'})
 const drafts=[]
 for(let offset=0;offset<count;offset+=25){const batch=await Promise.all(Array.from({length:Math.min(25,count-offset)},()=>request('/api/reservations',{instrument_id:instrument.id,start_at:`${tomorrow}T09:00`,end_at:`${tomorrow}T10:00`,samples:1,project:'自动负载测试数据',contact:'测试联系人',settlement:'LOAD-TEST'},token)));for(const r of batch){if(r.status!==200)throw new Error(JSON.stringify(r.body));drafts.push(r.body.id)}}
 // Warm pooled connections before starting the synchronized submission burst.
 await Promise.all(drafts.map(()=>request('/api/me',undefined,token)))
 const start=performance.now();const responses=await Promise.all(drafts.map(id=>request(`/api/reservations/${id}/submit`,{},token)));const duration=performance.now()-start
 const times=responses.map(r=>r.ms).sort((a,b)=>a-b)
 const counts={};for(const r of responses){const key=r.status===200?r.body.status:`HTTP_${r.status}`;counts[key]=(counts[key]||0)+1}
 const report={timestamp:new Date().toISOString(),environment:'localhost HTTP, H2 in-memory, Java 21, no coverage agent',requests:count,counts,p95_ms:Number(times[Math.ceil(count*.95)-1].toFixed(2)),max_ms:Number(times.at(-1).toFixed(2)),elapsed_ms:Number(duration.toFixed(2)),oversold:(counts.Pending||0)>1,target_p95_ms:800}
 report.target_met=report.p95_ms<=800&&!report.oversold&&counts.Pending===1&&counts.Waitlisted===count-1
 fs.mkdirSync(new URL('../docs/test-results/',import.meta.url),{recursive:true});fs.writeFileSync(new URL('../docs/test-results/http-load.json',import.meta.url),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2))
 if(report.oversold||counts.Pending!==1||counts.Waitlisted!==count-1)process.exitCode=1
}finally{agent.destroy()}
