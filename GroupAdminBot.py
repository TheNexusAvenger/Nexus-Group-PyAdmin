"""
TheNexusAvenger
Automated bot for deleting posts by users who have left.
Also handles bans and duplicate posts.

Roblox HTTP(S) Documentation:
https://groups.roblox.com/docs
https://auth.roblox.com/docs
"""

import re
import requests
import sys
import time
import threading
import json
import os,ntpath

BOT_SETTINGS_JSON_LOCATION = ntpath.split(os.path.realpath(__file__))[0] + "/BotSettings.json"

MAX_POSTS_PER_REQUEST = "100"
GLOBAL_USER_BAN_LIST = []
GLOBAL_POST_BLACK_LIST = []
GROUP_BOTS = []

LIGHT_SCAN_LOOP_DELAY_IN_SECONDS = 30
LIGHT_SCAN_LOOP_ITERATIONS = 10



# Creates a bot class.
class RobloxBot(object):
	# Initializes the class.
	def __init__(self):
		# Creates a session.
		self.session = requests.session()

		# Create the headers.
		headers = {"User-Agent":"Roblox/WinInet"}
		self.session.headers.update(headers)

		# Set the place holder rules.
		self.botGroupRank = 0
		self.removePostsFromList = False
		self.removePostsOnLeave = False
		self.removeMembers = False
		self.removeDuplicatePostsBySameUser = False
		self.postBlackList = []
		self.userBanList = []

		# Store base last post information.
		self.lastPostText = ""
		self.lastPostAuthorId = 0

	# Adds a site header to the list of headers.
	def addSiteKeyToHeaders(self,headers,url):
		response = self.session.get("https://www.roblox.com/",timeout=10)
		csrf_token = response.text.split("Roblox.XsrfToken.setToken('")[-1].split("');")[0]

		# Add the headers.
		headers["X-CSRF-TOKEN"] = csrf_token
		headers["Referer"]  = url

		# Return the headers.
		return headers

	# Returns if a posts should be deleted.
	def shouldPostBeDeleted(self,postData):
		# Return true if the poster is banned.
		if postData["poster"] is None:
			return True
		
		posterRank = int(postData["poster"]["role"]["rank"])
		posterId = int(postData["poster"]["role"]["id"])
		postBody = postData["body"]

		if posterRank == 0:
			# Handle the poster not being in the group.
			if self.removePostsOnLeave:
				return True
		elif posterRank < self.botGroupRank:
			# Handle blacklist posts.
			if self.removePostsFromList:
				for pattern in GLOBAL_POST_BLACK_LIST:
					if re.search(pattern,postBody) != None:
						return True

			# Handle duplicate posts.
			if self.removeDuplicatePostsBySameUser:
				if self.lastPostAuthorId == posterId and self.lastPostText == postBody:
					return True

				self.lastPostText = postBody
				self.lastPostAuthorId = posterId

		# Return false (don't delete).
		return False

	# Signs the bot in and returns if it was successful.
	def SignIn(self,username,password):
		# Assemble the arguments.
		arguments = {
			"username": username,
			"password": password,
		}

		# Send the request and return if it was successful.
		response = self.session.post('https://api.roblox.com/v2/login',headers=self.addSiteKeyToHeaders({},"https://www.roblox.com/"),data=arguments)
		return response.status_code < 400

	# Sets the bot rules for deleting posts.
	def SetPostDeletionRules(self,botGroupRank,removePostsFromList,removePostsOnLeave,postBlackList,removeDuplicatePostsBySameUser):
		self.botGroupRank = botGroupRank
		self.removePostsFromList = removePostsFromList
		self.removePostsOnLeave = removePostsOnLeave
		self.postBlackList = postBlackList
		self.removeDuplicatePostsBySameUser = removeDuplicatePostsBySameUser

		for pattern in GLOBAL_POST_BLACK_LIST:
			if not pattern in self.postBlackList:
				self.postBlackList.append(pattern)

	# Sets the bot rules for exiling users.
	def SetExileRules(self,botGroupRank,removeMembers,userBanList):
		self.botGroupRank = botGroupRank
		self.removeMembers = removeMembers
		self.userBanList = userBanList

		for userId in GLOBAL_USER_BAN_LIST:
			if not userId in self.userBanList:
				self.userBanList.append(userId)

	# Returns 100 posts. Accepts a cursor to move pages.
	def GetPosts(self,groupId,cursor = None):
		# Create the base URL.
		requestUrl = "https://groups.roblox.com/v2/groups/" + str(groupId) + "/wall/posts?sortOrder=Desc&limit=" + MAX_POSTS_PER_REQUEST
		headers = self.addSiteKeyToHeaders({},"https://www.roblox.com/My/Groups.aspx?gid=" + str(groupId))
		if cursor is not None:
			requestUrl += "&cursor=" + cursor

		# Send the request.
		response = self.session.get(requestUrl,headers=headers)

		# Return the response.
		return response.json()

	# Deletes a group wall post. Returns if it was successful.
	def DeletePost(self,groupId,postId):
		requestUrl = "https://groups.roblox.com/v1/groups/" + str(groupId) + "/wall/posts/" + str(postId)
		headers = self.addSiteKeyToHeaders({},"https://www.roblox.com/My/Groups.aspx?gid=" + str(groupId))

		# Send the request and return if it was successful.
		response = self.session.delete(requestUrl,headers=headers)

		# Display an error (if any) and return the status.
		if response.status_code < 400:
			return True
		else:
			print("An error occurred (with RobloxBot.DeletePost): " + response.text)
			return False

	# Exiles a user. Assumes the user is in the group.
	def ExileUser(self,groupId,userId):
		requestUrl = "https://groups.roblox.com/v1/groups/"  + str(groupId) + "/users/" + str(userId)
		headers = self.addSiteKeyToHeaders({}, "https://www.roblox.com/My/Groups.aspx?gid=" + str(groupId))

		# Send the request and return if it was successful.
		response = self.session.delete(requestUrl,headers=headers)

		# Display an error (if any) and return the status.
		if response.status_code < 400:
			return True
		else:
			print("An error occurred (with RobloxBot.DeletePost): " + response.text)
			return False

	# Gets the user's rank in the group.
	def GetUserRank(self,groupId,userId):
		requestUrl = "https://www.roblox.com/Game/LuaWebService/HandleSocialRequest.ashx?method=GetGroupRank&playerid=" + str(userId) + "&groupid=" + str(groupId)

		# Send the request.
		response = self.session.get(requestUrl) #, headers=headers)

		# Display an error (if any) and return the role
		if response.status_code < 400:
			return int(response.text[22:-8])
		else:
			print("An error occurred (with RobloxBot.DeletePost): " + response.text)
			return 0

	# Exiles banned users from the group.
	def ExileUsers(self,groupId):
		# Return if exiling is disabled.
		if not self.removeMembers:
			return

		# Go through the banned users and remove them if they are in the group.
		for userId in self.userBanList:
			userRank = self.GetUserRank(groupId,userId)
			if userRank > 0 and userRank < self.botGroupRank:
				self.ExileUser(groupId,userId)

	# Deletes group wall posts for the current cursor.
	def DeletePosts(self,groupId,runNextPages = False,cursor = None):
		# Get the posts.
		posts = self.GetPosts(groupId,cursor)

		if "data" in posts:
			# Iterate through the posts.
			for post in posts["data"]:
				if self.shouldPostBeDeleted(post) == True:
					postId = post["id"]
					self.DeletePost(groupId,postId)
		else:
			raise Exception("An error occurred (with RobloxBot.DeletePosts): " + str(posts))

		# Move to the next posts (if needed).
		nextCursor = posts["nextPageCursor"]
		if nextCursor is not None and runNextPages == True:
			self.DeletePosts(groupId,True,nextCursor)



# Creates a bot and go through the first MAX_POSTS_PER_REQUEST posts, and exiles users.
def RunLightScanForGroup(groupData):
	# Get the bot info.
	groupId = groupData["GroupId"]
	botGroupRank = groupData["GroupRank"]
	botUsername = groupData["Username"]
	botPassword = groupData["Password"]
	removePostsFromList = groupData["RemovePostsFromList"]
	removePostsOnLeave = groupData["RemovePostsOnLeave"]
	removeDuplicatePostsBySameUser = ("RemoveDuplicatePostsBySameUser" in groupData and groupData["RemoveDuplicatePostsBySameUser"] or False)
	removeMembers = groupData["RemoveMembers"]
	userBanList = groupData["UserBanList"]
	postBlackList = groupData["PostBlackList"]

	# Handle the bot actions.
	if removePostsFromList or removePostsOnLeave or removeMembers:
		bot = RobloxBot()
		bot.SignIn(botUsername,botPassword)
		bot.SetPostDeletionRules(botGroupRank,removePostsFromList,removePostsOnLeave,postBlackList,removeDuplicatePostsBySameUser)
		bot.SetExileRules(botGroupRank,removeMembers,userBanList)
		bot.ExileUsers(groupId)
		bot.DeletePosts(groupId,False)

# Creates a bot and go through all the posts, and exiles users.
def RunFullScanForGroup(groupData):
	# Get the bot info.
	groupId = groupData["GroupId"]
	botGroupRank = groupData["GroupRank"]
	botUsername = groupData["Username"]
	botPassword = groupData["Password"]
	removePostsFromList = groupData["RemovePostsFromList"]
	removePostsOnLeave = groupData["RemovePostsOnLeave"]
	removeMembers = groupData["RemoveMembers"]
	userBanList = groupData["UserBanList"]
	postBlackList = groupData["PostBlackList"]

	# Handle the bot actions.
	if removePostsFromList or removePostsOnLeave or removeMembers:
		bot = RobloxBot()
		bot.SignIn(botUsername,botPassword)
		bot.SetPostDeletionRules(botGroupRank,removePostsFromList,removePostsOnLeave,postBlackList)
		bot.SetExileRules(botGroupRank,removeMembers,userBanList)
		bot.ExileUsers(groupId)
		bot.DeletePosts(groupId,True)

# Runs a light scan on all groups.
def RunLightScan():
	for groupData in GROUP_BOTS:
		RunLightScanForGroup(groupData)

# Runs a full scan on all groups.
def RunFullScan():
	for groupData in GROUP_BOTS:
		RunFullScanForGroup(groupData)

# Calls a function and prints error checking.
def pcall(function,*parameters):
	try:
		function(*parameters)
	except Exception as e:
		print("An error occurred: " + str(e))

# Calls a function using pcall in a thread.
def threadedPCall(function,*parameters):
	threading.Thread(target=function,args=parameters).start()

# Loads the current settings.
def LoadJSONSettings(settingsFileLocation):
	with open(settingsFileLocation) as file:
		jsonData = json.load(file)

		# Set the globals.
		global MAX_POSTS_PER_REQUEST,GLOBAL_USER_BAN_LIST
		global GLOBAL_POST_BLACK_LIST,GROUP_BOTS
		global LIGHT_SCAN_LOOP_DELAY_IN_SECONDS,LIGHT_SCAN_LOOP_ITERATIONS

		MAX_POSTS_PER_REQUEST = jsonData["MaxPostsPerRequest"]
		GLOBAL_USER_BAN_LIST = jsonData["GlobalUserBanList"]
		GLOBAL_POST_BLACK_LIST = jsonData["GlobalPostBlackList"]
		GROUP_BOTS = jsonData["GroupBots"]
		LIGHT_SCAN_LOOP_DELAY_IN_SECONDS = jsonData["LightScanLoopDelayInSeconds"]
		LIGHT_SCAN_LOOP_ITERATIONS = jsonData["LightScanLoopIterations"]



# Runs the script if it is directly called.
if __name__ == '__main__':
	# Loads the JSON settings.
	LoadJSONSettings(BOT_SETTINGS_JSON_LOCATION)

	# Run the script based on command line arguments.
	if "FullScan" in sys.argv:
		threadedPCall(RunFullScan)
	elif "LightScan" in sys.argv:
		if "Loop" in sys.argv:
			# Run the loop 10 times.
			for _ in range(0,LIGHT_SCAN_LOOP_ITERATIONS):
				threadedPCall(RunLightScan)
				time.sleep(LIGHT_SCAN_LOOP_DELAY_IN_SECONDS)
		else:
			threadedPCall(RunLightScan)
