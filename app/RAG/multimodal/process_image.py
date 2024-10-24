from llms import chain_gpt_4_vision
from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage, AIMessage
from app.database.schemas.schemas import ResourceProcessingSchema
from app.RAG.weaviate import get_resouces_collection
import base64
import os
import json

OPENAI_KEY=os.getenv("OPENAI_API_KEY")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
   api_key=OPENAI_KEY,
    # base_url="...",
    # organization="...",
    # other params...
)

def process_image(image_resource:ResourceProcessingSchema):
  resouce_collection = get_resouces_collection()
  encoded_image = encode_image(image_resource.image_path)
  prompt = [
      AIMessage(content="You are a bot that is good at analyzing images."),
      HumanMessage(content=[
          {"type": "text", "text": "You are a helpful ai assistant, describe the image and provide a detailed explanation of it, return the explanation in an array of strings to be used for vectorization, make sure to include all the details of the image and provide an decent OVERLAP of the description! NO introductino needed."},
          {
              "type": "image_url",
              "image_url": {
                  "url": f"data:image/jpeg;base64,{encoded_image}"
              },
          },
      ])
  ]
  response = llm.invoke(prompt)
  try:
    description_array = json.loads(response.content)
    try:
       resouce_collection = get_resouces_collection()
       with resouce_collection.batch as batch:
          for description in description_array:
             batch.add_object({
                        "resource_id": image_resource.id,
                        "content": description,
                        "workspace": image_resource.workspace,
                        "tags": image_resource.tags,
                        "file_path": image_resource.file_path,
                        "file_size": image_resource.file_size,
                        "file_extension": image_resource.file_extension,
                        "file_name": image_resource.name,
                        "resource_type": image_resource.resource_type,
                        }
             )
    except Exception as e:
       print(e)

  except json.JSONDecodeError:
    description_array = [response.content]




