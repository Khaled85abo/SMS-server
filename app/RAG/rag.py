def search_and_generate(collection, query, limit=5):
    response = collection.generate.near_text(
            query=query,
            limit=limit,
            # filters=wq.Filter.by_property("runtime").less_than(100) & wq.Filter.by_property("runtime").greater_than(50),
            # prompt for every single object
            single_prompt="How can I use this item?: {description}",
            grouped_task="How can I use these items?"

        )
    return response

def search_and_generate_(collection, query, limit=5):
    #For generative search and llm response
    response = collection.generate.near_text(
        query="something to cook with",
        limit=5,
        # filters=wq.Filter.by_property("runtime").less_than(100) & wq.Filter.by_property("runtime").greater_than(50),
        # prompt for every single object
        # single_prompt="How can I use this item?: {description}",
        grouped_task="what can I do with this?: "

    )

# # the response for the grouped task will be in response.generated
# print(response.generated)
# #the return for the single prompt will be in object.generated
# for o in response.objects:
#     print("-------------")
#     print("Name:", o.properties['name'])
#     print("Description:", o.properties['description'])
#     print(o.generated)


