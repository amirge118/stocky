# UI/UX Pro Max (Cursor skill)

מקור: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) — הותקן בפרויקט עם `npx uipro-cli init --ai cursor`.

## מה זה עושה?

Skill שמוסיף **מודיעין עיצובי** לסוכן ב-Cursor:

- מאגר נתונים (CSV) עם סגנונות, פלטות צבעים, טיפוגרפיה, הנחיות UX, דפוסי landing, ועוד.
- סקריפט Python — `search.py` — שמריץ חיפושים ו־**Design System** מותאם לפי מילות מפתח (תעשייה, סגנון, מוצר).
- הנחיות כלליות (אייקונים, `cursor-pointer`, ניגודיות, `prefers-reduced-motion`).

הסוכן נטען עם **`.cursor/skills/ui-ux-pro-max/SKILL.md`** — כשמבקשים עבודת UI/UX (עיצוב, שיפור מסך, landing וכו'), Cursor יכול לעקוב אחרי ה-workflow שם (כולל הרצת הפקודות).

## מה התהליך הטכני?

1. **התקנה (בוצעה פעם אחת):**  
   `npx uipro-cli init --ai cursor`  
   יוצר את התיקייה **`.cursor/skills/ui-ux-pro-max/`** (סקריפטים + נתונים + `SKILL.md`).

2. **הפעלה:** אחרי התקנה — **Restart ל-Cursor** (או לחלון הסוכן) כדי שה-skill ייטען.

3. **שימוש בשיחה:** לדוגמה:  
   *"שפר את כרטיס המניה במסך הפורטפוליו"* או *"בנה landing ל-SaaS פיננסי"* — הסוכן אמור לשלב את ה-skill.

4. **שימוש ידני (Design System):** מהשורש של הריפו, הנתיב הנכון לסקריפט הוא:

```bash
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py "<תיאור מוצר / תעשייה / מילות מפתח>" --design-system -p "Stocky" -f markdown
```

אופציונלי: `--persist` ליצירת `design-system/MASTER.md` (ראו `SKILL.md`).

5. **Stack:** עבור Stocky מומלץ להוסיף חיפושים עם `--stack nextjs` או `--stack shadcn` כשצריך הנחיות יישום ספציפיות.

## האם זה מחליף את חוקי Stocky?

**לא.** זה **משלים**, לא מחליף:

| מקור | תפקיד |
|------|--------|
| **`frontend/.cursorrules`** | אמת לפרויקט: מבנה תיקיות, React Query, `@/lib/api/client`, Radix/Shadcn, **טוקני zinc dark**, פורמט מספרים/מטבע, בדיקות |
| **UI/UX Pro Max** | השראה גלובלית: פלטות, טיפוגרפיה, דפוסי עמוד, UX כללי, צ'קליסט לפני מסירה |

**כלל ברירת מחדל לפיתוח ב-Stocky:** אם יש סתירה בין המלצת ה-skill (צבעים/פונטים חדשים) לבין מה שכתוב ב-`frontend/.cursorrules` — **עדיפות לחוקי Stocky** כדי לשמור על מראה אחיד באפליקציה. אפשר לקחת מה-skill רק **רעיונות** (מרווחים, היררכיה, micro-interactions, a11y) וליישם אותם ב-Tailwind + הטוקנים הקיימים.

## עדכון ה-skill בעתיד

```bash
npm install -g uipro-cli   # או npx
uipro update
```

או התקנה מחדש: `npx uipro-cli init --ai cursor` (עוקב אחרי התבניות העדכניות של ה-CLI).
