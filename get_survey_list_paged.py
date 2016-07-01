from auth import auth_key, api_key
import requests
import json
import csv
import unicodedata

#setup the connection to the API
client = requests.session()
client.headers = {
    "Authorization": "bearer %s" % auth_key,
    "Content-Type": "application/json",
}
client.params = {
    "api_key": api_key
}
HOST = "https://api.surveymonkey.net"
SURVEY_LIST_ENDPOINT = "/v2/surveys/get_survey_list"

uri = "%s%s" % (HOST, SURVEY_LIST_ENDPOINT)

#declarations
data = {}
survey_list = []
current_page = 1

#loop through the surveys and store the survey_id's in an array
while True:
    # set the page of surveys to retrieve
    data["page"] = current_page
    response = client.post(uri, data=json.dumps(data))
    response_json = response.json()
    for survey in response_json["data"]["surveys"]:
        survey_list.append(survey)

    # if the number of surveys returned equals the page size,
    # there could still be surveys to retrieve
    if len(response_json["data"]["surveys"]) == response_json["data"]["page_size"]:
        current_page += 1
    else:
        # we have finished retrieving all surveys
        break
response.connection.close()

#setup connection to the API to pull details
detail_client = requests.session()
detail_client.headers = {
    "Authorization": "bearer %s" % auth_key,
    "Content-Type": "application/json",
}
detail_client.params = {
    "api_key": api_key
}

SURVEY_DETAIL_ENDPOINT = "/v2/surveys/get_survey_details"
detail_uri = "%s%s" % (HOST, SURVEY_DETAIL_ENDPOINT)

survey_data = {}
questions = []
answers = []
#survey_title = []
survey_title = {}

survey = survey_list[0]
#for now make sure we're working with the same survey_id
for s in survey_list:
    if s["survey_id"] == "76683626":
        survey = s

survey_id = survey["survey_id"]
survey_data = {"survey_id": survey_id}

detail_response = detail_client.post(detail_uri, data=json.dumps(survey_data))
detail_response_json = detail_response.json()

#get all the survey header data
survey_title["text"] = detail_response_json["data"]["title"]["text"]
survey_title["enabled"] = detail_response_json["data"]["title"]["enabled"]
survey_title["survey_id"] = detail_response_json["data"]["survey_id"]
survey_title["date_created"] = detail_response_json["data"]["date_created"]
survey_title["question_count"] = detail_response_json["data"]["question_count"]
survey_title["date_modified"] = detail_response_json["data"]["date_modified"]
survey_title["num_responses"] = detail_response_json["data"]["num_responses"]

for page in detail_response_json["data"]["pages"]:
    for question in page["questions"]:
        #capture the questions
        quest = {}
        quest["survey_id"] = detail_response_json["data"]["survey_id"]
        quest["name"] = question["type"]["subtype"]
        quest["subtype"] = question["type"]["subtype"]
        quest["family"] = question["type"]["family"]
        quest["position"] = question["position"]
        quest["question_id"] = question["question_id"]
        quest["heading"] = question["heading"]
        questions.append(quest)

        for answer in question["answers"]:
            #capture the answers
            ans = {}
            ans = answer
            ans["question_id"] = question["question_id"]
            answers.append(ans)

#convert the survey_title data to CSV file
f = csv.writer(open("surveys.csv", "wb+"))
#write CSV header
f.writerow(["text", "survey_id", "enabled", "question_count", "date_created", "date_modified", "num_responses"])
title = survey_title["text"]
survey_title["text"] = unicodedata.normalize("NFKD", title).encode('ASCII', 'ignore')
f.writerow([survey_title["text"], survey_title["survey_id"], survey_title["enabled"], survey_title["question_count"], survey_title["date_created"], survey_title["date_modified"], survey_title["num_responses"]])

#convert the questions data to CSV file
f = csv.writer(open("questions.csv", "wb+"))
#write a header
f.writerow(["name", "family", "subtype", "position", "survey_id", "heading", "question_id"])
for question in questions:
    title = question["heading"]
    question["heading"] = unicodedata.normalize("NFKD", title).encode('ASCII', 'ignore')
    f.writerow([question["name"], question["family"], question["subtype"], question["position"], question["survey_id"], question["heading"], question["question_id"]])

#convert the answers data to CSV file
f = csv.writer(open("answers.csv", "wb+"))
#write a header
f.writerow(["weight", "text", "visible", "position", "question_id", "type", "answer_id"])
for answer in answers:
    title = answer["text"]
    answer["text"] = unicodedata.normalize("NFKD", title).encode('ASCII', 'ignore')
    if 'weight' not in answer:
        answer["weight"] = ""
    if 'position' not in answer:
        answer["position"] = ""
    f.writerow([answer["weight"], answer["text"], answer["visible"], answer["position"], answer["question_id"], answer["type"], answer["answer_id"]])

detail_response.connection.close()

