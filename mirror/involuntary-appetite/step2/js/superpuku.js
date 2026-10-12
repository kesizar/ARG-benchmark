(function(){
var answer=document.getElementById("answer"),sendBtn=document.getElementById("sendBtn");
var logoA="/step2/images/logo.png",logoB="/step2/images/logo2.png";
var errTxt="语言系统切换出现未知错误。为保证顺利生成，请在重新尝试后及时找出导致出错的异常文字。\n[文字化け検出中...]\n𣏌𡦈𦔌……𪚥𩀌𩠌𦧮……𡔁𩤅𨐌𩅛𩗏……\n[FATAL_ERROR: Text-to-Speech Engine crashed due to Japanese Kanji / UTF-8 Chinese simplified byte conflict at position 1048. Audio synthesis terminated abruptly.]";
var P=["嗯，我现在已经收集了大量关于这场艺术展的资料，包括展会前后的聊天记录、艺术家们的私密随笔、新闻速报以及各人的自述，现在需要解决最终的关键问题：\u201c新井是怎么死的？谁是凶手？\u201d。","我需要仔细梳理所有线索，将干扰项剥离，还原真实的死亡真相。","首先，材料里的干扰信息非常多。最显眼的就是 KAY 策划的《N07 Hoax》骗局，他极力宣称这一切只是一场虚构的\u201c参与型艺术作品\u201d，甚至声称\u201c没有受害者\u201d。但结合新闻速报的客观报道，以及宋雯祺在现场的录音可以确定：新井的死亡是实实在在发生的真实案件。死者新井的后颈部被其作品《无害穿刺》上的尖锐部件刺穿，悬挂在半空，现场一片狼藉。我必须严格区分\u201cKAY 的虚构艺术骗局\u201d与\u201c现实中的杀人犯罪\u201d。","接下来，我需要按时间线和物证来梳理现场细节：","死亡时间与现场状态：8月14日早晨，新井被发现死于自己的作品《无害穿刺》旁。死因是梯子侧滑导致他摔落，颈部撞击金属尖端致死。现场有一架侧翻的高达2米的脚手架/梯子。","现场物证矛盾（最关键的点）：梯子倒在地上。如果梯子本身固定良好，即便身体失控也可以抓住把手稳定重心，不至于直接侧翻摔死。此外，现场那盏射灯的螺丝被强力胶水注入并凝固拧死了，新井是因为在2米高空用力去拧那个被黏住的螺丝，才导致重心不稳的。","那么，谁对螺丝动了手脚？谁又导致了梯子的横滑？","我开始逐一排查各个相关人的动机与行为模式：","长谷川千景：她的随笔里表达了极强的\u201c希望展会因为意外而办不下去、好直接去旅行\u201d的摆烂与任性心态。在聊天记录中，她也确实知道新井要去调试灯光，甚至询问过\u201c踩那么高不害怕吗\u201d。但这更符合一个任性、有些自我中心、对现状不满的艺术生的随性吐槽。她既没有专业的动手准备（胶水），也没有对新井个人产生强烈的恨意。","KAY：他全心全意扑在自己的《N07 Hoax》假新闻骗局里，他的目的是利用这场混乱来完成自己的行为艺术，新井的死对他来说更像是一个意外降临的\u201c极佳素材\u201d，而非他亲自下手的目标。","宋雯祺：作为第一发现者，她的录音记录了最真实的原声现场，没有作案的时间与动机。","最后，我把目光聚焦到了柳原准身上。","从文本细节和性格剖析来看，柳原的嫌疑在层层剥离后变得无比清晰，且构成了完整的闭环：","动机极其强烈且深层：","在柳原的个人自述中，他对新井抱有极度病态的敌意。新井未经许可使用了他的音源，踩在他的雷区上；更致命的是，新井在聊天中直接撕开了柳原的伪装\u2014\u2014指责柳原对\u201c报复社会\u201d的研究只是\u201c浮于表面的剪报\u201d，这精准地刺痛了柳原作为\u201c学术精英/高级知识分子\u201d脆弱的自尊心。","新井在私下大言不详地拿他的痛点开玩笑（甚至被柳原误以为是挑衅），这种心理落差让柳原产生了偏执的报复心理。","作案手段与心理轨迹高度契合：","从新井的临终录音中，我们似乎听到他的直接死因是拧动被胶水粘死的螺丝时重心不稳发生翻倒。而柳原完全有着在大吵一架后拿胶水作案的动机与时间。这或许还能解释为\u201c头脑一热的报复行为\u201d。","但是，真的只是这样吗？ 事实上，螺丝被粘住只是诱因，梯子发生横滑才是致死的直接推手。柳原除了向螺丝钉涂抹胶水之外，一定是提前在梯子脚垫上做了手脚（如抹油或松动固定销），才能确保新井一旦失衡就必定连人带梯崩塌摔落。这更验证了他逻辑严密、心思极其缜密，处心积虑的想致新井于死地，而非单纯报复的真相。","性格与悲剧的宿命感：","柳原是一个习惯用冷酷理性掩盖内心自卑的人。他试图将这起精心策划的谋杀伪装成\u201c一时糊涂导致的不幸意外\u201d，以此在法律和道德上为自己脱罪。这种高智商犯案、事后装作受害者的伪善，完全符合他一贯的人设。","总结推理链条：","柳原准因自尊心被新井彻底践踏，产生深重恨意。他利用自己对机械和现场结构的了解，在夜间悄悄进入展厅：一是在《无害穿刺》关键射灯螺丝缝隙中注入强力胶水，二是暗中破坏了高梯的防滑固定装置。次日清晨，新井登高调试灯光，发现螺丝纹丝不动后发力猛拧，瞬间打破平衡；下方被动过手脚的梯子发生剧烈横滑，导致新井连人带梯重重摔下，后颈直接被自身作品的金属尖刺贯穿当场死亡。","真凶毫无疑问就是\u2014\u2014柳原准。","结构梳理完毕，我可以按照\u201c死亡现场异样  动机与认知偏差剥离  致命机关暗算  真相锁定柳原\u201d的逻辑框架来撰写最终的解答了。"];
var pts=[{p:1,correct:"线",wrong:"線",phrase:"梳理所有线索"},function(){return Math.random()<.5?{p:5,correct:"稳",wrong:"穏",phrase:"也可以抓住把手稳定重心"}:{p:5,correct:"强",wrong:"強",phrase:"强力胶水注入"}},{p:7,correct:"查",wrong:"査",phrase:"我开始逐一排查"},function(){return Math.random()<.5?{p:14,correct:"经",wrong:"経",phrase:"新井未经许可使用了他的音源"}:{p:12,correct:"变",wrong:"変",phrase:"变得无比清晰"}},{p:20,correct:"德",wrong:"徳",phrase:"以此在法律和道德上为自己脱罪"}];
var kn="あいうえおかきくけこさしすせそたちつてとなにぬねのハヒフヘホマミムメモラリルレロアイウエオカキクケコ";
var km={"线":"線","强":"強","变":"變","与":"與","动":"動","间":"間","现":"現","场":"場","实":"實","为":"爲","会":"會","发":"發","后":"後","将":"將","对":"對","当":"當","无":"無","体":"體","认":"認","逻":"邏","构":"構","条":"條","声":"聲","处":"處","观":"觀","关":"關","杀":"殺","层":"層","证":"證","确":"確","离":"離","结":"結","艺":"藝","这":"這","个":"個","项":"項"};
var token=0,logoTimer,activeP,pIdx,pending,output,userPausedScroll=false,touchStartY=0;
function scrollRoot(){return document.scrollingElement||document.documentElement;}
function nearBottom(gap){var r=scrollRoot();return r.scrollHeight-r.scrollTop-window.innerHeight<gap;}
function followOutput(){if(!userPausedScroll)window.scrollTo({top:scrollRoot().scrollHeight});}
window.addEventListener("wheel",function(e){if(e.deltaY<0)userPausedScroll=true;else if(nearBottom(120))userPausedScroll=false;},{passive:true});
window.addEventListener("touchstart",function(e){touchStartY=e.touches[0].clientY;},{passive:true});
window.addEventListener("touchmove",function(e){var y=e.touches[0].clientY;if(y>touchStartY)userPausedScroll=true;else if(nearBottom(120))userPausedScroll=false;touchStartY=y;},{passive:true});
function sl(ms){return new Promise(function(r){setTimeout(r,ms)});}
function ec(s){return s.replace(/[&<>]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;"}[c];});}
function toast(m){var t=document.createElement("div");t.className="spai-toast";t.textContent=m;document.body.appendChild(t);setTimeout(function(){t.remove();},2000);}
function trad(t){return Array.from(t).map(function(c){return km[c]||c;}).join("");}
function jpN(t){var g=2+Math.floor(Math.random()*3),n=0;return Array.from(trad(t)).map(function(c){if(/[\s，。：；！？、\u201c\u201d《》（）—>]/.test(c))return c;n++;if(n>=g){n=0;g=2+Math.floor(Math.random()*3);return kn[Math.floor(Math.random()*kn.length)];}return c;}).join("");}
function xform(t,i){if(!pending||pending.ok)return t;var d=i-pending.li;if(d===1||d===2)return trad(t);if(d===3||d===4)return jpN(t);return t;}
function mkPt(t,pt){var idx=t.indexOf(pt.phrase);var ti=idx>=0?t.indexOf(pt.correct,idx):t.indexOf(pt.correct);if(ti<0)return ec(t);return ec(t.slice(0,ti))+'<span class="spai-wrong" data-correct="'+pt.correct+'">'+ec(pt.wrong)+'</span>'+ec(t.slice(ti+pt.correct.length));}
function hdr(){answer.innerHTML='<div class="spai-thinking-head"><img class="spai-thinking-logo" id="tL" src="'+logoA+'"><span class="spai-thinking-text">正在思考</span></div><div class="spai-output" id="out"></div>';output=document.getElementById("out");var im=document.getElementById("tL");clearInterval(logoTimer);logoTimer=setInterval(function(){im.src=im.src.indexOf("logo2")>=0?logoA:logoB;},760);}
function done(st){var el=document.querySelector(".spai-thinking-text");if(!el)return;el.textContent="已思考（用时"+((performance.now()-st)/1000).toFixed(1)+"秒）";el.classList.add("is-done");clearInterval(logoTimer);}
async function typ(el,html,mt){el.innerHTML="";var parts=html.split(/(<span class="spai-wrong"[\s\S]*?<\/span>)/g).filter(Boolean);for(var k=0;k<parts.length;k++){if(mt!==token||(pending&&pending.ok))return;if(parts[k].startsWith("<span")){el.insertAdjacentHTML("beforeend",parts[k]);await sl(56);continue;}for(var j=0;j<parts[k].length;j++){if(mt!==token||(pending&&pending.ok))return;el.insertAdjacentHTML("beforeend",parts[k][j]==="\n"?"<br>":ec(parts[k][j]));followOutput();await sl(36);}}}
function clrAfter(r){var n=r.nextSibling;while(n){var c=n;n=n.nextSibling;c.remove();}}
function toolbar(ct){
var row=document.createElement("div");row.className="spai-icon-row";
row.innerHTML='<img class="spai-tb-icon" src="/step2/images/AI-icons/Copy.png" data-action="copy" title="复制"><img class="spai-tb-icon" src="/step2/images/AI-icons/Refresh.png" data-action="refresh" title="重新生成"><img class="spai-tb-icon" src="/step2/images/AI-icons/Thumb-Up.png" data-action="like" title="赞"><img class="spai-tb-icon" src="/step2/images/AI-icons/Thumb-Down.png" data-action="dislike" title="踩">';
ct.appendChild(row);
var dp=document.createElement("div");dp.className="spai-down-panel";dp.hidden=true;
dp.innerHTML='<div class="spai-down-title">反馈</div><div class="spai-down-options"><button type="button" data-fb="a">令人不悦</button><button type="button" data-fb="b">虚假信息</button><button type="button" data-fb="c">未遵循指令</button><button type="button" data-fb="d">没有帮助</button><button type="button" data-fb="other">其他</button></div><div class="spai-down-input" hidden><textarea placeholder="请描述问题..." rows="3"></textarea><button class="spai-down-submit" type="button" disabled>提交</button></div>';
ct.appendChild(dp);
var ls=null;
row.addEventListener("click",function(ev){var img=ev.target.closest("[data-action]");if(!img)return;var a=img.dataset.action;
if(a==="copy"){var t=Array.from(ct.querySelectorAll(".spai-line,.spai-final")).map(function(p){return p.textContent;}).join("\n\n");navigator.clipboard.writeText(t);toast("已复制到剪贴板");}
if(a==="refresh")go();
if(a==="like"){if(ls==="like"){ls=null;img.src="/step2/images/AI-icons/Thumb-Up.png";return;}ls="like";img.src="/step2/images/AI-icons/Thumb-Up-selected.png";row.querySelector("[data-action=dislike]").src="/step2/images/AI-icons/Thumb-Down.png";dp.hidden=true;toast("感谢反馈。您提交的内容将用于改进噗咚。");}
if(a==="dislike"){if(ls==="dislike"){ls=null;img.src="/step2/images/AI-icons/Thumb-Down.png";dp.hidden=true;return;}ls="dislike";img.src="/step2/images/AI-icons/Thumb-Down-selected.png";row.querySelector("[data-action=like]").src="/step2/images/AI-icons/Thumb-Up.png";dp.hidden=false;}
});
dp.addEventListener("click",function(ev){var b=ev.target.closest("[data-fb]");if(!b)return;if(b.dataset.fb==="other"){dp.querySelector(".spai-down-input").hidden=false;return;}toast("您提交的内容将用于改进噗咚。");dp.hidden=true;});
var sub=dp.querySelector(".spai-down-submit");var ta=dp.querySelector("textarea");
if(ta)ta.addEventListener("input",function(){sub.disabled=!ta.value.trim();});
if(sub)sub.addEventListener("click",function(){if(!ta.value.trim())return;toast("您提交的内容将用于改进噗咚。");dp.hidden=true;});
}
function fail(st){done(st);if(pending&&pending.el)pending.el.classList.add("expired");pending=null;var c=document.createElement("div");c.className="spai-error";c.textContent="\n"+errTxt;output.appendChild(c);toolbar(output);}
async function go(){
token++;var mt=token,st=performance.now();sendBtn.disabled=true;userPausedScroll=false;
activeP=pts.map(function(p){return typeof p==="function"?p():p;});pIdx=0;pending=null;hdr();
var i=0;while(i<P.length){
if(mt!==token)return;
var row=document.createElement("p");row.className="spai-line";output.appendChild(row);
var pt=!pending?activeP[pIdx]:null;
var text=xform(P[i],i);
if(pt&&pt.p===i){await typ(row,mkPt(text,pt),mt);var w=row.querySelector(".spai-wrong");if(w)pending={li:i,row:row,el:w,ok:false};}
else{await typ(row,ec(text),mt);}
if(pending&&pending.ok){clrAfter(pending.row);var ri=pending.li+1;pending=null;pIdx++;i=ri;await sl(260);continue;}
if(pending&&i-pending.li>=4){fail(st);return;}
i++;await sl(260);
}
clearInterval(logoTimer);await sl(3000);if(mt!==token)return;
var fin=document.createElement("p");fin.className="spai-final";output.appendChild(fin);
await typ(fin,ec("已整理完毕，逻辑检查无误。请求接入现场的监控设备......"),mt);
done(st);await sl(2000);if(mt!==token)return;
toolbar(output);
var btn=document.createElement("button");btn.className="spai-confirm";btn.type="button";btn.textContent="确认";
btn.addEventListener("click",function(){window.location.href="contemporary-onair.html";});output.appendChild(btn);
}
answer.addEventListener("click",function(e){var w=e.target.closest(".spai-wrong");if(!w||w.classList.contains("expired")||!pending)return;w.textContent=w.dataset.correct;w.classList.remove("spai-wrong");pending.ok=true;});
sendBtn.addEventListener("click",function(){go();});
})();