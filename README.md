# 學習精靈 Learning Sprites — 英文單字 × 寵物戰棋

用背英文單字來養精靈寵物，再讓 6 隻寵物在六角格棋盤上自動對戰。

本專案目前包含一個**簡易版原型**（單一 HTML 檔），以及產品規格文件 [Brief.md](Brief.md)。

## 檔案

| 檔案 | 說明 |
| --- | --- |
| `learning-spirit.html` | 簡易版原型，單一網頁，不需安裝，直接用瀏覽器開啟即可 |
| `Brief.md` | 產品規格（目標、範圍、寵物、對戰、平台與 AI、風險） |

## 如何執行

1. 下載或 clone 本專案
   ```bash
   git clone https://github.com/Ruijun711/Learning-Sprites-English-Vocabulary-x-Pet-Chess-.git
   ```
2. 用瀏覽器（Chrome / Edge / Firefox）開啟 `learning-spirit.html`

進度存在瀏覽器的 `localStorage`，可在「說明與設定」頁清除重來。

## 原型功能

| 分頁 | 內容 |
| --- | --- |
| 做題 | 英選中、中選英、拼字、例句填空；依熟練度換題型；錯題題庫與強制練錯題；每日抽考；寵物額外題目 |
| 寵物倉庫 | 桌面隊伍（最多 6 隻）與倉庫；經驗值、升級、3 階段進化；掉蛋與孵化；心情 |
| 對戰 | 六角格棋盤戰前排陣，6 對 6 自動移動、攻擊、施放技能；同屬性羈絆加成；戰鬥回放 |
| 單字紀錄 | 每個看過的字的次數、對錯、上次看到的時間與熟練度 |
| 說明與設定 | 規則說明、清除資料 |

### 主要規則（摘要）

- 選擇題答對 10 點、拼字答對 15 點，每天上限 300 點（抽考不計入上限）
- 答對時桌面上每隻寵物都獲得全額經驗值
- 每答對一題 5% 機率掉蛋，蛋的屬性取決於單字類別；再答對 10 題孵化
- 進化需同時達到經驗值門檻與該屬性學會的單字數（第 2 階段 5 字、第 3 階段 15 字）
- 寵物屬性：食物、自然、身體與健康、生活、社會與工作、通用

完整規則請見 [Brief.md](Brief.md)。

## 正式版規劃

- **平台**：Windows 桌面小程式，PySide6（桌面寵物、系統匣）＋ QWebEngineView 內嵌本機 Flask 網頁
- **對戰伺服器**：Flask API（上傳隊伍、找對手、算戰鬥、排行榜），非同步對戰
- **AI**：以 Logistic Regression 預測遺忘（對照隨機森林／梯度提升），使用 Duolingo 公開資料集訓練，決定抽考與錯題順序
- **單字**：NGSL 高頻 300 字；例句來自 Tatoeba（CC BY 2.0 FR）

## 參考資料

- NGSL 新通用詞彙表：https://www.newgeneralservicelist.com
- Tatoeba 例句庫（CC BY 2.0 FR）：https://tatoeba.org/downloads
- Duolingo halflife-regression：https://github.com/duolingo/halflife-regression
