# Open Data Usage Markdown 工具

這個專案會整理臺北市與新北市開放資料平台的資料集資訊，並輸出 Markdown 報表。

目前目錄中的重點檔案：

- `fetch_open_data_stats.py`: 從 API 抓取資料並產生兩份總表
- `taipei_open_data_usage.md`: 臺北市總表（含全部主題）
- `ntpc_open_data_usage.md`: 新北市總表（含全部主題）
- `topics_taipei/`: 臺北市「每主題一檔」輸出
- `topics_ntpc/`: 新北市「每主題一檔」輸出

## 環境需求

- Python 3.10+
- 不需安裝第三方套件（只使用標準函式庫）

## 使用方式

1. 進入專案資料夾

```bash
cd "c:\\Users\\ncc\\Downloads\\open data"
```

2. 重新抓取資料並產生兩份總表

```bash
python fetch_open_data_stats.py
```

3. 若已經有總表，想要拆成每主題一個檔案（不重抓資料）

目前已完成拆分，輸出在：

- `topics_taipei/README.md`
- `topics_ntpc/README.md`

這兩份索引檔可直接在 GitHub 點進去看各主題檔案。

## 欄位說明

每個資料集會整理以下欄位：

1. 資料集名稱
2. 使用次數
3. 更新時間
4. 主題分類

排序方式：依使用次數由大到小。

> 新北市平台若沒有 `use_count`，會使用 `view_count` 作為使用次數。
