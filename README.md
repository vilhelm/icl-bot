# Inhouse Discord Bot

This bot is developed for the InterCompany League discord channel to help support inhouse games.

## Development

We use Bazel through bazelisk for build management.  Hopefully all you need is any version of python.

```
./bazelisk build server:inhouse

./bazelisk build bot:inhouse_bot

./bazel-bin/server/inhouse --riot_api_key=$YOUR_TOURNAMENT_KEY
./bazel-bin/bot/inhouse_bot --discord_token=$DISCORD_BOT_TOKEN
```
