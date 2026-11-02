const fs=require('fs'),vm=require('vm');
const s=fs.readFileSync('tasks/huaixia-qiri/original.html','utf8');
const a=s.indexOf('ge={rules:{name:');const b=s.indexOf(',ie={mom:',a);
if(a<0||b<0)throw Error('deduction bounds missing');
const [clues,defs]=vm.runInNewContext(`(()=>{const ${s.slice(a,b)};return [ge,En]})()`,Object.create(null));
const ids=Object.keys(clues).sort(), results={};
for(const ng of [1,2]){
 const accepted=[],rejected=[];
 for(let i=0;i<ids.length;i++)for(let j=i+1;j<ids.length;j++)for(let k=j+1;k<ids.length;k++){
  const subset=[ids[i],ids[j],ids[k]];
  const found=defs.find(d=>!(d.cond?.ng&&ng<d.cond.ng)&&d.requires.slice().sort().join('|')===subset.join('|'));
  (found?accepted:rejected).push(found?{clues:subset,id:found.id}:subset);
 }
 results[ng]={accepted,rejected_count:rejected.length,total:accepted.length+rejected.length};
}
if(results[1].accepted.length!==3||results[2].accepted.length!==4)throw Error('unexpected deduction count');
fs.writeFileSync('runs/huaixia-qiri/deduction-exhaustive.json',JSON.stringify({clue_ids:ids,results,scope:'Enumerates exact-set comparison from source for unsolved deductions; not UI execution or reachability of each clue combination.'},null,2));
console.log(JSON.stringify({clues:ids.length,first:results[1],second:results[2]}));
