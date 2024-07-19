import gradio as gr
import openai
import requests
from dotenv import load_dotenv
import os

load_dotenv()

## Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

#function for fetching weather details
def get_current_weather(locations, unit="celsius"):
    api_key = os.getenv("WEATHER_API_KEY")
    unit_param = "metric" if unit == "celsius" else "imperial"

    temperatures = []
    weather_descriptions = []

    for location in locations:
        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units={unit_param}"
        response = requests.get(base_url)
        data = response.json()

        temperatures.append(data['main']['temp'])
        weather_descriptions.append(data['weather'][0]['description'])

    return {
        "locations": locations,
        "temperatures": temperatures,
        "weather_descriptions": weather_descriptions
    }


#Function calling schema for openai
functions = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather in given locations",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "The city names, e.g. San Francisco, Dubai, etc."
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"]
                }
            },
            "required": ["location", "unit"],
        }
    }
]

#function to call openai
def call_openai_api(messages, functions):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=functions
    )
    return response

#build the assistant
def weather_chat(user_message):
    messages=[]
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": """You are a weather bot. Answer the questions related to weather only. Else politely say no to the user.""" })
       
    response = call_openai_api(messages, functions)

    try:
        function_call = response['choices'][0]['message']['function_call']
        arguments = eval(function_call['arguments'])

        # Fetch weather data using the extracted arguments
        weather_data = get_current_weather(arguments['location'],arguments['unit'])

        # Append the function call and weather data to the messages
        messages.append({"role": "assistant", "content": None, "function_call": {"name": "get_current_weather", "arguments": str(arguments)}})
        messages.append({"role": "function", "name": "get_current_weather", "content": str(weather_data)})

        response = call_openai_api(messages, functions)

        return response['choices'][0]['message']['content']
    
    except Exception as e:
        return "Hey, I'm your weather assistant to provide weather updates. Please ask me questions related to weather."


# Define Gradio interface
iface = gr.Interface(
    fn=weather_chat,
    inputs=gr.Textbox(label="Weather Queries"),
    outputs=gr.Textbox(label="Weather Updates"),
    title = "Weather Bot",
    description = "Ask me anything about weather!"
)

# Launch the Gradio interface
iface.launch(share="True")
