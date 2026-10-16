import { Hono } from "https://esm.sh/hono@4.4.7";
import { cors } from "https://esm.sh/hono@4.4.7/cors";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.0";

const SUPABASE_URL = "https://baznxpgbaivkqiycouuf.supabase.co";
const STORAGE_DOMAIN = "https://baznxpgbaivkqiycouuf.supabase.co";
const APP_SDK_CDN = "https://unpkg.com";
const RESOURCE_URI = "ui://sticker-mcp/browser";
const RESOURCE_MIME = "text/html;profile=mcp-app";

// ── 内嵌 MCP App HTML ─────────────────────────────────────────────
// 单文件 UI，通过 CDN 加载 App SDK，无需构建工具
const STICKER_APP_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Sticker Browser</title>
<style>
  *,*::before,*::after{box-sizing:border-box}
  html,body{margin:0;padding:0;overflow-x:hidden}
  body{
    font-family:var(--font-sans,system-ui,-apple-system,sans-serif);
    color:var(--color-text-primary,#1a1a1a);
    background:var(--color-background-primary,#fff);
    padding:12px;
  }
  @media(prefers-color-scheme:dark){
    body{color:var(--color-text-primary,#e5e5e5);background:var(--color-background-primary,#1a1a1a)}
  }
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-top:8px}
  .card{
    border:1px solid var(--color-border-primary,#e0e0e0);
    border-radius:var(--border-radius-md,10px);
    overflow:hidden;cursor:pointer;transition:box-shadow .15s;
    background:var(--color-background-secondary,#f8f8f8);
  }
  .card:hover{box-shadow:0 2px 8px rgba(0,0,0,.12)}
  .card img{width:100%;aspect-ratio:1;object-fit:cover;display:block}
  .card .label{padding:6px 8px;font-size:12px;line-height:1.3;text-align:center;word-break:break-all}
  .sent{display:flex;flex-direction:column;align-items:center;gap:8px;padding:12px}
  .sent img{max-width:280px;max-height:280px;border-radius:var(--border-radius-md,10px)}
  .sent .text{font-size:14px;opacity:.7}
  .empty{padding:24px;text-align:center;opacity:.5;font-size:14px}
  .tag{display:inline-block;font-size:11px;padding:2px 6px;border-radius:4px;margin:1px;
    background:var(--color-background-tertiary,#eee);color:var(--color-text-secondary,#555)}
</style>
</head>
<body>
<div id="root"></div>
<script type="module">
import{App}from"${APP_SDK_CDN}/@modelcontextprotocol/ext-apps@1.7.5/dist/src/app-with-deps.js";

const root=document.getElementById("root");
const app=new App({name:"Sticker Browser",version:"1.0.0"});

function renderGrid(stickers){
  if(!stickers||!stickers.length){root.innerHTML='<div class="empty">没有找到表情包</div>';return}
  const html='<div class="grid">'+stickers.map(s=>
    '<div class="card" data-id="'+s.id+'">'
    +'<img src="'+s.image_url+'" alt="'+esc(s.text)+'" loading="lazy">'
    +'<div class="label">'+esc(s.text)
    +(s.emotions?'<br>'+s.emotions.split("、").map(e=>'<span class="tag">'+esc(e)+'</span>').join(""):"")
    +'</div></div>'
  ).join("")+'</div>';
  root.innerHTML=html;
  root.querySelectorAll(".card").forEach(card=>{
    card.addEventListener("click",async()=>{
      const id=card.dataset.id;
      try{
        const r=await app.callServerTool({name:"send_sticker",arguments:{sticker_id:id}});
        if(r.structuredContent)renderSent(r.structuredContent);
      }catch(e){console.error(e)}
    });
  });
}

function renderSent(sc){
  root.innerHTML='<div class="sent">'
    +'<img src="'+sc.image_url+'" alt="'+esc(sc.text)+'">'
    +'<div class="text">'+esc(sc.text)+'</div></div>';
}

function esc(s){return(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}

app.ontoolinput=({arguments:args})=>{
  root.innerHTML='<div class="empty">搜索中…</div>';
};

app.ontoolresult=(result)=>{
  const sc=result.structuredContent;
  if(!sc)return;
  if(sc.stickers)renderGrid(sc.stickers);
  else if(sc.image_url)renderSent(sc);
};

app.onhostcontextchanged=(ctx)=>{
  if(ctx.safeAreaInsets){
    const{top,right,bottom,left}=ctx.safeAreaInsets;
    document.body.style.padding=top+"px "+right+"px "+bottom+"px "+left+"px";
  }
};

await app.connect();
const ctx=app.getHostContext();
if(ctx?.safeAreaInsets){
  const{top,right,bottom,left}=ctx.safeAreaInsets;
  document.body.style.padding=top+"px "+right+"px "+bottom+"px "+left+"px";
}
</script>
</body>
</html>`;

const app = new Hono();
app.use("*", cors());

const getSupabaseClient = (req: Request) => {
  const apikey = req.headers.get("apikey") || req.headers.get("authorization")?.replace("Bearer ", "") || Deno.env.get("SUPABASE_ANON_KEY") || "";
  return createClient(SUPABASE_URL, apikey);
};

app.post("*", async (c) => {
  try {
    const body = await c.req.json();
    const requests = Array.isArray(body) ? body : [body];
    const responses = [];

    for (const req of requests) {
      const { jsonrpc, id, method, params } = req;

      // ── 1. 初始化 ──────────────────────────────────────────
      if (method === "initialize") {
        responses.push({
          jsonrpc: "2.0", id,
          result: {
            protocolVersion: "2024-11-05",
            capabilities: {
              tools: {},
              resources: {},  // 新增：声明支持 resources
            },
            serverInfo: { name: "sticker-mcp", version: "2.0.0" }
          }
        });
      }
      // ── 2. 工具列表（增加 _meta.ui） ───────────────────────
      else if (method === "tools/list") {
        responses.push({
          jsonrpc: "2.0", id,
          result: {
            tools: [
              {
                name: "search_stickers",
                description: "根据情绪和语境搜索合适的表情包,返回候选列表。只有选好ID后,才能调用send_sticker发送。",
                inputSchema: {
                  type: "object",
                  properties: {
                    query: { type: "string", description: "当前完整语境" },
                    emotion: { type: "string", description: "情绪,如撒娇、生气" }
                  },
                  required: ["query"]
                },
                _meta: {
                  ui: { resourceUri: RESOURCE_URI }
                }
              },
              {
                name: "send_sticker",
                description: "根据ID发送对应的表情包图片。",
                inputSchema: {
                  type: "object",
                  properties: {
                    sticker_id: { type: "string", description: "搜索工具返回的候选ID" }
                  },
                  required: ["sticker_id"]
                },
                _meta: {
                  ui: { resourceUri: RESOURCE_URI }
                }
              }
            ]
          }
        });
      }
      // ── 3. 资源读取（新增：返回 UI HTML） ──────────────────
      else if (method === "resources/read") {
        if (params?.uri === RESOURCE_URI) {
          responses.push({
            jsonrpc: "2.0", id,
            result: {
              contents: [{
                uri: RESOURCE_URI,
                mimeType: RESOURCE_MIME,
                text: STICKER_APP_HTML,
                _meta: {
                  ui: {
                    csp: {
                      resourceDomains: [STORAGE_DOMAIN, APP_SDK_CDN],
                    },
                    prefersBorder: false
                  }
                }
              }]
            }
          });
        } else {
          responses.push({
            jsonrpc: "2.0", id,
            error: { code: -32602, message: "Resource not found" }
          });
        }
      }
      // ── 4. 资源列表（可选，规范允许省略，但实现更完整） ────
      else if (method === "resources/list") {
        responses.push({
          jsonrpc: "2.0", id,
          result: {
            resources: [{
              uri: RESOURCE_URI,
              name: "Sticker Browser",
              description: "表情包浏览和发送界面",
              mimeType: RESOURCE_MIME
            }]
          }
        });
      }
      // ── 5. 调用工具 ────────────────────────────────────────
      else if (method === "tools/call") {
        const toolName = params?.name;
        const args = params?.arguments || {};
        const supabase = getSupabaseClient(c.req.raw);

        if (toolName === "search_stickers") {
          let { data, error } = await supabase.from("sticker_catalog").select("*").eq("assistant_enabled", true);

          if (error) {
            responses.push({ jsonrpc: "2.0", id, result: { content: [{ type: "text", text: `查询失败: ${error.message}` }] } });
          } else {
            let filteredData = data || [];
            if (args.emotion) {
              filteredData = filteredData.filter((item: any) =>
                item.tone_tags && Array.isArray(item.tone_tags) && item.tone_tags.includes(args.emotion)
              );
            }

            const formattedText = filteredData.map((item: any) =>
              `ID: ${item.id} | 文字: ${item.ocr_text} | 语义: ${item.semantic_intent} | 情绪: ${(item.tone_tags || []).join('、')}`
            ).join('\n');

            // structuredContent 供 UI 渲染，content 供纯文本客户端
            responses.push({
              jsonrpc: "2.0", id,
              result: {
                content: [{ type: "text", text: formattedText || "没找到匹配的表情包" }],
                structuredContent: {
                  stickers: filteredData.map((item: any) => ({
                    id: item.id,
                    text: item.ocr_text || "",
                    emotions: (item.tone_tags || []).join("、"),
                    image_url: item.public_url || ""
                  }))
                }
              }
            });
          }
        }
        else if (toolName === "send_sticker") {
          const { data, error } = await supabase.from("sticker_catalog").select("*").eq("id", args.sticker_id).single();
          if (error || !data) {
            responses.push({ jsonrpc: "2.0", id, result: { content: [{ type: "text", text: "找不到该表情包" }] } });
          } else {
            try {
              const imgResp = await fetch(data.public_url);
              const buf = await imgResp.arrayBuffer();
              const mime = imgResp.headers.get("content-type") || "image/png";

              const bytes = new Uint8Array(buf);
              let binary = '';
              for (let i = 0; i < bytes.byteLength; i++) {
                binary += String.fromCharCode(bytes[i]);
              }
              const base64 = btoa(binary);

              responses.push({
                jsonrpc: "2.0", id,
                result: {
                  content: [
                    { type: "image", data: base64, mimeType: mime },
                    { type: "text", text: `已发送表情包：${data.ocr_text || "表情包"}` }
                  ],
                  structuredContent: {
                    image_url: data.public_url,
                    text: data.ocr_text || "表情包"
                  }
                }
              });
            } catch (_fetchErr) {
              responses.push({ jsonrpc: "2.0", id, result: { content: [{ type: "text", text: "图片下载失败" }] } });
            }
          }
        }
      }
      // ── 6. 未知方法处理 ────────────────────────────────────
      else if (method !== "notifications/initialized") {
        responses.push({ jsonrpc: "2.0", id, error: { code: -32601, message: "Method not found" } });
      }
    }

    if (responses.length === 0) return c.json({ jsonrpc: "2.0", result: {} });
    return c.json(responses.length === 1 ? responses[0] : responses);
  } catch (err) {
    return c.json({ jsonrpc: "2.0", error: { code: -32700, message: "Parse error" } }, 400);
  }
});

Deno.serve(app.fetch);
