# Open Data Usage Markdown 工具

本工具旨在協助使用者快速瀏覽和分析臺北市與新北市的 Open Data 使用情況。透過將資料分類並生成 Markdown 文件，使用者可以輕鬆地查看各類別的資料數量和相關主題。

## 主題連結（根目錄快速入口）

以下表格已按「各類別資料數量」由大到小排序，可直接點進各主題 Markdown。

### 臺北市（依類別資料數量排序）

| 排名 | 類別                | 資料數量 | 主題檔案                                                    |
| ---: | ------------------- | -------: | ----------------------------------------------------------- |
|    1 | 教育                |     7505 | [教育](topics_taipei/教育.md)                               |
|    2 | 未分類              |     5742 | [未分類](topics_taipei/未分類.md)                           |
|    3 | 醫療                |      994 | [醫療](topics_taipei/醫療.md)                               |
|    4 | 文化                |      864 | [文化](topics_taipei/文化.md)                               |
|    5 | 統計                |      820 | [統計](topics_taipei/統計.md)                               |
|    6 | 社福                |      794 | [社福](topics_taipei/社福.md)                               |
|    7 | 工務                |      721 | [工務](topics_taipei/工務.md)                               |
|    8 | 交通                |      579 | [交通](topics_taipei/交通.md)                               |
|    9 | 法律                |      485 | [法律](topics_taipei/法律.md)                               |
|   10 | 民政                |      404 | [民政](topics_taipei/民政.md)                               |
|   11 | 財稅                |      404 | [財稅](topics_taipei/財稅.md)                               |
|   12 | 觀光                |      362 | [觀光](topics_taipei/觀光.md)                               |
|   13 | 環保                |      320 | [環保](topics_taipei/環保.md)                               |
|   14 | 地政                |      178 | [地政](topics_taipei/地政.md)                               |
|   15 | 消防                |      167 | [消防](topics_taipei/消防.md)                               |
|   16 | 水利                |      156 | [水利](topics_taipei/水利.md)                               |
|   17 | 資訊                |      141 | [資訊](topics_taipei/資訊.md)                               |
|   18 | 農業                |      111 | [農業](topics_taipei/農業.md)                               |
|   19 | 勞動                |      100 | [勞動](topics_taipei/勞動.md)                               |
|   20 | 經濟                |       93 | [經濟](topics_taipei/經濟.md)                               |
|   21 | 治安                |       85 | [治安](topics_taipei/治安.md)                               |
|   22 | 族群                |       60 | [族群](topics_taipei/族群.md)                               |
|   23 | 無                  |       45 | [無](topics_taipei/無.md)                                   |
|   24 | 都更                |       35 | [都更](topics_taipei/都更.md)                               |
|   25 | 2026-01-14 12:05:36 |        1 | [2026-01-14 12:05:36](topics_taipei/2026-01-14_12_05_36.md) |

### 新北市（依類別資料數量排序）

| 排名 | 類別 | 資料數量 | 主題檔案                    |
| ---: | ---- | -------: | --------------------------- |
|    1 | 財稅 |      693 | [財稅](topics_ntpc/財稅.md) |
|    2 | 統計 |      237 | [統計](topics_ntpc/統計.md) |
|    3 | 交通 |      136 | [交通](topics_ntpc/交通.md) |
|    4 | 醫療 |      120 | [醫療](topics_ntpc/醫療.md) |
|    5 | 地政 |      115 | [地政](topics_ntpc/地政.md) |
|    6 | 資訊 |       76 | [資訊](topics_ntpc/資訊.md) |
|    7 | 社福 |       44 | [社福](topics_ntpc/社福.md) |
|    8 | 治安 |       38 | [治安](topics_ntpc/治安.md) |
|    9 | 環保 |       37 | [環保](topics_ntpc/環保.md) |
|   10 | 研考 |       32 | [研考](topics_ntpc/研考.md) |
|   11 | 消防 |       26 | [消防](topics_ntpc/消防.md) |
|   12 | 觀光 |       23 | [觀光](topics_ntpc/觀光.md) |
|   13 | 經濟 |       22 | [經濟](topics_ntpc/經濟.md) |
|   14 | 農業 |       22 | [農業](topics_ntpc/農業.md) |
|   15 | 水利 |       19 | [水利](topics_ntpc/水利.md) |
|   16 | 城鄉 |       18 | [城鄉](topics_ntpc/城鄉.md) |
|   17 | 文化 |       18 | [文化](topics_ntpc/文化.md) |
|   18 | 民政 |       17 | [民政](topics_ntpc/民政.md) |
|   19 | 工務 |       13 | [工務](topics_ntpc/工務.md) |
|   20 | 教育 |       12 | [教育](topics_ntpc/教育.md) |
|   21 | 勞動 |        9 | [勞動](topics_ntpc/勞動.md) |
|   22 | 族群 |        4 | [族群](topics_ntpc/族群.md) |


## 專案結構


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
