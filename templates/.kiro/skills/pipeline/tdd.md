# TDD 規則(給 code stage)

先寫會失敗的測試,再寫剛好能通過的程式,一次一小步。本檔說明好測試的樣子、測試放哪裡、不要踩的坑與迴圈規則。實作前與實作中都要對照。
改寫自 mattpocock/skills 的 tdd(授權見 `NOTICE.md`)。範例用 TypeScript,其他語言照意思寫。
測試名稱與程式命名照 `docs/glossary.md` 的「程式名稱」欄。

## 好測試

測試透過公開介面驗證行為,不驗證實作細節。程式內部可以全部重寫,測試不該壞。好測試讀起來像規格:「使用者可以用有效購物車結帳」一看就知道有什麼能力,重構後仍然成立。

```typescript
// 好:驗證可觀察的行為
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

特徵:

- 測呼叫端在乎的行為
- 只用公開介面
- 內部重構後仍通過
- 名稱描述「做什麼」,不描述「怎麼做」
- 每個測試一個邏輯斷言

## 驗證入口:測試放哪裡

驗證入口是你觀察行為的公開邊界,不用伸進內部。**只在計畫檔第 5 節列的入口寫測試。** 需要新入口時,回報給 orchestrator,不要自己加。

## 不要踩的坑

**綁實作**:mock 自己的內部模組、測私有方法、繞過介面從旁驗證(例如直接查資料庫)。徵兆:行為沒變,重構後測試卻壞了。

```typescript
// 壞:繞過介面直接查資料庫
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// 好:透過介面驗證
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

**同義反覆**:期望值照程式的算法重算,測試必然通過,永遠不會跟程式意見不同。期望值要來自獨立來源:寫死的值、計畫檔的例子。

```typescript
// 壞:期望值用跟程式一樣的方式算出來
test("calculateTotal sums line items", () => {
  const items = [{ price: 10 }, { price: 5 }];
  const expected = items.reduce((sum, i) => sum + i.price, 0);
  expect(calculateTotal(items)).toBe(expected);
});

// 好:期望值是獨立的已知值
test("calculateTotal sums line items", () => {
  expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
});
```

**水平切片**:先寫完所有測試,再寫所有實作。批次寫的測試驗證的是想像出來的行為,只測到事物的形狀,對真實改動不敏感,而且在理解實作之前就定死測試結構。改成垂直切片:一個測試、一個實作、再下一輪,每個測試都吸收上一輪學到的東西。

## 何時 mock

只在系統邊界 mock:

- 外部 API(付款、寄信等)
- 資料庫(有時;能用測試庫就用測試庫)
- 時間與隨機
- 檔案系統(有時)

不 mock:自己的類別與模組、內部協作者、自己能控制的東西。

邊界要設計成容易 mock:

- 用依賴注入。把外部依賴傳進來,不在函式內部建立。

```typescript
// 容易 mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// 難 mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

- 每個外部操作一個具體函式(`getUser`、`createOrder`),不用一個帶條件分支的通用 `fetch(endpoint, options)`。這樣每個 mock 只回一種形狀,測試設定不必寫條件,也看得出測試用到哪些端點。

## 迴圈規則

- **先紅後綠。** 先寫會失敗的測試,並實際執行確認它失敗,再寫剛好能通過的程式。不預做未來需求,不加投機功能。
- **一次一條切片。** 一個驗證入口、一個測試、一個最小實作。
- **重構不在迴圈內。** 重構留給 review 階段。

## 完成標準

- 計畫檔每條驗收條件都有對應測試。
- 全部測試通過。
- 型別檢查與 lint(repo 有的話)通過。
- 遵守檔案行數上限。
- repo 沒有測試框架時,不要自己新增依賴,回報給 orchestrator。
