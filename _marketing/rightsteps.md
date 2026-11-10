# RightSteps marketing kit

Not published: GitHub Pages skips folders that start with `_`.

Every download link should go through `/get/?s=<source>`, so the HQ Overview shows clicks by source. Examples: `?s=tiktok`, `?s=reddit`, `?s=site`, `?s=howto`, `?s=bio`.

---

## 1. App Store listing (ASO)

The App Store search ranks the name, subtitle and keyword field. A word only needs to appear once across all three, so don't repeat words.

| Field | Limit | Copy | Length |
|---|---|---|---|
| Name | 30 | `RightSteps: Sharpen Your Mind` (keep, already live) | 29 |
| Subtitle | 30 | `Daily Path Puzzle & Brain Game` | 30 |
| Keywords | 100 | `logic,maze,route,snake,line,draw,number,math,multiply,score,leaderboard,zen,relax,iq,strategy,grid` | 98 |
| Promotional text | 170 | `Today's Daily board is live. One route, one shot: stack your greens, save your multipliers for last, and see where you rank in the world.` | 137 |

The subtitle could also be `One-Finger Daily Logic Puzzle` (29). Test it against the main one for 4 weeks each and keep whichever gets more impressions in App Store Connect → App Analytics → Sources → App Store Search.

**Description (first 3 lines are the only ones most people read):**

> One finger. One route. One shot to bank the biggest number.
>
> Drag from the bottom-left corner to the flag. Every square is +1. Green squares add, orange squares multiply, red squares hurt, and the order you take them changes everything. Snake through the whole board, but never cross your own path.
>
> • DAILY: one board for the whole world, every day, with a live ranking and your percentile
> • CAMPAIGN: worlds of hand-built boards with star targets
> • ZEN: endless boards, no lives, no pressure
> • Plays in seconds, takes a lifetime to master
>
> Free to play. Optional Premium removes ads and adds hints on every level.

**Screenshots, in this order.** The first two show in search results, so they carry the listing:
1. A board mid-swipe with a big multiplied score. Caption: "One route. Biggest number wins."
2. Green, orange and red squares with arrows. Caption: "Add. Multiply. Avoid."
3. The Daily card with world rank and percentile. Caption: "Same board for the whole world."
4. A board where the trail nearly traps itself. Caption: "Never cross your own path."
5. Campaign world map. Caption: "Worlds of hand-built puzzles."
6. Zen. Caption: "Or just relax."

**Ratings:** ask for a review right after a personal best on the Daily board, using `SKStoreReviewController`. That's the moment players are happiest. Never ask after a lost life.

---

## 2. TikTok / Reels / Shorts

The format that works for puzzle games is a screen recording with a challenge on screen and the solve at the end. Post daily: the Daily board gives you a new video every day for free.

**Recurring series**
- **"Today's Daily: can you beat X?"** Show the board, pause 2 seconds before the first move, then play your best route. End card: "Rank yourself: link in bio." This one is repeatable forever.
- **"Wrong route vs right route."** Same board, split screen: the obvious route scores 40, the smart one scores 400.
- **"Don't trap yourself."** A run that walks into a dead end with one square left. Fails get shared more than wins.

**20 hooks** (put the first line on screen in the first second)
1. "The shortest route scores the least. Watch."
2. "99% of people grab the multiplier too early."
3. "This board has one route that scores over 1,000."
4. "Rate my route 1-10."
5. "I was one square from a perfect run."
6. "Pause and find the best route before I do."
7. "Same board, same squares, 10× the score."
8. "Order matters: add first, multiply last."
9. "The red square is worth taking. Here's why."
10. "Today's Daily board is evil."
11. "My mom beat my score on this one."
12. "Comment your score on today's board."
13. "Rule 1: never cross your own path. Rule 2: see rule 1."
14. "POV: you snake the whole board and the flag is blocked."
15. "Is this the hardest board in World 1?"
16. "I solo-built this game. Here's the level that broke testers."
17. "One finger. One route. One shot."
18. "Sharpen your mind in 30 seconds."
19. "Zen mode is the most relaxing thing on my phone."
20. "Stitch this with a better route."

**Build-in-public angle** (works on TikTok, X and Reddit): "I'm a solo dev, here is how many people played today's Daily." The HQ dashboard numbers make this easy.

Bio link: `https://gross1234.github.io/rightsteps/get/?s=tiktok` (and `?s=instagram`, `?s=youtube`).

---

## 3. Launch channels (free)

| Where | What to post | Link tag |
|---|---|---|
| r/iosgaming | "I made a one-finger path puzzle with a shared daily board". Post a GIF plus a short dev story. Read the self-promo rules first. | `?s=reddit` |
| r/puzzles, r/puzzlevideogames | Post a single board as a puzzle ("what's the max score?"). Put the game link in a comment, not the title. | `?s=reddit` |
| r/WebGames / r/gamedev "Screenshot Saturday" | A GIF of the multiplier moment. | `?s=reddit` |
| TouchArcade forums ("Upcoming iOS games" or "New releases") | A thread with screenshots and the link. Their writers read the forums. | `?s=toucharcade` |
| Press: Pocket Gamer, TouchArcade, 148Apps, AppAdvice | A short email with a 30-second video, 3 screenshots, and the hook "a Wordle-style daily board for path puzzles". | `?s=press` |
| Product Hunt | Launch on a Tuesday-Thursday. | `?s=producthunt` |
| Apple "Get Featured" form (App Store Connect → Apps → Featuring) | Submit 3-4 weeks before any big update, such as a new world. | n/a |

---

## 4. Website search and AI answers

Done in this repo:
- `index.html`: rewritten so search engines and ChatGPT / Perplexity / Google AI can quote it. It has a one-sentence answer, the rules, the modes, a FAQ, and `VideoGame` + `MobileApplication` + `FAQPage` structured data. It also has a Smart App Banner, so Safari shows an "Open / Get" bar on iPhone.
- `how-to-play/`: rules and strategy tips with `HowTo` + `FAQPage` structured data. It's built to answer searches like "how to play RightSteps" and "RightSteps strategy".
- `sitemap.xml` and `llms.txt`.

Next steps:
1. **Get a domain** (e.g. `rightsteps.app`) and point GitHub Pages at it. Search engines only read `robots.txt` and `llms.txt` at the root of a domain. On `gross1234.github.io/rightsteps/` they sit in a subfolder and get ignored. Once the domain is set, update the `canonical` URLs and `sitemap.xml`.
2. Add the site to **Google Search Console** and **Bing Webmaster Tools** (Bing feeds ChatGPT search). Submit `sitemap.xml`.
3. AI assistants recommend games that other sites mention. A Reddit thread, a TouchArcade post or a "best daily puzzle games" listicle mentioning RightSteps counts for more than anything on your own site.
