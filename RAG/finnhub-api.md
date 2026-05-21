# Finnhub API リファレンス

- 取得元: <https://finnhub.io/static/swagger.json> （`https://finnhub.io/docs/api` の元データ）
- 取得日: 2026-05-21
- API バージョン: 1.0.0
- ベース URL: `https://finnhub.io/api/v1`
- 認証: 全エンドポイント共通。クエリ引数 `token=<APIキー>` を付ける（例: `?symbol=AAPL&token=xxx`）
- レート制限: 無料枠は 1 分あたり 60 回。超過すると HTTP 429
- リアルタイム配信(WebSocket): `wss://ws.finnhub.io?token=<APIキー>`（無料枠は同時 50 銘柄まで）
- `Premium` 表記のエンドポイントは有料プラン専用

> RAG 用の自動生成リファレンス。1 エンドポイント = 1 見出し。

---

## Stock Fundamentals

### Symbol Lookup

`GET https://finnhub.io/api/v1/search`

Search for best-matching symbols based on your query. You can input anything from symbol, security's name to ISIN and Cusip.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `q` | query | string | はい | Query text can be symbol, name, isin, or cusip. |
| `exchange` | query | string | いいえ | Exchange limit. |

**応答**: `SymbolLookup` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `result` | array of SymbolLookupInfo | Array of search results. |
| `count` | integer | Number of results. |

<details><summary>応答例</summary>

```json
{
  "count": 4,
  "result": [
    {
      "description": "APPLE INC",
      "displaySymbol": "AAPL",
      "symbol": "AAPL",
      "type": "Common Stock"
    },
    {
      "description": "APPLE INC",
      "displaySymbol": "AAPL.SW",
      "symbol": "AAPL.SW",
      "type": "Common Stock"
    },
    {
      "description": "APPLE INC",
      "displaySymbol": "APC.BE",
      "symbol": "APC.BE",
      "type": "Common Stock"
    },
    {
      "description": "APPLE INC",
      "displaySymbol": "APC.DE",
      "symbol": "APC.DE",
      "type": "Common Stock"
    }
  ]
}
```

</details>

---

### Stock Symbol

`GET https://finnhub.io/api/v1/stock/symbol`

List supported stocks. We use the following symbology to identify stocks on Finnhub Exchange_Ticker.Exchange_Code. A list of supported exchange codes can be found here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `exchange` | query | string | はい | Exchange you want to get the list of symbols from. List of exchange codes can be found here. |
| `mic` | query | string | いいえ | Filter by MIC code. |
| `securityType` | query | string | いいえ | Filter by security type used by OpenFigi standard. |
| `currency` | query | string | いいえ | Filter by currency. |

**応答**: `StockSymbol` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `description` | string | Symbol description |
| `displaySymbol` | string | Display symbol name. |
| `symbol` | string | Unique symbol used to identify this symbol used in /stock/candle endpoint. |
| `type` | string | Security type. |
| `mic` | string | Primary exchange's MIC. |
| `figi` | string | FIGI identifier. |
| `shareClassFIGI` | string | Global Share Class FIGI. |
| `currency` | string | Price's currency. This might be different from the reporting currency of fundamental data. |
| `symbol2` | string | Alternative ticker for exchanges with multiple tickers for 1 stock such as BSE. |
| `isin` | string | ISIN. This field is only available for EU stocks and selected Asian markets. Entitlement from Finnhub is required to access this field. |

<details><summary>応答例</summary>

```json
[
  {
    "currency": "USD",
    "description": "UAN POWER CORP",
    "displaySymbol": "UPOW",
    "figi": "BBG000BGHYF2",
    "mic": "OTCM",
    "symbol": "UPOW",
    "type": "Common Stock"
  },
  {
    "currency": "USD",
    "description": "APPLE INC",
    "displaySymbol": "AAPL",
    "figi": "BBG000B9Y5X2",
    "mic": "XNGS",
    "symbol": "AAPL",
    "type": "Common Stock"
  },
  {
    "currency": "USD",
    "description": "EXCO TECHNOLOGIES LTD",
    "displaySymbol": "EXCOF",
    "figi": "BBG000JHDDS8",
    "mic": "OOTC",
    "symbol": "EXCOF",
    "type": "Common Stock"
  }
]
```

</details>

---

### Market Status

`GET https://finnhub.io/api/v1/stock/market-status`

区分: 新規

Get current market status for global exchanges (whether exchanges are open or close).

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `exchange` | query | string | はい | Exchange code. |

**応答**: `MarketStatus` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `exchange` | string | Exchange. |
| `timezone` | string | Timezone. |
| `session` | string | Market session. Can be 1 of the following values: pre-market,regular,post-market or null if the market is closed. |
| `holiday` | string | Holiday event. |
| `isOpen` | boolean | Whether the market is open at the moment. |
| `t` | integer | Current timestamp. |

<details><summary>応答例</summary>

```json
{
  "exchange": "US",
  "holiday": null,
  "isOpen": false,
  "session": "pre-market",
  "timezone": "America/New_York",
  "t": 1697018041
}
```

</details>

---

### Market Holiday

`GET https://finnhub.io/api/v1/stock/market-holiday`

区分: 新規

Get a list of holidays for global exchanges.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `exchange` | query | string | はい | Exchange code. |

**応答**: `MarketHoliday` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `timezone` | string | Timezone. |
| `exchange` | string | Exchange. |
| `data` | array of MarketHolidayData | Array of holidays. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "eventName": "Christmas",
      "atDate": "2023-12-25",
      "tradingHour": ""
    },
    {
      "eventName": "Independence Day",
      "atDate": "2023-07-03",
      "tradingHour": "09:30-13:00"
    }
  ],
  "exchange": "US",
  "timezone": "America/New_York"
}
```

</details>

---

### Company Profile

`GET https://finnhub.io/api/v1/stock/profile`

区分: **Premium(有料プラン専用)**

Get general information of a company. You can query by symbol, ISIN or CUSIP

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Symbol of the company: AAPL e.g. |
| `isin` | query | string | いいえ | ISIN |
| `cusip` | query | string | いいえ | CUSIP |

**応答**: `CompanyProfile` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `alias` | array of string | Company name alias. |
| `address` | string | Address of company's headquarter. |
| `city` | string | City of company's headquarter. |
| `country` | string | Country of company's headquarter. |
| `currency` | string | Currency used in company filings and financials. |
| `estimateCurrency` | string | Currency used in Estimates data. |
| `marketCapCurrency` | string | Currency used in market capitalization. |
| `cusip` | string | CUSIP number. |
| `sedol` | string | Sedol number. |
| `description` | string | Company business summary. |
| `exchange` | string | Listed exchange. |
| `ggroup` | string | Industry group. |
| `gind` | string | Industry. |
| `gsector` | string | Sector. |
| `gsubind` | string | Sub-industry. |
| `isin` | string | ISIN number. |
| `lei` | string | LEI number. |
| `irUrl` | string | Investor relations website. |
| `naicsNationalIndustry` | string | NAICS national industry. |
| `naics` | string | NAICS industry. |
| `naicsSector` | string | NAICS sector. |
| `naicsSubsector` | string | NAICS subsector. |
| `name` | string | Company name. |
| `phone` | string | Company phone number. |
| `state` | string | State of company's headquarter. |
| `ticker` | string | Company symbol/ticker as used on the listed exchange. |
| `weburl` | string | Company website. |
| `ipo` | string | IPO date. |
| `marketCapitalization` | number | Market Capitalization. |
| `shareOutstanding` | number | Number of oustanding shares. |
| `employeeTotal` | number | Number of employee. |
| `logo` | string | Logo image. |
| `finnhubIndustry` | string | Finnhub industry classification. |

<details><summary>応答例</summary>

```json
{
  "address": "1 Apple Park Way",
  "city": "CUPERTINO",
  "country": "US",
  "currency": "USD",
  "cusip": "",
  "sedol":"2046251",
  "description": "Apple Inc. is an American multinational technology company headquartered in Cupertino, California, that designs, develops, and sells consumer electronics, computer software, and online services. It is considered one of the Big Four technology companies, alongside Amazon, Google, and Microsoft. The company's hardware products include the iPhone smartphone, the iPad tablet computer, the Mac personal computer, the iPod portable media player, the Apple Watch smartwatch, the Apple TV digital media player, the AirPods wireless earbuds and the HomePod smart speaker. Apple's software includes the macOS, iOS, iPadOS, watchOS, and tvOS operating systems, the iTunes media player, the Safari web browser, the Shazam acoustic fingerprint utility, and the iLife and iWork creativity and productivity suites, as well as professional applications like Final Cut Pro, Logic Pro, and Xcode. Its online services include the iTunes Store, the iOS App Store, Mac App Store, Apple Music, Apple TV+, iMessage, and iCloud. Other services include Apple Store, Genius Bar, AppleCare, Apple Pay, Apple Pay Cash, and Apple Card.",
  "employeeTotal": "137000",
  "exchange": "NASDAQ/NMS (GLOBAL MARKET)",
  "ggroup": "Technology Hardware & Equipment",
  "gind": "Technology Hardware, Storage & Peripherals",
  "gsector": "Information Technology",
  "gsubind": "Technology Hardware, Storage & Peripherals",
  "ipo": "1980-12-12",
  "isin": "",
  "marketCapitalization": 1415993,
  "naics": "Communications Equipment Manufacturing",
  "naicsNationalIndustry": "Radio and Television Broadcasting and Wireless Communications Equipment Manufacturing",
  "naicsSector": "Manufacturing",
  "naicsSubsector": "Computer and Electronic Product Manufacturing",
  "name": "Apple Inc",
  "phone": "14089961010",
  "shareOutstanding": 4375.47998046875,
  "state": "CALIFORNIA",
  "ticker": "AAPL",
  "weburl": "https://www.apple.com/",
  "logo": "https://static.finnhub.io/logo/87cb30d8-80df-11ea-8951-00000000092a.png",
  "finnhubIndustry":"Technology"
}
```

</details>

---

### Company Profile 2

`GET https://finnhub.io/api/v1/stock/profile2`

区分: 新規

Get general information of a company. You can query by symbol, ISIN or CUSIP. This is the free version of Company Profile.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Symbol of the company: AAPL e.g. |
| `isin` | query | string | いいえ | ISIN |
| `cusip` | query | string | いいえ | CUSIP |

**応答**: `CompanyProfile2` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `country` | string | Country of company's headquarter. |
| `currency` | string | Currency used in company filings. |
| `exchange` | string | Listed exchange. |
| `name` | string | Company name. |
| `ticker` | string | Company symbol/ticker as used on the listed exchange. |
| `ipo` | string | IPO date. |
| `marketCapitalization` | number | Market Capitalization. |
| `shareOutstanding` | number | Number of oustanding shares. |
| `logo` | string | Logo image. |
| `phone` | string | Company phone number. |
| `weburl` | string | Company website. |
| `finnhubIndustry` | string | Finnhub industry classification. |

<details><summary>応答例</summary>

```json
{
  "country": "US",
  "currency": "USD",
  "exchange": "NASDAQ/NMS (GLOBAL MARKET)",
  "ipo": "1980-12-12",
  "marketCapitalization": 1415993,
  "name": "Apple Inc",
  "phone": "14089961010",
  "shareOutstanding": 4375.47998046875,
  "ticker": "AAPL",
  "weburl": "https://www.apple.com/",
  "logo": "https://static.finnhub.io/logo/87cb30d8-80df-11ea-8951-00000000092a.png",
  "finnhubIndustry":"Technology"
}
```

</details>

---

### Company Executive

`GET https://finnhub.io/api/v1/stock/executive`

区分: **Premium(有料プラン専用)**

Get a list of company's executives and members of the Board.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |

**応答**: `CompanyExecutive` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Company symbol. |
| `executive` | array of Company | Array of company's executives and members of the Board. |

<details><summary>応答例</summary>

```json
{
  "executive": [
    {
      "age": 56,
      "compensation": 25209637,
      "currency": "USD",
      "name": "Luca Maestri",
      "position": "Senior Vice President and Chief Financial Officer",
      "sex": "male",
      "since": "2014"
    },
    {
      "age": 59,
      "compensation": 11555466,
      "currency": "USD",
      "name": "Mr. Timothy Cook",
      "position": "Director and Chief Executive Officer",
      "sex": "male",
      "since": "2011"
    }
  ]
}
```

</details>

---

### Market News

`GET https://finnhub.io/api/v1/news`

Get latest market news.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `category` | query | string | はい | This parameter can be 1 of the following values general, forex, crypto, merger. |
| `minId` | query | integer | いいえ | Use this field to get only news after this ID. Default to 0 |

**応答**: `MarketNews` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `category` | string | News category. |
| `datetime` | integer | Published time in UNIX timestamp. |
| `headline` | string | News headline. |
| `id` | integer | News ID. This value can be used for minId params to get the latest news only. |
| `image` | string | Thumbnail image URL. |
| `related` | string | Related stocks and companies mentioned in the article. |
| `source` | string | News source. |
| `summary` | string | News summary. |
| `url` | string | URL of the original article. |

<details><summary>応答例</summary>

```json
[
  {
    "category": "technology",
    "datetime": 1596589501,
    "headline": "Square surges after reporting 64% jump in revenue, more customers using Cash App",
    "id": 5085164,
    "image": "https://image.cnbcfm.com/api/v1/image/105569283-1542050972462rts25mct.jpg?v=1542051069",
    "related": "",
    "source": "CNBC",
    "summary": "Shares of Square soared on Tuesday evening after posting better-than-expected quarterly results and strong growth in its consumer payments app.",
    "url": "https://www.cnbc.com/2020/08/04/square-sq-earnings-q2-2020.html"
  },
  {
    "category": "business",
    "datetime": 1596588232,
    "headline": "B&G Foods CEO expects pantry demand to hold up post-pandemic",
    "id": 5085113,
    "image": "https://image.cnbcfm.com/api/v1/image/106629991-1595532157669-gettyimages-1221952946-362857076_1-5.jpeg?v=1595532242",
    "related": "",
    "source": "CNBC",
    "summary": "\"I think post-Covid, people will be working more at home, which means people will be eating more breakfast\" and other meals at home, B&G CEO Ken Romanzi said.",
    "url": "https://www.cnbc.com/2020/08/04/bg-foods-ceo-expects-pantry-demand-to-hold-up-post-pandemic.html"
  },
  {
    "category": "top news",
    "datetime": 1596584406,
    "headline": "Anthony Levandowski gets 18 months in prison for stealing Google self-driving car files",
    "id": 5084850,
    "image": "https://image.cnbcfm.com/api/v1/image/106648265-1596584130509-UBER-LEVANDOWSKI.JPG?v=1596584247",
    "related": "",
    "source": "CNBC",
    "summary": "A U.S. judge on Tuesday sentenced former Google engineer Anthony Levandowski to 18 months in prison for stealing a trade secret from Google related to self-driving cars months before becoming the head of Uber Technologies Inc's rival unit.",
    "url": "https://www.cnbc.com/2020/08/04/anthony-levandowski-gets-18-months-in-prison-for-stealing-google-self-driving-car-files.html"
  }
  }]
```

</details>

---

### Company News

`GET https://finnhub.io/api/v1/company-news`

区分: 無料枠あり / 利用頻度高

List latest company news by symbol. This endpoint is only available for North American companies.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Company symbol. |
| `from` | query | string | はい | From date YYYY-MM-DD. |
| `to` | query | string | はい | To date YYYY-MM-DD. |

**応答**: `CompanyNews` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `category` | string | News category. |
| `datetime` | integer | Published time in UNIX timestamp. |
| `headline` | string | News headline. |
| `id` | integer | News ID. This value can be used for minId params to get the latest news only. |
| `image` | string | Thumbnail image URL. |
| `related` | string | Related stocks and companies mentioned in the article. |
| `source` | string | News source. |
| `summary` | string | News summary. |
| `url` | string | URL of the original article. |

<details><summary>応答例</summary>

```json
[
  {
    "category": "company news",
    "datetime": 1569550360,
    "headline": "More sops needed to boost electronic manufacturing: Top govt official More sops needed to boost electronic manufacturing: Top govt official.  More sops needed to boost electronic manufacturing: Top govt official More sops needed to boost electronic manufacturing: Top govt official",
    "id": 25286,
    "image": "https://img.etimg.com/thumb/msid-71321314,width-1070,height-580,imgsize-481831,overlay-economictimes/photo.jpg",
    "related": "AAPL",
    "source": "The Economic Times India",
    "summary": "NEW DELHI | CHENNAI: India may have to offer electronic manufacturers additional sops such as cheap credit and incentives for export along with infrastructure support in order to boost production and help the sector compete with China, Vietnam and Thailand, according to a top government official.These incentives, over and above the proposed reduction of corporate tax to 15% for new manufacturing units, are vital for India to successfully attract companies looking to relocate manufacturing facilities.“While the tax announcements made last week send a very good signal, in order to help attract investments, we will need additional initiatives,” the official told ET, pointing out that Indian electronic manufacturers incur 8-10% higher costs compared with other Asian countries.Sops that are similar to the incentives for export under the existing Merchandise Exports from India Scheme (MEIS) are what the industry requires, the person said.MEIS gives tax credit in the range of 2-5%. An interest subvention scheme for cheaper loans and a credit guarantee scheme for plant and machinery are some other possible measures that will help the industry, the official added.“This should be 2.0 (second) version of the electronic manufacturing cluster (EMC) scheme, which is aimed at creating an ecosystem with an anchor company plus its suppliers to operate in the same area,” he said.Last week, finance minister Nirmala Sitharaman announced a series of measures to boost economic growth including a scheme allowing any new manufacturing company incorporated on or after October 1, to pay income tax at 15% provided the company does not avail of any other exemption or incentives.",
    "url": "https://economictimes.indiatimes.com/industry/cons-products/electronics/more-sops-needed-to-boost-electronic-manufacturing-top-govt-official/articleshow/71321308.cms"
  },
  {
    "category": "company news",
    "datetime": 1569528720,
    "headline": "How to disable comments on your YouTube videos in 2 different ways",
    "id": 25287,
    "image": "https://amp.businessinsider.com/images/5d8d16182e22af6ab66c09e9-1536-768.jpg",
    "related": "AAPL",
    "source": "Business Insider",
    "summary": "You can disable comments on your own YouTube video if you don't want people to comment on it. It's easy to disable comments on YouTube by adjusting the settings for one of your videos in the beta or classic version of YouTube Studio. Visit Business Insider's homepage for more stories . The comments section has a somewhat complicated reputation for creators, especially for those making videos on YouTube . While it can be useful to get the unfiltered opinions of your YouTube viewers and possibly forge a closer connection with them, it can also open you up to quite a bit of negativity. So it makes sense that there may be times when you want to turn off the feature entirely. Just keep in mind that the action itself can spark conversation. If you decide that you don't want to let people leave comments on your YouTube video, here's how to turn off the feature, using either the classic or beta version of the creator studio: How to disable comments on YouTube in YouTube Studio (beta) 1. Go to youtube.com and log into your account, if necessary. 2.",
    "url": "https://www.businessinsider.com/how-to-disable-comments-on-youtube"
  },
  {
    "category": "company news",
    "datetime": 1569526180,
    "headline": "Apple iPhone 11 Pro Teardowns Look Encouraging for STMicro and Sony",
    "id": 25341,
    "image": "http://s.thestreet.com/files/tsc/v2008/photos/contrib/uploads/ba140938-d409-11e9-822b-fda891ce1fc1.png",
    "related": "AAPL",
    "source": "TheStreet",
    "summary": "STMicroelectronics and Sony each appear to be supplying four chips for Apple's latest flagship iPhones. Many other historical iPhone suppliers also make appearances in the latest teardowns….STM",
    "url": "https://realmoney.thestreet.com/investing/technology/iphone-11-pro-teardowns-look-encouraging-for-stmicro-sony-15105767"
  },
]
```

</details>

---

### Major Press Releases

`GET https://finnhub.io/api/v1/press-releases`

区分: **Premium(有料プラン専用)**

Get latest major press releases of a company. This data can be used to highlight the most significant events comprised of mostly press releases sourced from the exchanges, BusinessWire, AccessWire, GlobeNewswire, Newsfile, and PRNewswire.

Full-text press releases data is available for Enterprise clients. Contact Us to learn more.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Company symbol. |
| `from` | query | string | いいえ | From time: 2020-01-01. |
| `to` | query | string | いいえ | To time: 2020-01-05. |

**応答**: `PressRelease` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Company symbol. |
| `majorDevelopment` | array of Development | Array of major developments. |

<details><summary>応答例</summary>

```json
{
  "majorDevelopment": [
    {
      "symbol": "AAPL",
      "datetime": "2020-08-04 17:06:32",
      "headline": "27-inch iMac Gets a Major Update",
      "description": "CUPERTINO, Calif.--(BUSINESS WIRE)-- Apple today announced a major update to its 27-inch iMac®. By far the most powerful and capable iMac ever, it features faster Intel processors up to 10 cores, double the memory capacity, next-generation AMD graphics, superfast SSDs across the line with four times the storage capacity, a new nano-texture glass option for an even more stunning Retina® 5K display, a 1080p FaceTime® HD camera, higher fidelity speakers, and studio-quality mics. For the consumer using their iMac all day, every day, to the aspiring creative looking for inspiration, to the serious pro pushing the limits of their creativity, the new 27-inch iMac delivers the ultimate desktop experience that is now better in every way."
    },
    {
      "symbol": "AAPL",
      "datetime": "2020-03-28 09:41:23",
      "headline": "Apple Central World Opens Friday in Thailand",
      "description": "BANGKOK--(BUSINESS WIRE)-- Apple® today previewed Apple Central World, its second and largest retail location in Thailand. Nestled in the heart of Ratchaprasong, Bangkok’s iconic intersection, the store provides a completely new and accessible destination within the lively city. Apple Central World’s distinctive architecture is brought to life with the first-ever all-glass design, housed under a cantilevered Tree Canopy roof. Once inside, customers can travel between two levels via a spiral staircase that wraps around a timber core, or riding a unique cylindrical elevator clad in mirror-polished stainless steel. Guests can enter from the ground or upper level, which provides a direct connection to the Skytrain and the city’s largest shopping center. The outdoor plaza offers a place for the community to gather, with benches and large Terminalia trees surrounding the space."
    }
  ],
   "symbol": "AAPL"
}
```

</details>

---

### News Sentiment

`GET https://finnhub.io/api/v1/news-sentiment`

区分: **Premium(有料プラン専用)**

Get company's news sentiment and statistics. This endpoint is only available for US companies.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Company symbol. |

**応答**: `NewsSentiment` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `buzz` | CompanyNewsStatistics | Statistics of company news in the past week. |
| `companyNewsScore` | number | News score. |
| `sectorAverageBullishPercent` | number | Sector average bullish percent. |
| `sectorAverageNewsScore` | number | Sectore average score. |
| `sentiment` | Sentiment | News sentiment. |
| `symbol` | string | Requested symbol. |

<details><summary>応答例</summary>

```json
{
  "buzz": {
    "articlesInLastWeek": 20,
    "buzz": 0.8888,
    "weeklyAverage": 22.5
  },
  "companyNewsScore": 0.9166,
  "sectorAverageBullishPercent": 0.6482,
  "sectorAverageNewsScore": 0.5191,
  "sentiment": {
    "bearishPercent": 0,
    "bullishPercent": 1
  },
  "symbol": "V"
}
```

</details>

---

### Peers

`GET https://finnhub.io/api/v1/stock/peers`

Get company peers. Return a list of peers operating in the same country and sector/industry.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `grouping` | query | string | いいえ | Specify the grouping criteria for choosing peers.Supporter values: sector, industry, subIndustry. Default to subIndustry. |

**応答**: array of string

<details><summary>応答例</summary>

```json
[
  "AAPL",
  "EMC",
  "HPQ",
  "DELL",
  "WDC",
  "HPE",
  "NTAP",
  "CPQ",
  "SNDK",
  "SEG"
]
```

</details>

---

### Basic Financials

`GET https://finnhub.io/api/v1/stock/metric`

区分: 利用頻度高

Get company basic financials such as margin, P/E ratio, 52-week high/low etc.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `metric` | query | string | はい | Metric type. Can be 1 of the following values all |

**応答**: `BasicFinancials` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol of the company. |
| `metricType` | string | Metric type. |
| `series` | MetricSeriesMap | Map key-value pair of time-series ratios. |
| `metric` | MetricMap | Map key-value pair of key ratios and metrics. |

<details><summary>応答例</summary>

```json
{
   "series": {
    "annual": {
      "currentRatio": [
        {
          "period": "2019-09-28",
          "v": 1.5401
        },
        {
          "period": "2018-09-29",
          "v": 1.1329
        }
      ],
      "salesPerShare": [
        {
          "period": "2019-09-28",
          "v": 55.9645
        },
        {
          "period": "2018-09-29",
          "v": 53.1178
        }
      ],
      "netMargin": [
        {
          "period": "2019-09-28",
          "v": 0.2124
        },
        {
          "period": "2018-09-29",
          "v": 0.2241
        }
      ]
    }
  },
  "metric": {
    "10DayAverageTradingVolume": 32.50147,
    "52WeekHigh": 310.43,
    "52WeekLow": 149.22,
    "52WeekLowDate": "2019-01-14",
    "52WeekPriceReturnDaily": 101.96334,
    "beta": 1.2989,
  },
  "metricType": "all",
  "symbol": "AAPL"
}
```

</details>

---

### Price Metrics

`GET https://finnhub.io/api/v1/stock/price-metric`

区分: **Premium(有料プラン専用)**

Get company price performance statistics such as 52-week high/low, YTD return and much more.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `date` | query | string | いいえ | Get data on a specific date in the past. The data is available weekly so your date will be automatically adjusted to the last day of that week. |

**応答**: `PriceMetrics` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol of the company. |
| `atDate` | string | Data date. |
| `data` | PriceMetricMap | Map key-value pair of key ratios and metrics. |

<details><summary>応答例</summary>

```json
{
  "data": {
    "100DayEMA": 295.7694,
    "100DaySMA": 319.2297,
    "10DayAverageTradingVolume": 53717320,
    "10DayEMA": 247.4641,
    "10DaySMA": 247.372,
    "14DayRSI": 34.0517,
    "1MonthHigh": 314.67,
    "1MonthHighDate": "2022-08-16",
    "50DayEMA": 277.482,
    "50DaySMA": 288.313,
    "52WeekHigh": 414.5,
    "52WeekHighDate": "2021-11-04",
    "52WeekLow": 206.86,
    "52WeekLowDate": "2022-05-24",
    "5DayEMA": 245.8814,
    "ytdPriceReturn": 10.1819
  },
  "symbol": "TSLA"
}
```

</details>

---

### Symbol Change

`GET https://finnhub.io/api/v1/ca/symbol-change`

区分: **Premium(有料プラン専用)**

Get a list of symbol changes for US-listed, EU-listed, NSE and ASX securities. Limit to 2000 events at a time.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `from` | query | string | はい | From date YYYY-MM-DD. |
| `to` | query | string | はい | To date YYYY-MM-DD. |

**応答**: `SymbolChange` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `fromDate` | string | From date. |
| `toDate` | string | To date. |
| `data` | array of SymbolChangeInfo | Array of symbol change events. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "atDate": "2022-10-05",
      "newSymbol": "MEN.L",
      "oldSymbol": "PPC.L"
    }
  ],
  "fromDate": "2022-10-01",
  "toDate": "2022-10-30"
}
```

</details>

---

### ISIN Change

`GET https://finnhub.io/api/v1/ca/isin-change`

区分: **Premium(有料プラン専用)**

Get a list of ISIN changes for EU-listed securities. Limit to 2000 events at a time.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `from` | query | string | はい | From date YYYY-MM-DD. |
| `to` | query | string | はい | To date YYYY-MM-DD. |

**応答**: `IsinChange` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `fromDate` | string | From date. |
| `toDate` | string | To date. |
| `data` | array of IsinChangeInfo | Array of ISIN change events. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "atDate": "2021-08-30",
      "newIsin": "DE000A3E5CP0",
      "oldIsin": "DE0007239402"
    }
  ],
  "fromDate": "2021-08-07",
  "toDate": "2021-10-07"
}
```

</details>

---

### Historical Market Cap

`GET https://finnhub.io/api/v1/stock/historical-market-cap`

区分: **Premium(有料プラン専用)**

Get historical market cap data for global companies.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Company symbol. |
| `from` | query | string | はい | From date YYYY-MM-DD. |
| `to` | query | string | はい | To date YYYY-MM-DD. |

**応答**: `HistoricalMarketCapData` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of MarketCapData | Array of market data. |
| `symbol` | string | Symbol |
| `currency` | string | Currency |

<details><summary>応答例</summary>

```json
{
  "currency": "USD",
  "data": [
    {
      "atDate": "2024-06-10",
      "marketCapitalization": 3759.182
    },
    {
      "atDate": "2024-06-09",
      "marketCapitalization": 21508.447
    }
  ],
  "symbol": "SYM"
}
```

</details>

---

### Historical Employee Count

`GET https://finnhub.io/api/v1/stock/historical-employee-count`

区分: **Premium(有料プラン専用)**

Get historical employee count for global companies.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Company symbol. |
| `from` | query | string | はい | From date YYYY-MM-DD. |
| `to` | query | string | はい | To date YYYY-MM-DD. |

**応答**: `HistoricalEmployeeCount` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of EmployeeCount | Array of market data. |
| `symbol` | string | Symbol |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "atDate": "2023-09-30",
      "employee": 161000
    },
    {
      "atDate": "2022-09-24",
      "employee": 164000
    },
    {
      "atDate": "2021-09-25",
      "employee": 154000
    },
    {
      "atDate": "2020-09-26",
      "employee": 147000
    }
  ],
  "symbol": "AAPL"
}
```

</details>

---

### Institutional Profile

`GET https://finnhub.io/api/v1/institutional/profile`

区分: **Premium(有料プラン専用)**

Get a list of well-known institutional investors. Currently support 60+ profiles.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `cik` | query | string | いいえ | Filter by CIK. Leave blank to get the full list. |

**応答**: `InstitutionalProfile` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `cik` | string | CIK. |
| `data` | array of InstitutionalProfileInfo | Array of investors. |

<details><summary>応答例</summary>

```json
{
  "cik": "1067983",
  "data": [
    {
      "cik": "1067983",
      "firmType": "Institutional Investment Manager",
      "manager": "Warren Buffett",
      "philosophy": "Value investing is the hallmark of Warren Buffett's investment approach. By choosing stocks whose share price is below their intrinsic or book value, value investors can increase their returns. This suggests that the stock will increase in value going forward and that the market is now undervaluing it. Only enterprises that Buffett is familiar with are chosen for investment by Berkshire, and a safety margin is always required.",
      "profile": "Warren Edward Buffett (born August 30, 1930) is an American business magnate, investor, and philanthropist. He is currently the chairman and CEO of Berkshire Hathaway. He is one of the most successful investors in the world and has a net worth of over $103 billion as of August 2022, making him the world's seventh-wealthiest person. Buffett has been the chairman and largest shareholder of Berkshire Hathaway since 1970. He has been referred to as the \"Oracle\" or \"Sage\" of Omaha by global media. He is noted for his adherence to value investing, and his personal frugality despite his immense wealth. Buffett is a philanthropist, having pledged to give away 99 percent of his fortune to philanthropic causes, primarily via the Bill \u0026 Melinda Gates Foundation. He founded The Giving Pledge in 2010 with Bill Gates, whereby billionaires pledge to give away at least half of their fortunes.",
      "profileImg": "https://static4.finnhub.io/file/publicdatany5/guru_profile_pic/1067983.jpg"
    }
  ]
}
```

</details>

---

### Institutional Portfolio

`GET https://finnhub.io/api/v1/institutional/portfolio`

区分: **Premium(有料プラン専用)**

Get the holdings/portfolio data of institutional investors from 13-F filings. Limit to 1 year of data at a time. You can get a list of supported CIK here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `cik` | query | string | はい | Fund's CIK. |
| `from` | query | string | はい | From date YYYY-MM-DD. |
| `to` | query | string | はい | To date YYYY-MM-DD. |

**応答**: `InstitutionalPortfolio` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `name` | string | Investor's name. |
| `cik` | string | CIK. |
| `data` | array of InstitutionalPortfolioGroup | Array of positions. |

<details><summary>応答例</summary>

```json
{
  "cik": "1000097",
  "data": [
    {
      "filingDate": "2022-06-30",
      "portfolio": [
        {
          "change": -41600,
          "name": "ABBOTT LABS",
          "noVoting": 0,
          "percentage": 0,
          "putCall": "",
          "share": 0,
          "sharedVoting": 0,
          "soleVoting": 41600,
          "symbol": "ABT",
          "value": 0
        },
        {
          "change": -275000,
          "name": "ADICET BIO INC",
          "noVoting": 0,
          "percentage": 0,
          "putCall": "",
          "share": 0,
          "sharedVoting": 0,
          "soleVoting": 275000,
          "symbol": "ACET",
          "value": 0
        }
      ],
      "reportDate": "2022-06-30"
    }
  ],
  "name": "KINGDON CAPITAL MANAGEMENT, L.L.C."
}
```

</details>

---

### Institutional Ownership

`GET https://finnhub.io/api/v1/institutional/ownership`

区分: **Premium(有料プラン専用)**

Get a list institutional investors' positions for a particular stock overtime. Data from 13-F filings. Limit to 1 year of data at a time.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Filter by symbol. |
| `cusip` | query | string | はい | Filter by CUSIP. |
| `from` | query | string | はい | From date YYYY-MM-DD. |
| `to` | query | string | はい | To date YYYY-MM-DD. |

**応答**: `InstitutionalOwnership` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `cusip` | string | Cusip. |
| `data` | array of InstitutionalOwnershipGroup | Array of institutional investors. |

<details><summary>応答例</summary>

```json
{
  "cusip": "023135106",
  "data": [
    {
      "ownership": [
        {
          "change": null,
          "cik": "1000097",
          "name": "KINGDON CAPITAL MANAGEMENT, L.L.C.",
          "noVoting": 0,
          "percentage": 6.23893,
          "putCall": "",
          "share": 11250,
          "sharedVoting": 0,
          "soleVoting": 11250,
          "value": 36674000
        }
      ],
      "reportDate": "2022-03-31"
    }
  ],
  "symbol": "AMZN"
}
```

</details>

---

### Ownership

`GET https://finnhub.io/api/v1/stock/ownership`

区分: **Premium(有料プラン専用)**

Get a full list of shareholders of a company in descending order of the number of shares held. Data is sourced from 13F form, Schedule 13D and 13G for US market, UK Share Register for UK market, SEDI for Canadian market and equivalent filings for other international markets.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `limit` | query | integer | いいえ | Limit number of results. Leave empty to get the full list. |

**応答**: `Ownership` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol of the company. |
| `ownership` | array of OwnershipInfo | Array of investors with detailed information about their holdings. |

<details><summary>応答例</summary>

```json
{
  "ownership": [
    {
      "name": "The Vanguard Group, Inc.",
      "share": 329323420,
      "change": -1809077,
      "filingDate": "2019-12-31"
    },
    {
      "name": "BRK.A | Berkshire Hathaway Inc.",
      "share": 245155570,
      "change": -3683113,
      "filingDate": "2019-12-31"
    },
    {
      "name": "BlackRock Institutional Trust Co NA",
      "share": 187354850,
      "change": -2500563,
      "filingDate": "2020-03-31"
    }
  ],
  "symbol": "AAPL"
}
```

</details>

---

### Fund Ownership

`GET https://finnhub.io/api/v1/stock/fund-ownership`

区分: **Premium(有料プラン専用)**

Get a full list fund and institutional investors of a company in descending order of the number of shares held. Data is sourced from 13F form, Schedule 13D and 13G for US market, UK Share Register for UK market, SEDI for Canadian market and equivalent filings for other international markets.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `limit` | query | integer | いいえ | Limit number of results. Leave empty to get the full list. |

**応答**: `FundOwnership` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol of the company. |
| `ownership` | array of FundOwnershipInfo | Array of investors with detailed information about their holdings. |

<details><summary>応答例</summary>

```json
{
  "ownership": [
    {
      "name": "AGTHX | American Funds Growth Fund of America",
      "share": 5145353,
      "change": 57427,
      "filingDate": "2020-03-31",
      "portfolioPercent": 1.88
    },
    {
      "name": "Vanguard Total Stock Market Index Fund",
      "share": 4227464,
      "change": 73406,
      "filingDate": "2020-03-31",
      "portfolioPercent": 0.45
    },
    {
      "name": "ANWPX | American Funds New Perspective",
      "share": 3377612,
      "change": 0,
      "filingDate": "2020-03-31",
      "portfolioPercent": 2.64
    }
  ],
  "symbol": "TSLA"
}
```

</details>

---

### Insider Transactions

`GET https://finnhub.io/api/v1/stock/insider-transactions`

区分: 新規

Company insider transactions data sourced from Form 3,4,5, SEDI and relevant companies' filings. This endpoint covers US, UK, Canada, Australia, India, and all major EU markets. Limit to 100 transactions per API call.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. Leave this param blank to get the latest transactions. |
| `from` | query | string | いいえ | From date: 2020-03-15. |
| `to` | query | string | いいえ | To date: 2020-03-16. |

**応答**: `InsiderTransactions` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol of the company. |
| `data` | array of Transactions | Array of insider transactions. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "name": "Kirkhorn Zachary",
      "share": 57234,
      "change": -1250,
      "filingDate": "2021-03-19",
      "transactionDate": "2021-03-17",
      "transactionCode": "S",
      "transactionPrice": 655.81
    },
    {
      "name": "Baglino Andrew D",
      "share": 20614,
      "change": 1000,
      "filingDate": "2021-03-31",
      "transactionDate": "2021-03-29",
      "transactionCode": "M",
      "transactionPrice": 41.57
    },
    {
      "name": "Baglino Andrew D",
      "share": 19114,
      "change": -1500,
      "filingDate": "2021-03-31",
      "transactionDate": "2021-03-29",
      "transactionCode": "S",
      "transactionPrice": 615.75
    }
  ],
  "symbol": "TSLA"
}
```

</details>

---

### Insider Sentiment

`GET https://finnhub.io/api/v1/stock/insider-sentiment`

区分: 新規

Get insider sentiment data for US companies calculated using method discussed here. The MSPR ranges from -100 for the most negative to 100 for the most positive which can signal price changes in the coming 30-90 days.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `from` | query | string | はい | From date: 2020-03-15. |
| `to` | query | string | はい | To date: 2020-03-16. |

**応答**: `InsiderSentiments` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol of the company. |
| `data` | array of InsiderSentimentsData | Array of sentiment data. |

<details><summary>応答例</summary>

```json
{
  "data":[
    {
      "symbol":"TSLA",
      "year":2021,
      "month":3,
      "change":5540,
      "mspr":12.209097
    },
    {
      "symbol":"TSLA",
      "year":2022,
      "month":1,
      "change":-1250,
      "mspr":-5.6179776
    },
    {
      "symbol":"TSLA",
      "year":2022,
      "month":2,
      "change":-1250,
      "mspr":-2.1459227
    },
    {
      "symbol":"TSLA",
      "year":2022,
      "month":3,
      "change":5870,
      "mspr":8.960191
    }
  ],
  "symbol":"TSLA"
}
```

</details>

---

### Financial Statements

`GET https://finnhub.io/api/v1/stock/financials`

区分: **Premium(有料プラン専用)**

Get standardized balance sheet, income statement and cash flow for global companies going back 30+ years. Data is sourced from original filings most of which made available through SEC Filings and International Filings endpoints.

Set preliminary param to true for faster updates for US companies.

Wondering why our standardized data is different from Bloomberg, Reuters, Factset, S&P or Yahoo Finance ? Check out our FAQ page to learn more

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `statement` | query | string | はい | Statement can take 1 of these values bs, ic, cf for Balance Sheet, Income Statement, Cash Flow respectively. |
| `freq` | query | string | はい | Frequency can take 1 of these values annual, quarterly, ttm, ytd.  TTM (Trailing Twelve Months) option is available for Income Statement and Cash Flow. YTD (Year To Date) option is only available for Cash Flow. |
| `preliminary` | query | string | いいえ | If set to true, it will return Preliminary financial statements for the latest period which are usually available within an hour of the earnings announcement if finalized data is not available yet. This preliminary data is currently available for US companies. You will see "preliminary": true in the data if that period is using preliminary data. |

**応答**: `FinancialStatements` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol of the company. |
| `financials` | array of FinancialMap | An array of map of key, value pairs containing the data for each period. |

<details><summary>応答例</summary>

```json
{
  "financials": [
    {
      "costOfGoodsSold": 161782,
      "ebit": 63930,
      "grossIncome": 98392,
      "interestExpense": 3576,
      "netIncome": 55256,
      "netIncomeAfterTaxes": 55256,
      "period": "2019-09-28",
      "pretaxIncome": 65737,
      "provisionforIncomeTaxes": 10481,
      "researchDevelopment": 16217,
      "revenue": 260174,
      "sgaExpense": 18245,
      "totalOperatingExpense": 34462,
      "year": 2019
    }
  ],
  "symbol": "AAPL"
}    
```

</details>

---

### Financials As Reported

`GET https://finnhub.io/api/v1/stock/financials-reported`

区分: 新規

Get financials as reported. This data is available for bulk download on Kaggle SEC Financials database.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Symbol. |
| `cik` | query | string | いいえ | CIK. |
| `accessNumber` | query | string | いいえ | Access number of a specific report you want to retrieve financials from. |
| `freq` | query | string | いいえ | Frequency. Can be either annual or quarterly. Default to annual. |
| `from` | query | string | いいえ | From date YYYY-MM-DD. Filter for endDate. |
| `to` | query | string | いいえ | To date YYYY-MM-DD. Filter for endDate. |

**応答**: `FinancialsAsReported` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol |
| `cik` | string | CIK |
| `data` | array of Report | Array of filings. |

<details><summary>応答例</summary>

```json
{
  "cik": "320193",
  "data": [
    {
      "accessNumber": "0000320193-19-000119",
      "symbol": "AAPL",
      "cik": "320193",
      "year": 2019,
      "quarter": 0,
      "form": "10-K",
      "startDate": "2018-09-30 00:00:00",
      "endDate": "2019-09-28 00:00:00",
      "filedDate": "2019-10-31 00:00:00",
      "acceptedDate": "2019-10-30 18:12:36",
      "report": {
        "bs": {
          "Assets": 338516000000,
          "Liabilities": 248028000000,
          "InventoryNet": 4106000000,
          ...
        },
        "cf": {
          "NetIncomeLoss": 55256000000,
          "InterestPaidNet": 3423000000,
          ...
        },
        "ic": {
          "GrossProfit": 98392000000,
          "NetIncomeLoss": 55256000000,
          "OperatingExpenses": 34462000000,
           ...
        }
      }
    }
  ],
  "symbol": "AAPL"
}
```

</details>

---

### Revenue Breakdown

`GET https://finnhub.io/api/v1/stock/revenue-breakdown`

区分: **Premium(有料プラン専用)**

Get revenue breakdown as-reporetd by product and geography. Users on personal plans can access data for US companies which disclose their revenue breakdown in the annual or quarterly reports.

Global standardized revenue breakdown/segments data is available for Enterprise users. Contact us to inquire about the access for Global standardized data.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Symbol. |
| `cik` | query | string | いいえ | CIK. |

**応答**: `RevenueBreakdown` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol |
| `cik` | string | CIK |
| `data` | array of BreakdownItem | Array of revenue breakdown over multiple periods. |

<details><summary>応答例</summary>

```json
{
  "cik": "320193",
  "data": [
    {
      "accessNumber": "0000320193-21-000010",
      "breakdown": {
        "unit": "usd",
        "value": 111439000000,
        "concept": "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "endDate": "2020-12-26",
        "startDate": "2020-09-27",
        "revenueBreakdown": [
          {
            "axis": "srt:ProductOrServiceAxis",
            "data": [
              {
                "unit": "usd",
                "label": "Products",
                "value": 95678000000,
                "member": "us-gaap:ProductMember",
                "percentage": 85.85683647556061
              },
              {
                "unit": "usd",
                "label": "Services",
                "value": 15761000000,
                "member": "us-gaap:ServiceMember",
                "percentage": 14.14316352443938
              },
              {
                "unit": "usd",
                "label": "Services",
                "value": 15761000000,
                "member": "us-gaap:ServiceMember",
                "percentage": 14.14316352443938
              },
              {
                "unit": "usd",
                "label": "iPhone",
                "value": 65597000000,
                "member": "aapl:IPhoneMember",
                "percentage": 58.86359353547681
              },
              {
                "unit": "usd",
                "label": "Mac",
                "value": 8675000000,
                "member": "aapl:MacMember",
                "percentage": 7.784527858290185
              },
              {
                "unit": "usd",
                "label": "iPad",
                "value": 8435000000,
                "member": "aapl:IPadMember",
                "percentage": 7.569163398810111
              },
              {
                "unit": "usd",
                "label": "Wearables, Home and Accessories",
                "value": 12971000000,
                "member": "aapl:WearablesHomeandAccessoriesMember",
                "percentage": 11.639551682983516
              }
            ],
            "label": "Product and Service [Axis]"
          },
        ]
      }
    }
  ],
  "symbol": "AAPL"
}
```

</details>

---

### SEC Filings

`GET https://finnhub.io/api/v1/stock/filings`

区分: 新規

List company's filing. Limit to 250 documents at a time. This data is available for bulk download on Kaggle SEC Filings database.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Symbol. Leave symbol,cik and accessNumber empty to list latest filings. |
| `cik` | query | string | いいえ | CIK. |
| `accessNumber` | query | string | いいえ | Access number of a specific report you want to retrieve data from. |
| `form` | query | string | いいえ | Filter by form. You can use this value NT 10-K to find non-timely filings for a company. |
| `from` | query | string | いいえ | From date: 2023-03-15. |
| `to` | query | string | いいえ | To date: 2023-03-16. |

**応答**: `Filing` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `accessNumber` | string | Access number. |
| `symbol` | string | Symbol. |
| `cik` | string | CIK. |
| `form` | string | Form type. |
| `filedDate` | string | Filed date %Y-%m-%d %H:%M:%S. |
| `acceptedDate` | string | Accepted date %Y-%m-%d %H:%M:%S. |
| `reportUrl` | string | Report's URL. |
| `filingUrl` | string | Filing's URL. |

<details><summary>応答例</summary>

```json
[
  {
    "accessNumber": "0001193125-20-050884",
    "symbol": "AAPL",
    "cik": "320193",
    "form": "8-K",
    "filedDate": "2020-02-27 00:00:00",
    "acceptedDate": "2020-02-27 06:14:21",
    "reportUrl": "https://www.sec.gov/ix?doc=/Archives/edgar/data/320193/000119312520050884/d865740d8k.htm",
    "filingUrl": "https://www.sec.gov/Archives/edgar/data/320193/000119312520050884/0001193125-20-050884-index.html"
  },
  {
    "accessNumber": "0001193125-20-039203",
    "symbol": "AAPL",
    "cik": "320193",
    "form": "8-K",
    "filedDate": "2020-02-18 00:00:00",
    "acceptedDate": "2020-02-18 06:24:57",
    "reportUrl": "https://www.sec.gov/ix?doc=/Archives/edgar/data/320193/000119312520039203/d845033d8k.htm",
    "filingUrl": "https://www.sec.gov/Archives/edgar/data/320193/000119312520039203/0001193125-20-039203-index.html"
  },
  ...
]
```

</details>

---

### SEC Sentiment Analysis

`GET https://finnhub.io/api/v1/stock/filings-sentiment`

区分: **Premium(有料プラン専用)**

Get sentiment analysis of 10-K and 10-Q filings from SEC. An abnormal increase in the number of positive/negative words in filings can signal a significant change in the company's stock price in the upcoming 4 quarters. We make use of Loughran and McDonald Sentiment Word Lists to calculate the sentiment for each filing.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `accessNumber` | query | string | はい | Access number of a specific report you want to retrieve data from. |

**応答**: `SECSentimentAnalysis` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `accessNumber` | string | Access number. |
| `symbol` | string | Symbol. |
| `cik` | string | CIK. |
| `sentiment` | FilingSentiment | Filing Sentiment |

<details><summary>応答例</summary>

```json
{
  "cik": "320193",
  "symbol": "AAPL",
  "accessNumber": "0000320193-20-000052",
  "sentiment": {
    "negative": 1.2698412698412698,
    "polarity": -0.1147540479911535,
    "positive": 0.5042016806722689,
    "litigious": 0.2427637721755369,
    "modal-weak": 0.392156862745098,
    "uncertainty": 1.1391223155929038,
    "constraining": 0.5975723622782446,
    "modal-strong": 0.14939309056956115,
    "modal-moderate": 0.11204481792717086
  }
}
```

</details>

---

### Similarity Index

`GET https://finnhub.io/api/v1/stock/similarity-index`

区分: **Premium(有料プラン専用)**

Calculate the textual difference between a company's 10-K / 10-Q reports and the same type of report in the previous year using Cosine Similarity. For example, this endpoint compares 2019's 10-K with 2018's 10-K. Companies breaking from its routines in disclosure of financial condition and risk analysis section can signal a significant change in the company's stock price in the upcoming 4 quarters.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Symbol. Required if cik is empty |
| `cik` | query | string | いいえ | CIK. Required if symbol is empty |
| `freq` | query | string | いいえ | annual or quarterly. Default to annual |

**応答**: `SimilarityIndex` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `cik` | string | CIK. |
| `similarity` | array of SimilarityIndexInfo | Array of filings with its cosine similarity compared to the same report of the previous year. |

<details><summary>応答例</summary>

```json
{
  "cik": "320193",
  "similarity": [
    {
      "cik": "320193",
      "accessNumber": "0000320193-19-000119",
      "item1": 0.8833750347608914,
      "item2": 0,
      "item1a": 0.994836154829746,
      "item7": 0.897030072745,
      "item7a": 0.9843052590436008,
      "form": "10-K",
      "reportUrl": "https://www.sec.gov/ix?doc=/Archives/edgar/data/320193/000032019319000119/a10-k20199282019.htm",
      "filingUrl": "https://www.sec.gov/Archives/edgar/data/320193/000032019319000119/0000320193-19-000119-index.html",
      "filedDate": "2019-10-31 00:00:00",
      "acceptedDate": "2019-10-30 18:12:36"
    },
    {
      "cik": "320193",
      "accessNumber": "0000320193-18-000145",
      "item1": 0.9737784696339462,
      "item2": 0,
      "item1a": 0.9931651573630014,
      "item7": 0.9441063774798184,
      "item7a": 0.9856181212005336,
      "form": "10-K",
      "reportUrl": "https://www.sec.gov/Archives/edgar/data/320193/000032019318000145/a10-k20189292018.htm",
      "filingUrl": "https://www.sec.gov/Archives/edgar/data/320193/000032019318000145/0000320193-18-000145-index.html",
      "filedDate": "2018-11-05 00:00:00",
      "acceptedDate": "2018-11-05 08:01:40"
    }
  ],
  "symbol": "AAPL"
}
```

</details>

---

### IPO Calendar

`GET https://finnhub.io/api/v1/calendar/ipo`

区分: 新規

Get recent and upcoming IPO.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `from` | query | string | はい | From date: 2020-03-15. |
| `to` | query | string | はい | To date: 2020-03-16. |

**応答**: `IPOCalendar` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `ipoCalendar` | array of IPOEvent | Array of IPO events. |

<details><summary>応答例</summary>

```json
{
  "ipoCalendar": [
    {
      "date": "2020-04-03",
      "exchange": "NASDAQ Global",
      "name": "ZENTALIS PHARMACEUTICALS, LLC",
      "numberOfShares": 7650000,
      "price": "16.00-18.00",
      "status": "expected",
      "symbol": "ZNTL",
      "totalSharesValue": 158355000
    },
    {
      "date": "2020-04-01",
      "exchange": "NASDAQ Global",
      "name": "WIMI HOLOGRAM CLOUD INC.",
      "numberOfShares": 5000000,
      "price": "5.50-7.50",
      "status": "expected",
      "symbol": "WIMI",
      "totalSharesValue": 43125000
    },
  ]
}
```

</details>

---

### Sector Metrics

`GET https://finnhub.io/api/v1/sector/metrics`

区分: **Premium(有料プラン専用)**

Get ratios for different sectors and regions/indices.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `region` | query | string | はい | Region. A list of supported values for this field can be found here. |

**応答**: `SectorMetric` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `region` | string | Region. |
| `data` | array of SectorMetricData | Metrics for each sector. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "metrics": {
        "assetTurnoverAnnual": {
          "a": 0.7245,
          "m": 0.5426
        },
        "assetTurnoverTTM": {
          "a": 0.7254,
          "m": 0.5463
        },
      },
      "sector": "Communication Services"
    },
    {
      "metrics": {
        "currentDividendYieldTTM": {
          "a": 30.9763,
          "m": 2.09
        },
        "currentEv/freeCashFlowAnnual": {
          "a": 286.4793,
          "m": 19.8488
        },
      },
      "sector": "Consumer Discretionary"
    }
  ],
  "region": "Asia_Ocenia"
}
```

</details>

---

### Dividends

`GET https://finnhub.io/api/v1/stock/dividend`

区分: **Premium(有料プラン専用)**

Get dividends data for common stocks going back 30 years.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |
| `from` | query | string | はい | YYYY-MM-DD. |
| `to` | query | string | はい | YYYY-MM-DD. |

**応答**: `Dividends` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `date` | string | Ex-Dividend date. |
| `amount` | number | Amount in local currency. |
| `adjustedAmount` | number | Adjusted dividend. |
| `payDate` | string | Pay date. |
| `recordDate` | string | Record date. |
| `declarationDate` | string | Declaration date. |
| `currency` | string | Currency. |
| `freq` | string | Dividend frequency. Can be 1 of the following values:   0: Annually 1: Monthly 2: Quarterly 3: Semi-annually 4: Other/Unknown 5: Bimonthly 6: Trimesterly 7: Weekly |

<details><summary>応答例</summary>

```json
[
  {
    "symbol": "AAPL",
    "date": "2019-11-07",
    "amount": 0.77,
    "adjustedAmount": 0.77,
    "payDate": "2019-11-14",
    "recordDate": "2019-11-11",
    "declarationDate": "2019-10-30",
    "currency": "USD"
  },
  {
    "symbol": "AAPL",
    "date": "2019-08-09",
    "amount": 0.77,
    "adjustedAmount": 0.77,
    "payDate": "2019-08-15",
    "recordDate": "2019-08-12",
    "declarationDate": "2019-07-30",
    "currency": "USD"
  },
  {
    "symbol": "AAPL",
    "date": "2019-05-10",
    "amount": 0.77,
    "adjustedAmount": 0.77,
    "payDate": "2019-05-16",
    "recordDate": "2019-05-13",
    "declarationDate": "2019-05-01",
    "currency": "USD"
  },
  {
    "symbol": "AAPL",
    "date": "2019-02-08",
    "amount": 0.73,
    "adjustedAmount": 0.77,
    "payDate": "2019-02-14",
    "recordDate": "2019-02-11",
    "declarationDate": "2019-01-29",
    "currency": "USD"
  }
]
```

</details>

---

## Stock Estimates

### Recommendation Trends

`GET https://finnhub.io/api/v1/stock/recommendation`

Get latest analyst recommendation trends for a company.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |

**応答**: `RecommendationTrend` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Company symbol. |
| `buy` | integer | Number of recommendations that fall into the Buy category |
| `hold` | integer | Number of recommendations that fall into the Hold category |
| `period` | string | Updated period |
| `sell` | integer | Number of recommendations that fall into the Sell category |
| `strongBuy` | integer | Number of recommendations that fall into the Strong Buy category |
| `strongSell` | integer | Number of recommendations that fall into the Strong Sell category |

<details><summary>応答例</summary>

```json
[
  {
    "buy": 24,
    "hold": 7,
    "period": "2025-03-01",
    "sell": 0,
    "strongBuy": 13,
    "strongSell": 0,
    "symbol": "AAPL"
  },
  {
    "buy": 17,
    "hold": 13,
    "period": "2025-02-01",
    "sell": 5,
    "strongBuy": 13,
    "strongSell": 0,
    "symbol": "AAPL"
  }
]
```

</details>

---

### Price Target

`GET https://finnhub.io/api/v1/stock/price-target`

区分: **Premium(有料プラン専用)**

Get latest price target consensus.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |

**応答**: `PriceTarget` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Company symbol. |
| `targetHigh` | number | Highes analysts' target. |
| `targetLow` | number | Lowest analysts' target. |
| `targetMean` | number | Mean of all analysts' targets. |
| `targetMedian` | number | Median of all analysts' targets. |
| `numberAnalysts` | integer | Number of Analysts. |
| `lastUpdated` | string | Updated time of the data |

<details><summary>応答例</summary>

```json
{
  "lastUpdated": "2023-04-06 00:00:00",
  "numberAnalysts": 39,
  "symbol": "NFLX",
  "targetHigh": 462,
  "targetLow": 217.15,
  "targetMean": 364.37,
  "targetMedian": 359.04
}
```

</details>

---

### Stock Upgrade/Downgrade

`GET https://finnhub.io/api/v1/stock/upgrade-downgrade`

区分: **Premium(有料プラン専用)**

Get latest stock upgrade and downgrade.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Symbol of the company: AAPL. If left blank, the API will return latest stock upgrades/downgrades. |
| `from` | query | string | いいえ | From date: 2000-03-15. |
| `to` | query | string | いいえ | To date: 2020-03-16. |

**応答**: `UpgradeDowngrade` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Company symbol. |
| `gradeTime` | integer | Upgrade/downgrade time in UNIX timestamp. |
| `fromGrade` | string | From grade. |
| `toGrade` | string | To grade. |
| `company` | string | Company/analyst who did the upgrade/downgrade. |
| `action` | string | Action can take any of the following values: up(upgrade), down(downgrade), main(maintains), init(initiate), reit(reiterate). |

<details><summary>応答例</summary>

```json
[
  {
    "symbol": "BYND",
    "gradeTime": 1567728000,
    "company": "DA Davidson",
    "fromGrade": "",
    "toGrade": "Underperform",
    "action": "init"
  },
  {
    "symbol": "BYND",
    "gradeTime": 1566259200,
    "company": "JP Morgan",
    "fromGrade": "Neutral",
    "toGrade": "Overweight",
    "action": "up"
  },
  {
    "symbol": "BYND",
    "gradeTime": 1564704000,
    "company": "Bank of America",
    "fromGrade": "",
    "toGrade": "Neutral",
    "action": "reit"
  }
]
```

</details>

---

### Revenue Estimates

`GET https://finnhub.io/api/v1/stock/revenue-estimate`

区分: **Premium(有料プラン専用)**

Get company's revenue estimates.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `freq` | query | string | いいえ | Can take 1 of the following values: annual, quarterly. Default to quarterly |

**応答**: `RevenueEstimates` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of RevenueEstimatesInfo | List of estimates |
| `freq` | string | Frequency: annual or quarterly. |
| `symbol` | string | Company symbol. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "numberAnalysts": 31,
      "period": "2020-06-30",
      "revenueAvg": 58800500000,
      "revenueHigh": 64060000000,
      "revenueLow": 54072000000,
      "quarter": 3,
      "year": 2020
    },
    {
      "numberAnalysts": 31,
      "period": "2020-03-31",
      "revenueAvg": 61287300000,
      "revenueHigh": 66557000000,
      "revenueLow": 54871000000,
      "quarter": 2,
      "year": 2020
    }
  ],
  "freq": "quarterly",
  "symbol": "AAPL"
}
```

</details>

---

### EBITDA Estimates

`GET https://finnhub.io/api/v1/stock/ebitda-estimate`

区分: **Premium(有料プラン専用)**

Get company's ebitda estimates.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `freq` | query | string | いいえ | Can take 1 of the following values: annual, quarterly. Default to quarterly |

**応答**: `EbitdaEstimates` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of EbitdaEstimatesInfo | List of estimates |
| `freq` | string | Frequency: annual or quarterly. |
| `symbol` | string | Company symbol. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "numberAnalysts": 31,
      "period": "2020-06-30",
      "ebitdaAvg": 58800500000,
      "ebitdaHigh": 64060000000,
      "ebitdaLow": 54072000000,
      "quarter": 3,
      "year": 2020
    },
    {
      "numberAnalysts": 31,
      "period": "2020-03-31",
      "ebitdaAvg": 61287300000,
      "ebitdaHigh": 66557000000,
      "ebitdaLow": 54871000000,
      "quarter": 2,
      "year": 2020
    }
  ],
  "freq": "quarterly",
  "symbol": "AAPL"
}
```

</details>

---

### EBIT Estimates

`GET https://finnhub.io/api/v1/stock/ebit-estimate`

区分: **Premium(有料プラン専用)**

Get company's ebit estimates.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `freq` | query | string | いいえ | Can take 1 of the following values: annual, quarterly. Default to quarterly |

**応答**: `EbitEstimates` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of EbitEstimatesInfo | List of estimates |
| `freq` | string | Frequency: annual or quarterly. |
| `symbol` | string | Company symbol. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "numberAnalysts": 31,
      "period": "2020-06-30",
      "ebitAvg": 58800500000,
      "ebitHigh": 64060000000,
      "ebitLow": 54072000000
      "quarter": 3,
      "year": 2020,
    },
    {
      "numberAnalysts": 31,
      "period": "2020-03-31",
      "ebitAvg": 61287300000,
      "ebitHigh": 66557000000,
      "ebitLow": 54871000000,
      "quarter": 2,
      "year": 2020,
    }
  ],
  "freq": "quarterly",
  "symbol": "AAPL"
}
```

</details>

---

### Net Income Estimates

`GET https://finnhub.io/api/v1/stock/net-income-estimate`

区分: **Premium(有料プラン専用)**

Get company's net income estimates.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `freq` | query | string | いいえ | Can take 1 of the following values: annual, quarterly. Default to quarterly |

**応答**: `NetIncomeEstimates` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of NetIncomeEstimatesInfo | List of estimates |
| `freq` | string | Frequency: annual or quarterly. |
| `symbol` | string | Company symbol. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "numberAnalysts": 31,
      "period": "2020-06-30",
      "netIncomeAvg": 58800500000,
      "netIncomeHigh": 64060000000,
      "netIncomeLow": 54072000000,
      "quarter": 3,
      "year": 2020
    },
    {
      "numberAnalysts": 31,
      "period": "2020-03-31",
      "netIncomeAvg": 61287300000,
      "netIncomeHigh": 66557000000,
      "netIncomeLow": 54871000000,
      "quarter": 2,
      "year": 2020
    }
  ],
  "freq": "quarterly",
  "symbol": "AAPL"
}
```

</details>

---

### Pretax Income Estimates

`GET https://finnhub.io/api/v1/stock/pretax-income-estimate`

区分: **Premium(有料プラン専用)**

Get company's pretax income estimates.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `freq` | query | string | いいえ | Can take 1 of the following values: annual, quarterly. Default to quarterly |

**応答**: `PretaxIncomeEstimates` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of PretaxIncomeEstimatesInfo | List of estimates |
| `freq` | string | Frequency: annual or quarterly. |
| `symbol` | string | Company symbol. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "numberAnalysts": 31,
      "period": "2020-06-30",
      "pretaxIncomeAvg": 58800500000,
      "pretaxIncomeHigh": 64060000000,
      "pretaxIncomeLow": 54072000000,
      "quarter": 3,
      "year": 2020
    },
    {
      "numberAnalysts": 31,
      "period": "2020-03-31",
      "pretaxIncomeAvg": 61287300000,
      "pretaxIncomeHigh": 66557000000,
      "pretaxIncomeLow": 54871000000,
      "quarter": 2,
      "year": 2020
    }
  ],
  "freq": "quarterly",
  "symbol": "AAPL"
}
```

</details>

---

### Gross Income Estimates

`GET https://finnhub.io/api/v1/stock/gross-income-estimate`

区分: **Premium(有料プラン専用)**

Get company's gross income estimates.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `freq` | query | string | いいえ | Can take 1 of the following values: annual, quarterly. Default to quarterly |

**応答**: `GrossIncomeEstimates` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of GrossIncomeEstimatesInfo | List of estimates |
| `freq` | string | Frequency: annual or quarterly. |
| `symbol` | string | Company symbol. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "numberAnalysts": 31,
      "period": "2020-06-30",
      "grossIncomeAvg": 58800500000,
      "grossIncomeHigh": 64060000000,
      "grossIncomeLow": 54072000000,
      "quarter": 3,
      "year": 2020
    },
    {
      "numberAnalysts": 31,
      "period": "2020-03-31",
      "grossIncomeAvg": 61287300000,
      "grossIncomeHigh": 66557000000,
      "grossIncomeLow": 54871000000,
      "quarter": 2,
      "year": 2020
    }
  ],
  "freq": "quarterly",
  "symbol": "AAPL"
}
```

</details>

---

### DPS Estimates

`GET https://finnhub.io/api/v1/stock/dps-estimate`

区分: **Premium(有料プラン専用)**

Get company's Dividend per Share estimates.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `freq` | query | string | いいえ | Can take 1 of the following values: annual, quarterly. Default to quarterly |

**応答**: `DpsEstimates` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of DpsEstimatesInfo | List of estimates |
| `freq` | string | Frequency: annual or quarterly. |
| `symbol` | string | Company symbol. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "numberAnalysts": 31,
      "period": "2020-06-30",
      "dpsAvg": 0.82,
      "dpsHigh": 0.9,
      "dpsLow": 0.74,
      "quarter": 3,
      "year": 2020
    },
    {
      "numberAnalysts": 31,
      "period": "2020-03-31",
      "dpsAvg": 0.77,
      "dpsHigh": 0.88,
      "dpsLow": 0.7,
      "quarter": 2,
      "year": 2020
    }
  ],
  "freq": "quarterly",
  "symbol": "AAPL"
}
```

</details>

---

### Earnings Estimates

`GET https://finnhub.io/api/v1/stock/eps-estimate`

区分: **Premium(有料プラン専用)**

Get company's EPS estimates.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `freq` | query | string | いいえ | Can take 1 of the following values: annual, quarterly. Default to quarterly |

**応答**: `EarningsEstimates` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of EarningsEstimatesInfo | List of estimates |
| `freq` | string | Frequency: annual or quarterly. |
| `symbol` | string | Company symbol. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "epsAvg": 2.65,
      "epsHigh": 2.98,
      "epsLow": 2.05,
      "numberAnalysts": 35,
      "period": "2020-06-30",
      "quarter": 3,
      "year": 2020
    },
    {
      "epsAvg": 2.52,
      "epsHigh": 3.02,
      "epsLow": 2.21,
      "numberAnalysts": 34,
      "period": "2020-03-31",
      "quarter": 2,
      "year": 2020
    }
  ],
  "freq": "quarterly",
  "symbol": "AAPL"
}
```

</details>

---

### Earnings Surprises

`GET https://finnhub.io/api/v1/stock/earnings`

区分: 無料枠あり / 利用頻度高

Get company historical quarterly earnings surprise going back to 2000.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `limit` | query | integer | いいえ | Limit number of period returned. Leave blank to get the full history. |

**応答**: `EarningResult` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `actual` | number | Actual earning result. |
| `estimate` | number | Estimated earning. |
| `surprise` | number | Surprise - The difference between actual and estimate. |
| `surprisePercent` | number | Surprise percent. |
| `period` | string | Reported period. |
| `symbol` | string | Company symbol. |
| `year` | integer | Fiscal year. |
| `quarter` | integer | Fiscal quarter. |

<details><summary>応答例</summary>

```json
[
  {
    "actual": 1.88,
    "estimate": 1.9744,
    "period": "2023-03-31",
    "quarter": 1,
    "surprise": -0.0944,
    "surprisePercent": -4.7812,
    "symbol": "AAPL",
    "year": 2023
  },
  {
    "actual": 1.29,
    "estimate": 1.2957,
    "period": "2022-12-31",
    "quarter": 4,
    "surprise": -0.0057,
    "surprisePercent": -0.4399,
    "symbol": "AAPL",
    "year": 2022
  },
  {
    "actual": 1.2,
    "estimate": 1.1855,
    "period": "2022-09-30",
    "quarter": 3,
    "surprise": 0.0145,
    "surprisePercent": 1.2231,
    "symbol": "AAPL",
    "year": 2022
  }
]
```

</details>

---

### Earnings Calendar

`GET https://finnhub.io/api/v1/calendar/earnings`

区分: 無料枠あり / 新規

Get historical and coming earnings release. EPS and Revenue in this endpoint are non-GAAP, which means they are adjusted to exclude some one-time or unusual items. This is the same data investors usually react to and talked about on the media. Estimates are sourced from both sell-side and buy-side analysts.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `from` | query | string | いいえ | From date: 2020-03-15. |
| `to` | query | string | いいえ | To date: 2020-03-16. |
| `symbol` | query | string | いいえ | Filter by symbol: AAPL. |
| `international` | query | boolean | いいえ | Set to true to include international markets. Default value is false |

**応答**: `EarningsCalendar` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `earningsCalendar` | array of EarningRelease | Array of earnings release. |

<details><summary>応答例</summary>

```json
{
  "earningsCalendar": [
    {
      "date": "2020-01-28",
      "epsActual": 4.99,
      "epsEstimate": 4.5474,
      "hour": "amc",
      "quarter": 1,
      "revenueActual": 91819000000,
      "revenueEstimate": 88496400810,
      "symbol": "AAPL",
      "year": 2020
    },
    {
      "date": "2019-10-30",
      "epsActual": 3.03,
      "epsEstimate": 2.8393,
      "hour": "amc",
      "quarter": 4,
      "revenueActual": 64040000000,
      "revenueEstimate": 62985161760,
      "symbol": "AAPL",
      "year": 2019
    }
   ]
}
```

</details>

---

## Stock Price

### Quote

`GET https://finnhub.io/api/v1/quote`

区分: 利用頻度高

Get real-time quote data for US stocks. Constant polling is not recommended. Use websocket if you need real-time updates.

Real-time stock prices for international markets are supported for Enterprise clients via our partner's feed. Contact Us to learn more.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol |

**応答**: `Quote` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `o` | number | Open price of the day |
| `h` | number | High price of the day |
| `l` | number | Low price of the day |
| `c` | number | Current price |
| `pc` | number | Previous close price |
| `d` | number | Change |
| `dp` | number | Percent change |

<details><summary>応答例</summary>

```json
{
  "c": 261.74,
  "h": 263.31,
  "l": 260.68,
  "o": 261.07,
  "pc": 259.45,
  "t": 1582641000 
}
```

</details>

---

### Stock Candles

`GET https://finnhub.io/api/v1/stock/candle`

区分: **Premium(有料プラン専用)**

Get candlestick data (OHLCV) for stocks.

Daily data will be adjusted for Splits. Intraday data will remain unadjusted. Only 1 month of intraday will be returned at a time. If you need more historical intraday data, please use the from and to params iteratively to request more data.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |
| `resolution` | query | string | はい | Supported resolution includes 1, 5, 15, 30, 60, D, W, M .Some timeframes might not be available depending on the exchange. |
| `from` | query | integer | はい | UNIX timestamp. Interval initial value. |
| `to` | query | integer | はい | UNIX timestamp. Interval end value. |

**応答**: `StockCandles` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `o` | array of number | List of open prices for returned candles. |
| `h` | array of number | List of high prices for returned candles. |
| `l` | array of number | List of low prices for returned candles. |
| `c` | array of number | List of close prices for returned candles. |
| `v` | array of number | List of volume data for returned candles. |
| `t` | array of integer | List of timestamp for returned candles. |
| `s` | string | Status of the response. This field can either be ok or no_data. |

<details><summary>応答例</summary>

```json
{
  "c": [
    217.68,
    221.03,
    219.89
  ],
  "h": [
    222.49,
    221.5,
    220.94
  ],
  "l": [
    217.19,
    217.1402,
    218.83
  ],
  "o": [
    221.03,
    218.55,
    220
  ],
  "s": "ok",
  "t": [
    1569297600,
    1569384000,
    1569470400
  ],
  "v": [
    33463820,
    24018876,
    20730608
  ]
}
```

</details>

---

### Tick Data

`GET https://finnhub.io/api/v1/stock/tick`

区分: **Premium(有料プラン専用)**

Get historical tick data for global exchanges.

For more historical tick data, you can visit our bulk download page in the Dashboard here to speed up the download process.


  
    
      Exchange
      Segment
      Delay
    
  
  
    
      US CTA/UTP
      Full SIP
      End-of-day
    
    
      TSX
      TSXTSX VentureIndex
      End-of-day
    
    
      LSE
      London Stock Exchange (L)LSE International (L)LSE European (L)
      15 minute
    
    
      Euronext
       Euronext Paris (PA) Euronext Amsterdam (AS) Euronext Lisbon (LS) Euronext Brussels (BR) Euronext Oslo (OL) Euronext London (LN) Euronext Dublin (IR) Index Warrant
      End-of-day
    
    
      Deutsche Börse
       Frankfurt (F) Xetra (DE) Duesseldorf (DU) Hamburg (HM) Berlin (BE) Hanover (HA) Stoxx (SX) TradeGate (TG) Zertifikate (SC) Index Warrant
      End-of-day

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |
| `date` | query | string | はい | Date: 2020-04-02. |
| `limit` | query | integer | はい | Limit number of ticks returned. Maximum value: 25000 |
| `skip` | query | integer | はい | Number of ticks to skip. Use this parameter to loop through the entire data. |

**応答**: `TickData` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `s` | string | Symbol. |
| `skip` | integer | Number of ticks skipped. |
| `count` | integer | Number of ticks returned. If count limit, all data for that date has been returned. |
| `total` | integer | Total number of ticks for that date. |
| `v` | array of number | List of volume data. |
| `p` | array of number | List of price data. |
| `t` | array of integer | List of timestamp in UNIX ms. |
| `x` | array of string | List of venues/exchanges. A list of exchange codes can be found here |
| `c` | array of array | List of trade conditions. A comprehensive list of trade conditions code can be found here |

<details><summary>応答例</summary>

```json
{
  "p": [
    255,
    255,
    255
  ],
  "s": "AAPL",
  "skip": 0,
  "t": [
    1585108800073,
    1585108800315,
    1585108800381
  ],
  "v": [
    2513,
    24,
    1
  ],
  "x": [
    "P",
    "P",
    "P"
  ],
  "count": 3,
  "c":[["1","24"],["1","24","12"],["1","24","12"]]
}
```

</details>

---

### Historical NBBO

`GET https://finnhub.io/api/v1/stock/bbo`

区分: **Premium(有料プラン専用)**

Get historical best bid and offer for US stocks, LSE, TSX, Euronext and Deutsche Borse.

For US market, this endpoint only serves historical NBBO from the beginning of 2023. To download more historical data, please visit our bulk download page in the Dashboard here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |
| `date` | query | string | はい | Date: 2020-04-02. |
| `limit` | query | integer | はい | Limit number of ticks returned. Maximum value: 25000 |
| `skip` | query | integer | はい | Number of ticks to skip. Use this parameter to loop through the entire data. |

**応答**: `HistoricalNBBO` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `s` | string | Symbol. |
| `skip` | integer | Number of ticks skipped. |
| `count` | integer | Number of ticks returned. If count limit, all data for that date has been returned. |
| `total` | integer | Total number of ticks for that date. |
| `av` | array of number | List of Ask volume data. |
| `a` | array of number | List of Ask price data. |
| `ax` | array of string | List of venues/exchanges - Ask price. A list of exchange codes can be found here |
| `bv` | array of number | List of Bid volume data. |
| `b` | array of number | List of Bid price data. |
| `bx` | array of string | List of venues/exchanges - Bid price. A list of exchange codes can be found here |
| `t` | array of integer | List of timestamp in UNIX ms. |
| `c` | array of array | List of quote conditions. A comprehensive list of quote conditions code can be found here |

<details><summary>応答例</summary>

```json
{
  "a": [
    137,
    133.2,
    126.08
  ],
  "av": [
    1,
    2,
    1
  ],
  "ax": [
    "P",
    "P",
    "P"
  ],
  "b": [
    116.5,
    116.5,
    116.5
  ],
  "bv": [
    1,
    1,
    1
  ],
  "bx": [
    "P",
    "P",
    "P"
  ],
  "c": [
    [
      "1"
    ],
    [
      "1"
    ],
    [
      "1"
    ]
  ],
  "count": 3,
  "s": "AAPL",
  "skip": 5,
  "t": [
    1615280400047,
    1615280400047,
    1615280400047
  ],
  "total": 2739880
}
```

</details>

---

### Last Bid-Ask

`GET https://finnhub.io/api/v1/stock/bidask`

区分: **Premium(有料プラン専用)**

Get last bid/ask data for US stocks.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |

**応答**: `LastBid-Ask` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `b` | number | Bid price. |
| `a` | number | Ask price. |
| `bv` | number | Bid volume. |
| `av` | number | Ask volume. |
| `t` | integer | Reference UNIX timestamp in ms. |

<details><summary>応答例</summary>

```json
{
  "a": 338.65,
  "av": 2,
  "b": 338.61,
  "bv": 2,
  "t": 1591995678874
}
```

</details>

---

### Splits

`GET https://finnhub.io/api/v1/stock/split`

区分: **Premium(有料プラン専用)**

Get splits data for stocks.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |
| `from` | query | string | はい | YYYY-MM-DD. |
| `to` | query | string | はい | YYYY-MM-DD. |

**応答**: `Split` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `date` | string | Split date. |
| `fromFactor` | number | From factor. |
| `toFactor` | number | To factor. |

<details><summary>応答例</summary>

```json
[
  {
    "symbol": "AAPL",
    "date": "2014-06-09",
    "fromFactor": 1,
    "toFactor": 7
  }
]
```

</details>

---

### Dividends 2 (Basic)

`GET https://finnhub.io/api/v1/stock/dividend2`

区分: **Premium(有料プラン専用)**

Get global dividends data.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |

**応答**: `Dividends2` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol |
| `data` | array of Dividends2Info |  |

<details><summary>応答例</summary>

```json
{
  "data": [
  {
    "exDate": "2019-11-07",
    "amount": 0.77,
    
  },
  {
    "exDate": "2019-08-09",
    "amount": 0.77,
  },
  {
    "exDate": "2019-05-10",
    "amount": 0.77,
  }
],
  "symbol": "AAPL"
}
```

</details>

---

## ETFs & Indices

### Indices Constituents

`GET https://finnhub.io/api/v1/index/constituents`

区分: **Premium(有料プラン専用)**

Get a list of index's constituents. A list of supported indices for this endpoint can be found here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | symbol |

**応答**: `IndicesConstituents` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Index's symbol. |
| `constituents` | array of string | Array of constituents. |
| `constituentsBreakdown` | array of IndicesConstituentsBreakdown | Array of constituents' details. |

<details><summary>応答例</summary>

```json
{
  "constituents": [
    "AAPL",
    "MSFT"
  ],
  "constituentsBreakdown": [
    {
      "cusip": "037833100",
      "isin": "US0378331005",
      "name": "Apple Inc",
      "shareClassFIGI": "BBG001S5N8V8",
      "symbol": "AAPL",
      "weight": 7.03049
    },
    {
      "cusip": "594918104",
      "isin": "US5949181045",
      "name": "Microsoft Corp",
      "shareClassFIGI": "BBG001S5TD05",
      "symbol": "MSFT",
      "weight": 6.3839
    }
  ],
  "symbol": "^GSPC"
}
```

</details>

---

### Indices Historical Constituents

`GET https://finnhub.io/api/v1/index/historical-constituents`

区分: **Premium(有料プラン専用)**

Get full history of index's constituents including symbols and dates of joining and leaving the Index. A list of supported indices for this endpoint can be found here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | symbol |

**応答**: `IndicesHistoricalConstituents` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Index's symbol. |
| `historicalConstituents` | array of IndexHistoricalConstituent | Array of historical constituents. |

<details><summary>応答例</summary>

```json
{
  "historicalConstituents": [
    {
      "action": "add",
      "symbol": "TYL",
      "date": "2020-06-22"
    },
    {
      "action": "add",
      "symbol": "TDY",
      "date": "2020-06-22"
    },
    {
      "action": "remove",
      "symbol": "JWN",
      "date": "2020-06-22"
    }
  ],
  "symbol": "^GSPC"
}
```

</details>

---

### ETFs Profile

`GET https://finnhub.io/api/v1/etf/profile`

区分: **Premium(有料プラン専用)**

Get ETF profile information. This endpoint has global coverage. A list of supported ETFs can be found here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | ETF symbol. |
| `isin` | query | string | いいえ | ETF isin. |

**応答**: `ETFsProfile` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `profile` | ETFProfileData | Profile data. |

<details><summary>応答例</summary>

```json
{
  "profile": {
    "assetClass": "Equity",
    "aum": 318374000000,
    "avgVolume": 63794600,
    "cusip": "",
    "description": "SPY was created on 1993-01-22 by SPDR. The fund's investment portfolio concentrates primarily on large cap equity. The ETF currently has 318374.0m in AUM and 504 holdings. SPY tracks a market-cap-weighted index of US large- and midcap stocks selected by the S\u0026P Committee.",
    "domicile": "US",
    "etfCompany": "SPDR",
    "expenseRatio": 0.0945,
    "inceptionDate": "1993-01-22",
    "investmentSegment": "Large Cap",
    "isin": "",
    "name": "SPDR S\u0026P 500 ETF Trust",
    "nav": 366.2784,
    "navCurrency": "USD",
    "priceToBook": 3.943968,
    "priceToEarnings": 26.82968,
    "trackingIndex": "S\u0026P 500",
    "logo": "https://static2.finnhub.io/file/publicdatany/finnhubimage/etf_logo/spdr.png",
    "website": "https://us.spdrs.com/en/etf/spdr-sp-500-etf-SPY"
  },
  "symbol": "SPY"
}
```

</details>

---

### ETFs Holdings

`GET https://finnhub.io/api/v1/etf/holdings`

区分: **Premium(有料プラン専用)**

Get full ETF holdings/constituents. This endpoint has global coverage. Widget only shows top 10 holdings. A list of supported ETFs can be found here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | ETF symbol. |
| `isin` | query | string | いいえ | ETF isin. |
| `skip` | query | integer | いいえ | Skip the first n results. You can use this parameter to query historical constituents data. The latest result is returned if skip=0 or not set. |
| `date` | query | string | いいえ | Query holdings by date. You can use either this param or skip param, not both. |

**応答**: `ETFsHoldings` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | ETF symbol. |
| `atDate` | string | Holdings update date. |
| `numberOfHoldings` | integer | Number of holdings. |
| `holdings` | array of ETFHoldingsData | Array of holdings. |

<details><summary>応答例</summary>

```json
{
  "atDate": "2023-03-24",
  "holdings": [
    {
      "assetType": "Equity",
      "cusip": "88160R101",
      "isin": "US88160R1014",
      "name": "TESLA INC",
      "percent": 10.54,
      "share": 3971395,
      "symbol": "TSLA",
      "value": 763381546.9
    },
    {
      "assetType": "Equity",
      "cusip": "98980L101",
      "isin": "US98980L1017",
      "name": "ZOOM VIDEO COMMUNICATIONS-A",
      "percent": 8.05,
      "share": 8418916,
      "symbol": "ZM",
      "value": 582504798.04
    },
  ],
  "numberOfHoldings": 28,
  "symbol": "ARKK"
}
```

</details>

---

### ETFs Sector Exposure

`GET https://finnhub.io/api/v1/etf/sector`

区分: **Premium(有料プラン専用)**

Get ETF sector exposure data.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | ETF symbol. |
| `isin` | query | string | いいえ | ETF isin. |

**応答**: `ETFsSectorExposure` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | ETF symbol. |
| `sectorExposure` | array of ETFSectorExposureData | Array of industries and exposure levels. |

<details><summary>応答例</summary>

```json
{
  "sectorExposure": [
    {
      "exposure": 31.96,
      "industry": "Technology"
    },
    {
      "exposure": 14.79,
      "industry": "Healthcare"
    },
    {
      "exposure": 13.46,
      "industry": "Consumer Cyclicals"
    }
  ],
  "symbol": "SPY"
}
```

</details>

---

### ETFs Country Exposure

`GET https://finnhub.io/api/v1/etf/country`

区分: **Premium(有料プラン専用)**

Get ETF country exposure data.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | ETF symbol. |
| `isin` | query | string | いいえ | ETF isin. |

**応答**: `ETFsCountryExposure` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | ETF symbol. |
| `countryExposure` | array of ETFCountryExposureData | Array of countries and and exposure levels. |

<details><summary>応答例</summary>

```json
{
  "countryExposure": [
    {
      "country": "United States of America (the)",
      "exposure": 97.02
    },
    {
      "country": "Ireland",
      "exposure": 1.65
    },
    {
      "country": "United Kingdom of Great Britain and Northern Ireland (the)",
      "exposure": 0.88
    },
    {
      "country": "Switzerland",
      "exposure": 0.41
    },
    {
      "country": "Bermuda",
      "exposure": 0.03
    }
  ],
  "symbol": "SPY"
}
```

</details>

---

### ETFs Equity Allocation

`GET https://finnhub.io/api/v1/etf/allocation`

区分: **Premium(有料プラン専用)**

Get ETF equity allocation based on the characteristics of the holdings.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | ETF symbol. |
| `isin` | query | string | いいえ | ETF isin. |

**応答**: `ETFsAllocation` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | ETF symbol. |
| `data` | ETFAllocationData | ETF allocation. |

<details><summary>応答例</summary>

```json
{
  "data": {
    "largeBlend": 38.1,
    "largeGrowth": 20.41,
    "largeValue": 22.03,
    "midBlend": 8.67,
    "midGrowth": 3.88,
    "midValue": 5.94,
    "smallBlend": 0.52,
    "smallGrowth": 0.05,
    "smallValue": 0.4
  },
  "symbol": "SPY"
}
```

</details>

---

## Mutual Funds

### Mutual Funds Profile

`GET https://finnhub.io/api/v1/mutual-fund/profile`

区分: **Premium(有料プラン専用)**

Get mutual funds profile information. This endpoint covers both US and global mutual funds. For international funds, you must query the data using ISIN. A list of supported funds can be found here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Fund's symbol. |
| `isin` | query | string | いいえ | Fund's isin. |

**応答**: `MutualFundProfile` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `profile` | MutualFundProfileData | Profile data. |

<details><summary>応答例</summary>

```json
{
  "profile": {
    "benchmark": "CRSP US Total Stock Market TR",
    "beta": 1.05,
    "category": "Multi-Cap Core",
    "cusip": "",
    "deferredLoad": 0,
    "description": "Created in 1992, Vanguard Total Stock Market Index Fund is designed to provide investors with exposure to the entire U.S. equity market, including small-, mid-, and large-cap growth and value stocks. The fund’s key attributes are its low costs, broad diversification, and the potential for tax efficiency. Investors looking for a low-cost way to gain broad exposure to the U.S. stock market who are willing to accept the volatility that comes with stock market investing may wish to consider this fund as either a core equity holding or your only domestic stock fund.",
    "expenseRatio": 0.04,
    "fee12b1": 0,
    "frontLoad": 0,
    "fundFamily": "VANGUARD ADMIRAL",
    "inceptionDate": "2000-11-13",
    "investmentSegment": "Growth & Income",
    "iraMinInvestment": 0,
    "isin": "",
    "manager": "O'Reilly,Nejman",
    "maxRedemptionFee": 0,
    "name": "Vanguard Index Funds: Vanguard Total Stock Market Index Fund; Admiral Class Shares",
    "standardMinInvestment": 3000,
    "status": "Open",
    "totalNav": 280758000000,
    "turnover": 8
  },
  "symbol": "VTSAX"
}
```

</details>

---

### Mutual Funds Holdings

`GET https://finnhub.io/api/v1/mutual-fund/holdings`

区分: **Premium(有料プラン専用)**

Get full Mutual Funds holdings/constituents. This endpoint covers both US and global mutual funds. For international funds, you must query the data using ISIN. A list of supported funds can be found here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Fund's symbol. |
| `isin` | query | string | いいえ | Fund's isin. |
| `skip` | query | integer | いいえ | Skip the first n results. You can use this parameter to query historical constituents data. The latest result is returned if skip=0 or not set. |

**応答**: `MutualFundHoldings` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `atDate` | string | Holdings update date. |
| `numberOfHoldings` | integer | Number of holdings. |
| `holdings` | array of MutualFundHoldingsData | Array of holdings. |

<details><summary>応答例</summary>

```json
{
  "atDate": "2023-01-31",
  "holdings": [
    {
      "assetType": "Equity",
      "cusip": "037833100",
      "isin": "US0378331005",
      "name": "Apple Inc",
      "percent": 5.36984,
      "share": 463159883,
      "symbol": "AAPL",
      "value": 66829339518
    },
    {
      "assetType": "Equity",
      "cusip": "594918104",
      "isin": "US5949181045",
      "name": "Microsoft Corp",
      "percent": 4.54903,
      "share": 228457719,
      "symbol": "MSFT",
      "value": 56614107345
    }
  ],
  "numberOfHoldings": 3972,
  "symbol": "VTSAX"
}
```

</details>

---

### Mutual Funds Sector Exposure

`GET https://finnhub.io/api/v1/mutual-fund/sector`

区分: **Premium(有料プラン専用)**

Get Mutual Funds sector exposure data.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Mutual Fund symbol. |
| `isin` | query | string | いいえ | Fund's isin. |

**応答**: `MutualFundSectorExposure` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Mutual symbol. |
| `sectorExposure` | array of MutualFundSectorExposureData | Array of sector and exposure levels. |

<details><summary>応答例</summary>

```json
{
  "sectorExposure": [
    {
      "exposure": 26.2,
      "sector": "Information Technology"
    },
    {
      "exposure": 13.84,
      "sector": "Health Care"
    },
    {
      "exposure": 12.29,
      "sector": "Consumer Discretionary"
    },
    {
      "exposure": 10.46,
      "sector": "Financials"
    }
  ],
  "symbol": "VTSAX"
}
```

</details>

---

### Mutual Funds Country Exposure

`GET https://finnhub.io/api/v1/mutual-fund/country`

区分: **Premium(有料プラン専用)**

Get Mutual Funds country exposure data.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Symbol. |
| `isin` | query | string | いいえ | Fund's isin. |

**応答**: `MutualFundCountryExposure` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `countryExposure` | array of MutualFundCountryExposureData | Array of countries and and exposure levels. |

<details><summary>応答例</summary>

```json
{
  "countryExposure": [
    {
      "country": "United States of America (the)",
      "exposure": 96.87
    },
    {
      "country": "Ireland",
      "exposure": 1.58
    },
    {
      "country": "United Kingdom of Great Britain and Northern Ireland (the)",
      "exposure": 0.62
    },
    {
      "country": "Switzerland",
      "exposure": 0.32
    },
    {
      "country": "Bermuda",
      "exposure": 0.29
    },
    {
      "country": "Canada",
      "exposure": 0.2
    }
  ],
  "symbol": "VTSAX"
}
```

</details>

---

### Mutual Funds EET

`GET https://finnhub.io/api/v1/mutual-fund/eet`

区分: **Premium(有料プラン専用)**

Get EET data for EU funds. For PAIs data, please see the EET PAI endpoint.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `isin` | query | string | はい | ISIN. |

**応答**: `MutualFundEet` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `isin` | string | ISIN. |
| `data` | MutualFundEetData | EET data. |

<details><summary>応答例</summary>

```json
{
   "data":{
      "boardGenderDiversityConsidered":true,
      "carbonFootprintScope123Considered":false,
      "carbonFootprintScope12Considered":false,
      "clientSustainabilityPreferencesConsidered":true,
      "controversialWeaponsConsidered":true,
      "energyConsumptionIntensityNACEAConsidered":false,
      "exposuretoEnergyEfficientRealEstateAssetsConsidered":false,
      "exposuretoFossilFuelSectorConsidered":false,
      "exposuretoFossilFuelsExtractionStorageTransportManufactureConsidered":false,
      "greenhouseGasEmissionsScope1Considered":false,
      "greenhouseGasEmissionsScope2Considered":false,
      "greenhouseGasEmissionsScope3Considered":false,
   },
   "isin":"LU2036931686"
}
```

</details>

---

### Mutual Funds EET PAI

`GET https://finnhub.io/api/v1/mutual-fund/eet-pai`

区分: **Premium(有料プラン専用)**

Get EET PAI data for EU funds.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `isin` | query | string | はい | ISIN. |

**応答**: `MutualFundEetPai` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `isin` | string | ISIN. |
| `data` | MutualFundEetPaiData | EET data. |

<details><summary>応答例</summary>

```json
{
   "data":{
      "airPollutantEmissionsCoveredHoldings":27.94263,
      "airPollutantEmissionsEligibleHoldings":490.89858,
      "airPollutantEmissionsNumberHoldingsCovered":14,
      "airPollutantEmissionsPctPortfolioCoverage":4.57,
      "airPollutantEmissionsPctPortfolioEligibleAssets":79.65,
      "airPollutantEmissionsTonnesPerEURm":1.28271,
      "antiHumanTraffickingNumberHoldingsCovered":67,
   },
   "isin":"LU2036931686"
}
```

</details>

---

## Forex

### Forex Exchanges

`GET https://finnhub.io/api/v1/forex/exchange`

List supported forex exchanges

引数: なし

**応答**: array of string

<details><summary>応答例</summary>

```json
[
  "oanda",
  "fxcm",
  "forex.com",
  "ic markets",
  "fxpro"
]
```

</details>

---

### Forex Symbol

`GET https://finnhub.io/api/v1/forex/symbol`

List supported forex symbols.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `exchange` | query | string | はい | Exchange you want to get the list of symbols from. |

**応答**: `ForexSymbol` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `description` | string | Symbol description |
| `displaySymbol` | string | Display symbol name. |
| `symbol` | string | Unique symbol used to identify this symbol used in /forex/candle endpoint. |

<details><summary>応答例</summary>

```json
[
  {
    "description": "IC MARKETS Euro vs US Dollar EURUSD",
    "displaySymbol": "EUR/USD",
    "symbol": "IC MARKETS:1"
  },
  {
    "description": "IC MARKETS Australian vs US Dollar AUDUSD",
    "displaySymbol": "AUD/USD",
    "symbol": "IC MARKETS:5"
  },
  {
    "description": "IC MARKETS British Pound vs US Dollar GBPUSD",
    "displaySymbol": "GBP/USD",
    "symbol": "IC MARKETS:2"
  }]
```

</details>

---

### Forex Candles

`GET https://finnhub.io/api/v1/forex/candle`

区分: **Premium(有料プラン専用)**

Get candlestick data for forex symbols.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Use symbol returned in /forex/symbol endpoint for this field. |
| `resolution` | query | string | はい | Supported resolution includes 1, 5, 15, 30, 60, D, W, M .Some timeframes might not be available depending on the exchange. |
| `from` | query | integer | はい | UNIX timestamp. Interval initial value. |
| `to` | query | integer | はい | UNIX timestamp. Interval end value. |

**応答**: `ForexCandles` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `o` | array of number | List of open prices for returned candles. |
| `h` | array of number | List of high prices for returned candles. |
| `l` | array of number | List of low prices for returned candles. |
| `c` | array of number | List of close prices for returned candles. |
| `v` | array of number | List of volume data for returned candles. |
| `t` | array of number | List of timestamp for returned candles. |
| `s` | string | Status of the response. This field can either be ok or no_data. |

<details><summary>応答例</summary>

```json
{
  "c": [
    1.10713,
    1.10288,
    1.10397,
    1.10182
  ],
  "h": [
    1.1074,
    1.10751,
    1.10729,
    1.10595
  ],
  "l": [
    1.09897,
    1.1013,
    1.10223,
    1.10101
  ],
  "o": [
    1.0996,
    1.107,
    1.10269,
    1.10398
  ],
  "s": "ok",
  "t": [
    1568667600,
    1568754000,
    1568840400,
    1568926800
  ],
  "v": [
    75789,
    75883,
    73485,
    5138
  ]
}
```

</details>

---

### Forex rates

`GET https://finnhub.io/api/v1/forex/rates`

区分: **Premium(有料プラン専用)**

Get rates for all forex pairs. Ideal for currency conversion

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `base` | query | string | いいえ | Base currency. Default to EUR. |
| `date` | query | string | いいえ | Date. Leave blank to get the latest data. |

**応答**: `Forexrates` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `base` | string | Base currency. |
| `quote` | ForexRate | A map of base/quote rates for all currency pair. |

<details><summary>応答例</summary>

```json
{
  "base": "USD",
  "quote": {
    "AED": 3.968012,
    "AFN": 82.373308,
    "ALL": 124.235408,
    "AMD": 520.674275,
    "CAD": 1.525368,
    "CDF": 1904.576741,
    "CHF": 1.053259,
    "CNY": 7.675235,
    "COP": 4282.32676,
    "CRC": 614.796995,
    "CUC": 1.080304,
    "CUP": 28.628067,
    "CVE": 110.517004,
    "CZK": 27.096737,
    "DJF": 191.991344,
    "DKK": 7.461229,
    "DOP": 59.195018,
    "DZD": 139.384021,
    "EGP": 17.018597,
    "ERN": 16.204913,
    "ETB": 36.296767,
    "EUR": 0.91,
    "GBP": 0.874841,
    "JPY": 114.583548,
    "MDL": 19.120251,
    "MGA": 4105.156776,
    "USD": 1,
  }
}
```

</details>

---

## Crypto

### Crypto Exchanges

`GET https://finnhub.io/api/v1/crypto/exchange`

List supported crypto exchanges

引数: なし

**応答**: array of string

<details><summary>応答例</summary>

```json
[
  "KRAKEN",
  "HITBTC",
  "COINBASE",
  "GEMINI",
  "POLONIEX",
  "Binance",
  "ZB",
  "BITTREX",
  "KUCOIN",
  "OKEX",
  "BITFINEX",
  "HUOBI"
]
```

</details>

---

### Crypto Symbol

`GET https://finnhub.io/api/v1/crypto/symbol`

List supported crypto symbols by exchange

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `exchange` | query | string | はい | Exchange you want to get the list of symbols from. |

**応答**: `CryptoSymbol` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `description` | string | Symbol description |
| `displaySymbol` | string | Display symbol name. |
| `symbol` | string | Unique symbol used to identify this symbol used in /crypto/candle endpoint. |

<details><summary>応答例</summary>

```json
[
  {
    "description": "Binance ETHBTC",
    "displaySymbol": "ETH/BTC",
    "symbol": "ETHBTC"
  },
  {
    "description": "Binance LTCBTC",
    "displaySymbol": "LTC/BTC",
    "symbol": "BINANCE:LTCBTC"
  },
  {
    "description": "Binance BNBBTC",
    "displaySymbol": "BNB/BTC",
    "symbol": "BINANCE:BNBBTC"
  }]
```

</details>

---

### Crypto Profile

`GET https://finnhub.io/api/v1/crypto/profile`

区分: **Premium(有料プラン専用)**

Get crypto's profile.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Crypto symbol such as BTC or ETH. |

**応答**: `CryptoProfile` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `longName` | string | Long name. |
| `name` | string | Name. |
| `description` | string | Description. |
| `website` | string | Project's website. |
| `marketCap` | number | Market capitalization. |
| `totalSupply` | number | Total supply. |
| `maxSupply` | number | Max supply. |
| `circulatingSupply` | number | Circulating supply. |
| `logo` | string | Logo image. |
| `launchDate` | string | Launch date. |
| `proofType` | string | Proof type. |

<details><summary>応答例</summary>

```json
{
  "name": "Bitcoin",
  "longName": "Bitcoin (BTC)",
  "description": "Bitcoin uses peer-to-peer technology to operate with no central authority or banks; managing transactions and the issuing of bitcoins is carried out collectively by the network. Although other cryptocurrencies have come before, Bitcoin is the first decentralized cryptocurrency - Its reputation has spawned copies and evolution in the space.With the largest variety of markets and the biggest value - having reached a peak of 318 billion USD - Bitcoin is here to stay. As with any new invention, there can be improvements or flaws in the initial model however the community and a team of dedicated developers are pushing to overcome any obstacle they come across. It is also the most traded cryptocurrency and one of the main entry points for all the other cryptocurrencies. The price is as unstable as always and it can go up or down by 10%-20% in a single day.Bitcoin is an SHA-256 POW coin with almost 21,000,000 total minable coins. The block time is 10 minutes. See below for a full range of Bitcoin markets where you can trade US Dollars for Bitcoin, crypto to Bitcoin and many other fiat currencies too.Bitcoin Whitepaper PDF - A Peer-to-Peer Electronic Cash SystemBlockchain data provided by: Blockchain (main source), Blockchair (backup)",
  "marketCap": 1119891535870.4905,
  "totalSupply": 18876550,
  "maxSupply": 21000000,
  "circulatingSupply": 18876550,
  "logo": "",
  "launchDate": "2009-01-03",
  "website": "https://bitcoin.org/en/",
  "proofType": "PoW"
}
```

</details>

---

### Crypto Candles

`GET https://finnhub.io/api/v1/crypto/candle`

区分: **Premium(有料プラン専用)**

Get candlestick data for crypto symbols.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Use symbol returned in /crypto/symbol endpoint for this field. |
| `resolution` | query | string | はい | Supported resolution includes 1, 5, 15, 30, 60, D, W, M .Some timeframes might not be available depending on the exchange. |
| `from` | query | integer | はい | UNIX timestamp. Interval initial value. |
| `to` | query | integer | はい | UNIX timestamp. Interval end value. |

**応答**: `CryptoCandles` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `o` | array of number | List of open prices for returned candles. |
| `h` | array of number | List of high prices for returned candles. |
| `l` | array of number | List of low prices for returned candles. |
| `c` | array of number | List of close prices for returned candles. |
| `v` | array of number | List of volume data for returned candles. |
| `t` | array of integer | List of timestamp for returned candles. |
| `s` | string | Status of the response. This field can either be ok or no_data. |

<details><summary>応答例</summary>

```json
{
  "c": [
    1.10713,
    1.10288,
    1.10397,
    1.10182
  ],
  "h": [
    1.1074,
    1.10751,
    1.10729,
    1.10595
  ],
  "l": [
    1.09897,
    1.1013,
    1.10223,
    1.10101
  ],
  "o": [
    1.0996,
    1.107,
    1.10269,
    1.10398
  ],
  "s": "ok",
  "t": [
    1568667600,
    1568754000,
    1568840400,
    1568926800
  ],
  "v": [
    75789,
    75883,
    73485,
    5138
  ]
}
```

</details>

---

## Technical Analysis

### Pattern Recognition

`GET https://finnhub.io/api/v1/scan/pattern`

区分: **Premium(有料プラン専用)**

Run pattern recognition algorithm on a symbol. Support double top/bottom, triple top/bottom, head and shoulders, triangle, wedge, channel, flag, and candlestick patterns.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol |
| `resolution` | query | string | はい | Supported resolution includes 1, 5, 15, 30, 60, D, W, M .Some timeframes might not be available depending on the exchange. |

**応答**: `PatternRecognition` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `points` | array of ScanPattern | Array of patterns. |

<details><summary>応答例</summary>

```json
"points": [
    {
      "aprice": 1.09236,
      "atime": 1567458000,
      "bprice": 1.1109,
      "btime": 1568322000,
      "cprice": 1.09897,
      "ctime": 1568667600,
      "dprice": 0,
      "dtime": 0,
      "end_price": 1.1109,
      "end_time": 1568926800,
      "entry": 1.1109,
      "eprice": 0,
      "etime": 0,
      "mature": 0,
      "patternname": "Double Bottom",
      "patterntype": "bullish",
      "profit1": 1.1294,
      "profit2": 0,
      "sortTime": 1568926800,
      "start_price": 1.1109,
      "start_time": 1566853200,
      "status": "incomplete",
      "stoploss": 1.0905,
      "symbol": "EUR_USD",
      "terminal": 0
    },
    {
      "aprice": 1.09236,
      "atime": 1567458000,
      "bprice": 1.1109,
      "btime": 1568322000,
      "cprice": 1.09897,
      "ctime": 1568667600,
      "dprice": 1.13394884,
      "dtime": 1568926800,
      "entry": 1.1339,
      "mature": 0,
      "patternname": "Bat",
      "patterntype": "bearish",
      "profit1": 1.1181,
      "profit2": 1.1082,
      "przmax": 1.1339,
      "przmin": 1.129,
      "rrratio": 3.34,
      "sortTime": 1568667600,
      "status": "incomplete",
      "stoploss": 1.1416,
      "symbol": "EUR_USD",
      "terminal": 0,
      "xprice": 1.1393,
      "xtime": 1561669200
    }
]
```

</details>

---

### Support/Resistance

`GET https://finnhub.io/api/v1/scan/support-resistance`

区分: **Premium(有料プラン専用)**

Get support and resistance levels for a symbol.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol |
| `resolution` | query | string | はい | Supported resolution includes 1, 5, 15, 30, 60, D, W, M .Some timeframes might not be available depending on the exchange. |

**応答**: `SupportResistance` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `levels` | array of number | Array of support and resistance levels. |

<details><summary>応答例</summary>

```json
{
  "levels": [
    1.092360019683838,
    1.1026300191879272,
    1.113450050354004,
    1.1233500242233276,
    1.134719967842102,
    1.1513700485229492
  ]
}
```

</details>

---

### Aggregate Indicators

`GET https://finnhub.io/api/v1/scan/technical-indicator`

区分: **Premium(有料プラン専用)**

Get aggregate signal of multiple technical indicators such as MACD, RSI, Moving Average v.v. A full list of indicators can be found here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | symbol |
| `resolution` | query | string | はい | Supported resolution includes 1, 5, 15, 30, 60, D, W, M .Some timeframes might not be available depending on the exchange. |

**応答**: `AggregateIndicators` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `technicalAnalysis` | TechnicalAnalysis | Number of indicator signals strong buy, buy, neutral, sell, strong sell signals. |
| `trend` | Trend | Whether the market is trending. |

<details><summary>応答例</summary>

```json
{
  "technicalAnalysis": {
    "count": {
      "buy": 6,
      "neutral": 7,
      "sell": 4
    },
    "signal": "neutral"
  },
  "trend": {
    "adx": 24.46020733373421,
    "trending": false
  }
}
```

</details>

---

### Technical Indicators

`GET https://finnhub.io/api/v1/indicator`

区分: **Premium(有料プラン専用)**

Return technical indicator with price data. List of supported indicators can be found here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | symbol |
| `resolution` | query | string | はい | Supported resolution includes 1, 5, 15, 30, 60, D, W, M .Some timeframes might not be available depending on the exchange. |
| `from` | query | integer | はい | UNIX timestamp. Interval initial value. |
| `to` | query | integer | はい | UNIX timestamp. Interval end value. |
| `indicator` | query | string | はい | Indicator name. Full list can be found here. |
| `indicator_fields` | body |  | いいえ | Check out this page to see which indicators and params are supported. |

**応答**: `TechnicalIndicator` (object)

<details><summary>応答例</summary>

```json
{"sma":[0,0,74.23916,73.74833,73.72416,70.676666,70.045,68.911,67.41666,66.802],"t":[1583107200,1583193600,1583280000,1583366400,1583452800,1583712000,1583798400,1583884800,1583971200,1584057600]}
```

</details>

---

## Alternative Data

### Earnings Call Transcripts List

`GET https://finnhub.io/api/v1/stock/transcripts/list`

区分: **Premium(有料プラン専用)**

List earnings call transcripts' metadata. This endpoint is available for Global companies. You can get a list of supported symbols here

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Company symbol: AAPL. Leave empty to list the latest transcripts |

**応答**: `EarningsCallTranscriptsList` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Company symbol. |
| `transcripts` | array of StockTranscripts | Array of transcripts' metadata |

<details><summary>応答例</summary>

```json
{
  "symbol": "AAPL",
  "transcripts": [
    {
      "id": "AAPL_326091",
      "quarter": 1,
      "symbol": "AAPL",
      "time": "2020-01-28 21:35:45",
      "title": "AAPL - Earnings Call Transcript Q1 2020",
      "year": 2020
    },
    {
      "id": "AAPL_322579",
      "quarter": 4,
      "symbol": "AAPL",
      "time": "2019-10-30 22:27:15",
      "title": "AAPL - Earnings Call Transcript Q4 2019",
      "year": 2019
    },
    {
      "id": "AAPL_318112",
      "quarter": 3,
      "symbol": "AAPL",
      "time": "2019-07-30 22:26:28",
      "title": "AAPL - Earnings Call Transcript Q3 2019",
      "year": 2019
    },
    {
      "id": "AAPL_313737",
      "quarter": 2,
      "symbol": "AAPL",
      "time": "2019-04-30 19:55:19",
      "title": "AAPL - Earnings Call Transcript Q2 2019",
      "year": 2019
    },
    {
      "id": "AAPL_308757",
      "quarter": 1,
      "symbol": "AAPL",
      "time": "2019-01-29 21:06:06",
      "title": "AAPL - Earnings Call Transcript Q1 2019",
      "year": 2019
    }
  ]
}
```

</details>

---

### Earnings Call Transcripts

`GET https://finnhub.io/api/v1/stock/transcripts`

区分: **Premium(有料プラン専用)**

Get earnings call transcripts, audio and participants' list. Data is available for US, UK, European, Australian and Canadian companies.15+ years of data is available with 220,000+ audio which add up to 7TB in size.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `id` | query | string | はい | Transcript's id obtained with Transcripts List endpoint. |

**応答**: `EarningsCallTranscripts` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Company symbol. |
| `transcript` | array of TranscriptContent | Transcript content. |
| `participant` | array of TranscriptParticipant | Participant list |
| `audio` | string | Audio link. |
| `id` | string | Transcript's ID. |
| `title` | string | Title. |
| `time` | string | Time of the event. |
| `year` | integer | Year of earnings result in the case of earnings call transcript. |
| `quarter` | integer | Quarter of earnings result in the case of earnings call transcript. |

<details><summary>応答例</summary>

```json
{
  "audio": "https://static.finnhub.io/transcripts_audio/4319666.mp3",
  "id": "AAPL_326091",
  "participant": [
    {
      "name": "Tejas Gala",
      "description": "Senior Analyst at Corporate Finance and IR"
    },
    {
      "name": "Tim Cook",
      "description": "CEO"
    }
  ],
  "quarter": 1,
  "symbol": "AAPL",
  "time": "2020-01-28 21:35:45",
  "title": "AAPL - Earnings call transcripts Q1 2020",
  "transcript": [
    {
      "name": "Operator",
      "speech": [
        "Good day, everyone. Welcome to the Apple Incorporated First Quarter Fiscal Year 2020 Earnings Conference Call. Today's conference is being recorded. At this time for opening remarks and introductions, I would like to turn the call over to Tejas Gala, Senior Analyst, Corporate Finance and Investor Relations. Please go ahead."
      ]
    },
    {
      "name": "Tejas Gala",
      "speech": [
        "Thank you. Good afternoon, and thank you for joining us. Speaking first today is Apple's CEO, Tim Cook, and he'll be followed by CFO, Luca Maestri. After that, we'll open the call to questions from analysts. Please note that some of the information you'll hear during our discussion today will consist of forward-looking statements, including without limitation, those regarding revenue, gross margin, operating expenses, other income and expenses, taxes, capital allocation and future business outlook. Actual results or trends could differ materially from our forecast. For more information, please refer to the risk factors discussed in Apple's most recently filed periodic reports on Form 10-K and Form 10-Q and the Form 8-K filed with the SEC today, along with the associated press release. Apple assumes no obligation to update any forward-looking statements or information, which speaks as of their respective dates. I'd now like to turn the call over to Tim for introductory remarks."
      ]
    }
  ],
  "year": 2020
}
```

</details>

---

### Earnings Call Audio Live

`GET https://finnhub.io/api/v1/stock/earnings-call-live`

区分: **Premium(有料プラン専用)**

Stream live earnings calls with data provided in the calendar. The data will be available in m3u8 format. mp3 files will be available once the calls finish in the recording field.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `from` | query | string | いいえ | From date YYYY-MM-DD. |
| `to` | query | string | いいえ | To date YYYY-MM-DD. |
| `symbol` | query | string | いいえ | Filter by symbol: AAPL. |

**応答**: `EarningsCallLive` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `event` | array of EarningsCallLiveResult | Array of earnings call events that support live streaming. |

<details><summary>応答例</summary>

```json
{
  "event": [
    {
      "symbol": "NVDA",
      "year": 2025,
      "quarter": 3,
      "event": "NVDA - Earnings call Q3 year",
      "time": "2024-11-20 22:00:00",
      "liveAudio": "https://live.finnhub.io/hls/2063191eb8563e1645fe3bde2b057511dce4f8a0fb39a2fb9/audio.m3u8",
      "recording": ""
    },
    {
      "symbol": "SNOW",
      "year": 2025,
      "quarter": 3,
      "event": "SNOW - Earnings call Q3 year",
      "time": "2024-11-20 22:00:00",
      "liveAudio": "https://live.finnhub.io/hls/869c16f0fe27d972d49b511f18eea69499c6f0c460a28/audio.m3u8",
      "recording": ""
    }
  ]
}
```

</details>

---

### Company Presentation

`GET https://finnhub.io/api/v1/stock/presentation`

区分: **Premium(有料プラン専用)**

Get presentations/slides data in PDF format that are usually used during earnings calls. You can get a list of supported symbols here

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Company symbol. |

**応答**: `StockPresentation` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Company symbol. |
| `res` | array of PresentationData | Presentation data. |

<details><summary>応答例</summary>

```json
{
  "res": [
    {
      "atTime": "2025-01-29 22:00:00",
      "quarter": 4,
      "title": "IBM Q4 2024",
      "url": "https://finnhub.io/api/redirect?urlType=transcripts-slides2&id=d244c28ec5ee4767b2",
      "year": 2024
    },
    {
      "atTime": "2024-10-23 21:00:00",
      "quarter": 3,
      "title": "IBM Q3 2024",
      "url": "https://finnhub.io/api/redirect?urlType=transcripts-slides2&id=491dc513be934082f1",
      "year": 2024
    }
  ],
  "symbol": "IBM"
}
```

</details>

---

### Social Sentiment

`GET https://finnhub.io/api/v1/stock/social-sentiment`

区分: **Premium(有料プラン専用)**

Get social sentiment for stocks on Reddit and Twitter.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Company symbol. |
| `from` | query | string | いいえ | From date YYYY-MM-DD. |
| `to` | query | string | いいえ | To date YYYY-MM-DD. |

**応答**: `SocialSentiment` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Company symbol. |
| `data` | array of SentimentContent | Sentiment data. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "atTime": "2021-05-08 14:00:00",
      "mention": 32,
      "positiveScore": 0.9213675,
      "negativeScore": -0.9864475,
      "positiveMention": 20,
      "negativeMention": 12,
      "score": -0.0341123222115352
    },
    {
      "atTime": "2021-05-08 13:00:00",
      "mention": 25,
      "positiveScore": 0.92,
      "negativeScore": -0.991266,
      "positiveMention": 8,
      "negativeMention": 17,
      "score": -0.56282
    }
  ],
  "symbol": "AAPL"
}
```

</details>

---

### Investment Themes (Thematic Investing)

`GET https://finnhub.io/api/v1/stock/investment-theme`

区分: **Premium(有料プラン専用)**

Thematic investing involves creating a portfolio (or portion of a portfolio) by gathering together a collection of companies involved in certain areas that you predict will generate above-market returns over the long term. Themes can be based on a concept such as ageing populations or a sub-sector such as robotics, and drones. Thematic investing focuses on predicted long-term trends rather than specific companies or sectors, enabling investors to access structural, one-off shifts that can change an entire industry.

This endpoint will help you get portfolios of different investment themes that are changing our life and are the way of the future.

A full list of themes supported can be found here. The theme coverage and portfolios are updated bi-weekly by our analysts. Our approach excludes penny, super-small cap and illiquid stocks.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `theme` | query | string | はい | Investment theme. A full list of themes supported can be found here. |

**応答**: `InvestmentThemes` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `theme` | string | Investment theme |
| `data` | array of InvestmentThemePortfolio | Investment theme portfolio. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "symbol": "ICE"
    },
    {
      "symbol": "NDAQ"
    },
    {
      "symbol": "CBOE"
    },
    {
      "symbol": "FDS"
    },
    {
      "symbol": "SPGI"
    },
    {
      "symbol": "TW"
    }
  ],
  "theme": "financialExchangesData"
}
```

</details>

---

### Supply Chain Relationships

`GET https://finnhub.io/api/v1/stock/supply-chain`

区分: **Premium(有料プラン専用)**

This endpoint provides an overall map of public companies' key customers and suppliers. The data offers a deeper look into a company's supply chain and how products are created. The data will help investors manage risk, limit exposure or generate alpha-generating ideas and trading insights.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |

**応答**: `SupplyChainRelationships` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | symbol |
| `data` | array of KeyCustomersSuppliers | Key customers and suppliers. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "customer": true,
      "name": "Costco Wholesale Corporation",
      "oneMonthCorrelation": 0.26,
      "oneYearCorrelation": 0.63,
      "sixMonthCorrelation": 0.87,
      "supplier": false,
      "symbol": "COST",
      "threeMonthCorrelation": 0.89,
      "twoWeekCorrelation": 0.35,
      "twoYearCorrelation": 0.91
    },
    {
      "customer": true,
      "name": "Qualcomm",
      "oneMonthCorrelation": 0.06,
      "oneYearCorrelation": 0.58,
      "sixMonthCorrelation": 0.87,
      "supplier": true,
      "symbol": "QCOM",
      "threeMonthCorrelation": 0.88,
      "twoWeekCorrelation": 0.71,
      "twoYearCorrelation": 0.94
    },
    {
      "customer": false,
      "name": "Foxconn Industrial Internet Co., Ltd.",
      "oneMonthCorrelation": 0.25,
      "oneYearCorrelation": -0.48,
      "sixMonthCorrelation": -0.65,
      "supplier": true,
      "symbol": "601138.SS",
      "threeMonthCorrelation": -0.79,
      "twoWeekCorrelation": -0.55,
      "twoYearCorrelation": -0.6
    }
  ],
  "symbol": "AAPL"
}
```

</details>

---

### Company ESG Scores

`GET https://finnhub.io/api/v1/stock/esg`

区分: **Premium(有料プラン専用)**

This endpoint provides the latest ESG scores and important indicators for 7000+ global companies. The data is collected through company's public ESG disclosure and public sources.

Our ESG scoring models takes into account more than 150 different inputs to calculate the level of ESG risks and how well a company is managing them. A higher score means lower ESG risk or better ESG management. ESG scores are in the the range of 0-100. Some key indicators might contain letter-grade score from C- to A+ with C- is the lowest score and A+ is the highest score.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |

**応答**: `CompanyESG` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | symbol |
| `totalESGScore` | number | Total ESG Score |
| `environmentScore` | number | Environment Score |
| `governanceScore` | number | Governance Score |
| `socialScore` | number | Social Score |
| `data` | CompanyESGMap | Map key-value pair of key ESG data points. |

<details><summary>応答例</summary>

```json
{
  "data": {
    "womenManagementPercentage": 17.02,
    "adultContent": false,
    "alcoholic": false,
    "animalTesting": false,
    "antitrust": "C+",
    "asianEmployeePercentage": 27,
    "asianManagementPercentage": 27,
    "blackEmployeePercentage": 9,
    "blackManagementPercentage": 4,
    "carbonReductionPolicy": null,
    "catholic": false,
    "climateStrategy": "A+",
    "co2EmissionScope1": 47430,
    "co2EmissionScope2": 890189,
    "co2EmissionScope3": 22648000,
    "co2EmissionTotal": 937619,
    "coalEnergy": false,
    "ecofriendlyPackaging": null,
    "environmentalReporting": true,
    "firearms": false,
    "fuelEfficiencyConsumption": null,
    "furLeather": false,
    "gambling": false,
    "gmo": false,
    "hazardousSubstances": null,
    "hispanicLatinoEmployeePercentage": 14,
    "hispanicLatinoManagementPercentage": 8,
    "humanRightsPolicy": "C-",
    "militaryContract": false,
    "nuclear": false,
    "palmOil": false,
    "pesticides": false,
    "privacyPolicy": "B-",
    "recallPolicySafety": null,
    "recyclingPolicy": null,
    "stakeholderEngagement": null,
    "sustainableForestryPolicy": null,
    "tobacco": false,
    "totalWomenPercentage": 34,
    "waterEfficiencyConsumption": null,
    "weapons": false,
    "whiteEmployeePercentage": 47,
    "whiteManagementPercentage": 59,
    "workplaceHealthSafety": null
  },
  "environmentScore": 73.21,
  "governanceScore": 56.06,
  "socialScore": 45.81,
  "symbol": "AAPL",
  "totalESGScore": 56.04
}
```

</details>

---

### Historical ESG Scores

`GET https://finnhub.io/api/v1/stock/historical-esg`

区分: **Premium(有料プラン専用)**

This endpoint provides historical ESG scores and important indicators for 7000+ global companies. The data is collected through company's public ESG disclosure and public sources.

Our ESG scoring models takes into account more than 150 different inputs to calculate the level of ESG risks and how well a company is managing them. A higher score means lower ESG risk or better ESG management. ESG scores are in the the range of 0-100. Some key indicators might contain letter-grade score from C- to A+ with C- is the lowest score and A+ is the highest score.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |

**応答**: `HistoricalCompanyESG` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | symbol |
| `data` | array of CompanyESG2 | Historical ESG data points. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "data": {
        "adultContent": false,
        "alcoholic": false,
        "animalTesting": false,
        "antitrust": "62.0",
        "asianEmployeePercentage": 27.9,
        "asianManagementPercentage": 29.2,
        "blackEmployeePercentage": 9.4,
        "blackManagementPercentage": 4,
        "carbonReductionPolicy": "True",
        "catholic": true,
        "co2EmissionScope1": 55202,
        "co2EmissionScope2": 1003246,
        "co2EmissionScope3": 23128420,
        "co2EmissionTotal": 1058448,
        "coalEnergy": false
      },
      "environmentScore": 61.74593,
      "governanceScore": 92.81813,
      "period": "2021-09-25",
      "socialScore": 76.52558,
      "totalESGScore": 77.02988
    },
    {
      "data": {
        "adultContent": false,
        "alcoholic": false,
        "animalTesting": false,
        "antitrust": "28.0",
        "asianEmployeePercentage": 27,
        "asianManagementPercentage": 27,
        "blackEmployeePercentage": 9,
        "blackManagementPercentage": 4,
        "carbonReductionPolicy": "True",
        "catholic": true,
        "co2EmissionScope1": 47430,
        "co2EmissionScope2": 890189,
        "co2EmissionScope3": 22547000,
        "co2EmissionTotal": 937619
      },
      "environmentScore": 59.460255,
      "governanceScore": 85.85033,
      "period": "2020-09-26",
      "socialScore": 74.40586,
      "totalESGScore": 73.238815
    }
  ],
  "symbol": "AAPL"
}
```

</details>

---

### Company Earnings Quality Score

`GET https://finnhub.io/api/v1/stock/earnings-quality-score`

区分: **Premium(有料プラン専用)**

This endpoint provides Earnings Quality Score for global companies.

 Earnings quality refers to the extent to which current earnings predict future earnings. "High-quality" earnings are expected to persist, while "low-quality" earnings do not. A higher score means a higher earnings quality

Finnhub uses a proprietary model which takes into consideration 4 criteria:

 ProfitabilityGrowthCash Generation & Capital AllocationLeverage
We then compare the metrics of each company in each category against its peers in the same industry to gauge how quality its earnings is.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |
| `freq` | query | string | はい | Frequency. Currently support annual and quarterly |

**応答**: `CompanyEarningsQualityScore` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol |
| `freq` | string | Frequency |
| `data` | array of CompanyEarningsQualityScoreData | Array of earnings quality score. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "capitalAllocation": 67.6878,
      "growth": 55.8022,
      "letterScore": "B+",
      "leverage": 24.5122,
      "period": "2021-06-01",
      "profitability": 82.3843,
      "score": 57.5966
    },
    {
      "capitalAllocation": 75.1464,
      "growth": 70.2461,
      "letterScore": "A-",
      "leverage": 39.5682,
      "period": "2021-03-01",
      "profitability": 88.4613,
      "score": 68.3555
    },
    {
      "capitalAllocation": 43.8708,
      "growth": 68.1803,
      "letterScore": "A-",
      "leverage": 56.1926,
      "period": "2020-12-01",
      "profitability": 92.6311,
      "score": 65.2187
    },
  ],
  "freq": "quarterly",
  "symbol": "AAPL"
}
```

</details>

---

### COVID-19

`GET https://finnhub.io/api/v1/covid19/us`

区分: 利用頻度高

Get real-time updates on the number of COVID-19 (Corona virus) cases in the US with a state-by-state breakdown. Data is sourced from CDC and reputable sources. You can also access this API here

引数: なし

**応答**: `CovidInfo` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `state` | string | State. |
| `case` | number | Number of confirmed cases. |
| `death` | number | Number of confirmed deaths. |
| `updated` | string | Updated time. |

<details><summary>応答例</summary>

```json
[
  {
    "state": "New York",
    "case": 8403,
    "death": 46,
    "updated": "2020-03-20 21:38:50"
  },
  {
    "state": "Washington",
    "case": 1524,
    "death": 83,
    "updated": "2020-03-20 21:38:50"
  }
]
```

</details>

---

### FDA Committee Meeting Calendar

`GET https://finnhub.io/api/v1/fda-advisory-committee-calendar`

FDA's advisory committees are established to provide functions which support the agency's mission of protecting and promoting the public health, while meeting the requirements set forth in the Federal Advisory Committee Act. Committees are either mandated by statute or established at the discretion of the Department of Health and Human Services. Each committee is subject to renewal at two-year intervals unless the committee charter states otherwise.

引数: なし

**応答**: `FDAComitteeMeeting` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `fromDate` | string | Start time of the event in EST. |
| `toDate` | string | End time of the event in EST. |
| `eventDescription` | string | Event's description. |
| `url` | string | URL. |

<details><summary>応答例</summary>

```json
[
  {
    "fromDate": "2016-01-11 19:00:00",
    "toDate": "2016-01-11 19:00:00",
    "eventDescription": "January 12, 2016: Meeting of the Psychopharmacologic Drugs Advisory Committee Meeting Announcement - 01/11/2016 - 01/11/2016",
    "url": "https://www.fda.gov/advisory-committees/advisory-committee-calendar/january-12-2016-meeting-psychopharmacologic-drugs-advisory-committee-meeting-announcement-01112016"
  },
  {
    "fromDate": "2016-01-14 13:00:00",
    "toDate": "2016-01-14 17:00:00",
    "eventDescription": "January 14, 2016: Vaccines and Related Biological Products Advisory Committee Meeting Announcement - 01/14/2016 - 01/14/2016",
    "url": "https://www.fda.gov/advisory-committees/advisory-committee-calendar/january-14-2016-vaccines-and-related-biological-products-advisory-committee-meeting-announcement"
  }
]
```

</details>

---

### USPTO Patents

`GET https://finnhub.io/api/v1/stock/uspto-patent`

区分: 新規

List USPTO patents for companies. Limit to 250 records per API call.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |
| `from` | query | string | はい | From date YYYY-MM-DD. |
| `to` | query | string | はい | To date YYYY-MM-DD. |

**応答**: `UsptoPatentResult` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `data` | array of UsptoPatent | Array of patents. |

<details><summary>応答例</summary>

```json
{
   "data":[
      {
         "applicationNumber":"17163855",
         "companyFilingName":[
            "NVIDIA CORPORATION"
         ],
         "description":"DYNAMIC DIRECTIONAL ROUNDING",
         "filingDate":"2021-02-01 00:00:00",
         "filingStatus":"Application",
         "patentNumber":"US20210232366A1",
         "publicationDate":"2021-07-29 00:00:00",
         "type":"Utility",
         "url":"https://patentimages.storage.googleapis.com/33/ed/0c/0b6b6f87e55fea/US20210232366A1.pdf"
      },
      {
         "applicationNumber":"17162550",
         "companyFilingName":[
            "NVIDIA CORPORATION"
         ],
         "description":"REAL-TIME HARDWARE-ASSISTED GPU TUNING USING MACHINE LEARNING",
         "filingDate":"2021-01-29 00:00:00",
         "filingStatus":"Application",
         "patentNumber":"US20210174569A1",
         "publicationDate":"2021-06-10 00:00:00",
         "type":"Utility",
         "url":"https://patentimages.storage.googleapis.com/23/40/45/98b27a921d657c/US20210174569A1.pdf"
      }
   ],
   "symbol":"NVDA"
}
```

</details>

---

### H1-B Visa Application

`GET https://finnhub.io/api/v1/stock/visa-application`

区分: 新規

Get a list of H1-B and Permanent visa applications for companies from the DOL. The data is updated quarterly.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |
| `from` | query | string | はい | From date YYYY-MM-DD. Filter on the beginDate column. |
| `to` | query | string | はい | To date YYYY-MM-DD. Filter on the beginDate column. |

**応答**: `VisaApplicationResult` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `data` | array of VisaApplication | Array of H1b and Permanent visa applications. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "year": 2020,
      "quarter": 1,
      "symbol": "AAPL",
      "caseNumber": "I-200-19268-472068",
      "caseStatus": "Certified",
      "receivedDate": "2019-09-25",
      "visaClass": "H-1B",
      "jobTitle": "ASIC DESIGN VERIFICATION ENGINEER",
      "socCode": "17-2072",
      "fullTimePosition": "Y",
      "beginDate": "2019-10-14",
      "endDate": "2022-10-13",
      "employerName": "APPLE INC.",
      "worksiteAddress": "320 S Capital of Texas Highway",
      "worksiteCity": "West Lake Hills",
      "worksiteCounty": "Travis",
      "worksiteState": "TX",
      "worksitePostalCode": "78746",
      "wageRangeFrom": 120000,
      "wageRangeTo": null,
      "wageUnitOfPay": "Year",
      "wageLevel": "II",
      "h1bDependent": "N"
    },
    ...
  ],
  "symbol": "AAPL"
}
```

</details>

---

### Senate Lobbying

`GET https://finnhub.io/api/v1/stock/lobbying`

区分: 新規

Get a list of reported lobbying activities in the Senate and the House.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |
| `from` | query | string | はい | From date YYYY-MM-DD. |
| `to` | query | string | はい | To date YYYY-MM-DD. |

**応答**: `LobbyingResult` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `data` | array of LobbyingData | Array of lobbying activities. |

<details><summary>応答例</summary>

```json
{
  "data":[
    {
      "symbol":"AAPL",
      "name":"APPLE, INC.",
      "description":"Hardware and software maunfacturer",
      "country":"US",
      "uuid":"db75bb6f-162a-433a-a997-a679eb4c6af6",
      "year":2020,
      "period":"fourth_quarter",
      "type":"Q4",
      "documentUrl":"https://lda.senate.gov/filings/public/filing/db75bb6f-162a-433a-a997-a679eb4c6af6/print/",
      "income":40000,
      "expenses":null,
      "postedName":"",
      "dtPosted":"",
      "clientId":"173094",
      "registrantId":"86196",
      "senateId":"86196-173094",
      "houseRegistrantId":"36548"
    },
    {
      "symbol":"AAPL",
      "name":"APPLE INC",
      "description":"",
      "country":"US",
      "uuid":"cad6db2f-c3ca-4b9d-bc24-4c56fc7eaadb",
      "year":2020,
      "period":"fourth_quarter",
      "type":"Q4",
      "documentUrl":"https://lda.senate.gov/filings/public/filing/cad6db2f-c3ca-4b9d-bc24-4c56fc7eaadb/print/",
      "income":null,
      "expenses":1450000,
      "postedName":"",
      "dtPosted":"",
      "clientId":"103979",
      "registrantId":"4152",
      "senateId":"4152-103979",
      "houseRegistrantId":"31450"
    }
  ],
  "symbol":"AAPL"
}
```

</details>

---

### USA Spending

`GET https://finnhub.io/api/v1/stock/usa-spending`

区分: 新規

Get a list of government's spending activities from USASpending dataset for public companies. This dataset can help you identify companies that win big government contracts which is extremely important for industries such as Defense, Aerospace, and Education. Only recent data is available via the API.

For historical data, you can download it here: Pre-2021, 2021, 2022, 2023, 2024

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |
| `from` | query | string | はい | From date YYYY-MM-DD. Filter for actionDate |
| `to` | query | string | はい | To date YYYY-MM-DD. Filter for actionDate |

**応答**: `UsaSpendingResult` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `data` | array of UsaSpending | Array of government's spending data points. |

<details><summary>応答例</summary>

```json
{
  "data":[
    {
      "symbol":"AAPL",
      "recipientName":"APPLE INC.",
      "recipientParentName":"APPLE INC.",
      "country":"USA",
      "totalValue":4238,
      "actionDate":"2021-11-12",
      "performanceStartDate":"2021-11-12",
      "performanceEndDate":"2021-12-10",
      "awardingAgencyName":"SMITHSONIAN INSTITUTION (SI)",
      "awardingSubAgencyName":"SMITHSONIAN INSTITUTION",
      "awardingOfficeName":"SMITHSONIAN ASTROPHYSICAL OBSERVATORY",
      "performanceCountry":"USA",
      "performanceCity":"CUPERTINO",
      "performanceCounty":"SANTA CLARA",
      "performanceState":"CALIFORNIA",
      "performanceZipCode":"950140642",
      "performanceCongressionalDistrict":"17",
      "awardDescription":"MACBOOK PRO",
      "naicsCode":"334111",
      "permalink":"https://www.usaspending.gov/award/CONT_AWD_33131222P00465925_3300_-NONE-_-NONE-/"
    }
  ],
  "symbol":"AAPL"
}
```

</details>

---

### Congressional Trading

`GET https://finnhub.io/api/v1/stock/congressional-trading`

区分: **Premium(有料プラン専用)**

Get stock trades data disclosed by members of congress.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol of the company: AAPL. |
| `from` | query | string | はい | From date YYYY-MM-DD. |
| `to` | query | string | はい | To date YYYY-MM-DD. |

**応答**: `CongressionalTrading` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol of the company. |
| `data` | array of CongressionalTransaction | Array of stock trades. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "amountFrom": 100001,
      "amountTo": 250000,
      "assetName": "Oppenheimer SteelPath MLP Select 40 Y (NASDAQ)",
      "filingDate": "2015-05-14",
      "name": "Lamar Alexander",
      "ownerType": "Spouse",
      "position": "senator",
      "symbol": "MLPTX",
      "transactionDate": "2014-04-04",
      "transactionType": "Purchase"
    },
    {
      "amountFrom": 1001,
      "amountTo": 15000,
      "assetName": "Oppenheimer SteelPath MLP Select 40 Y (NASDAQ)",
      "filingDate": "2015-05-14",
      "name": "Lamar Alexander",
      "ownerType": "Spouse",
      "position": "senator",
      "symbol": "MLPTX",
      "transactionDate": "2014-02-07",
      "transactionType": "Purchase"
    }
  ],
  "symbol": "MLPTX"
}
```

</details>

---

### Bank Branch List

`GET https://finnhub.io/api/v1/bank-branch`

区分: **Premium(有料プラン専用)**

Retrieve list of US bank branches information for a given symbol.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |

**応答**: `BankBranchRes` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of BankBranchData | Array of branches. |
| `symbol` | string | Symbol |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "branchId": "201601",
      "address": "1910 E 95th St",
      "state": "IL",
      "zipCode": "60617",
      "date": "2000-02-28"
    },
    {
      "branchId": "359157",
      "address": "401 W 49th St",
      "state": "FL",
      "zipCode": "33012",
      "date": "2000-02-01"
    }
  ],
  "symbol": "JPM"
}
```

</details>

---

### Airline Price Index

`GET https://finnhub.io/api/v1/airline/price-index`

区分: **Premium(有料プラン専用)**

The Flight Ticket Price Index API provides comprehensive data on airline ticket prices, including the average daily ticket price and its percentage change (price index). This data, collected weekly and projected two weeks ahead, aggregates daily prices and indexes from the 50 busiest and largest airports across the USA. The dataset includes detailed information on airlines, dates, and average ticket prices, offering valuable insights for market analysis and pricing strategies.

The price index is calculated as percentage change of average daily ticket price from the previous weekly reading. Raw ticket prices data is available for Enterprise users. Contact us to inquire about the raw price data.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `airline` | query | string | はい | Filter data by airline. Accepted values: united,delta,american_airlines,southwest,southern_airways_express,alaska_airlines,frontier_airlines,jetblue_airways,spirit_airlines,sun_country_airlines,breeze_airways,hawaiian_airlines |
| `from` | query | string | はい | From date YYYY-MM-DD. |
| `to` | query | string | はい | To date YYYY-MM-DD. |

**応答**: `AirlinePriceIndexData` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of AirlinePriceIndex | Array of price index. |
| `airline` | string | Airline name |
| `from` | string | From date |
| `to` | string | To date |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "airline": "united",
      "date": "2024-06-17",
      "priceIndex": 0.832755,
      "dailyAvgPrice": 360.918
    },
    {
      "airline": "united",
      "date": "2024-06-19",
      "priceIndex": 0.850855,
      "dailyAvgPrice": 307.089
    },
    {
      "airline": "united",
      "date": "2024-06-20",
      "priceIndex": 1.33928,
      "dailyAvgPrice": 411.278
    },
    {
      "airline": "united",
      "date": "2024-06-21",
      "priceIndex": 1.0872,
      "dailyAvgPrice": 447.143
    },
    {
      "airline": "united",
      "date": "2024-06-22",
      "priceIndex": 0.994883,
      "dailyAvgPrice": 444.855
    },
    {
      "airline": "united",
      "date": "2024-06-23",
      "priceIndex": 1,
      "dailyAvgPrice": 784.301
    },
    {
      "airline": "united",
      "date": "2024-06-24",
      "priceIndex": 0.857554,
      "dailyAvgPrice": 672.58
    }
  ],
  "from": "2024-04-04",
  "to": "2024-07-10",
  "airline": "united"
}
```

</details>

---

## Bonds

### Bond Profile

`GET https://finnhub.io/api/v1/bond/profile`

区分: **Premium(有料プラン専用)**

Get general information of a bond. You can query by FIGI, ISIN or CUSIP. A list of supported bonds can be found here.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `isin` | query | string | いいえ | ISIN |
| `cusip` | query | string | いいえ | CUSIP |
| `figi` | query | string | いいえ | FIGI |

**応答**: `BondProfile` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `isin` | string | ISIN. |
| `cusip` | string | Cusip. |
| `figi` | string | FIGI. |
| `coupon` | number | Coupon. |
| `maturityDate` | string | Period. |
| `offeringPrice` | number | Offering price. |
| `issueDate` | string | Issue date. |
| `bondType` | string | Bond type. |
| `debtType` | string | Bond type. |
| `industryGroup` | string | Industry. |
| `industrySubGroup` | string | Sub-Industry. |
| `asset` | string | Asset. |
| `assetType` | string | Asset. |
| `datedDate` | string | Dated date. |
| `firstCouponDate` | string | First coupon date. |
| `originalOffering` | number | Offering amount. |
| `amountOutstanding` | number | Outstanding amount. |
| `paymentFrequency` | string | Payment frequency. |
| `securityLevel` | string | Security level. |
| `callable` | boolean | Callable. |
| `couponType` | string | Coupon type. |

<details><summary>応答例</summary>

```json
{
  "isin":"US912810TD00",
  "cusip":"",
  "figi":"BBG0152KFHS6",
  "coupon":2.25,
  "maturityDate":"2052-02-15",
  "offeringPrice":100,
  "issueDate":"2022-03-15",
  "bondType":"US Government",
  "debtType":"",
  "industryGroup":"Government",
  "industrySubGroup":"U.S. Treasuries",
  "asset":"",
  "assetType":"",
  "datedDate":"2022-02-15",
  "firstCouponDate":"2022-08-15",
  "originalOffering":20000000000,
  "amountOutstanding":36914000000,
  "paymentFrequency":"Semi-Annual",
  "securityLevel":"",
  "callable":null,
  "couponType":"",
  "dayCount":""
}
```

</details>

---

### Bond price data

`GET https://finnhub.io/api/v1/bond/price`

区分: **Premium(有料プラン専用)**

Get bond's price data. The following datasets are supported:


  
    
      Exchange
      Segment
      Delay
    
  
  
  
      US Government Bonds
      Government Bonds
      End-of-day
    
    
      FINRA Trace
      BTDS: US Corporate Bonds
      Delayed 4h
    
    
      FINRA Trace
      144A Bonds
      Delayed 4h
    
    
  	  International Bonds
      International Bonds
      End-of-day

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `isin` | query | string | はい | ISIN. |
| `from` | query | integer | はい | UNIX timestamp. Interval initial value. |
| `to` | query | integer | はい | UNIX timestamp. Interval end value. |

**応答**: `BondCandles` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `c` | array of number | List of close prices for returned candles. |
| `t` | array of integer | List of timestamp for returned candles. |
| `s` | string | Status of the response. This field can either be ok or no_data. |

<details><summary>応答例</summary>

```json
{
  "c":[
    97.5,
    97.96875,
    98.78125,
  ],
  "s":"ok",
  "t":[
    1644883200,
    1644969600,
    1645056000,
  ]
}
```

</details>

---

### Bond Tick Data

`GET https://finnhub.io/api/v1/bond/tick`

区分: **Premium(有料プラン専用)**

Get trade-level data for bonds. The following datasets are supported:


  
    
      Exchange
      Segment
      Delay
    
  
  
    
      FINRA Trace
      BTDS: US Corporate Bonds
      Delayed 4h
    
    
      FINRA Trace
      144A Bonds
      Delayed 4h

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `isin` | query | string | はい | ISIN. |
| `date` | query | string | はい | Date: 2020-04-02. |
| `limit` | query | integer | はい | Limit number of ticks returned. Maximum value: 25000 |
| `skip` | query | integer | はい | Number of ticks to skip. Use this parameter to loop through the entire data. |
| `exchange` | query | string | はい | Currently support the following values: trace. |

**応答**: `BondTickData` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `skip` | integer | Number of ticks skipped. |
| `count` | integer | Number of ticks returned. If count limit, all data for that date has been returned. |
| `total` | integer | Total number of ticks for that date. |
| `v` | array of number | List of volume data. |
| `p` | array of number | List of price data. |
| `y` | array of number | List of yield data. |
| `t` | array of integer | List of timestamp in UNIX ms. |
| `si` | array of string | List of values showing the side (Buy/sell) of each trade. List of supported values: here |
| `cp` | array of string | List of values showing the counterparty of each trade. List of supported values: here |
| `rp` | array of string | List of values showing the reporting party of each trade. List of supported values: here |
| `ats` | array of string | ATS flag. Y or empty |
| `c` | array of array | List of trade conditions. A comprehensive list of trade conditions code can be found here |

<details><summary>応答例</summary>

```json
{
   "c":[[],[],[]],
   "count":3,
   "cp":[
      "3",
      "1",
      "1"
   ],
   "p":[
      100.592,
      100.492,
      100.234
   ],
   "si":[
      "2",
      "2",
      "2"
   ],
   "skip":6,
   "t":[
      1660929161000,
      1660929161000,
      1660929778000
   ],
   "total":211,
   "v":[
      3000,
      3000,
      50000
   ]
}
```

</details>

---

### Bond Yield Curve

`GET https://finnhub.io/api/v1/bond/yield-curve`

区分: **Premium(有料プラン専用)**

Get yield curve data for Treasury bonds.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `code` | query | string | はい | Bond's code. You can find the list of supported code here. |

**応答**: `BondYieldCurve` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of BondYieldCurveInfo | Array of data. |
| `code` | string | Bond's code |

<details><summary>応答例</summary>

```json
{
  "code": "10y",
  "data": [
    {
      "d": "2022-10-31",
      "v": 4.1
    },
    {
      "d": "2022-11-01",
      "v": 4.07
    }
  ]
}
```

</details>

---

## Economic

### Country Metadata

`GET https://finnhub.io/api/v1/country`

List all countries and metadata.

引数: なし

**応答**: `CountryMetadata` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `country` | string | Country name |
| `code2` | string | Alpha 2 code |
| `code3` | string | Alpha 3 code |
| `codeNo` | string | UN code |
| `currency` | string | Currency name |
| `currencyCode` | string | Currency code |
| `region` | string | Region |
| `subRegion` | string | Sub-Region |
| `rating` | string | Moody's credit risk rating. |
| `defaultSpread` | number | Default spread |
| `countryRiskPremium` | number | Country risk premium |
| `equityRiskPremium` | number | Equity risk premium |
| `logo` | string | Flag image |

<details><summary>応答例</summary>

```json
[
  {
    "code2": "US",
    "code3": "USA",
    "codeNo": "840",
    "country": "United States",
    "countryRiskPremium": 0,
    "currency": "US Dollar",
    "currencyCode": "USD",
    "defaultSpread": 0,
    "equityRiskPremium": 5,
    "rating": "Aaa",
    "region": "Americas",
    "subRegion": "Northern America",
    "logo": "https://static2.finnhub.io/file/publicdatany/finnhubimage/country_logo/us.svg"
  },
  {
    "code2": "GB",
    "code3": "GBR",
    "codeNo": "826",
    "country": "United Kingdom of Great Britain and Northern Ireland",
    "countryRiskPremium": 0.91,
    "currency": "Sterling",
    "currencyCode": "GBP",
    "defaultSpread": 0.64,
    "equityRiskPremium": 5.91,
    "rating": "Aa3",
    "region": "Europe",
    "subRegion": "Northern Europe",
    "logo": "https://static2.finnhub.io/file/publicdatany/finnhubimage/country_logo/gb.svg"
  }
]
```

</details>

---

### Economic Calendar

`GET https://finnhub.io/api/v1/calendar/economic`

区分: **Premium(有料プラン専用)**

Get recent and upcoming economic releases.

Historical events and surprises are available for Enterprise clients.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `from` | query | string | いいえ | From date YYYY-MM-DD. |
| `to` | query | string | いいえ | To date YYYY-MM-DD. |

**応答**: `EconomicCalendar` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `economicCalendar` | array of Economic event | Array of economic events. |

<details><summary>応答例</summary>

```json
{
  "economicCalendar": [
    {
      "actual": 8.4,
      "country": "AU",
      "estimate": 6.9,
      "event": "Australia - Current Account Balance",
      "impact": "low",
      "prev": 1,
      "time": "2020-06-02 01:30:00",
      "unit": "AUD"
    },
    {
      "actual": 0.5,
      "country": "AU",
      "estimate": 0.4,
      "event": "Australia- Net Exports",
      "impact": "low",
      "prev": -0.1,
      "time": "2020-06-02 01:30:00",
      "unit": "%"
    }
  ]
}
```

</details>

---

### Economic Code

`GET https://finnhub.io/api/v1/economic/code`

区分: **Premium(有料プラン専用)**

List codes of supported economic data.

引数: なし

**応答**: `EconomicCode` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `code` | string | Finnhub economic code used to get historical data |
| `country` | string | Country |
| `name` | string | Indicator name |
| `unit` | string | Unit |

<details><summary>応答例</summary>

```json
[
  {
    "code": "MA-USA-656880",
    "country": "USA",
    "name": "1-Day Repo Rate",
    "unit": "%"
  },
  {
    "code": "MA-USA-6667797870",
    "country": "USA",
    "name": "ISM Purchasing Managers Index",
    "unit": "unit"
  }
]
```

</details>

---

### Economic Data

`GET https://finnhub.io/api/v1/economic`

区分: **Premium(有料プラン専用)**

Get economic data.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `code` | query | string | はい | Economic code. |

**応答**: `EconomicData` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `data` | array of EconomicDataInfo | Array of economic data for requested code. |
| `code` | string | Finnhub economic code |

<details><summary>応答例</summary>

```json
{
  "code": "MA-USA-656880",
  "data": [
    {
      "date": "2020-05-31",
      "value": -2760
    },
    {
      "date": "2020-04-30",
      "value": -19557
    }
  ]
}
```

</details>

---

## Global Filings Search

### International Filings

`GET https://finnhub.io/api/v1/stock/international-filings`

区分: **Premium(有料プラン専用)**

List filings for international companies. Limit to 500 documents at a time. These are the documents we use to source our fundamental data. Enterprise clients who need access to the full filings for global markets should contact us for the access.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | いいえ | Symbol. Leave empty to list latest filings. |
| `country` | query | string | いいえ | Filter by country using country's 2-letter code. |
| `from` | query | string | いいえ | From date: 2023-01-15. |
| `to` | query | string | いいえ | To date: 2023-12-16. |

**応答**: `InternationalFiling` (array)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol. |
| `companyName` | string | Company name. |
| `filedDate` | string | Filed date %Y-%m-%d %H:%M:%S. |
| `category` | string | Category. |
| `title` | string | Document's title. |
| `description` | string | Document's description. |
| `url` | string | Url. |
| `language` | string | Language. |
| `country` | string | Country. |

<details><summary>応答例</summary>

```json
[
  {
    "symbol": "MINDTREE.NS",
    "companyName": "MindTree Limited",
    "filedDate": "2015-03-31 20:27:00",
    "category": "Resignation of Director",
    "title": "MindTree Limited has informed the Exchange that Mr. David B Yoffie has resigned as Independent Director of the company. The Board of Directors have accepted his resignation effective March 30, 2015.",
    "description": "",
    "url": "https://finnhub.io/international-filings?id=523566",
    "language": "en",
    "country": "IN"
  },
  {
    "symbol": "INOXLEISUR.NS",
    "companyName": "INOX Leisure Limited",
    "filedDate": "2015-03-31 20:24:00",
    "category": "Updates",
    "title": "INOX Leisure Limited has informed the Exchange regarding Commencement of Commercial Operations of Multiplex Cinema Theatre situated at E-wing, Osia Commercial Arcade, SGPDA Market Complex, Margao, Goa 403601.",
    "description": "",
    "url": "https://finnhub.io/international-filings?id=52152",
    "language": "en",
    "country": "IN"
  }
]
```

</details>

---

### Global Filings Search

`POST https://finnhub.io/api/v1/global-filings/search`

区分: **Premium(有料プラン専用)**

Search for best-matched filings across global companies' filings, transcripts and press releases. You can filter by anything from symbol, ISIN to form type, and document sources.

This endpoint will return a list of documents that match your search criteria. If you would like to get the excerpts as well, please set highlighted to true. Once you have the list of documents, you can get a list of excerpts and positions to highlight the document using the /search-in-filing endpoint

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `search` | body |  | いいえ | Search body |

**応答**: `SearchResponse` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `count` | integer | Total filing matched your search criteria. |
| `took` | integer | Time took to execute your search query on our server, value in ms. |
| `page` | integer | Current search page |
| `filings` | array of FilingResponse | Filing match your search criteria. |

<details><summary>応答例</summary>

```json
{
    "count": 8,
    "filings": [
        {
            "acceptanceDate": "2022-10-27 00:00:00",
            "amend": false,
            "documentCount": 1,
            "filedDate": "2022-10-27",
            "filerId": "3285503214",
            "filingId": "AAPL_1113753",
            "form": "TR/E",
            "name": "Apple Inc",
            "pageCount": 4,
            "reportPeriod": "",
            "source": "TR",
            "symbols": [
                "AAPL"
            ],
            "title": "AAPL - Earnings call Q4 2022",
            "url": "https://alpharesearch.io/platform/share?filingId=AAPL_1113753"
        }
        ...
    ],
    "page": 1,
    "took": 1986
}
```

</details>

---

### Search In Filing

`POST https://finnhub.io/api/v1/global-filings/search-in-filing`

区分: **Premium(有料プラン専用)**

Get a list of excerpts and highlight positions within a document using your query.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `search` | body |  | いいえ | Search body |

**応答**: `InFilingResponse` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `filingId` | string | Filing Id in Alpharesearch platform |
| `title` | string | Filing title |
| `filerId` | string | Id of the entity submitted the filing |
| `symbol` |  | List of symbol associate with this filing |
| `name` | string | Filer name |
| `acceptanceDate` | string | Date the filing is submitted. |
| `filedDate` | string | Date the filing is make available to the public |
| `reportDate` | string | Date as which the filing is reported |
| `form` | string | Filing Form |
| `amend` | boolean | Amendment |
| `source` | string | Filing Source |
| `pageCount` | integer | Estimate number of page when printing |
| `documentCount` | integer | Number of document in this filing |
| `documents` | array of DocumentResponse | Document for this filing. |

<details><summary>応答例</summary>

```json
{
  "acceptanceDate": "2022-10-27 00:00:00",
  "amend": false,
  "documentCount": 1,
  "documents": [
      {
          "documentId": "AAPL_1113753",
          "excerpts": [
              {
                  "content": "If you compare it to pre-<span class='search-highlight'>pandemic</span> kind of levels, that has not returned to pre <span class='search-highlight'>pandemic</span> levels by any means.\n",
                  "endOffset": 494,
                  "snippetId": "tran-46",
                  "startOffset": 385
              }
              ...
          ],
          "format": "html",
          "hits": 5,
          "title": "Transcript",
          "url": "https://alpharesearch.io/filing/transcript?documentId=AAPL_1113753"
      }
  ],
  "filedDate": "2022-10-27",
  "filerId": "4295905573",
  "filingId": "AAPL_1113753",
  "form": "TR/E",
  "name": "Apple Inc",
  "pageCount": 4,
  "reportPeriod": "",
  "source": "TR",
  "symbols": [
      "AAPL"
  ],
  "title": "AAPL - Earnings call Q4 2022",
  "url": "https://alpharesearch.io/platform/share?filingId=AAPL_1113753"
}
```

</details>

---

### Search Filter

`GET https://finnhub.io/api/v1/global-filings/filter`

区分: **Premium(有料プラン専用)**

Get available values for each filter in search body.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `field` | query | string | はい | Field to get available filters. Available filters are "countries", "exchanges", "exhibits", "forms", "gics", "naics", "caps", "acts", and "sort". |
| `source` | query | string | いいえ | Get available forms for each source. |

**応答**: `SearchFilter` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | string | Filter id, use with respective field in search query body. |
| `name` | string | Display name. |

<details><summary>応答例</summary>

```json
[
    {
        "id": "SEC",
        "name": "US SEC Edgar Filings"
    },
    {
        "id": "TR",
        "name": "Event Transcripts"
    },
    {
        "id": "SEDAR",
        "name": "Canada SEDAR Filings"
    },
    {
        "id": "CH",
        "name": "UK Companies House Filings"
    },
    {
        "id": "PR",
        "name": "Press Releases"
    },
    {
        "id": "RR",
        "name": "Research Reports"
    },
    {
        "id": "GF",
        "name": "Global Filings"
    }
]
```

</details>

---

### Download Filings

`GET https://finnhub.io/api/v1/global-filings/download`

区分: **Premium(有料プラン専用)**

Download filings using document ids.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `documentId` | query | string | はい | Document's id. Note that this is different from filingId as 1 filing can contain multiple documents. |

---

## Enterprise data

### Revenue Breakdown & KPI

`GET https://finnhub.io/api/v1/stock/revenue-breakdown2`

区分: **Premium(有料プラン専用)**

Get standardized revenue breakdown and KPIs data for 30,000+ global companies.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Symbol. |

**応答**: `RevenueBreakdown2` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Symbol |
| `currency` | string | currency |
| `data` | object | Revenue breakdown data. |

<details><summary>応答例</summary>

```json
{
  "currency": "USD",
  "data": {
    "annual": {
      "revenue_by_geography": [
        [
          {
            "data": [
              {
                "period": "2023-09-30",
                "value": 162560000000
              },
              {
                "period": "2024-09-28",
                "value": 167045000000
              }
            ],
            "label": "Americas"
          }
        ]
      ],
      "revenue_by_product": [
        [
          {
            "data": [
              {
                "period": "2023-09-30",
                "value": 200583000000
              },
              {
                "period": "2024-09-28",
                "value": 201183000000
              }
            ],
            "label": "iPhone"
          }
        ]
      ]
    },
    "quarterly": {
      "revenue_by_geography": [
        [
          {
            "data": [
              {
                "period": "2024-09-28",
                "value": 41664000000
              },
              {
                "period": "2024-12-28",
                "value": 52648000000
              }
            ],
            "label": "Americas"
          }
        ]
      ],
      "revenue_by_product": [
        [
          {
            "data": [
              {
                "period": "2024-09-28",
                "value": 46222000000
              },
              {
                "period": "2024-12-28",
                "value": 69138000000
              }
            ],
            "label": "iPhone"
          }
        ]
      ]
    }
  },
  "symbol": "AAPL"
}
```

</details>

---

### Newsroom

`GET https://finnhub.io/api/v1/stock/newsroom`

区分: **Premium(有料プラン専用)**

Get latest articles posted directly on the companies' newsroom and investor relations page. Newsroom API along with the Press Releases API provide a comprehensive text-based dataset directly from the company. We currently cover 1,250 US Companies with this dataset.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `symbol` | query | string | はい | Company symbol. |
| `from` | query | string | いいえ | From time: 2025-01-01. |
| `to` | query | string | いいえ | To time: 2026-01-05. |

**応答**: `Newsroom` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `symbol` | string | Company symbol. |
| `data` | array of NewsroomArticle | Array of articles. |

<details><summary>応答例</summary>

```json
{
  "data": [
    {
      "atDate": "2025-11-25 14:47:50",
      "fullText": "https://static2.finnhub.io/file/publicdatany/newsroom_new/5def2b7215a5cae2334ad221236da9978f9eb20e737bcccc9080307f7df068ad.html.gz",
      "title": "AI at Work: Which future of jobs are we building toward?",
      "url": "https://www.microsoft.com/en-us/worklab/ai-at-work-which-future-of-jobs-are-we-building-towards"
    },
    {
      "atDate": "2025-11-20 05:50:57",
      "fullText": "https://static2.finnhub.io/file/publicdatany/newsroom_new/36de40a2fc8c24227dd6fca77f7acc842bf4550ab7b51ab01a2fbecff250d2f2.html.gz",
      "title": "Why becoming an AI Frontier Firm is hard – Raffaella Sadun",
      "url": "https://www.microsoft.com/en-us/worklab/podcast/harvard-raffaella-sadun-on-why-its-so-hard-to-become-a-frontier-firm"
    }
  ],
  "symbol": "MSFT"
}
```

</details>

---

### AI Copilot

`POST https://finnhub.io/api/v1/ai-chat`

区分: **Premium(有料プラン専用)**

Chat with our AI copilot trained on the extensive Finnhub's global data. You can ask it any finance-related questions just like with other LLM models and receive results in texts and widgets.

**引数**

| 名前 | 位置 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `search` | body |  | いいえ | Search body |

**応答**: `AIChatResponse` (object)

| フィールド | 型 | 説明 |
|---|---|---|
| `chatId` | string | Chat ID. |
| `content` | string | Response text. |
| `querySummary` | string | Query summary |
| `relatedQueries` | array of object | Related queries. |
| `tickers` | array of object | List of tickers mentioned. |
| `sources` | array of object | Sources. |
| `widgets` | array of object | Widgets. |

<details><summary>応答例</summary>

```json
{
  "chatId": "uQElLdY7vZ",
  "content": "The current price of NVIDIA Corp (NVDA) is $124.92. The price has increased by 3.97% in the past 24 hours.\n",
  "querySummary": "NVDA Stock Price",
  "relatedQueries": [
    "What is NVDA's price target?",
    "Is NVDA a good stock to buy?",
    "What factors affect NVDA's price?"
  ],
  "sources": [
    {
      "link": "https://finnhub.io/docs/api",
      "shortURL": "finnhub.io",
      "snippet": "Comprehensive stock API for realtime market data, global company fundamentals, economic data, and alternative data...",
      "title": "Finnhub API Documentation",
      "websiteName": "Finnhub"
    }
  ],
  "tickers": [
    {
      "priceCurrency": "USD",
      "reportingCurrency": "USD",
      "ticker": "NVDA"
    }
  ],
  "widgets": [
    "https://finnhub.io/widget?ticker=NVDA&which=historical-price"
  ]
}
```

</details>

---
