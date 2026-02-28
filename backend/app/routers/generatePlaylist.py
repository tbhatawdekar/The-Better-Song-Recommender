from groq import Groq
import os

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(message):
  response = groq_client.chat.completions.create(
    messages=[
      {
        "role": "user",
        "content": message
      }
    ],
    model="groq/compound-mini"
  )
  return (response.choices[0].message.content, response.choices[0].message.executed_tools)

def visit_website(message):
  response = groq_client.chat.completions.create(
    messages=[
      {
        "role": "user",
        "content": message
      }
    ],
    model="groq/compound-mini"
  )
  return (response.choices[0].message.content, response.choices[0].message.executed_tools)


if __name__ == "__main__":
  # response, executed_tools = call_llm("What is the highest grossing movie this week?")
  # print(response)
  # print(executed_tools)
  response, executed_tools = call_llm("Summarize the key points of this page: https://tbhatawdekar.github.io/")
  print(response)