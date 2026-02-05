# test runs

test artifacts (frames, labels, models, videos) are gitignored.
each test dir has its own `.env` with `OPENAI_API_KEY`.

## how to test

1. `cd tests/subway-surfers`
2. make sure `.env` has your `OPENAI_API_KEY`
3. open codex in that directory
4. paste the test prompt

## test: subway surfers

```
train a yolo model on this subway surfers gameplay: https://www.youtube.com/watch?v=i0M4ARe9v0Y

detect these classes: player, train, coins, powerup, obstacle, barrier

use 0.7 target accuracy
```
