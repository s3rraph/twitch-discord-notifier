This application monitors a game id on twitch and sends a notification in a discord channel via a web hook if someone starts streaming it

needed environment variables are 

DISCORD_WEBHOOK_URL  
TWITCH_SECRET  
TWITCH_CLIENT_ID  
GAME_NAME  

It will poll the game on twitch for new streams every 60 seconds  
It only looks at the top 100 streams  
It will not send another discord notification for a streamer until their stream has been off the monitored game for an hour  

built image available at
[https://hub.docker.com/r/s3rraph/twitch-discord-notifier](https://hub.docker.com/r/s3rraph/twitch-discord-notifier)

you have to register an app on twitch to get the client id and secret
https://dev.twitch.tv/console/apps

follow this to make your webhook
https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks

```
docker run -d \
        -e TWITCH_CLIENT_ID=xxxxyourtwitchclientidxxxx \
        -e TWITCH_SECRET=xxxxyourtwitchclientsecretxxxx \
        -e DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/..... \
        -e GAME_NAME="bump in the night" \
        --name twitch-discord-notifier \
        s3rraph/twitch-discord-notifier
```

