from app.services.rag.pipeline import retrieve_for_query

query = "What is EcoLens project?"

result = retrieve_for_query(query, top_k=5, min_similarity=0.65)

print("QUERY:", result["query"])
print("\nCONTEXT:\n")
print(result["context"])

print("\nRAW CHUNKS:\n")
for i, chunk in enumerate(result["chunks"], start=1):
    print(f"{i}. score={chunk.similarity:.4f} source={chunk.source}")