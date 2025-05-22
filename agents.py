""" agents.py """


def InitialQueryGen(client, openai_model_name, claim):
    """
    Input: Atomic claim
    Output: Query
    """
    with open("prompts/InitialQueryGen.txt", "r") as file:
        prompt = file.read()
    prompt = prompt.replace("{{claim}}", claim)
    #print(prompt)
    response = client.chat.completions.create(model=openai_model_name,
                                              max_completion_tokens=100,
                                              messages=[{"role": "user",
                                                         "content": prompt}])
    output = response.choices[0].message.content
    if '"' in output:
        output = output.replace('"', "")
    if "'" in output:
        output = output.replace("'", "")
    return output


def SearchRank(client, openai_model_name, search_query, result_list):
    """
    Input: search query and list of results returned
    Output: Ranking of results (filtered and there should also be a limit)
    """
    with open("prompts/SearchRank.txt", "r") as file:
        prompt = file.read()
    prompt = prompt.replace("{{search_query}}", search_query)
    prompt = prompt.replace("{{results}}", "\n".join([str(item) for item in result_list]))
    #print(prompt)
    response = client.chat.completions.create(model=openai_model_name,
                                              max_completion_tokens=100,
                                              messages=[{"role": "user",
                                                         "content": prompt}])
    output = response.choices[0].message.content
    #print(output)
    positions = output.split("|")
    positions = [int(pos) for pos in positions]
    pos_to_result = {result.position:result for result in result_list}
    return [pos_to_result[pos] for pos in positions]


def WebPageExtractor(client, openai_model_name, webpage_url, webpage_text):
    """
    Input: Text of webpage
    Output: Important parts of text
    """
    with open("prompts/WebPageExtractor.txt", "r") as file:
        prompt = file.read()
    prompt = prompt.replace("{{URL}}", webpage_url)
    prompt = prompt.replace("{{webpage_text}}", webpage_text)
    #print(prompt)
    response = client.chat.completions.create(model=openai_model_name,
                                              max_completion_tokens=2048,
                                              messages=[{"role": "user",
                                                         "content": prompt}])
    output = response.choices[0].message.content
    return output


def SelfContainedCheck(client, openai_model_name, claim, memory_bank, new_result):
    """
    Input: Claim, memory bank (list of SerperResult instances), new_result
    Output: True/False (self-contained/not self-contained)
    """
    with open("prompts/SelfContainedCheck.txt", "r") as file:
        prompt = file.read()
    prompt = prompt.replace("{{claim}}", claim)
    if len(memory_bank) > 0:
        prompt = prompt.replace("{{memory_bank}}", "\n\n".join([result.make_into_memory() for result in memory_bank]))
    else:
        prompt = prompt.replace("{{memory_bank}}", "The set is currently empty.")
    prompt = prompt.replace("{{new_result}}", new_result.make_into_memory())
    #print(prompt)
    response = client.chat.completions.create(model=openai_model_name,
                                              max_completion_tokens=10,
                                              messages=[{"role": "user",
                                                         "content": prompt}])
    output = response.choices[0].message.content.strip().lower()
    #print(output)
    mapping = lambda _output: True if _output == "yes" else False
    return mapping(output)
    

def DetHelpful(client, openai_model_name, claim, memory_bank, new_result):
    """
    Input: Claim, memory bank (list of SerperResult instances), new_result (self-contained)
    Output: True/False (helpful/not helpful)
    """
    with open("prompts/DetHelpful.txt", "r") as file:
        prompt = file.read()
    prompt = prompt.replace("{{claim}}", claim)
    if len(memory_bank) > 0:
        prompt = prompt.replace("{{memory_bank}}", "\n\n".join([result.make_into_memory() for result in memory_bank]))
    else:
        prompt = prompt.replace("{{memory_bank}}", "The set is currently empty.")
    prompt = prompt.replace("{{new_result}}", new_result.make_into_memory())
    #print(prompt)
    response = client.chat.completions.create(model=openai_model_name,
                                              max_completion_tokens=10,
                                              messages=[{"role": "user",
                                                         "content": prompt}])
    output = response.choices[0].message.content.strip().lower()
    #print(output)
    mapping = lambda _output: True if _output == "yes" else False
    return mapping(output)


def SufficientEvidence(client, openai_model_name, claim, memory_bank):
    """
    Input: Claim, memory bank (list of SerperResult instances)
    Output: True/False (sufficient/insufficient)
    """
    with open("prompts/SufficientEvidence.txt", "r") as file:
        prompt = file.read()
    prompt = prompt.replace("{{claim}}", claim)
    if len(memory_bank) > 0:
        prompt = prompt.replace("{{memory_bank}}", "\n\n".join([result.make_into_memory() for result in memory_bank]))
    else:
        prompt = prompt.replace("{{memory_bank}}", "The set is currently empty.")
    #print(prompt)
    response = client.chat.completions.create(model=openai_model_name,
                                              max_completion_tokens=10,
                                              messages=[{"role": "user",
                                                         "content": prompt}])
    output = response.choices[0].message.content.strip().lower()
    #print(output)
    mapping = lambda _output: True if _output == "yes" else False
    return mapping(output)


def Classifier(client, openai_model_name, claim, memory_bank):
    """
    Input: Claim, memory bank (list of SerperResult instances)
    Output: True/False (label)
    """
    with open("prompts/Classifier.txt", "r") as file:
        prompt = file.read()
    prompt = prompt.replace("{{claim}}", claim)
    if len(memory_bank) > 0:
        prompt = prompt.replace("{{memory_bank}}", "\n\n".join([result.make_into_memory() for result in memory_bank]))
    else:
        prompt = prompt.replace("{{memory_bank}}", "The set is currently empty.")
    #print(prompt)
    response = client.chat.completions.create(model=openai_model_name,
                                              max_completion_tokens=10,
                                              messages=[{"role": "user",
                                                         "content": prompt}])
    output = response.choices[0].message.content.strip().lower()
    #print(output)
    mapping = lambda _output: True if _output == "true" else False
    return mapping(output)


def AdditionalQueryGen(client, openai_model_name, claim, memory_bank):
    """
    Input: Claim, memory bank
    Output: Search query
    """
    with open("prompts/AdditionalQueryGen.txt", "r") as file:
        prompt = file.read()
    prompt = prompt.replace("{{claim}}", claim)
    if len(memory_bank) > 0:
        prompt = prompt.replace("{{memory_bank}}", "\n\n".join([result.make_into_memory() for result in memory_bank]))
    else:
        prompt = prompt.replace("{{memory_bank}}", "The set is currently empty.")
    #print(prompt)
    response = client.chat.completions.create(model=openai_model_name,
                                              max_completion_tokens=100,
                                              messages=[{"role": "user",
                                                         "content": prompt}])
    output = response.choices[0].message.content
    #print(output)
    if '"' in output:
        output = output.replace('"', "")
    if "'" in output:
        output = output.replace("'", "")
    return output