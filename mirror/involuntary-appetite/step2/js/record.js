(function(){
var recordMenu=document.getElementById("recordMenu");
var recordSidebar=document.getElementById("recordSidebar");
var recordSidebarToggle=document.getElementById("recordSidebarToggle");
var speakerTools=document.getElementById("speakerTools");
var transcript=document.getElementById("recordTranscript");
var params=new URLSearchParams(window.location.search);
function normalizeRecordKeyword(value){
var map={"無害穿刺":"无害穿刺","特價清倉":"特价清仓","淺野慧":"浅野慧","錄音":"录音","便籤":"便签","便簽":"便签","吉祥物製作":"吉祥物制作","長谷川千景":"长谷川千景","柳原準":"柳原准"};
return map[value]||value;
}
var keyword=normalizeRecordKeyword(params.get("keyword")||"");
var storageKey="pukuRecordDiscoveredKeywordsV2";
var speakerStorageKey="pukuRecordSpeakers:"+keyword;
var speakerSavedKey="pukuRecordSpeakersSaved:"+keyword;
var artists=["宋雯祺","新井拓也","KAY","长谷川千景","柳原准"];
var activeSpeakers=[];
var draftSpeakers={};
var isEditing=false;
var feedbackTimer=null;
var records={
永田町:{title:"永田町",isArticle:true,content:'永田町站位于日本东京都千代田区，是东京地下铁重要的枢纽车站之一。<br><br>本次艺术展的举办地Gallery CROP就位于离永田町站步行2分钟的地方，交通便利。<br><br>如果您需要规划具体的来场路线，可以参照<a href="/step2/tokyometro-202305-number-cn.pdf" target="_blank" rel="noopener">官方运行线路图</a>。'},
无害穿刺:{title:"会议记录",time:"2026-08-01 15:38:27-15:42:43",paragraphs:[["A","……好嘞，我来详细介绍下《无害穿刺》。正如之前多次提到，这件装置的核心是用粗铁丝网、废旧电缆等工业废料缠绕成的物体，悬挂在展区的半空中。最关键的设计在于光影——我会精确计算天花板的光源，使观众走到最佳观赏区时，展品的阴影会拉长，像一根尖刺般直指他们的头部。我想借此把消费社会的'侵入感'具象化——我们看似出于自愿的行为，实则只是对信息垃圾的被动应允。"],["B","听起来很有冲击力和深度。不过你评估过现场的安全隐患吗？把一大块废铁挂在空中，会不会有掉落或者划伤人的风险？"],["A","芬奇老师放心，安全措施我是做足了的。悬挂部分我会用三根工业级的双绞钢丝绳固定，承重系数绝对超标；外围的铁丝网和废电缆看起来很硬，其实都经过了打磨和固化。底部观众能够伸手碰到的位置还会再贴上一圈黑胶带，不会有物理上的危险。"],["C","我插一句……物理上安全，但这个装置给人的观感还是太暴力了。会不会让人感到不舒服，甚至因为害怕而不敢走近作品？"],["D","我觉得很有意思诶。跟《非自愿摄入》的立意很搭，而且大家的作品有温和、有激进，才能让展会变得更加丰富多彩嘛。虽然我的作品也挺激进，哈哈哈。"],["A","KAY很懂嘛~前辈，我们还是同一所学校的呢，就不能向着学弟一点吗。要多试着理解不同的思维，眼界才能更开阔哦。"],["C","……哦。"]]},
特价清仓:{title:"会议记录",time:"2026-08-07 12:15:33-12:19:01",paragraphs:[["A","……大家最终选了我的《特价清仓》作为这次艺术展的主视觉海报，我一直很感激。我再简单介绍一下这件作品：它整体看起来就是一个放大了的超市打折便当，里面放一个蜷缩着的硅胶假人，还有其他象征人生重要阶段的道具，比如毕业证、婚戒等等。我觉得\u201c非自愿摄入\u201d的尽头，就是意识到自己也是一件商品。"],["B","诶，既然说到这个份上，用假人来呈现是不是冲击力还不够？干脆直接用真人模特怎么样？"],["C","如果想用真人的话，单纯蜷在作品里一动不动感觉挺无聊的。最好还是增加一些互动比较好。"],["D","说起来，长谷川，你之前说最喜欢的那个行为艺术装置叫什么名字来着？"],["C","This is so contemporary!"],["D","对对，是这个。当时你说它是个有好多真人表演的装置，不知道能不能给KAY提供点灵感。"],["C","嗯~但是那个全靠一群人突然开始唱“Oh! This is so contemporary~”来实现，连个实体展品都没有。我是觉得很莫名其妙所以才喜欢啦，但可能不适合这次的主题。"],["A","既然是商品，我希望它是死掉的、失去灵魂的。当然鲜活的事物也能成为商品，但我还是觉得\u201c死寂\u201d更适合这一层属性......其实，我已经想到了更有趣、更冲击的<span class='record-replace-word is-original' data-swap-word='\u5c38\u4f53' data-replace-word='\u80a2\u4f53'>\u5c38\u4f53</span><b>\u6a21\u7279</b>方案……"],["E","等等，各位天才，打住一下。我们只是一个小型独立展，用真人模特有点太夸张了吧？<br>……好了好了，你要是能用方案说服我，也不是不能考虑。"],["D","……真好搞定啊。"]]},
浅野慧:{title:"会议记录",time:"2026-08-01 15:30:03-15:31:59",paragraphs:[["A","……我想说的就是这些，我全名是浅野慧，不过大家叫我KAY就好。请多关照！<br>对了，既然把搭建展会官网的工作交给我，那我提议在官网做一个智能检索的Chatbot。如果大家有兴趣，后续甚至可以由我来做接口调试，把它培养成一个真正的AI。"],["B","那如果要做的话，干脆把它包装成一个美术展的官方吉祥物好了？具体的形象我可以来画，我还挺喜欢这种工作的。"],["A","好啊好啊，你是叫……长谷川对吧？感谢你愿意帮忙。"],["C","嗯，我也觉得挺好。那我们又多了个\u201c吉祥物制作\u201d的议题，晚点再讨论吧。"],["D","不过我觉得，设计得太纯粹可爱就没意思了。我觉得可以弄得表面上萌萌的、人畜无害，但只要触发了某些关键词就会突然变脸。刚才我也提过我那个装置——观众只有站对了角度，才会猛然发现自己其实早就被\u201c噗嗤\u201d地一声刺穿了，这种反差才符合……"],["C","行了，别在这儿自夸了。还没轮到你自我介绍，就已经绕着弯说了好几次你那件《无害穿刺》了。"],["D","嘿嘿，多说几次还是有用的嘛。您这不是已经记住了？"],["A","没事，我也是突然想到才补充了一个提议。我的部分说完了，换下一位吧。"]]},
录音:{title:"录音",isLocked:true,lockText:"欢迎回家。告诉我面包上的信息",sections:[{time:"2026-08-12 22:34:01-22:36:47",paragraphs:[["A","……怎么直接约在展厅这里？虽然是晚上，但这毕竟是公共场所。"],["B","放心吧芬奇老师，我亲眼看到他们两个走人的。门我也锁上了，安全得很。"],["C","好了，赶紧介绍一下你的计划。上次开会时你说什么\u201c尸体模特\u201d，可真敢说啊。连我也都吓了一跳。我太感兴趣了，快讲讲怎么回事。"],["B","嘿嘿，因为只有这样才够冲击啊。为了完美实现我的艺术……我需要一具真正的\u201c尸体\u201d。"],["C","哇哦……"],["A","什么？你认真的吗？！"],["A","我绝对不能参与。这种出格的事我不能沾边。我要先走了，你们两个自己看着办。"],["","......"],["","......"],["","......"]]},{time:"2026-08-12 22:37:15-22:41:30",isDark:true,warning:"警告：无法解析以下内容，请自行承担阅览风险。",paragraphs:[["？？？1","碍事的终于走了。"],["？？？2","你要做什么？为什么把灯关了？"],["？？？1","......"],["？？？2","你手里拿的是...你疯了？！你现在……是认真的吗？"],["？？？1","我一直都是认真的呀。"],["？？？2","你真的疯了！就，就为了什么艺术追求，你要搭上一条人命？你到底有没有正常的价值观？！"],["？？？1","我有啊，我一直有。我遵守规则，我<a href='breadcrumbs.html' class='record-breadcrumb-link' target='_blank' rel='noopener'>上学</a>、<a href='breadcrumbs.html' class='record-breadcrumb-link' target='_blank' rel='noopener'>打工</a>、<a href='breadcrumbs.html' class='record-breadcrumb-link' target='_blank' rel='noopener'>礼貌</a>、<a href='breadcrumbs.html' class='record-breadcrumb-link' target='_blank' rel='noopener'>忍耐</a>。我按照社会希望看到的样子活着。<br>可社会是怎么对待我的？"],["？？？2","这……这种事很正常，每个人都会经历——"],["？？？1","我当然知道。所以我才忍气吞声、逆来顺受了这么久。<br>但是够了，我已经下定决心了。既然社会是正常的，那我就接受自己的不正常。"],["？？？2","可这跟我有什么关系！为什么是我？！就算整个世界都亏欠了你，就算你要走极端，又不是我的错！"],["？？？1","没有。你是无辜的。<br>可我要报复的，是整个社会。你只是很不幸，成了集体意志的一个代言人罢了。"],["？？？2","……你是疯子！你是反社会人格。"],["？？？1","也许吧。"],["？？？2","——所以我很高兴。"],["？？？1","……什么？"],["？？？2","我说，我很高兴。<br>因为这说明，我们是同类。"],["","......"],["","......"],["","......"]]},{time:"2026-08-12 22:44:44-22:45:29",isDark:true,paragraphs:[["？？？2","难得遇到这么志同道合的人，却不得不反目，还真是悲哀啊。"],["？？？2","也许这就是\u201c疯子\u201d的宿命吧。"],["？？？2","想要无差别地袭击别人，就要做好随时被别人袭击的准备。"],["？？？2","不过...我对你的艺术追求很有共鸣。你的愿望，就由我来代你实现吧。"],["？？？2","寻木乃伊者反成木乃伊……多美的音律啊。"]]}]},
便签:{title:"便签",isArticle:true,content:'<div class="record-memo-list"><img src="/step2/images/memo1.jpg" alt="便签 1"><img src="/step2/images/memo1-translated.jpg" alt="便签 1 翻译"><img src="/step2/images/memo2.jpg" alt="便签 2"><img src="/step2/images/memo2-translated.jpg" alt="便签 2 翻译"><img src="/step2/images/memo3.jpg" alt="便签 3"><img src="/step2/images/memo3-translated.jpg" alt="便签 3 翻译"></div>'},
吉祥物制作:{title:"会议记录",sections:[{time:"2026-08-01 17:12:27-17:13:14",paragraphs:[["A","真的让我按自己的想法来设计就可以吗？"],["B","你的专业就是这个嘛，我相信你。柳原是学摄影的，宣传片就交给他负责了；KAY比较擅长编程，官网就交给他来做。这次展会预算有限，你们都要多发挥一下价值。"],["C","诶～您这样说的好像只有我没给集体作出贡献一样。那我能来参与吉祥物设计吗？做出来之后，我还可以负责联系工厂做成周边！"],["B","嗯，我感觉挺好的。千景觉得呢？"],["A","知道了，我会努力不被新井带偏审美的。"],["C","怎么这样～"]]},{time:"2026-08-10 17:44:17-17:46:00",paragraphs:[["A","我们的语音记录之后都是要输入给噗咚的对吧？"],["D","\u201c噗咚\u201d？"],["C","哦！看来是已经想好吉祥物的名字了。<br>…在没和我商量的情况下。<br>宋芬奇老师是这么说的哦。"],["A","KAY，能不能拜托你，给我的语音记录做个小彩蛋？只做给一页就可以了。"],["E","可以是可以，你想要什么样的？"],["A","嗯～我等下给你写个<b>便签</b>吧，你按照上面的内容做。"],["E","好啊，其他人有需求吗？我收集一下统一做。"],["D","我就不用了。而且做那种东西也就是自娱自乐吧，不会有多少人浏览官网的。"],["C","好消极啊前辈～自娱自乐不也挺好的嘛。<br>不过我也没想到能做什么就是了。"],["B","嗯，那我等下也写张便签。KAY，千景，谢谢你们有趣的点子。就算是毫无名气的小型独立展，也要办出属于我们的风格来。"],["A","雯祺过奖啦，我只是做了我想做的事情而已。"]]}]}
};

function readJson(key,fallback){try{return JSON.parse(localStorage.getItem(key)||JSON.stringify(fallback))}catch(e){return fallback}}
function writeJson(key,value){localStorage.setItem(key,JSON.stringify(value))}
function discoveredKeywords(){
var stored=readJson(storageKey,[]).map(normalizeRecordKeyword);
return Array.from(new Set(stored)).filter(function(item){return Object.prototype.hasOwnProperty.call(records,item)});
}
function renderMenu(){var items=discoveredKeywords();recordMenu.innerHTML=items.map(function(item){return '<a class="'+(item===keyword?"active":"")+'" href="record.html?keyword='+encodeURIComponent(item)+'">'+item+'</a>'}).join("")}
function setupRecordSidebarToggle(){
if(!recordSidebar||!recordSidebarToggle)return;
var sidebarStorageKey="recordSidebarOpenSmall";
var smallViewport=window.matchMedia("(max-width: 820px)");
function setOpen(open){
recordSidebar.classList.toggle("is-open",open);
document.documentElement.classList.toggle("record-sidebar-open-small",smallViewport.matches&&open);
recordSidebarToggle.setAttribute("aria-expanded",open?"true":"false");
if(smallViewport.matches)localStorage.setItem(sidebarStorageKey,open?"true":"false");
}
if(smallViewport.matches&&localStorage.getItem(sidebarStorageKey)==="true")setOpen(true);
recordSidebarToggle.addEventListener("click",function(){setOpen(!recordSidebar.classList.contains("is-open"))});
recordMenu.addEventListener("click",function(event){
if(!smallViewport.matches)return;
if(event.target.closest("a"))localStorage.setItem(sidebarStorageKey,"true");
});
function handleViewportChange(event){
if(!event.matches){recordSidebar.classList.remove("is-open");document.documentElement.classList.remove("record-sidebar-open-small");recordSidebarToggle.setAttribute("aria-expanded","false")}
else if(localStorage.getItem(sidebarStorageKey)==="true")setOpen(true);
}
if(smallViewport.addEventListener)smallViewport.addEventListener("change",handleViewportChange);
else smallViewport.addListener(handleViewportChange);
}
function uniqueLetters(paragraphs){return Array.from(new Set(paragraphs.map(function(p){return p[0]}))).sort()}

function renderLockedContent(record){
localStorage.setItem("pukuRecordUnlocked:录音","true");
var scrollEl=transcript.closest(".record-scroll")||transcript;
var sections=record.sections;
var html="";
for(var i=0;i<sections.length;i++){
var section=sections[i];
var cls="record-log-section";
if(section.isDark)cls+=" record-dark-section";
var warn="";
if(section.warning)warn='<p class="record-warning-text">'+section.warning+'</p>';
var lines="";
for(var j=0;j<section.paragraphs.length;j++){
var letter=section.paragraphs[j][0];
var text=section.paragraphs[j][1];
if(letter==="")lines+='<p class="record-ellipsis">'+text+'</p>';
else lines+='<p><strong>'+letter+'</strong>:'+text+'</p>';
}
html+='<section class="'+cls+'"><h3>录音记录 <span>'+section.time+'</span></h3>'+warn+lines+'</section>';
}
html+='<div class="record-bottom-image" id="recordFinalImage" hidden><img src="/step2/images/me.gif" alt=""><button class="record-return-button" type="button" data-record-return>返回</button></div>';
transcript.innerHTML=html;
speakerTools.innerHTML="";
var overlay=document.createElement("div");
overlay.className="record-cannibal-overlay";
document.body.appendChild(overlay);
var filledRows=0;
var rowHeight=120;
var gazeTriggered=false;
var mobileScrollMode=window.matchMedia("(max-width: 820px)").matches;
var scrollTarget=mobileScrollMode?window:scrollEl;
if(mobileScrollMode&&window.recordLockedMobileScrollHandler){
window.removeEventListener("scroll",window.recordLockedMobileScrollHandler);
}
function getScrollProgress(){
if(!mobileScrollMode){
return {top:scrollEl.scrollTop,max:scrollEl.scrollHeight-scrollEl.clientHeight||1};
}
var root=document.documentElement;
return {top:window.scrollY||root.scrollTop,max:Math.max(1,root.scrollHeight-window.innerHeight)};
}
function handleRecordScroll(){
var progress=getScrollProgress();
var ratio=Math.min(1,progress.top/progress.max);
var totalRows=Math.ceil(window.innerHeight/rowHeight);
var targetRows=Math.ceil(ratio*totalRows);
if(targetRows>filledRows){filledRows=targetRows;overlay.style.height=filledRows*rowHeight+"px"}
if(ratio>=0.99&&!gazeTriggered){
gazeTriggered=true;
if(mobileScrollMode){window.removeEventListener("scroll",handleRecordScroll);window.recordLockedMobileScrollHandler=null}
setTimeout(function(){
overlay.style.transition="opacity 0.3s ease";overlay.style.opacity="0";
setTimeout(function(){
overlay.style.display="none";
var gaze=document.createElement("div");
gaze.className="record-gaze-overlay";
gaze.innerHTML='<img src="/step2/images/pukupon_gaze.png" alt="">';
document.body.appendChild(gaze);
setTimeout(function(){
gaze.style.opacity="0";
setTimeout(function(){
gaze.remove();
if(mobileScrollMode)window.scrollTo({top:0,behavior:"smooth"});else scrollEl.scrollTo({top:0,behavior:"smooth"});
var finalImage=document.getElementById("recordFinalImage");
if(finalImage)finalImage.hidden=false;
},300);
},1500);
},300);
},2000);
}
}
scrollTarget.addEventListener("scroll",handleRecordScroll,{passive:true});
if(mobileScrollMode)window.recordLockedMobileScrollHandler=handleRecordScroll;
}

transcript.addEventListener("click",function(event){
var returnButton=event.target.closest("[data-record-return]");
if(!returnButton)return;
localStorage.removeItem("pukuRecordUnlocked:录音");
if(window.recordLockedMobileScrollHandler){
window.removeEventListener("scroll",window.recordLockedMobileScrollHandler);
window.recordLockedMobileScrollHandler=null;
}
var overlay=document.querySelector(".record-cannibal-overlay");
if(overlay)overlay.remove();
var gaze=document.querySelector(".record-gaze-overlay");
if(gaze)gaze.remove();
renderRecord();
});

function normalizeUnlockValue(value){return value.replace(/\s+/g,"").toLowerCase()}
function renderRecord(){
var record=records[keyword]||null;
if(!record){
activeSpeakers=[];
transcript.innerHTML="";
speakerTools.innerHTML="";
return;
}
if(record.isArticle){
activeSpeakers=[];
transcript.innerHTML='<section class="record-log-section"><h3>'+record.title+'</h3><div class="record-article">'+record.content+'</div></section>';
speakerTools.innerHTML="";
return;
}
if(record.isLocked){
activeSpeakers=[];
if(localStorage.getItem("pukuRecordUnlocked:录音")==="true"){renderLockedContent(record);return}
transcript.innerHTML='<section class="record-locked-section"><div class="record-locked-image"><img src="/step2/images/me.jpg" alt=""></div><p class="record-locked-text">'+record.lockText+'</p><div class="record-locked-form"><input type="text" id="recordPasswordInput" placeholder="输入密码" autocomplete="off"><button type="button" id="recordPasswordSubmit">确认</button></div><p class="record-locked-error" id="recordPasswordError"></p></section>';
speakerTools.innerHTML="";
var pwInput=document.getElementById("recordPasswordInput");
var pwBtn=document.getElementById("recordPasswordSubmit");
var pwError=document.getElementById("recordPasswordError");
var pwErrorFadeTimer=null;
var pwErrorClearTimer=null;
function showPasswordError(){
clearTimeout(pwErrorFadeTimer);
clearTimeout(pwErrorClearTimer);
pwError.textContent="密码错误";
pwError.classList.add("is-visible");
pwErrorFadeTimer=setTimeout(function(){pwError.classList.remove("is-visible")},1200);
pwErrorClearTimer=setTimeout(function(){pwError.textContent=""},1500);
}
async function tryUnlock(){
if(pwBtn.disabled)return;
pwBtn.disabled=true;
try{
var val=pwInput.value;
if(await window.passwordVerifier.verify(2,val)){localStorage.setItem("pukuHoaxTeaserUnlocked","true");localStorage.removeItem("pukuRecordUnlocked:录音");window.location.href="index.html#news";return}
if(await window.passwordVerifier.verify(1,val)){renderLockedContent(record);return}
showPasswordError();pwInput.value="";
}catch(error){showPasswordError();pwInput.value=""}
finally{if(document.body.contains(pwBtn))pwBtn.disabled=false}
}
pwBtn.addEventListener("click",tryUnlock);
pwInput.addEventListener("keydown",function(e){if(e.key==="Enter")tryUnlock()});
return;
}
var sections=record.sections||[{time:record.time,paragraphs:record.paragraphs}];
var sectionSpeakers=sections.map(function(s){return uniqueLetters(s.paragraphs)});
activeSpeakers=sectionSpeakers.reduce(function(longest,current){return current.length>longest.length?current:longest},[]);
var html="";
for(var i=0;i<sections.length;i++){
var section=sections[i];
var lines="";
for(var j=0;j<section.paragraphs.length;j++){
var letter=section.paragraphs[j][0];
var text=section.paragraphs[j][1];
lines+='<p><strong data-section="'+i+'" data-speaker="'+letter+'" data-letter="'+letter+'">'+letter+'</strong>:'+text+'</p>';
}
html+='<section class="record-log-section"><h3>'+record.title+' <span>'+section.time+'</span></h3>'+lines+'</section>';
}
transcript.innerHTML=html;
}

function applyDelayedWordSwap(){
var targets=transcript.querySelectorAll("[data-swap-word]");
if(!targets.length)return;
function runSwap(target){
if(target.dataset.swapStarted==="true")return;
target.dataset.swapStarted="true";
setTimeout(function(){
target.textContent="";
target.classList.remove("is-original");
target.classList.add("is-erasing");
var word=target.dataset.replaceWord||"";
var index=0;
function typeNext(){
if(index===0){target.classList.remove("is-erasing");target.classList.add("is-swapped")}
if(index>=word.length)return;
target.textContent+=word[index];index++;setTimeout(typeNext,700);
}
setTimeout(typeNext,80);
},2000);
}
if(!("IntersectionObserver" in window)){targets.forEach(runSwap);return}
var observer=new IntersectionObserver(function(entries){entries.forEach(function(entry){if(!entry.isIntersecting)return;runSwap(entry.target);observer.unobserve(entry.target)})},{threshold:0.85});
targets.forEach(function(t){observer.observe(t)});
}

function applySpeakerNames(){
var speakerNames=readJson(speakerStorageKey,{});
transcript.querySelectorAll("[data-speaker]").forEach(function(node){var letter=node.dataset.letter;node.textContent=speakerNames[letter]||letter});
}
function usedArtists(exceptLetter){return Object.entries(draftSpeakers).filter(function(e){return e[0]!==exceptLetter}).map(function(e){return e[1]})}

function renderSpeakerTools(){
if(activeSpeakers.length===0){speakerTools.innerHTML="";return}
var savedSpeakers=readJson(speakerStorageKey,{});
var hasSaved=localStorage.getItem(speakerSavedKey)==="true";
if(hasSaved&&!isEditing){
speakerTools.innerHTML='<section class="speaker-tool" aria-label="设定发言者"><p>无法判断发言者，您可以自行设定。</p><div class="speaker-panel is-saved speaker-count-'+activeSpeakers.length+'"><div class="speaker-summary-list">'+activeSpeakers.map(function(l){return '<div class="speaker-summary"><span>'+l+'</span><strong>'+(savedSpeakers[l]||"未设定")+'</strong></div>'}).join("")+'</div><button class="speaker-main-action" type="button" data-action="edit-all">修改</button></div><p class="speaker-feedback" aria-live="polite"></p></section>';
return;
}
speakerTools.innerHTML='<section class="speaker-tool" aria-label="设定发言者"><p>无法判断发言者，您可以自行设定。</p><div class="speaker-panel is-editing speaker-count-'+activeSpeakers.length+'"><div class="speaker-choice-list">'+activeSpeakers.map(function(letter){return '<article class="speaker-choice" data-letter="'+letter+'"><div class="speaker-choice-head"><span>'+letter+'</span><strong>'+(draftSpeakers[letter]||"未选定")+'</strong></div><div class="speaker-options">'+artists.map(function(artist){var sel=draftSpeakers[letter]===artist;var dis=usedArtists(letter).indexOf(artist)!==-1;return '<button type="button" class="'+(sel?"selected":"")+'" data-artist="'+artist+'" '+(dis?"disabled":"")+'>'+artist+'</button>'}).join("")+'</div></article>'}).join("")+'</div><button class="speaker-main-action" type="button" data-action="save-all">保存</button></div><p class="speaker-feedback" aria-live="polite"></p></section>';
}

function showFeedback(){
var feedback=speakerTools.querySelector(".speaker-feedback");
if(!feedback)return;
feedback.textContent="感谢反馈，这对噗咚智能性的改善很有帮助";
feedback.classList.add("is-visible");
clearTimeout(feedbackTimer);
feedbackTimer=setTimeout(function(){feedback.classList.remove("is-visible");feedback.textContent=""},1500);
}

speakerTools.addEventListener("click",function(event){
var action=event.target.dataset.action;
if(action==="edit-all"){draftSpeakers=Object.assign({},readJson(speakerStorageKey,{}));isEditing=true;renderSpeakerTools();return}
if(action==="save-all"){writeJson(speakerStorageKey,draftSpeakers);localStorage.setItem(speakerSavedKey,"true");isEditing=false;applySpeakerNames();renderSpeakerTools();showFeedback();return}
var artistButton=event.target.closest("[data-artist]");
if(!artistButton||artistButton.disabled)return;
var card=artistButton.closest("[data-letter]");
var letter=card.dataset.letter;
var artist=artistButton.dataset.artist;
if(draftSpeakers[letter]===artist){delete draftSpeakers[letter]}else{draftSpeakers[letter]=artist}
renderSpeakerTools();
});

document.body.style.backgroundImage="";
var existingOverlay=document.querySelector(".record-cannibal-overlay");
if(existingOverlay)existingOverlay.remove();
renderMenu();
setupRecordSidebarToggle();
renderRecord();
applyDelayedWordSwap();
draftSpeakers=Object.assign({},readJson(speakerStorageKey,{}));
isEditing=localStorage.getItem(speakerSavedKey)!=="true";
applySpeakerNames();
renderSpeakerTools();
})();
