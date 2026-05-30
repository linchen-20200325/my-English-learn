"""閱讀理解題庫(離線、不需 API)。

以閱讀本的 id 對應一組選擇題,讓「互動閱讀」從「讀過去」升級為
「讀懂了沒」——符合主動回憶(active recall)的科學學習原則。

每題格式:
    {"q": 題目, "options": [...], "answer": 正解, "explain": 解析}

view_reading() 讀完文章後渲染對應題組並即時批改。
"""

READING_QUESTIONS = {
    "morning-cafe": [
        {"q": "When does the writer pass the cafe?",
         "options": ["On the way to work every morning", "Only on weekends", "After dinner"],
         "answer": "On the way to work every morning",
         "explain": "首句：I walk past a small cafe on my way to work, every morning。"},
        {"q": "What does the owner NOT charge for?",
         "options": ["The first cup", "The second cup", "The cake"],
         "answer": "The second cup",
         "explain": "He never charges me for the second cup。"},
        {"q": "How does the cafe feel to the writer?",
         "options": ["Loud and crowded", "A small escape from the busy city", "Expensive"],
         "answer": "A small escape from the busy city",
         "explain": "It feels like a small escape from the busy city。"},
    ],
    "trip-kyoto": [
        {"q": "How did the writer feel about traveling alone BEFORE the trip?",
         "options": ["Excited", "Afraid", "Bored"],
         "answer": "Afraid",
         "explain": "I had always been afraid of going to a new country by myself。"},
        {"q": "Why did the writer go to Kyoto alone?",
         "options": ["The friends canceled at the last minute", "It was cheaper", "Work required it"],
         "answer": "The friends canceled at the last minute",
         "explain": "After my friends canceled at the last minute, I decided to go anyway。"},
        {"q": "What did the writer realize during the trip?",
         "options": ["Being alone is the same as being lonely",
                     "Being alone is not the same as being lonely",
                     "Traveling is a waste of money"],
         "answer": "Being alone is not the same as being lonely",
         "explain": "核心領悟句：being alone is not the same as being lonely。"},
    ],
    "rainy-saturday": [
        {"q": "Why is the writer staying home?",
         "options": ["It is raining outside", "It is too hot", "They are sick"],
         "answer": "It is raining outside",
         "explain": "It is raining outside, so I am staying home today。"},
        {"q": "How does the sound of rain make the writer feel?",
         "options": ["Anxious", "Calm", "Sleepy and annoyed"],
         "answer": "Calm",
         "explain": "The sound of rain makes me feel calm。"},
        {"q": "What does the writer plan to do before dinner?",
         "options": ["Go shopping", "Take a nap", "Call a friend"],
         "answer": "Take a nap",
         "explain": "I will probably take a nap before dinner。"},
    ],
    "supermarket": [
        {"q": "When does the writer usually go to the supermarket?",
         "options": ["Every Sunday morning", "Every weekday evening", "Once a month"],
         "answer": "Every Sunday morning",
         "explain": "I go to the supermarket every Sunday morning。"},
        {"q": "What deal is on the olive oil today?",
         "options": ["Half price", "Buy one, get one free", "No discount"],
         "answer": "Buy one, get one free",
         "explain": "It's on sale today — buy one, get one free。"},
        {"q": "How does the writer pay?",
         "options": ["Cash", "Credit card", "Mobile payment"],
         "answer": "Credit card",
         "explain": "I pay with my credit card and head home。"},
    ],
    "daily-routine": [
        {"q": "What time does the writer usually wake up on weekdays?",
         "options": ["Six o'clock", "Seven o'clock", "Eight o'clock"],
         "answer": "Seven o'clock",
         "explain": "I usually wake up at seven o'clock on weekdays。"},
        {"q": "How often does the writer work late?",
         "options": ["Always", "Often", "Rarely"],
         "answer": "Rarely",
         "explain": "I rarely work late because I value my free time。"},
        {"q": "What does the writer do in the evening?",
         "options": ["Go to the gym", "Cook dinner and relax with a book", "Work overtime"],
         "answer": "Cook dinner and relax with a book",
         "explain": "In the evening, I cook dinner and then relax with a book。"},
    ],
    "learning-to-cook": [
        {"q": "What could the writer NOT do a year ago?",
         "options": ["Boil an egg properly", "Drive a car", "Speak English"],
         "answer": "Boil an egg properly",
         "explain": "A year ago, I couldn't even boil an egg properly。"},
        {"q": "Why did the writer decide to learn cooking?",
         "options": ["For a competition", "Eating out was getting expensive", "A friend asked"],
         "answer": "Eating out was getting expensive",
         "explain": "I decided to learn because eating out was getting expensive。"},
        {"q": "How does the writer feel about cooking now?",
         "options": ["It's a chore", "It's their favorite way to relax", "They gave it up"],
         "answer": "It's their favorite way to relax",
         "explain": "Cooking has become my favorite way to relax after work。"},
    ],
    "why-quit-social-media": [
        {"q": "How much time was the writer spending on social media each day?",
         "options": ["About one hour", "Nearly three hours", "Six hours"],
         "answer": "Nearly three hours",
         "explain": "I had been spending nearly three hours a day scrolling。"},
        {"q": "What improved after two weeks?",
         "options": ["Their sleep", "Their salary", "Their phone battery"],
         "answer": "Their sleep",
         "explain": "After two weeks, I noticed I was sleeping better。"},
        {"q": "What was the BEST part of quitting, according to the writer?",
         "options": ["Saving money", "Getting their mind back", "Making new friends"],
         "answer": "Getting their mind back",
         "explain": "the best part was getting my mind back。"},
    ],
}


def get_questions(passage_id: str) -> list:
    """回傳指定閱讀的理解題清單;沒有則回空。"""
    return READING_QUESTIONS.get(passage_id, [])
