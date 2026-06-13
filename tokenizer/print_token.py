import tiktoken

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
tokens = encoding.encode("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
print(tokens)

#print total tokens 
print(f"Total tokens: {len(tokens)}")