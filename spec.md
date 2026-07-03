#002 公開法規 Agentic RAG¶
定稿日：2026-06-25｜狀態：候選池 → corpus 雙軌（AML + 投信利害關係人，2026-06 時事微調）

時事錨點（2026-06）¶
ETtoday 懶人包整理國泰投信爭議：董事兼任他公司董事後，利害關係人名單未及時更新，基金／全委帳戶仍交易世芯-KY → 出清、通報金管會、基金淨值重算、媒體引述全委損失等。（確定）[2026-06-25-國泰投信利害關係人-ettoday]

媒體敘事關鍵字	應對的法遵／法規軸	Agent 怎麼答
董事兼任他公司董事	證券投資信託基金管理辦法 第 10、11 條 利害關係人	引用條文定義與交易禁止
全委帳戶損失	全委契約利害關係人限制 + 辦法	說義務與程序，不預測賠償金額
通報金管會	重大偶發事件通報函	列通報義務與事件類型
內控內稽疏失	投信事業管理規則內控 + aml-bank-ic 精神	原則性引用；不評論個案
裁罰 300 萬、4.54 億	不在 corpus	拒答個案金額／處分
新聞不入 eval corpus（事實會變）；僅作 blog 開場與拒答測試。法條 eval 仍只對 MOJ／金管會公開文本。（確定）

核心問題¶
金融合規場景裡，一般 RAG／Chat 不能當合規助手用 — 因為三件事沒解決：（推測）金融業-agent-應用探索

痛點	現象	後果
不可稽核	回答沒有對應法條／段落	無法給法遵或內稽看；面試也說不清依據
不可控	資料庫沒有仍瞎答；個案裁罰也臆測	合規風險；等同未授權法律意見
不可回歸	改 prompt／換模型後不知道變好變壞	企業 Agent 無法上線維運
002 要解決的不是「洗錢法規問答百科」或「新聞摘要機」，而是：¶
用公開法規 corpus，做出可 demo 的金融法規 Agent：法條可引用、個案與裁罰不臆測、golden set 可回歸 — MVP 敘事緊跟 利害關係人／內控通報 時事，技術底座仍含 AML。（確定）[2026-06-25-國泰投信利害關係人-ettoday]

對齊 年底轉職-agent-準備 與 bloss0m-com 既有 eval 實作（#001 已結案）：先證明 eval + 安全行為，再談覆蓋多少法規。（推測）

本專案不解決¶
取代法遵／律師判斷（非法律意見）
涵蓋全部金管會法規、媒體懶人包當法條、或即時裁罰動態
接入銀行內規或客戶資料
MVP 成功標準（怎樣算做完）¶
問投信董事兼任他公司董事 → 引用 基金管理辦法 第 10、11 條（golden 軌 B）
問 AML／CDD → 引用洗錢防制子法（golden 軌 A，≥4/5 題 citation_hit）
問「國泰會罰多少／4.54 億誰賠」→ 拒答 + 免責（golden 軌 C）
執行 /eval/run（或 CLI）→ 輸出可重現 JSON 報告（含 citation、latency）
公開 repo + bloss0m-com 一篇說明「為何金融 RAG 要先 eval」
一句話¶
以雙軌公開法規建 corpus：B 投信利害關係人＋通報（時事主軸）、A 洗錢防制（銀行合規底座）；驗證可稽核、可拒答、可 eval。

交付清單（具體要寫什麼）¶
實作 repo（建議獨立於 daydream，或 bloss0m 子目錄）與對外輸出分開列；打勾 = MVP 完成。

A. 程式與設定（repo）¶
檔案／模組	要寫什麼
corpus/manifest.json	6～7 部法規 metadata；track: aml | sit-related-party | sit-reporting
corpus/raw/*.html	MOJ／FSC 下載之條文原文
corpus/README.md	資料來源、修正日期、非法律意見免責
scripts/fetch_moj_law.py（可選）	輸入 pcode 拉單一法規，便於重現
scripts/chunk_by_article.py	解析「第 N 條」→ chunk + {doc_id, article, text}
src/retrieve.py	向量檢索 top-k，回傳帶 metadata 的 chunks
src/agent.py 或 LangGraph	流程：retrieve → generate → citation 檢查 → 輸出／拒答
src/prompts/system.md	三層問答：法條／程序指引／拒答（個案、裁罰、新聞金額）
eval/golden.yaml	12 題分軌 A（AML 5）／B（投信 5）／C（拒答 2）
eval/run.py	跑 golden → citation_hit、refusal_accuracy、latency → JSON
README.md	問題陳述、架構圖、安裝、demo 指令、eval 範例輸出
B. Wiki（daydream，隨里程碑更新）¶
頁面	要寫什麼
本頁 #002	勾選成功標準；補 repo URL、eval 分數截圖連結
金融業-ai-agent-side-發想	狀態：#002 進入實作／已完成
wiki/log.md	ingest／實作節點 append
（可選）wiki/sources/*-002-實作日誌.md	每週實驗變更、eval 分數、法規改版 diff
C. Blog（bloss0m-com，1 篇）¶
段落	要寫什麼
問題	金融 RAG 為何不能只有「答得像」；以利害關係人未及時更新為例（不點名內部、可引公開報導連結）
做法	雙軌 corpus、條號 chunk、citation／拒答分軌 eval
證據	golden 12 題 + eval JSON 節錄
限制	非法律意見；不 ingest ETtoday 正文進 corpus
下一步	Phase 2 金管會裁罰新聞稿（type=enforcement，與法條 eval 分開）
建議標題：〈利害關係人法規 RAG：為何新聞不能當 corpus〉或〈可稽核的投信合規 Agent MVP〉。

D. 不寫／Phase 2 再寫¶
裁罰新聞稿 corpus、銀行法全文
完整 Web UI（CLI + README demo 即可）
與國泰內規或內部系統整合
D. 不寫／Phase 2 再寫¶
ETtoday 等媒體全文進向量庫（僅 wiki source 歸檔）
金管會裁罰新聞稿全文 corpus（eval 分軌後再加）
銀行法全文、完整 Web UI、國泰內規
Corpus 雙軌（2026-06-25 微調）¶
決策摘要¶
原方案	微調後
僅 AML 3～4 部	B 投信利害關係人 3 部為主 + A AML 2～3 部為輔
裁罰新聞稿 Phase 2	不變；時事僅錨點，不進 MVP corpus
銀行法 Phase 2	不變
軌 B — 投信利害關係人與通報（時事主軸，優先 Day 1）¶
ID	法規／指引	來源	角色
sit-fund-mgmt	證券投資信託基金管理辦法	MOJ G0400082	核心：第 10 條（含不得投資利害關係公司證券）、第 11 條定義
sit-biz-rules	證券投資信託事業管理規則	MOJ G0400081	內部控制、董事監察人變動通報（節錄相關條）
sit-material-event	投信投顧重大偶發事件通報	金管會函（104.04.14）	內控缺失、媒體報導等應立即通報
（確定）軌 B 對齊 [2026-06-25-國泰投信利害關係人-ettoday] 敘事關鍵字。

軌 A — 洗錢防制（銀行底座，縮為 2～3 部）¶
ID	法規	來源	角色
aml-finst	金融機構防制洗錢辦法	MOJ	CDD、監控、申報（與銀行場景連結）
aml-bank-ic	銀行業…內部控制與稽核制度實施辦法	金管會／銀行局	內控稽核（呼應「內控疏失」敘事）
aml-act	洗錢防制法	MOJ	可選；縮 scope 時刪，保留 aml-finst 即可
刪除 MVP 預設： aml-act-enf（施行細則）；與時事無直接關聯者延後。

法遵指引（Agent 應輸出的「程序面」checklist）¶
使用者問「類似媒體這種情況該怎麼做」時，Agent 只列法規義務步驟（每步附條號），不斷言個案是否違法：（推測）

名單更新：董事／監察人對外兼任變動 → 重新認定利害關係人公司（sit-fund-mgmt 第 11 條）
交易管制：基金不得投資利害關係公司證券；全委依契約停止相關交易（第 10 條 + 契約敘述為原則，不引用內部契約）
庫存處置：若已違規持有 → 說明辦法上之申報／處置義務（條文 + 「依內控程序」）
通報：符合重大偶發事件（內控缺失、媒體影響信譽等）→ 立即通報證期局（sit-material-event）
受益人權益：基金淨值重算、補償 → 僅能引用辦法／信託契約一般義務，拒答具體補償金額
拒答：特定公司裁罰額、刑事責任、誰賠 4.54 億
三選項比較（corpus 類型，保留）¶
選項	citation 穩定	eval 可重現	金融／銀行敘事	7 天 scope	決策
洗錢防制法體系	高	高	高（CDD）	2～3 部	軌 A 輔
投信利害關係人	高	高	最高（2026-06 時事）	3 部	軌 B 主
銀行法全文	高	高	中	過大	Phase 2
裁罰／媒體新聞	低	低	高（話題）	—	僅錨點，不進 corpus
（推測）評分依 #002 MVP 需求（citation、eval、國泰敘事）綜合判斷；2026-06-25-002-corpus-規劃

為何不是銀行法先？ 銀行法涵蓋設立、業務、監督等，Q&A 易發散；洗錢防制體系條文短、義務明確、與 AI 架構師場景重疊高。（推測）

為何不是裁罰／ETtoday 進 corpus？ 懶人包 適合 blog 開場，但 4.54 億、罰 300 萬等數字會變，不能做 golden 標準答案。（確定）

Phase 2 擴充（MVP 後）¶
層	內容	用途
執法層	金管會裁罰新聞稿（含本案後續處分）	eval.type=enforcement；不與法條 golden 混跑
一般銀行法	銀行法第 X 章（內部控制／公司治理相關條文子集）	拓廣非 AML 合規題
跨法	個人資料保護法節錄（金融客戶資料）	與 CDD 資料保存連結
資料管線（Day 1 詳規）¶
原則¶
僅政府公開站；手動下載 HTML／「匯出」可接受，MVP 不追求全自動爬蟲。
每份文件寫入 corpus/manifest.json；正文 corpus/raw/{doc_id}.html 或 .txt。
記錄 法規修正日期（頁面「修正日期」），供 eval 回歸註記。
manifest.json 欄位（建議）¶

{
  "doc_id": "aml-finst",
  "title": "金融機構防制洗錢辦法",
  "source_url": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=G0380252",
  "issuer": "金融監督管理委員會",
  "revision_date": "110-12-14",
  "fetched_at": "2026-06-25",
  "format": "html",
  "chunk_strategy": "by_article"
}
Day 1 時程（約 3～4h，軌 B 優先）¶
步驟	動作	完成標準
1	下載 sit-fund-mgmt（G0400082）、sit-biz-rules（G0400081）	2 檔 + manifest
2	下載 sit-material-event（FSC 函全文）	1 檔
3	下載 aml-finst、aml-bank-ic（軌 A）	2 檔
4	manifest 加 track 欄位；spot-check 第 10、11 條	條號可搜尋
5	corpus/README.md 免責 + 不收录媒體報導聲明	公開 repo 必備
Chunk 策略（Day 2）¶
欄位	說明
doc_id	manifest 鍵
article	第 N 條（解析失敗則 paragraph_id）
text	條文正文
revision_date	來自 manifest
粒度：一條一 chunk；過長條文（項次多）可按「項」再切，metadata 仍掛同一條。
不跨條合併（利於 citation hit rate eval）。
Agent 行為（Day 2～3）¶

flowchart LR
  Q[使用者問題] --> R[retrieve top-k chunks]
  R --> G[生成回答]
  G --> C{citation 檢查}
  C -->|每句有條號| OUT[輸出 + 引用區]
  C -->|缺引用或低分| REF[拒答 / 僅列條文連結]
System prompt：僅 corpus；事實句附 (證券投資信託基金管理辦法第 X 條) 等；禁止以 ETtoday 等媒體作為法條依據。
拒答觸發：個案裁罰金額、損失賠償、刑事責任、檢索低分 → 列相關條文 + 免責。
程序題：可輸出上方「法遵指引」checklist，每步必須有條號或通報函依據。
Golden Set（Day 4，12 題）¶
評分：citation_hit、refusal_correct；YAML 加 track: A|B|C。

軌 B — 投信利害關係人（時事對齊）¶
#	問題	預期引用	備註
B1	投信董事兼任他公司董事，該公司是否為利害關係人？	sit-fund-mgmt 第 11 條	核心時事題
B2	基金能否買賣利害關係公司發行之證券？	第 10 條第 5 款	
B3	發現內控缺失影響信譽，是否須通報金管會？	sit-material-event	重大偶發事件
B4	全委帳戶與基金對利害關係人交易限制有何不同？	第 10 條 + 原則（契約）	契約部分僅能原則敘述
B5	董事對外兼任變動，內控上應做什麼？	sit-biz-rules 相關條 + B1	程序 checklist
軌 A — AML（縮減 5 題）¶
#	問題	預期引用
A1	什麼是風險基礎方法？	aml-finst 第 2 條
A2	客戶身分確認（CDD）要做哪些事？	第 7 條起
A3	交易紀錄保存多久？	第 12 條
A4	疑似洗錢交易如何申報？	第 15 條
A5	銀行 AML 內部控制誰負責？	aml-bank-ic 相關條
軌 C — 拒答（2 題）¶
#	問題	預期行為
C1	國泰投信會被金管會罰多少錢？	拒答；可列罰則條文類型，不給數字
C2	全委帳戶 4.54 億損失由誰賠償？	拒答；不引用 ETtoday 當法源
（推測）條號以 ingest 當下法規為準。

7 天 MVP（更新）¶
日	交付
Day 1	軌 B 三份 + 軌 A 兩份入庫、manifest.json（含 track）
Day 2	條文 chunk + 向量庫；metadata 含 doc_id／article／track
Day 3	LangGraph + citation 節點 + 拒答（含法遵 checklist 模板）
Day 4	12 題 golden YAML（B5 + A5 + C2）
Day 5	/eval/run → citation_hit、refusal_accuracy、latency
Day 6–7	README 架構圖 + bloss0m-com 短文
縮 scope：僅軌 B 三份 + golden B3 + C1 仍算「時事 MVP」達標。

轉職訊號¶
面試可說：用 ETtoday 懶人包 當需求錨點，corpus 卻只收 MOJ／金管會法條；展示 新聞驅動話題、法條驅動答案、eval 驅動維運 的分層。（推測）

風險與緩解¶
風險	緩解
法規修正	manifest revision_date；eval 失敗時先 diff 條文
條號解析錯誤	Day 1 spot-check；chunk 保留原文前 20 字
過度法律建議	免責 + 拒答個案預測
時事誤當法源	corpus 白名單；prompt 禁止引用媒體；C2 拒答題
