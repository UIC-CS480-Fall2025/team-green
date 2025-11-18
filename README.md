# Team Green Fall CS480 Final Project
Maaz, Andrew, and Elliot's implementation for the Fall 2025 CS480 Final Project.

### Project Summary
This project reads PDF files from a predetermined corpus and converts the text in to embeddings. Then it uses these embeddings to prompt an LLM front-end to respond to user 
queries based on the embeddings given.

## Document Preparation
- First we convert pdf files in to txt files (via pdfminer.six).
- Then we chunk the large, raw text in to fixed sized chunks.
- After converting all the PDFs into chunks, we then use an exisiting embedding model from HuggingFace to convert chunks to embeddings.

EX from TA Demo:
```
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")  # 384-dim
emb_matrix = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
```

## Create Vector Database
- We store the newly created embdeddings into a FAISS vector database, in memory.
- We use these embeddings to build a flat index, as well as an HSNW index.

## Query the LLM
- We accept a user query via command line and convert it in to an embedding. We then use our vectorDB index to find the top K most relevant chunks. We have chosen our default K to be 5, after some testing.
- We inject these fetched embeddings in to the LLM prompt alongside the original user query.
- Instruct LLM to answer the users query using these embeddings.

## Database Application
- Wrap the Ollama LLM in a full app with a basic GUI, supporting user sign up and log in.
- Implement CRUD operations on our relational database component.

# Project Checklist
| Project Step               | Status | Location          |
|----------------------------|:------:|-------------------|
| Document Preparation       |   <ul><li>- [x] </li></ul> | pdf_helper.py     |
| Vector Database            |   <ul><li>- [x] </li></ul>| answer_queries.py |
| Query Large Language Model |   <ul><li>- [x] </li></ul> | answer_queries.py |
| Database Application       | <ul><li>- [ ] </li></ul>   |                   |

# Deliverables
1. Text Chunking
- pdf_helper.py line 65: chunk_processed_txt
- Run `python pdf_helper.py` to create chunks directly. Or run `python answer_queries.py` which will also call it.
2. Chunk to Embedding
- answer_queries.py starting at line 56
- After we build our list of chunks, we encode our list with an existing embedding model `all-MiniLM-L6-v2`.
- model.encode returns a tuple of (chunk count, embedding dimensions), we use the dimensions to build our FAISS index with cosine similarity approximation.
3. Vector Storage:
- answer_queries.py line 59: This is where we build our flat index.
- This index is used in `search` starting on line 64 in answer_queries.py to fetch the top K nearest neighbors to the query embedding.

# Set Up Instructions
Project Set Up
1. `git clone git@github.com:UIC-CS480-Fall2025/team-green.git` via SSH
2. `cd team-green`
3. `python3 -m venv ./venv`
4. `source ./venv/bin/activate`
5. `pip install -r requirements.txt`
   
Ollama Set Up:
1. `curl -fsSL https://ollama.com/install.sh | sh`
2. `ollama --version`
3. `ollama pull llama3`

Run `python answer_queries.py` in your terminal. Note that embedding performance is significantly better on machines with CUDA installed.


# Sample Program Run
```
What would you like to know about? Answer with "X" or nothing to exit.  
->Tell me about the future of waste management in Texas.

Top matches:  
[4] score=0.819  
Q U A L I T Y Municipal Solid Waste in Texas: A Year in Review 2024 Data Summary and...  
---  
[5] score=0.818  
Waste in Texas: A Year in Review COG 18: Alamo Area Council of Governments—Processing Facility Locations September 2025 • Page...  
---  
[5] score=0.369  
23 September 2025 • Page 72 TCEQ AS-187/25 • Municipal Solid Waste in Texas: A Year in Review September 2025...  
---  
[4] score=0.367  
Waste in Texas: A Year in Review September 2025 ● Page 76 TCEQ AS-187/25 • Municipal Solid Waste in Texas:...  
---  
[3] score=0.357  
September 2025 • Page 67 TCEQ AS-187/25 • Municipal Solid Waste in Texas: A Year in Review COG 19: South...  
---  
[2] score=0.353  
September 2025 • Page 53 TCEQ AS-187/25 • Municipal Solid Waste in Texas: A Year in Review COG 10: Concho...  
---  
[1] score=0.349  
September 2025 ● Page 103 TCEQ AS-187/25 • Municipal Solid Waste in Texas: A Year in Review COG 18: Alamo...  
---  

Thinking...  

Based on the provided context, which appears to be a report on municipal solid waste management in Texas for 2024 and 2025, I can provide some insights on the future of Texas waste management.  

The reports highlight various trends and statistics on municipal solid waste (MSW) generation, disposal methods, and processing facilities in Texas. While there is no explicit mention of long-term projections or goals for the future, we can draw some inferences based on national and international trends in waste management.  

In recent years, there has been a growing emphasis on sustainable waste management practices, including:  

1. Increased recycling: As the public becomes more aware of environmental concerns, there may be an upward trend in recycling rates across Texas.  
2. Waste reduction: Efforts to minimize waste generation through education, consumer behavior change, and business practices innovation are likely to continue.  
3. Composting: Organic waste composting is gaining popularity, and we can expect this trend to persist, especially as cities like Austin and Houston aim to divert more organic waste from landfills.  
4. Alternative disposal methods: Technologies like gasification, pyrolysis, and anaerobic digestion may become more prevalent in Texas, offering cleaner and more efficient waste treatment options.  
5. Increased focus on end-of-life management: As the public becomes more aware of the environmental impact of electronic waste (e-waste) and other hazardous materials, we can expect to see more emphasis on responsible disposal and recycling practices for these materials.  

To support these trends and achieve a more sustainable future in Texas waste management:  

1. Collaboration between governments, industry stakeholders, and consumers will be crucial.  
2. Education and awareness campaigns can help promote best practices in waste reduction, recycling, and proper disposal methods.  
3. Incentivizing innovative technologies and infrastructure investments can drive progress toward more efficient and environmentally friendly waste management solutions.  
4. Developing a circular economy approach, where materials are kept in use for as long as possible, will be essential to minimizing waste generation and environmental impact.  

While the reports do not provide explicit projections for the future of Texas waste management, these trends and recommendations offer a glimpse into what might be on the horizon.  

What would you like to know about? Answer with "X" or nothing to exit.  
->X
```