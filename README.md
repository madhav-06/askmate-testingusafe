# AskMate

A chat assistant for **HomeShine**, a shop that sells toilets, wash basins, kitchen sinks and taps. Customers ask things
like "Do you have a rimless toilet?" and AskMate answers from HomeShine's real product list. It never makes up a product.

## Start here

1. Press **Ctrl+Shift+B** in VS Code. Madhu starts in the terminal.
2. Click the link Madhu prints. Madhu opens beside your code.
3. Do what Madhu says, one small step at a time. Save with **Ctrl+S**, and Madhu checks your work.

If Ctrl+Shift+B does nothing, open a terminal and type `python madhu.py`.

Each task starts in the portal. Madhu helps you here, in your code.

## Run it on your laptop

```
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8001
```

Then open http://127.0.0.1:8001

## The files

| File | What it does |
|---|---|
| `main.py` | The web app: the chat page, `/api/ask` and `/healthz` |
| `answer.py` | How a reply is made: understand, find, decide, then word it |
| `catalogue.py` | Reads HomeShine's product list and cleans it |
| `search.py` | Finds the products a customer means |
| `ai.py` | Words the reply, with a real AI or AskMate's own sentences |
| `config.py` | Every setting, read from `.env` on your laptop or Render's Environment page |
| `askmate.json` | Your AskMate's name and greeting |
| `data/products_raw.csv` | The product list you start with: 35 products |
| `data/catalogue.pdf` | HomeShine's whole catalogue. You read all of it later in the project |

**The rule that never bends:** code decides what AskMate says. The AI only makes it sound natural. So every answer can
be checked, and AskMate still works when the AI is resting.
