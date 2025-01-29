import requests
from datetime import date
# import secrets


# def get_new_code_verifier() -> str:
#     token = secrets.token_urlsafe(100)
#     return token[:128]


# code_verifier = code_challenge = get_new_code_verifier()

# print(len(code_verifier))
# print(code_verifier)


CLIENT_id = "1d3beaba083f37a9a9942b68a8a6c2ed"
CLIENT_secret = "f9277eae84be4fb809ce250b42c015ed411272e2d39e6f89c570a424e2d303d5"
parameters = {
        "fields":"id,title,main_picture,alternative_titles,synopsis,genres,num_episodes,start_season,recommendations"
    }
headers = {
    "X-MAL-CLIENT-ID":f"{CLIENT_id}"
    }

response = requests.get(url="https://api.myanimelist.net/v2/anime/21",params=parameters,headers=headers)
print(response.status_code)
animes = response.json()
print(animes['recommendations'])
print(animes.id)
# "https://myanimelist.net/v1/oauth2/authorize?"

print(date.today().strftime("%B"))


def get_season(month):
    winter = ["January","Febuary","March"] 
    spring = ["April","May","June"]
    summer = ["July","August","September"]
    fall = ["October","November","December"]
    if month in winter:
        return "winter"
    elif month in spring:
        return "spring"
    elif month in summer:
        return "summer"
    else:
        return "fall"
    

# year = str(date.today().strftime("%Y"))
# season = get_season(str(date.today().strftime("%B")))
# parameters = {
#         "sort":"anime_score",
#         "limit":30
#     }
# headers = {
#     "X-MAL-CLIENT-ID":f"{CLIENT_id}"
#     }
# response = requests.get(url=f"https://api.myanimelist.net/v2/anime/season/{year}/{season}",
#                         params=parameters,headers=headers) 
# print(response.status_code)
# print(season)
# if response.status_code == 200:
#     print(response.json()['data'])