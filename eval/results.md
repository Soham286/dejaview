# Evaluation

50 vague descriptions of known films; a hit means the right film is in the top k.

| Ranking | Top 1 | Top 3 | Top 10 | MRR | Median ms | Slowest ms |
|---|---|---|---|---|---|---|
| Keywords only (BM25) | 54% | 64% | 84% | 0.625 | 24 | 52 |
| Smart, meaning weight 0.0 | 54% | 64% | 84% | 0.625 | 31 | 55 |
| Smart, meaning weight 0.2 | 58% | 68% | 86% | 0.660 | 31 | 57 |
| Smart, meaning weight 0.4 | 60% | 72% | 90% | 0.690 | 30 | 57 |
| Smart, meaning weight 0.6 (default) | 66% | 72% | 90% | 0.720 | 30 | 52 |
| Smart, meaning weight 0.8 | 60% | 72% | 84% | 0.675 | 30 | 53 |
| Smart, meaning weight 1.0 | 30% | 50% | 68% | 0.420 | 30 | 52 |

## Misses at the default weight (0.6): not in the top 3

| Query | Keyword rank | Smart rank | Smart's top result |
|---|---|---|---|
| weatherman keeps waking up on the same morning over and over | 4 | 5 | The Weather Man (2005) |
| guy slowly figures out his whole town is a fake set and everyone around him is acting | >10 | >10 | Once (2007) |
| teenager accidentally goes back to the 1950s and has to make his parents fall in love | 9 | 6 | Why Do Fools Fall in Love (1998) |
| scientists bring extinct reptiles back for an amusement park and it all goes wrong | >10 | 5 | Alligator (1980) |
| grumpy old widower flies his house to south america and a boy scout is stuck on the porch | 7 | 7 | Grumpy Old Men (1993) |
| hacker finds out reality is a computer simulation run by machines | 7 | 4 | WarGames (1983) |
| boy hides a lost alien from the government and helps it get back to its spaceship | >10 | >10 | Kids vs. Aliens (2022) |
| banker wrongly jailed for murdering his wife secretly digs his way out of prison | 8 | 8 | The Banker (2020) |
| simple man from the south ends up at every big moment in american history | >10 | >10 | Trouble Man (1972) |
| killer robot from the future is sent back to murder a young waitress | 9 | 8 | Terminal (2018) |
| divorced dad dresses up as an old british nanny so he can see his kids | 1 | 5 | Nanny McPhee and the Big Bang (2010) |
| young prince blamed for his father's death runs away and later comes back to take the throne | >10 | >10 | Black Is King (None) |
| lonely insomniac veteran driving a cab at night in new york slowly turns violent | >10 | 4 | Dream for an Insomniac (1996) |
| family has to live in total silence because monsters hunt by sound | >10 | >10 | The Silence (2019) |
