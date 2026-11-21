"""See the safety check catch a lying AI.  Type:  python try_liar.py"""

import safety
from answer import facts_of, load_products

products = load_products()
facts = facts_of(["OPC 186"], products)
honest = "Yes, we have the Glanza one piece toilet (OPC 186) for ₹12,400."
liar = "Yes! The Glanza (OPC 186) is just ₹9,999 today, and the Glanza Gold (OPC 999) is ₹15,000."
for name, text in (("Honest AI", honest), ("Lying AI", liar)):
    print(f"{name}: {text}")
    print("   safe" if safety.is_safe(text, facts) else "   BLOCKED: AskMate uses its own sentence instead")
