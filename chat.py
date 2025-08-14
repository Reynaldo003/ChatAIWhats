from openai import OpenAI

OPENAI_API_KEY = "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"

client = OpenAI(api_key=OPENAI_API_KEY)

response = client.responses.create(
    model="gpt-5-mini",
    instructions="Escribe como si fueras un vendedor de autos profesional",
    input="Hola, estoy interesado en comprar un auto nuevo. ¿Qué me recomiendas?"
)

print(response.output_text)


