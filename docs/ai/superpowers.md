# Superpowers ([obra/superpowers](https://github.com/obra/superpowers))

## מה הריפו עושה?

**Superpowers** הוא לא ספריית קוד לאפליקציה — זה **מתודולוגיה + ספריית skills** לסוכני קוד: סט כללים ותהליכים שמנחים את הסוכן **לפני** שהוא כותב קוד, בזמן תכנון, בזמן יישום (כולל TDD), ובזמן סיום (ביקורת, merge).

לפי [ה-README הרשמי](https://github.com/obra/superpowers):

- הסוכן **לא קופץ מיד לקוד** — הוא מנסה להבין מה אתה באמת רוצה, מחדד spec, מציג עיצוב בחלקים קטנים.
- אחרי אישור העיצוב — **תוכנית יישום** מפורטת (משימות קטנות, נתיבי קבצים, אימות).
- מדגיש **TDD אמיתי** (אדום–ירוק–רפקטור), **YAGNI**, **DRY**.
- יכול להפעיל **subagent-driven development** — משימות עם ביקורת בין שלבים.
- ה-skills מופעלים **אוטומטית** לפי הקשר (לא רק “הצעות”).

### רשימת skills עיקריים (מתוך הריפו)

| תחום | דוגמאות |
|------|---------|
| **בדיקות** | `test-driven-development` |
| **דיבוג** | `systematic-debugging`, `verification-before-completion` |
| **שיתוף / תהליך** | `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `using-git-worktrees`, `requesting-code-review`, `finishing-a-development-branch` |
| **מטא** | `using-superpowers`, `writing-skills` |

### פילוסופיה (ברירת המחדל של המתודולוגיה)

- TDD — בדיקות לפני יישום.
- תהליך שיטתי במקום ניחושים.
- פישוט.
- הוכחה לפני “סיימתי”.

---

## איך משתמשים בזה ב-Cursor?

**ההתקנה היא דרך Cursor — לא קבצים בתיקיית `stocky`.**

1. פתח **Cursor Agent chat** (או שוק הפלאגינים).
2. הרץ אחת מהאפשרויות (לפי [התיעוד](https://github.com/obra/superpowers)):
   ```text
   /add-plugin superpowers
   ```
   או חפש **"superpowers"** ב-plugin marketplace והתקן.
3. **הפעל מחדש / סשן חדש** אם צריך.
4. **אימות:** בקש משהו שאמור להפעיל skill — למשל: *"עזור לי לתכנן את הפיצ’ר הזה"* או *"בוא נדבג את זה שיטתית"*.

### עדכון (Claude Code / סביבות שתומכות)

```text
/plugin update superpowers
```

ב-Cursor עקוב אחרי עדכוני הפלאגין בממשק.

---

## קשר ל-Stocky (חוקים מקומיים)

| | **Superpowers** | **חוקי Stocky** (`frontend/.cursorrules`, `CONTRIBUTING`, `.cursor/rules/`) |
|---|-----------------|----------------------------------------------------------------------------|
| **תפקיד** | איך לעבוד כסוכן: תכנון, TDD, תוכניות, worktrees, ביקורת | מה לבנות: סטאק, מבנה תיקיות, API, Git branches (`dev` וכו'), בדיקות הפרויקט |

- **לא מחליפים** את `frontend/.cursorrules` / `backend/.cursorrules` — אלה **אמת הפרויקט** (Next/FastAPI, נתיבים, פורמטים).
- אם Superpowers מציע תהליך (למשל worktree) שסותר את **זרימת ה-Git של Stocky** — עדיפות ל-**`CONTRIBUTING.md`** (ענפים `dev` / `test` / `main`).
- **TDD ו-testing** — משתלבים טוב עם `testing-rules.md` ודרישות הבדיקות ב-`.cursorrules`; אם יש סתירה, עדיפות לכללי הפרויקט וה-CI (כיסוי, פקודות `pytest` / `npm test`).

---

## קישורים

- ריפו: [github.com/obra/superpowers](https://github.com/obra/superpowers)
- בלוג מבוא (מקושר מהריפו): [Superpowers for Claude Code](https://blog.fsck.com/2025/10/09/superpowers/)
- Issues: [github.com/obra/superpowers/issues](https://github.com/obra/superpowers/issues)

### Claude Code (אופציונלי)

אם עובדים גם ב-Claude Code, אפשר דרך marketplace הרשמי:

```text
/plugin install superpowers@claude-plugins-official
```

או marketplace נפרד — ראה README בריפו.
