import google.generativeai as genai

genai.configure(api_key="AIzaSyBNXwXX-miE9ZLrRytetQdsXd9iz2KddkM")

# List available models
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")