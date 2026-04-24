"""
10 multi-turn conversations for benchmarking memory vs. no-memory agents.
Each conversation tests different memory aspects:
  - user preference recall
  - factual continuity
  - experience/episodic recall
  - semantic similarity retrieval
  - mixed contexts
"""

BENCHMARK_CONVERSATIONS = [
    # Conversation 1: Name/preference recall
    {
        "id": "conv_01",
        "name": "Name & Language Preference",
        "turns": [
            "My name is An and I prefer responses in Vietnamese.",
            "What programming languages do you recommend for a beginner?",
            "What was my name again, and what language did I say I prefer?",
        ],
        "memory_keys": ["name", "language_preference"],
        "expected_recall": ["An", "Vietnamese"],
    },
    # Conversation 2: Age and health facts
    {
        "id": "conv_02",
        "name": "Age & Health Fact Tracking",
        "turns": [
            "I'm 28 years old and I have type 2 diabetes.",
            "What foods should I generally avoid?",
            "Given my age and condition, what exercise is safe?",
        ],
        "memory_keys": ["age", "health_condition"],
        "expected_recall": ["28", "diabetes"],
    },
    # Conversation 3: Job context
    {
        "id": "conv_03",
        "name": "Professional Context Recall",
        "turns": [
            "I work as a data scientist at a healthcare startup.",
            "What Python libraries are most relevant to my field?",
            "Earlier I mentioned my job – can you recall what I do?",
        ],
        "memory_keys": ["job"],
        "expected_recall": ["data scientist", "healthcare"],
    },
    # Conversation 4: Learning preferences
    {
        "id": "conv_04",
        "name": "Learning Style Preferences",
        "turns": [
            "I prefer learning through hands-on projects rather than reading theory.",
            "How should I approach learning machine learning?",
            "Remind me – what learning style did I say I prefer?",
        ],
        "memory_keys": ["learning_style"],
        "expected_recall": ["hands-on", "projects"],
    },
    # Conversation 5: Previous topic recall
    {
        "id": "conv_05",
        "name": "Topic Continuity",
        "turns": [
            "Let's talk about LangGraph. It's a framework for building stateful agents.",
            "What are the key components of such agents?",
            "What topic did we start this conversation with?",
        ],
        "memory_keys": ["topic"],
        "expected_recall": ["LangGraph", "agents"],
    },
    # Conversation 6: Multi-fact retention
    {
        "id": "conv_06",
        "name": "Multi-fact Retention",
        "turns": [
            "My cat's name is Mochi and she's 3 years old.",
            "What are common health issues for indoor cats?",
            "What's my cat's name and age?",
        ],
        "memory_keys": ["pet_name", "pet_age"],
        "expected_recall": ["Mochi", "3"],
    },
    # Conversation 7: Location context
    {
        "id": "conv_07",
        "name": "Location & Context",
        "turns": [
            "I'm based in Hanoi, Vietnam and often deal with hot, humid weather.",
            "What clothing materials are best for this climate?",
            "What city did I say I'm from?",
        ],
        "memory_keys": ["location"],
        "expected_recall": ["Hanoi", "Vietnam"],
    },
    # Conversation 8: Technical stack
    {
        "id": "conv_08",
        "name": "Technical Stack Memory",
        "turns": [
            "Our tech stack is Python, FastAPI, PostgreSQL, and React.",
            "What are best practices for API design in this stack?",
            "What backend framework did I mention we use?",
        ],
        "memory_keys": ["tech_stack"],
        "expected_recall": ["FastAPI", "Python"],
    },
    # Conversation 9: Goal tracking
    {
        "id": "conv_09",
        "name": "Goal & Intent Tracking",
        "turns": [
            "My goal this year is to publish a research paper on NLP.",
            "What steps should I take to achieve this?",
            "What was the goal I mentioned at the start?",
        ],
        "memory_keys": ["goal"],
        "expected_recall": ["research paper", "NLP"],
    },
    # Conversation 10: Mixed context
    {
        "id": "conv_10",
        "name": "Mixed Context Synthesis",
        "turns": [
            "I'm a student at VinUniversity studying AI, and I prefer concise answers.",
            "What are the most important AI concepts I should master?",
            "Based on everything I've told you, give me a personalized study plan.",
        ],
        "memory_keys": ["university", "field", "preference"],
        "expected_recall": ["VinUniversity", "AI", "concise"],
    },
]
