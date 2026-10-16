const state = { catalog: [], selected: null, currentRun: null, category: "all", generation: 0 };
const $ = selector => document.querySelector(selector);
const pretty = value => JSON.stringify(value, null, 2);
const categories = {all:"Все проекты",training:"Обучение и данные",retrieval:"Поиск и документы",inference:"Локальные модели",applications:"Приложения и агенты",quality:"Качество и безопасность"};
const metadata = {
  1:["PyTorch Classifier","Обучение классификатора и проверка уверенности его предсказаний.","training"],
  2:["Hugging Face · LoRA","Дообучение и проверка датасета на дубликаты и утечку между выборками.","training"],
  3:["RAG по документам","Поиск контекста и проверка опоры предложений ответа на источники.","retrieval"],
  4:["LlamaIndex Agent","Инструменты агента и безопасное вычисление арифметических выражений.","applications"],
  5:["Ollama · Model Arena","Сравнение локальных моделей по качеству и скорости ответа.","inference"],
  6:["llama.cpp · GGUF","Локальный инференс и проверка целостности файлов моделей.","inference"],
  7:["vLLM Serving","Сервер инференса и расчёт задержек запросов, включая p95.","inference"],
  8:["Dify Workflows","Проверка изменений workflow и удаление секретов из экспортов.","applications"],
  9:["ComfyUI Pipeline","Генерация изображений и связь результата с точным workflow.","applications"],
  10:["Code Repair Agent","Проверка исправлений кода, подготовленных ИИ-агентом.","quality"],
  11:["Local Knowledge OS","Локальная память: сохранение, поиск, экспорт и удаление знаний.","retrieval"],
  12:["Voice Companion","Локальный голосовой помощник и извлечение команды по слову активации.","applications"],
  13:["Fine-tuning Lab","Подготовка данных и воспроизводимое разделение выборок для дообучения.","training"],
  14:["Local Model Router","Выбор модели по приватности, стоимости и задержке с объяснением решения.","inference"],
  15:["Local Code Reviewer","Локальный анализ кода и экспорт замечаний в формат SARIF.","quality"],
  16:["Synthetic Data Factory","Генерация данных и проверка дубликатов и персональной информации.","training"],
  17:["Document Parser","Извлечение полей документа со ссылками на исходные фрагменты.","retrieval"],
  18:["AI Observability","Обработка чувствительных данных и трассировка запросов к LLM.","quality"],
  19:["Local Edge Fleet","Выбор узла для запроса и исключение узлов после сбоев.","inference"],
  20:["Red-Team Arena","Оценка атак на модели с учётом неопределённости и ошибок сервера.","quality"],
  21:["Universal Skill Forge","Проверка схем и переносимости инструментов ИИ-агентов.","applications"]
};
const reviewLabels = {pending:"ожидает проверки",approved:"принято",needs_changes:"на доработке",rejected:"отклонено"};
async function api(path, options={}) {
  const response = await fetch(path, {headers:{"Content-Type":"application/json"}, ...options});
  if (!response.ok) {let detail=`HTTP ${response.status}`;try {const body=await response.json();detail=typeof body.detail==="string"?body.detail:pretty(body.detail);} catch {} throw new Error(detail);}
  return response.status===204 ? null : response.json();
}
function renderCatalog() {
  const query=$("#search").value.trim().toLocaleLowerCase("ru");
  const visible=state.catalog.filter(item => (state.category==="all" || item.category===state.category) && `${item.name} ${item.problem} ${item.feature} ${item.slug}`.toLocaleLowerCase("ru").includes(query));
  const root=$("#catalog");root.replaceChildren();
  for (const item of visible) {
    const card=document.createElement("article");card.className="card";card.dataset.projectId=item.id;
    const top=document.createElement("div");top.className="card-top";
    const number=document.createElement("span");number.className="number";number.textContent=String(item.id).padStart(2,"0");
    const group=document.createElement("span");group.className="card-category";group.textContent=categories[item.category];top.append(number,group);
    const title=document.createElement("h3");title.textContent=item.name;
    const problem=document.createElement("p");problem.textContent=item.problem;
    const feature=document.createElement("span");feature.className="feature";feature.textContent=item.feature;
    const button=document.createElement("button");button.textContent="Открыть инструмент";const arrow=document.createElement("span");arrow.textContent="↗";arrow.setAttribute("aria-hidden","true");button.append(arrow);button.addEventListener("click",()=>openRunner(item));
    card.append(top,title,problem,feature,button);root.append(card);
  }
  $("#matchCount").textContent=`${visible.length} из ${state.catalog.length}`;
  $("#emptyState").hidden=visible.length>0;
  $("#catalogTitle").textContent=categories[state.category];
}
function openRunner(item) {
  state.generation++;state.selected=item;state.currentRun=null;
  $("#runnerIndex").textContent=`ПРОЕКТ ${String(item.id).padStart(2,"0")} · ${item.feature}`;
  $("#runnerTitle").textContent=item.name;$("#runnerProblem").textContent=item.problem;
  $("#payload").value=pretty(item.sample);$("#result").textContent="Выберите данные и нажмите «Запустить функцию».";
  $("#runStatus").textContent="Не запускалось";$("#runStatus").className="badge";$("#runError").textContent="";
  $("#reviewActions").hidden=true;$("#runButton").disabled=false;$("#runner").showModal();
}
async function execute() {
  if (!state.selected) return;
  let payload;try {payload=JSON.parse($("#payload").value);} catch {$("#runError").textContent="Некорректный JSON. Проверьте скобки, кавычки и запятые.";return;}
  const generation=state.generation, selected=state.selected;
  state.currentRun=null;$("#reviewActions").hidden=true;$("#runButton").disabled=true;$("#runError").textContent="";$("#runStatus").textContent="Выполняется";
  try {
    const result=await api(`/api/run/${selected.id}`,{method:"POST",body:JSON.stringify({payload})});
    if (generation!==state.generation) return;
    state.currentRun=result;$("#result").textContent=pretty(result.result);$("#runStatus").textContent="Готово · ожидает проверки";$("#runStatus").className="badge ok";$("#reviewActions").hidden=false;
  } catch(error) {if(generation===state.generation){$("#runError").textContent=error.message;$("#runStatus").textContent="Ошибка";$("#runStatus").className="badge";}}
  finally {if(generation===state.generation)$("#runButton").disabled=false;}
}
async function review(status) {
  if(!state.currentRun)return;
  const generation=state.generation, run=state.currentRun;
  try {const updated=await api(`/api/history/${run.id}/review`,{method:"POST",body:JSON.stringify({status,note:"Проверено в ML Workbench"})});if(generation!==state.generation)return;state.currentRun=updated;$("#runStatus").textContent=`Готово · ${reviewLabels[status]}`;}
  catch(error){if(generation===state.generation)$("#runError").textContent=error.message;}
}
function download() {
  if(!state.currentRun)return;
  const url=URL.createObjectURL(new Blob([pretty(state.currentRun)],{type:"application/json"}));
  const link=document.createElement("a");link.href=url;link.download=`portfolio-run-${state.currentRun.id}.json`;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function openHistory() {
  const root=$("#history");root.textContent="Загрузка…";$("#historyDialog").showModal();
  try {
    const data=await api("/api/history"),names=new Map(state.catalog.map(item=>[item.id,item.name]));root.replaceChildren();
    if(!data.items.length)root.textContent="История пока пуста.";
    for(const item of data.items){
      const row=document.createElement("article");row.className="history-item";
      const info=document.createElement("div"),title=document.createElement("b"),meta=document.createElement("small");
      title.textContent=names.get(item.project_id)||`Проект ${item.project_id}`;meta.textContent=`${new Date(item.created_at).toLocaleString("ru-RU")} · ${reviewLabels[item.review_status]||item.review_status}`;info.append(title,meta);
      const remove=document.createElement("button");remove.textContent="Удалить";remove.setAttribute("aria-label",`Удалить запуск ${title.textContent}`);
      remove.addEventListener("click",async()=>{remove.disabled=true;try{await api(`/api/history/${item.id}`,{method:"DELETE"});row.remove();if(!root.children.length)root.textContent="История пока пуста.";}catch(error){meta.textContent=error.message;remove.disabled=false;}});
      row.append(info,remove);root.append(row);
    }
  }catch(error){root.textContent=`Не удалось загрузить историю: ${error.message}`;}
}
window.addEventListener("DOMContentLoaded",async()=>{
  $("#search").addEventListener("input",renderCatalog);$("#runButton").addEventListener("click",execute);$("#sampleButton").addEventListener("click",()=>{if(state.selected)$("#payload").value=pretty(state.selected.sample);});$("#historyButton").addEventListener("click",openHistory);$("#downloadButton").addEventListener("click",download);
  document.querySelectorAll("[data-review]").forEach(button=>button.addEventListener("click",()=>review(button.dataset.review)));
  document.querySelectorAll("[data-category]").forEach(button=>button.addEventListener("click",()=>{state.category=button.dataset.category;document.querySelectorAll("[data-category]").forEach(item=>{const active=item===button;item.classList.toggle("active",active);item.setAttribute("aria-pressed",String(active));});renderCatalog();}));
  try {const data=await api("/api/catalog");state.catalog=data.items.map(item=>{const [name,problem,category]=metadata[item.id]||[item.name,item.problem,"applications"];return {...item,name,problem,category};});$("#projectCount").textContent=state.catalog.length;renderCatalog();$("#connectionStatus").textContent="Локальный сервер";$("#connectionStatus").className="connection ready";}
  catch(error){$("#connectionStatus").textContent="Нет подключения";$("#connectionStatus").className="connection failed";$("#catalogError").hidden=false;$("#catalogError").textContent=`Не удалось загрузить проекты: ${error.message}. Обновите страницу после запуска сервера.`;$("#matchCount").textContent="Недоступно";}
});
