# Nexus-Group-PyAdmin
Nexus Group PyAdmin is a Roblox bot used for automating group actions. The actions it can handle include:
*  Removing posts from people who have left.
*  Removing posts that are in a blacklist, including regular expression entries.
*  Exiling users that are banned from the group.

To use all the included features, the bot must have the following:
*  Posts
    * View group wall
    * Delete group wall posts
*  Members
    * Kick lower-ranked members

It is recommended that only the needed permissions are enabled when they come up. If there is a data breach, the bot may become compromised and start removing members randomly.

# Dependencies
The bot currently requires the "requests" library. If you don't have requests, and are able to control the Python install, requests can be installed using the following:

```
pip install requests
```

If you aren't able to control your install, like in a shared hosting environment, you will need to down the appropriate requests folder from the [requests repository](https://github.com/requests/requests/releases).

# Setup
Setup of the bot requires an environment with a Python install. Python 2 and Python 3 both work as long as requests is included (see Dependencies). It is recommended to use a dedicated host, as opposed to a spare computer, to ensure it is always online. The bot is intended to be run using the command line with the following commands:

```
python LOCATION/GroupAdminBot.py LightScan
```
Goes through the entire ban list and the first MaxPostsPerRequest (see BotSettings.json).

```
python LOCATION/GroupAdminBot.py LightScan Loop
```
Runs the same behavior as LightScan, but performs if every LightScanLoopDelayInSeconds for LightScanLoopIterations times. This is intended for hosts that limit the intervals between Cron jobs. The repository assumes 5 minutes being the minimum.

```
python LOCATION/GroupAdminBot.py FullScan
```
Goes through the entire ban list and all of the group wall posts. Full scans should be run rarely (like once an hour) because of the number of requests created, and LightScan typically gets most of the important messages. Loop isn't implemented for this.

# BotSettings.json
BotSettings.json stores the settings for running the bot as a JSON file. The following parameters include:
*  MaxPostsPerRequest - the number of posts to grab in each request. It must be "10", "25", "50", or "100".
*  GlobalUserBanList - A list of the user ids of banned users. All bots use this list.
*  GlobalPostBlackList - A list of blacklisted phrases in the group wall. All bots use this list. Regular expressions can be used.
*  LightScanLoopDelayInSeconds - Delay between running the LightScan in a loop.
*  LightScanLoopIterations - Amount of times bot will loop in LightScan.
*  GroupBots - A list of bots handled by the host, including the following for each bot:
    * GroupId - Group id to handle.
    * GroupRank - Rank in the group as a number. This will prevent the bot sending requests to delete posts of higher ranks.
    * Username - Username of the bot. This is used for logging in.
    * Password - Password of the bot. This is used for logging in. A long, random password is recommended.
    * RemovePostsFromList - A bool that determines if the bot should remove blacklisted posts.
    * RemovePostsOnLeave - A bool that determines if the bot should remove posts from users that have left.
    * RemoveMembers - A bool that determines if the bot should exile banned users.
    * UserBanList - Same as GlobalUserBanList, but only applies to that group.
    * PostBlackList - Same as GlobalPostBlackList, but only applies to that group.
