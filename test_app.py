# test_scraper.py
import pytest
import pandas as pd
from app import parse_books_from_html, clean_data, scrape_books_async

sample_html = """
<html>
<head><title>Test Books</title></head>
<body>
    <article class="product_pod">
        <h3><a title="Book A"></a></h3>
        <p class="price_color">£23.88</p>
        <p class="instock availability">In stock</p>
        <p class="star-rating Three"></p>
    </article>
    <article class="product_pod">
        <h3><a title="Book B"></a></h3>
        <p class="price_color">£17.50</p>
        <p class="instock availability">In stock</p>
        <p class="star-rating Five"></p>
    </article>
</body>
</html>
"""

def test_parse_books_from_html():
    books = parse_books_from_html(sample_html)
    assert isinstance(books, list)
    assert len(books) == 2
    assert books[0]['title'] == 'Book A'
    assert books[1]['price'] == 17.50
    assert books[1]['rating'] == 'Five'

def test_clean_data():
    raw = pd.DataFrame([
        {"title": "Book A", "price": 10.0, "availability": "In stock", "rating": "Three"},
        {"title": "Book B", "price": 15.0, "availability": "In stock", "rating": "Five"},
        {"title": "Book C", "price": 8.0, "availability": "In stock", "rating": "Unknown"}
    ])
    cleaned = clean_data(raw)
    assert 'numeric_rating' in cleaned.columns
    assert cleaned.shape[0] == 2  # "Unknown" should be dropped
    assert cleaned['numeric_rating'].tolist() == [3, 5]

@pytest.mark.asyncio
async def test_scrape_books_async_one_page(monkeypatch):
    async def mock_fetch_page(session, url, page):
        return (page, sample_html)

    from app import fetch_page
    monkeypatch.setattr("app.fetch_page", mock_fetch_page)

    df = await scrape_books_async(num_pages=1)
    assert not df.empty
    assert list(df.columns) == ['title', 'price', 'availability', 'rating']
