import aiohttp
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Set before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns


async def fetch_page(session, url, page):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                return (page, text)
            else:
                print(f"Failed to fetch page {page}: {response.status}")
                return (page, None)
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        return (page, None)
    
def parse_books_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    books = soup.find_all('article', class_='product_pod')
    books_data = []
    for book in books:
        title = book.h3.a['title']
        price_text = book.find('p', class_='price_color').text
        price = float(price_text.replace('£', '').strip())
        availability = book.find('p', class_='instock availability').text.strip()
        rating = book.find('p', class_='star-rating').get('class', [None, None])[1]
        books_data.append({
            'title': title,
            'price': price,
            'availability': availability,
            'rating': rating
        })

    return books_data


async def scrape_books_async(num_pages=5):
    base_url = "http://books.toscrape.com/catalogue/page-{}.html"
    books_data = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for page in range(1, num_pages + 1):
            url = base_url.format(page)
            tasks.append(fetch_page(session, url, page))
        
        pages_content = await asyncio.gather(*tasks)
        
        for page, html in pages_content:
            if html:
                books_data.extend(parse_books_from_html(html))
    
    return pd.DataFrame(books_data)


def scrape_books(num_pages=5):
    return asyncio.run(scrape_books_async(num_pages))


def clean_data(df):
    """
    Cleans and transforms the scraped DataFrame.
    - Maps textual ratings to numeric values
    - Checks for missing values
    
    Parameters:
        df (pd.DataFrame): The raw scraped DataFrame.
        
    Returns:
        pd.DataFrame: A cleaned and transformed DataFrame.
    """
    rating_map = {'One':1, 'Two':2, 'Three':3, 'Four':4, 'Five':5}
    df['numeric_rating'] = df['rating'].map(rating_map)
    
    missing_values_count = df.isnull().sum()
    print("Missing Values Count before cleanup:")
    print(missing_values_count)
    
    df = df.dropna(subset=['numeric_rating'])
    
    return df


def visualize_data(df):
    """
    Creates basic visualizations for the scraped and cleaned data.
    
    Parameters:
        df (pd.DataFrame): The cleaned DataFrame.
    """
    plt.figure(figsize=(10, 5))
    sns.histplot(df['price'], kde=True)
    plt.title("Distribution of Book Prices")
    plt.xlabel("Price")
    plt.ylabel("Count")
    plt.savefig('price_distribution.png')
    plt.close()
    
    plt.figure(figsize=(10, 5))
    sns.countplot(x='numeric_rating', hue='numeric_rating', data=df, palette='viridis', legend=False)
    plt.title("Count of Ratings")
    plt.xlabel("Rating (1-5)")
    plt.ylabel("Count")
    plt.savefig('rating_count.png')
    plt.close()

    plt.figure(figsize=(10, 5))
    sns.boxplot(x='numeric_rating', y='price', hue='numeric_rating', data=df, palette='magma', legend=False)
    plt.title("Price vs. Numeric Rating")
    plt.xlabel("Numeric Rating")
    plt.ylabel("Price")
    plt.savefig('price_vs_rating.png')
    plt.close()


def main():
    # Step 1: Scrape the data
    df = scrape_books(num_pages=5)

    # Step 2: Clean and transform the data
    df = clean_data(df)

    # Step 3: Explore the cleaned data
    print("DataFrame Head:")
    print(df.head())

    print("\nSummary Statistics on Price:")
    print(df['price'].describe())

    print("\nValue Counts for Ratings:")
    print(df['rating'].value_counts())

    # Step 4: Visualize the data
    visualize_data(df)

    # Step 5: Save the cleaned data to a CSV file
    df.to_csv('books_data.csv', index=False)
    print("Data saved to books_data.csv")


if __name__ == "__main__":
    main()
