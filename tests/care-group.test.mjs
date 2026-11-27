// Run with: node --test tests/care-group.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source=fs.readFileSync(new URL('../src/index.js',import.meta.url),'utf8')
 .replace('export default {','const worker = {')
 .replace('export class Room','class Room')
 .replace('export class CareGroup','class CareGroup');
const ctx=vm.createContext({Response,Request,URL,crypto,console,Date,JSON,Map,Array,String,Number,Set});
vm.runInContext(source+';globalThis.TestCareGroup=CareGroup',ctx);
const CareGroup=ctx.TestCareGroup;
function setup(){const map=new Map();const state={storage:{get:async k=>map.get(k),put:async(k,v)=>map.set(k,structuredClone(v))}};return new CareGroup(state)}
async function call(group,path,token='',data){const r=await group.fetch(new Request('https://care.internal/'+path,{method:data?'POST':'GET',headers:{...(token?{Authorization:'Bearer '+token}:{}),...(data?{'Content-Type':'application/json'}:{})},...(data?{body:JSON.stringify(data)}:{})}));return {status:r.status,body:await r.json()}}
test('patient channels are isolated and unauthorized users denied',async()=>{
 const g=setup();const staff='staff-secret';
 assert.equal((await call(g,'init','',{name:'Test',type:'hospital',adminToken:staff})).status,200);
 const a=(await call(g,'patient',staff,{name:'A'})).body;
 const b=(await call(g,'patient',staff,{name:'B'})).body;
 assert.equal((await call(g,'state')).status,403);
 assert.equal((await call(g,'patient',a.token,{name:'C'})).status,403);
 assert.equal((await call(g,'message',a.token,{patientId:b.id,text:'A private message'})).status,200);
 assert.equal((await call(g,'message',b.token,{patientId:a.id,text:'B private message'})).status,200);
 const aView=(await call(g,'state',a.token)).body;
 const bView=(await call(g,'state',b.token)).body;
 assert.equal(aView.messages.length,1);
 assert.equal(aView.messages[0].text,'A private message');
 assert.equal(bView.messages.length,1);
 assert.equal(bView.messages[0].text,'B private message');
 assert.equal((await call(g,'status',a.token,{messageId:aView.messages[0].id,status:'completed'})).status,403);
 assert.equal((await call(g,'status',staff,{messageId:aView.messages[0].id,status:'acknowledged'})).status,200);
 assert.equal((await call(g,'message',staff,{patientId:'unknown',text:'X'})).status,403);
 assert.equal((await call(g,'state',staff)).body.messages.length,2);
});
