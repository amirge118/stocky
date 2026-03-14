# PR Review – Stocky Improvements

**תאריך:** 14 מרץ 2026  
**סטטוס Build:** ✅ עובר  
**סטטוס Tests:** ⚠️ 10 טסטים נכשלים (בעיקר StockTable, BulkActionsBar, useWatchlist)

---

## 1. Product Manager Review

### ערך עסקי
- **Watchlist** – תיקון באג קריטי: הוספה ל-watchlist עובדת (כוכב + bulk actions)
- **ממשק מניה** – פריסה משופרת: חדשות מימין, נתונים קומפקטיים
- **גרפים** – ציר זמן בתחתית לשיפור הקריאות
- **תכונות נוספות** – Alerts, Compare, WebSocket, Docker, CI/CD

### חוויית משתמש
- פריסת עמוד מניה ברורה יותר
- תיאור עם "Read more" נוח יותר
- ציר זמן בגרפים מקל על הבנת טווח הזמן

### המלצות
- לוודא שכל הטסטים עוברים לפני merge
- לשקול הוספת E2E לזרימת Watchlist

---

## 2. Developer Review

### איכות קוד – תוקן
- ✅ משתנים לא בשימוש הוסרו (isPositive, total, toggleWatchlist, useToast)
- ✅ Props לא בשימוש סומנו (_onBulkDelete)
- ✅ Import מיותר (Button) הוסר מ-alert-dialog
- ✅ InputProps הוחלף מ-interface ל-type
- ✅ useRef קיבל ערך התחלתי (StockSearchFilter, useStockPrices)
- ✅ AgentReportView – תיקון טיפוסים ל-unknown (ternary + String())
- ✅ StockComparisonChart – formatter תומך ב-undefined

### סטנדרטים
- WatchlistProvider – Context pattern נכון
- StockKeyStats – STATS array עם פונקציות format
- StockChart – ציר זמן ב-CandlestickChart

### אזהרות שנותרו (לא חוסמות build)
- `app/stocks/compare/page.tsx:27` – useEffect dependency: symbols
- `lib/hooks/useStockPrices.ts:59` – useCallback dependencies

### המלצות לפיתוח
1. לתקן את ה-hook dependencies ב-compare page ו-useStockPrices
2. לעדכן טסטי StockTable/BulkActionsBar לעבודה עם WatchlistProvider
3. להוסיף `frontend/lib/providers/` ל-git (כרגע untracked)

---

## 3. Quality Engineer Review

### כיסוי טסטים
- useWatchlist – 10 טסטים, כולם עוברים (אחרי mock ל-console.error)
- StockTable – נכשל: `getAllByRole("button", { name: "" })` – כנראה aria-label שונה
- BulkActionsBar – נכשל: כנראה צריך WatchlistProvider wrapper

### Edge Cases
- WatchlistProvider – טיפול ב-invalid JSON ב-localStorage
- CandlestickChart – points.length === 1 (uniqueIndices)

### סיכון רגרסיה
- Watchlist – שינוי מ-state מקומי ל-Context; יש לוודא שכל הדפים עטופים ב-Providers

### המלצות
1. לעטוף טסטים שמשתמשים ב-useWatchlist ב-WatchlistProvider
2. לעדכן StockTable test – כפתור הכוכב עם aria-label מתאים
3. להריץ `npm test` ולוודא שכל הטסטים עוברים

---

## 4. Security Engineer Review

### סיכונים
- **localStorage** – Watchlist נשמר ב-localStorage; אין מידע רגיש
- **WebSocket** – חיבור ל-backend; אין אימות נוסף מעבר ל-CORS
- **External links** – אתר החברה, חדשות – יש `rel="noopener noreferrer"` ✅

### המלצות
- אין סיכוני אבטחה משמעותיים בשינויים הנוכחיים

---

## 5. DevOps Review

### CI/CD
- `.github/` – קובץ workflow חדש (untracked)
- `.pre-commit-config.yaml` – hooks חדשים (untracked)
- `docker-compose.yml` – קובץ חדש (untracked)

### Build
- ✅ `npm run build` עובר
- ✅ אין שגיאות TypeScript
- ⚠️ 3 אזהרות ESLint (react-hooks/exhaustive-deps)

### המלצות
1. לוודא ש-CI מריץ את ה-pre-commit hooks
2. להריץ `docker-compose up` ולוודא שהשירותים עולים

---

## 6. UI/UX Designer Review

### עקביות
- עיצוב zinc-dark נשמר
- תגיות, כפתורים, גרפים – סגנון אחיד

### נגישות
- כפתורי watchlist עם aria-label
- קישורים חיצוניים עם rel="noopener noreferrer"

### רספונסיביות
- `grid-cols-1 lg:grid-cols-[1fr_300px]` – עמוד מניה
- StockKeyStats – `grid-cols-2 sm:grid-cols-4`

### המלצות
- אין בעיות תצוגה משמעותיות

---

## סיכום – פעולות לפני Push

### חובה (חוסם)
- [x] Build עובר
- [ ] לתקן את הטסטים הנכשלים (StockTable, BulkActionsBar, useWatchlist)

### מומלץ
- [ ] לתקן React Hook dependencies (compare, useStockPrices)
- [ ] להוסיף קבצים חדשים ל-git: `frontend/lib/providers/`, `.github/`, `docker-compose.yml`

### אופציונלי
- [ ] E2E tests ל-Watchlist flow
- [ ] תיעוד שינויים ב-CHANGELOG

---

## קבצים שנערכו (תיקוני PR)

| קובץ | שינוי |
|------|------|
| `app/stocks/[symbol]/page.tsx` | הסרת isPositive לא בשימוש |
| `app/stocks/page.tsx` | הסרת total לא בשימוש |
| `BulkActionsBar.tsx` | הסרת toggleWatchlist לא בשימוש |
| `StockTable.tsx` | הסרת useToast, _onBulkDelete, someSelected |
| `alert-dialog.tsx` | הסרת import Button |
| `input.tsx` | InputProps → type |
| `AgentReportView.tsx` | תיקון unknown → ReactNode |
| `StockComparisonChart.tsx` | formatter תומך undefined |
| `StockSearchFilter.tsx` | useRef עם ערך התחלתי |
| `useStockPrices.ts` | useRef עם ערך התחלתי |
| `useWatchlist.test.tsx` | mock ל-console.error |
