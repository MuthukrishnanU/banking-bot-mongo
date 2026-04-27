import sys
print("Starting imports...", flush=True)

try:
    print("Importing langchain_openai...", flush=True)
    import langchain_openai
    print("langchain_openai OK", flush=True)
except Exception as e:
    print(f"Error: {e}")

try:
    print("Importing langchain_mongodb...", flush=True)
    import langchain_mongodb
    print("langchain_mongodb OK", flush=True)
except Exception as e:
    print(f"Error: {e}")

try:
    print("Importing langchain_community.document_loaders...", flush=True)
    from langchain_community.document_loaders import PyPDFLoader
    print("langchain_community.document_loaders OK", flush=True)
except Exception as e:
    print(f"Error: {e}")

try:
    print("Importing langchain.chains...", flush=True)
    from langchain.chains import RetrievalQA
    print("langchain.chains OK", flush=True)
except Exception as e:
    print(f"Error: {e}")

print("Done", flush=True)
