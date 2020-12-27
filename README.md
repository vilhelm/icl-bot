# Inhouse Discord Bot

This bot is developed for the InterCompany League discord channel to help support inhouse games.

## Development

We use Bazel for build management.  [Installation on Linux](https://docs.bazel.build/versions/master/install-ubuntu.html)

```
bazel build -c opt server:inhouse

bazel build -c opt bot:inhouse_bot

./bazel-bin/server/inhouse --riot_api_key=$YOUR_TOURNAMENT_KEY
./bazel-bin/bot/inhouse_bot --discord_token=$DISCORD_BOT_TOKEN
```
