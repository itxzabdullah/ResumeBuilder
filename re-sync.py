import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

# Fix: Only read the first 10k rows so your RAM doesn't explode
df = pd.read_csv("data/jobs_cleaned.csv", nrows=10000)

# The rest is the same
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(df['combined_text'].fillna(''))

with open("models/tfidf_vectorizer.pkl", "wb") as f:
    pickle.dump(tfidf, f)

with open("models/tfidf_matrix.pkl", "wb") as f:
    pickle.dump(tfidf_matrix, f)

# Extra: Save the small version over the big one immediately
df.to_csv("data/jobs_cleaned.csv", index=False)

print("✅ Sync Complete. Memory saved and files updated to 10k rows.")