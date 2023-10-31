import os
import openai
openai.organization = "HACKRU"
openai.api_key = os.getenv("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")
openai.Model.list()


